"""
Verify local file service functionality
Run from project root: uv run python verify_local_files.py
"""

from services.local_file_service import get_file_service


def verify_local_file_service():
    """Verify local file service can perform all operations"""
    
    print("=" * 60)
    print("Local File Service Verification")
    print("=" * 60)
    
    try:
        # Initialize service
        print("\n1. Initializing local file service...")
        file_service = get_file_service()
        print(f"   ✅ Service initialized at {file_service.storage_path.absolute()}")
        
        # Test file upload
        print("\n2. Testing file upload...")
        test_content = b"This is a test file for RapidResolve local storage"
        test_filename = "test_file.txt"
        
        upload_result = file_service.upload_ticket_attachment(
            file_data=test_content,
            original_filename=test_filename,
            ticket_id=999,
            attachment_type="test"
        )
        print(f"   ✅ File uploaded: {upload_result['r2_key']}")
        print(f"      Size: {upload_result['file_size']} bytes")
        print(f"      Content-Type: {upload_result['content_type']}")
        test_file_key = upload_result['r2_key']
        
        # Test file metadata
        print("\n3. Testing file metadata retrieval...")
        metadata = file_service.get_file_metadata(test_file_key)
        print(f"   ✅ Metadata retrieved")
        print(f"      Content-Type: {metadata['content_type']}")
        print(f"      Size: {metadata['content_length']} bytes")
        print(f"      Last Modified: {metadata['last_modified']}")
        
        # Test file download
        print("\n4. Testing file download...")
        downloaded_content = file_service.download_file(test_file_key)
        if downloaded_content == test_content:
            print(f"   ✅ File downloaded and content matches")
        else:
            print(f"   ⚠️  File downloaded but content doesn't match")
        
        # Test file listing
        print("\n5. Testing file listing...")
        files = file_service.list_ticket_files(ticket_id=999)
        print(f"   ✅ Listed {len(files)} file(s) for ticket 999")
        for file in files:
            print(f"      - {file['key']} ({file['size']} bytes)")
        
        # Test file validation
        print("\n6. Testing file validation...")
        valid_image = file_service.validate_file_type("test.jpg", [".jpg", ".png"])
        invalid_image = file_service.validate_file_type("test.exe", [".jpg", ".png"])
        print(f"   ✅ Type validation: test.jpg = {valid_image}, test.exe = {invalid_image}")
        
        valid_size = file_service.validate_file_size(1024 * 1024)  # 1MB
        invalid_size = file_service.validate_file_size(100 * 1024 * 1024)  # 100MB
        print(f"   ✅ Size validation: 1MB = {valid_size}, 100MB = {invalid_size}")
        
        # Test storage stats
        print("\n7. Testing storage statistics...")
        stats = file_service.get_storage_stats()
        print(f"   ✅ Storage stats retrieved")
        print(f"      Total objects: {stats.get('total_objects', 0)}")
        print(f"      Total size: {stats.get('total_size_mb', 0)} MB")
        
        # Test batch upload
        print("\n8. Testing batch upload...")
        batch_files = [
            {
                'data': b"Test file 1",
                'filename': "batch_test_1.txt",
                'attachment_type': "test"
            },
            {
                'data': b"Test file 2",
                'filename': "batch_test_2.txt",
                'attachment_type': "test"
            }
        ]
        batch_results = file_service.batch_upload(batch_files, ticket_id=999)
        successful = sum(1 for r in batch_results if r['status'] == 'success')
        print(f"   ✅ Batch upload: {successful}/{len(batch_files)} successful")
        
        # Cleanup: delete test files
        print("\n9. Cleaning up test files...")
        deleted_count = 0
        for file in file_service.list_ticket_files(ticket_id=999):
            if file_service.delete_file(file['key']):
                deleted_count += 1
        print(f"   ✅ Deleted {deleted_count} test file(s)")
        
        print("\n" + "=" * 60)
        print("✅ Local file service verification complete!")
        print("=" * 60)
        print(f"\n📁 Storage location: {file_service.storage_path.absolute()}")
        print("💡 All files are stored locally - no cloud costs!")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Local file service verification failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_local_file_service()