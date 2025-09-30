import boto3
import hashlib
import mimetypes
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class R2FileService:
    """
    Cloudflare R2 service for handling file uploads and management.
    Integrates with the ticketing system for multimodal content storage.
    """
    
    def __init__(self):
        """Initialize R2 client with credentials from settings"""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.r2_endpoint_url,
                aws_access_key_id=settings.cloudflare_r2_access_key,
                aws_secret_access_key=settings.cloudflare_r2_secret_key,
                region_name='auto'
            )
            self.bucket = settings.cloudflare_r2_bucket
            
            # Test connection
            self._verify_bucket_access()
            logger.info("R2 file service initialized successfully")
            
        except NoCredentialsError:
            logger.error("R2 credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize R2 service: {e}")
            raise
    
    def _verify_bucket_access(self):
        """Verify bucket exists and is accessible"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.warning(f"Bucket {self.bucket} not found, attempting to create...")
                self._create_bucket()
            else:
                raise
    
    def _create_bucket(self):
        """Create R2 bucket if it doesn't exist"""
        try:
            self.s3_client.create_bucket(Bucket=self.bucket)
            logger.info(f"Created R2 bucket: {self.bucket}")
        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    def upload_media_file(
        self,
        file_data: bytes,
        original_filename: str,
        ticket_id: int,
        interaction_id: int,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload media file associated with an interaction.
        
        Args:
            file_data: Binary file data
            original_filename: Original filename
            ticket_id: Associated ticket ID
            interaction_id: Associated interaction ID
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            Dict with r2_key, r2_bucket, r2_url, content_type, file_size
        """
        try:
            # Generate unique filename
            file_extension = self._get_file_extension(original_filename)
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            r2_key = f"tickets/{ticket_id}/interactions/{interaction_id}/{timestamp}_{file_hash}{file_extension}"
            
            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(original_filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=r2_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    'ticket_id': str(ticket_id),
                    'interaction_id': str(interaction_id),
                    'original_filename': original_filename,
                    'upload_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Uploaded media file {original_filename} for ticket {ticket_id}")
            
            return {
                'r2_key': r2_key,
                'r2_bucket': self.bucket,
                'r2_url': self._generate_public_url(r2_key),
                'content_type': content_type,
                'file_size': len(file_data)
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload media file: {e}")
            raise
    
    def upload_ticket_attachment(
        self,
        file_data: bytes,
        original_filename: str,
        ticket_id: int,
        attachment_type: str = "general",
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload general file attachment to a ticket.
        
        Args:
            file_data: Binary file data
            original_filename: Original filename
            ticket_id: Associated ticket ID
            attachment_type: Type of attachment (screenshot, log_file, manual, etc.)
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            Dict with r2_key, r2_bucket, r2_url, content_type, file_size
        """
        try:
            file_extension = self._get_file_extension(original_filename)
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            r2_key = f"tickets/{ticket_id}/attachments/{attachment_type}/{timestamp}_{file_hash}{file_extension}"
            
            if not content_type:
                content_type, _ = mimetypes.guess_type(original_filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=r2_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    'ticket_id': str(ticket_id),
                    'attachment_type': attachment_type,
                    'original_filename': original_filename,
                    'upload_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Uploaded attachment {original_filename} for ticket {ticket_id}")
            
            return {
                'r2_key': r2_key,
                'r2_bucket': self.bucket,
                'r2_url': self._generate_public_url(r2_key),
                'content_type': content_type,
                'file_size': len(file_data)
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload ticket attachment: {e}")
            raise
    
    def download_file(self, r2_key: str) -> bytes:
        """
        Download file from R2 storage.
        
        Args:
            r2_key: R2 object key
        
        Returns:
            Binary file data
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=r2_key
            )
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to download file {r2_key}: {e}")
            raise
    
    def get_file_metadata(self, r2_key: str) -> Dict[str, Any]:
        """
        Get file metadata from R2.
        
        Args:
            r2_key: R2 object key
        
        Returns:
            Dict with content_type, content_length, last_modified, metadata
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=r2_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified', '').isoformat() if response.get('LastModified') else None,
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get metadata for {r2_key}: {e}")
            raise
    
    def generate_presigned_url(
        self,
        r2_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for secure file access.
        
        Args:
            r2_key: R2 object key
            expiration: URL expiration time in seconds (default 1 hour)
        
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': r2_key
                },
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, r2_key: str) -> bool:
        """
        Delete file from R2 storage.
        
        Args:
            r2_key: R2 object key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=r2_key
            )
            logger.info(f"Deleted file {r2_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file {r2_key}: {e}")
            return False
    
    def list_ticket_files(
        self,
        ticket_id: int,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all files for a specific ticket.
        
        Args:
            ticket_id: Ticket ID
            file_type: Optional filter (interactions, attachments)
        
        Returns:
            List of file information dicts
        """
        try:
            prefix = f"tickets/{ticket_id}/"
            if file_type:
                prefix += f"{file_type}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'public_url': self._generate_public_url(obj['Key'])
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files for ticket {ticket_id}: {e}")
            return []
    
    def validate_file_type(self, filename: str, allowed_types: List[str]) -> bool:
        """
        Validate file type against allowed types.
        
        Args:
            filename: Filename to validate
            allowed_types: List of allowed extensions (e.g., ['.jpg', '.png'])
        
        Returns:
            True if valid, False otherwise
        """
        file_extension = self._get_file_extension(filename).lower()
        return file_extension in [ext.lower() for ext in allowed_types]
    
    def validate_file_size(self, file_size: int, max_size_mb: Optional[int] = None) -> bool:
        """
        Validate file size against maximum limit.
        
        Args:
            file_size: File size in bytes
            max_size_mb: Maximum size in MB (uses settings default if not provided)
        
        Returns:
            True if valid, False otherwise
        """
        max_size = (max_size_mb or settings.max_file_size_mb) * 1024 * 1024
        return file_size <= max_size
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Returns:
            Dict with total_objects, total_size_bytes, total_size_mb, file_types
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket)
            
            total_objects = response.get('KeyCount', 0)
            total_size = sum(obj['Size'] for obj in response.get('Contents', []))
            
            # Calculate by file type
            file_types = {}
            for obj in response.get('Contents', []):
                ext = self._get_file_extension(obj['Key'])
                if ext not in file_types:
                    file_types[ext] = {'count': 0, 'size': 0}
                file_types[ext]['count'] += 1
                file_types[ext]['size'] += obj['Size']
            
            return {
                'total_objects': total_objects,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': file_types,
                'bucket': self.bucket
            }
            
        except ClientError as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
    
    def batch_upload(
        self,
        files: List[Dict[str, Any]],
        ticket_id: int
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple files in batch.
        
        Args:
            files: List of dicts with 'data', 'filename', 'interaction_id' (optional), 'attachment_type' (optional)
            ticket_id: Ticket ID
        
        Returns:
            List of upload results
        """
        results = []
        
        for file_info in files:
            try:
                if 'interaction_id' in file_info:
                    result = self.upload_media_file(
                        file_data=file_info['data'],
                        original_filename=file_info['filename'],
                        ticket_id=ticket_id,
                        interaction_id=file_info['interaction_id'],
                        content_type=file_info.get('content_type')
                    )
                else:
                    result = self.upload_ticket_attachment(
                        file_data=file_info['data'],
                        original_filename=file_info['filename'],
                        ticket_id=ticket_id,
                        attachment_type=file_info.get('attachment_type', 'general'),
                        content_type=file_info.get('content_type')
                    )
                
                result['status'] = 'success'
                result['original_filename'] = file_info['filename']
                
            except Exception as e:
                result = {
                    'status': 'error',
                    'error': str(e),
                    'original_filename': file_info['filename']
                }
            
            results.append(result)
        
        return results
    
    # Private helper methods
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        if '.' in filename:
            return '.' + filename.split('.')[-1]
        return ''
    
    def _generate_public_url(self, r2_key: str) -> str:
        """
        Generate public URL for R2 object.
        Note: This assumes you have a public domain configured for your R2 bucket.
        If not, use generate_presigned_url() instead.
        """
        # This is a placeholder - replace with your actual R2 public domain
        return f"{settings.r2_endpoint_url}/{self.bucket}/{r2_key}"


# Singleton instance
_r2_service_instance: Optional[R2FileService] = None


def get_r2_service() -> R2FileService:
    """
    Get R2 service singleton instance.
    Used for dependency injection in FastAPI.
    """
    global _r2_service_instance
    if _r2_service_instance is None:
        _r2_service_instance = R2FileService()
    return _r2_service_instance