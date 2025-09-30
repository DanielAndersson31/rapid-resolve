"""
Verify R2 file service functionality
Run from project root: uv run python verify_r2.py

NOTE: This requires valid R2 credentials in your .env file
"""

from services.r2_service import get_r2_service
import io


def verify_r2_service():
    """Verify R2 service can connect and perform basic operations"""
    
    print("=" * 60)
    print("R2 File Service Verification")
    print("=" * 60)
    
    try:
        # Initialize service
        print("\n1. Initializing R2 service...")
        r2_service = get_r2_service()
        print("   ✅ R2 service initialized")
        
        # Test file upload
        print("\n2. Testing file upload...")
        test_content = b"This is a test file for RapidResolve"
        test_filename = "test_file.txt"
        
        try:
            upload_result = r2_service.upload_ticket_attachment(
                file_data=test_content,
                original_filename=test_filename,
                ticket_id=999,  # Test ticket ID
                attachment_type="test"
            )
            print(f"   ✅ File uploaded: {upload_result['r2_key']}")
            print(f"      Size: {upload_result['file_size']} bytes")
            print(f"      Content-Type: {upload_result['content_type']}")
            test_r2_key = upload_result['r2_key']
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            return
        
        # Test file metadata
        print("\n3. Testing file metadata retrieval...")
        try:
            metadata = r2_service.get_file_metadata(test_r2_key)
            print(f"   ✅ Metadata retrieved")
            print(f"      Content-Type: {metadata['content_type']}")
            print(f"      Size: {metadata['content_length']} bytes")
        except Exception as e:
            print(f"   ❌ Metadata retrieval failed: {e}")
        
        # Test presigned URL generation
        print("\n4. Testing presigned URL generation...")
        try:
            presigned_url = r2_service.generate_presigned_url(test_r2_key, expiration=300)
            print(f"   ✅ Presigned URL generated")
            print(f"      URL: {presigned_url[:80]}...")
        except Exception as e:
            print(f"   ❌ Presigned URL generation failed: {e}")
        
        # Test file download
        print("\n5. Testing file download...")
        try:
            downloaded_content = r2_service.download_file(test_r2_key)
            if downloaded_content == test_content:
                print(f"   ✅ File downloaded and content matches")
            else:
                print(f"   ⚠️  File downloaded but content doesn't match")
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
        
        # Test file listing
        print("\n6. Testing file listing...")
        try:
            files = r2_service.list_ticket_files(ticket_id=999)
            print(f"   ✅ Listed {len(files)} file(s) for ticket 999")
            for file in files:
                print(f"      - {file['key']} ({file['size']} bytes)")
        except Exception as e:
            print(f"   ❌ File listing failed: {e}")
        
        # Test file validation
        print("\n7. Testing file validation...")
        valid_image = r2_service.validate_file_type("test.jpg", [".jpg", ".png"])
        invalid_image = r2_service.validate_file_type("test.exe", [".jpg", ".png"])
        print(f"   ✅ Image validation: test.jpg = {valid_image}, test.exe = {invalid_image}")
        
        valid_size = r2_service.validate_file_size(1024 * 1024)  # 1MB
        invalid_size = r2_service.validate_file_size(100 * 1024 * 1024)  # 100MB
        print(f"   ✅ Size validation: 1MB = {valid_size}, 100MB = {invalid_size}")
        
        # Test storage stats
        print("\n8. Testing storage statistics...")
        try:
            stats = r2_service.get_storage_stats()
            print(f"   ✅ Storage stats retrieved")
            print(f"      Total objects: {stats.get('total_objects', 0)}")
            print(f"      Total size: {stats.get('total_size_mb', 0)} MB")
        except Exception as e:
            print(f"   ❌ Storage stats failed: {e}")
        
        # Cleanup: delete test file
        print("\n9. Cleaning up test file...")
        try:
            deleted = r2_service.delete_file(test_r2_key)
            if deleted:
                print(f"   ✅ Test file deleted")
            else:
                print(f"   ⚠️  Failed to delete test file")
        except Exception as e:
            print(f"   ❌ Cleanup failed: {e}")
        
        print("\n" + "=" * 60)
        print("✅ R2 service verification complete!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ R2 service verification failed: {e}")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Check your .env file has valid R2 credentials")
        print("2. Verify CLOUDFLARE_R2_* variables are set correctly")
        print("3. Ensure your R2 bucket exists or service can create it")
        print("=" * 60)


if __name__ == "__main__":
    verify_r2_service()