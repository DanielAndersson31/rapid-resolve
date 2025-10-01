import os
import hashlib
import mimetypes
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LocalFileService:
    """
    Local file storage service with same interface as R2FileService.
    Stores files in local directory structure for development/demo purposes.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize local file service.
        
        Args:
            storage_path: Base directory for file storage (uses settings.storage_path if not provided)
        """
        if storage_path is None:
            storage_path = settings.storage_path
            
        self.storage_path = Path(storage_path)
        self.metadata_path = Path(storage_path) / ".metadata"
        
        # Create storage directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Local file service initialized at {self.storage_path.absolute()}")
    
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
            
            # Create local path structure
            relative_path = f"tickets/{ticket_id}/interactions/{interaction_id}/{timestamp}_{file_hash}{file_extension}"
            full_path = self.storage_path / relative_path
            
            # Detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(original_filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Create directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'wb') as f:
                f.write(file_data)
            
            # Store metadata
            metadata = {
                'ticket_id': ticket_id,
                'interaction_id': interaction_id,
                'original_filename': original_filename,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'content_type': content_type,
                'file_size': len(file_data)
            }
            self._save_metadata(relative_path, metadata)
            
            logger.info(f"Uploaded media file {original_filename} for ticket {ticket_id}")
            
            return {
                'r2_key': relative_path,
                'r2_bucket': 'local',
                'r2_url': f"file://{full_path.absolute()}",
                'content_type': content_type,
                'file_size': len(file_data)
            }
            
        except Exception as e:
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
            
            relative_path = f"tickets/{ticket_id}/attachments/{attachment_type}/{timestamp}_{file_hash}{file_extension}"
            full_path = self.storage_path / relative_path
            
            if not content_type:
                content_type, _ = mimetypes.guess_type(original_filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(file_data)
            
            metadata = {
                'ticket_id': ticket_id,
                'attachment_type': attachment_type,
                'original_filename': original_filename,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'content_type': content_type,
                'file_size': len(file_data)
            }
            self._save_metadata(relative_path, metadata)
            
            logger.info(f"Uploaded attachment {original_filename} for ticket {ticket_id}")
            
            return {
                'r2_key': relative_path,
                'r2_bucket': 'local',
                'r2_url': f"file://{full_path.absolute()}",
                'content_type': content_type,
                'file_size': len(file_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to upload ticket attachment: {e}")
            raise
    
    def download_file(self, r2_key: str) -> bytes:
        """
        Download file from local storage.
        
        Args:
            r2_key: File path (relative to storage_path)
        
        Returns:
            Binary file data
        """
        try:
            full_path = self.storage_path / r2_key
            
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {r2_key}")
            
            with open(full_path, 'rb') as f:
                return f.read()
            
        except Exception as e:
            logger.error(f"Failed to download file {r2_key}: {e}")
            raise
    
    def get_file_metadata(self, r2_key: str) -> Dict[str, Any]:
        """
        Get file metadata from local storage.
        
        Args:
            r2_key: File path (relative to storage_path)
        
        Returns:
            Dict with content_type, content_length, last_modified, metadata
        """
        try:
            full_path = self.storage_path / r2_key
            
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {r2_key}")
            
            stat = full_path.stat()
            stored_metadata = self._load_metadata(r2_key)
            
            return {
                'content_type': stored_metadata.get('content_type', 'application/octet-stream'),
                'content_length': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'metadata': stored_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {r2_key}: {e}")
            raise
    
    def generate_presigned_url(
        self,
        r2_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate file path (presigned URLs not needed for local storage).
        
        Args:
            r2_key: File path
            expiration: Ignored for local storage
        
        Returns:
            File path as URL
        """
        full_path = self.storage_path / r2_key
        return f"file://{full_path.absolute()}"
    
    def delete_file(self, r2_key: str) -> bool:
        """
        Delete file from local storage.
        
        Args:
            r2_key: File path (relative to storage_path)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.storage_path / r2_key
            
            if full_path.exists():
                full_path.unlink()
                
                # Delete metadata
                metadata_file = self._get_metadata_path(r2_key)
                if metadata_file.exists():
                    metadata_file.unlink()
                
                logger.info(f"Deleted file {r2_key}")
                return True
            else:
                logger.warning(f"File not found for deletion: {r2_key}")
                return False
            
        except Exception as e:
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
            search_path = self.storage_path / f"tickets/{ticket_id}"
            if file_type:
                search_path = search_path / file_type
            
            if not search_path.exists():
                return []
            
            files = []
            for file_path in search_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    relative_path = file_path.relative_to(self.storage_path)
                    stat = file_path.stat()
                    
                    files.append({
                        'key': str(relative_path),
                        'size': stat.st_size,
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'public_url': f"file://{file_path.absolute()}"
                    })
            
            return files
            
        except Exception as e:
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
            total_objects = 0
            total_size = 0
            file_types = {}
            
            for file_path in self.storage_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    total_objects += 1
                    size = file_path.stat().st_size
                    total_size += size
                    
                    ext = self._get_file_extension(file_path.name)
                    if ext not in file_types:
                        file_types[ext] = {'count': 0, 'size': 0}
                    file_types[ext]['count'] += 1
                    file_types[ext]['size'] += size
            
            return {
                'total_objects': total_objects,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': file_types,
                'bucket': 'local'
            }
            
        except Exception as e:
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
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """
        Delete files older than specified days (useful for cleanup).
        
        Args:
            days_old: Delete files older than this many days
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        try:
            for file_path in self.storage_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return deleted_count
    
    # Private helper methods
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        if '.' in filename:
            return '.' + filename.split('.')[-1]
        return ''
    
    def _get_metadata_path(self, r2_key: str) -> Path:
        """Get path to metadata file for a given file"""
        # Create unique metadata filename from r2_key
        metadata_name = r2_key.replace('/', '_').replace('\\', '_') + '.json'
        return self.metadata_path / metadata_name
    
    def _save_metadata(self, r2_key: str, metadata: Dict[str, Any]):
        """Save metadata for a file"""
        metadata_file = self._get_metadata_path(r2_key)
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_metadata(self, r2_key: str) -> Dict[str, Any]:
        """Load metadata for a file"""
        metadata_file = self._get_metadata_path(r2_key)
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}


# Singleton instance
_file_service_instance: Optional[LocalFileService] = None


def get_file_service() -> LocalFileService:
    """
    Get file service singleton instance.
    Used for dependency injection in FastAPI.
    """
    global _file_service_instance
    if _file_service_instance is None:
        _file_service_instance = LocalFileService()
    return _file_service_instance