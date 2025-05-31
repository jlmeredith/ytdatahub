#!/usr/bin/env python3
"""
Test script to verify video duplicate field fixes are working correctly.
This tests:
1. Video CANONICAL_FIELD_MAP has no duplicate mappings
2. Video database schema has no duplicate columns
3. Video data collection and storage works properly
"""

import sys
import os
sys.path.append('/Users/jamiemeredith/Projects/ytdatahub')

from src.database.video_repository import VideoRepository, CANONICAL_FIELD_MAP
from src.database.sqlite import SQLiteSetup
from src.utils.video_processor import process_video_data
import tempfile

def test_canonical_field_map():
    """Test that CANONICAL_FIELD_MAP has no duplicate values (API field names)"""
    print("🔍 Testing Video CANONICAL_FIELD_MAP for duplicate values...")
    
    api_fields = list(CANONICAL_FIELD_MAP.values())
    unique_api_fields = set(api_fields)
    
    if len(api_fields) != len(unique_api_fields):
        duplicates = {}
        for field in api_fields:
            if api_fields.count(field) > 1:
                duplicates[field] = [k for k, v in CANONICAL_FIELD_MAP.items() if v == field]
        
        print(f"❌ FAILED: Found duplicate API field mappings:")
        for api_field, db_columns in duplicates.items():
            print(f"   API field '{api_field}' maps to DB columns: {db_columns}")
        return False
    else:
        print(f"✅ PASSED: No duplicate API field mappings found")
        print(f"   Total mappings: {len(CANONICAL_FIELD_MAP)}")
        return True

def test_video_database_schema():
    """Test that video table schema has no duplicate columns"""
    print("\n🔍 Testing Video database schema for duplicate columns...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        # Initialize database
        db_setup = SQLiteSetup(temp_db_path)
        db_setup.initialize_database()
        
        # Get video table schema
        import sqlite3
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(videos)")
        columns = cursor.fetchall()
        conn.close()
        
        column_names = [col[1] for col in columns]  # col[1] is column name
        unique_columns = set(column_names)
        
        print(f"   Video table columns: {len(column_names)}")
        print(f"   Unique columns: {len(unique_columns)}")
        
        if len(column_names) != len(unique_columns):
            duplicates = [col for col in column_names if column_names.count(col) > 1]
            print(f"❌ FAILED: Found duplicate columns: {set(duplicates)}")
            return False
        else:
            print("✅ PASSED: No duplicate columns found")
            
            # Check for expected columns
            expected_columns = [
                'youtube_id', 'kind', 'etag', 'snippet_title', 'snippet_description', 
                'snippet_channel_id', 'snippet_channel_title', 'published_at'
            ]
            
            missing_columns = [col for col in expected_columns if col not in column_names]
            unexpected_legacy = ['channel_id', 'title', 'description']  # These should be removed
            found_legacy = [col for col in unexpected_legacy if col in column_names]
            
            if missing_columns:
                print(f"⚠️  WARNING: Missing expected columns: {missing_columns}")
            if found_legacy:
                print(f"❌ FAILED: Found legacy duplicate columns that should be removed: {found_legacy}")
                return False
            else:
                print("✅ PASSED: Legacy duplicate columns properly removed")
                
            return True
            
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_db_path)
        except:
            pass

def test_video_data_processing():
    """Test that video data processing handles kind and etag correctly"""
    print("\n🔍 Testing Video data processing for kind/etag extraction...")
    
    # Sample video data similar to YouTube API response
    sample_videos = [
        {
            'id': 'test_video_1',
            'kind': 'youtube#video',
            'etag': 'test_etag_123',
            'snippet': {
                'title': 'Test Video 1',
                'description': 'Test description',
                'channelId': 'UC123',
                'publishedAt': '2023-01-01T00:00:00Z'
            },
            'statistics': {
                'viewCount': '1000',
                'likeCount': '50',
                'commentCount': '10'
            }
        },
        {
            'id': 'test_video_2',
            'kind': 'youtube#video',
            'etag': 'test_etag_456',
            'snippet': {
                'title': 'Test Video 2',
                'description': 'Another test',
                'channelId': 'UC456',
                'publishedAt': '2023-01-02T00:00:00Z'
            }
        }
    ]
    
    # Process the video data
    processed_videos = process_video_data(sample_videos)
    
    # Check that kind and etag are preserved
    success = True
    for i, video in enumerate(processed_videos):
        if 'kind' not in video or video['kind'] != f'youtube#video':
            print(f"❌ Video {i}: Missing or incorrect kind field")
            success = False
        if 'etag' not in video or not video['etag'].startswith('test_etag_'):
            print(f"❌ Video {i}: Missing or incorrect etag field")
            success = False
            
    if success:
        print("✅ PASSED: Video processing preserves kind and etag fields")
    
    return success

def test_video_repository_save():
    """Test that video repository can save data without field conflicts"""
    print("\n🔍 Testing Video repository save operation...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        # Initialize database and repository
        db_setup = SQLiteSetup(temp_db_path)
        db_setup.initialize_database()
        
        repo = VideoRepository(temp_db_path)
        
        # Test data with both legacy and new field formats
        test_video = {
            'youtube_id': 'test_video_123',
            'kind': 'youtube#video',
            'etag': 'test_etag_123',
            'snippet_title': 'Test Video Title',
            'snippet_description': 'Test video description',
            'snippet_channel_id': 'UC123456',
            'snippet_channel_title': 'Test Channel',
            'published_at': '2023-01-01T00:00:00Z',
            'statistics_view_count': 1000,
            'statistics_like_count': 50,
            'statistics_comment_count': 10
        }
        
        # Try to save the video
        try:
            repo.save_video(test_video)
            print("✅ PASSED: Video saved successfully without field conflicts")
            
            # Verify the video was saved correctly
            saved_videos = repo.get_all_videos()
            if len(saved_videos) > 0:
                saved_video = saved_videos[0]
                if (saved_video.get('youtube_id') == 'test_video_123' and 
                    saved_video.get('kind') == 'youtube#video' and
                    saved_video.get('etag') == 'test_etag_123'):
                    print("✅ PASSED: Video data retrieved correctly with kind and etag")
                    return True
                else:
                    print("❌ FAILED: Video data not saved/retrieved correctly")
                    return False
            else:
                print("❌ FAILED: Video not found after saving")
                return False
                
        except Exception as e:
            print(f"❌ FAILED: Error saving video: {str(e)}")
            return False
            
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_db_path)
        except:
            pass

def main():
    """Run all video fix tests"""
    print("🧪 Testing Video Duplicate Field Fixes")
    print("=" * 50)
    
    tests = [
        test_canonical_field_map,
        test_video_database_schema,
        test_video_data_processing,
        test_video_repository_save
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ FAILED: Test {test.__name__} crashed with error: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED! ({passed}/{total})")
        print("✅ Video duplicate field fixes are working correctly!")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        print("❌ Video duplicate field fixes need more work")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
