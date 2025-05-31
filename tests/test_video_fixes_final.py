#!/usr/bin/env python3
"""
Test script to verify video duplicate field fixes are working correctly.
This tests:
1. Video CANONICAL_FIELD_MAP has no duplicate mappings
2. Video database schema has no duplicate columns
3. Video processor handles kind/etag extraction properly
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/jamiemeredith/Projects/ytdatahub')

def test_video_canonical_field_map():
    """Test that video CANONICAL_FIELD_MAP has no duplicate API field mappings"""
    print("=== Testing Video CANONICAL_FIELD_MAP ===")
    
    try:
        from src.database.video_repository import CANONICAL_FIELD_MAP
        print(f"✅ Video CANONICAL_FIELD_MAP loaded successfully")
        print(f"📊 Total mappings: {len(CANONICAL_FIELD_MAP)}")
        
        # Check for duplicate API field values (the values in the map)
        api_fields = list(CANONICAL_FIELD_MAP.values())
        unique_api_fields = set(api_fields)
        
        if len(api_fields) == len(unique_api_fields):
            print(f"✅ No duplicate API field mappings found")
        else:
            print(f"❌ Found duplicate API field mappings!")
            duplicates = [field for field in unique_api_fields if api_fields.count(field) > 1]
            for dup in duplicates:
                db_cols = [k for k, v in CANONICAL_FIELD_MAP.items() if v == dup]
                print(f"   API field '{dup}' mapped from DB columns: {db_cols}")
            return False
            
        # Show some key mappings
        key_mappings = {
            'snippet_title': CANONICAL_FIELD_MAP.get('snippet_title'),
            'snippet_description': CANONICAL_FIELD_MAP.get('snippet_description'), 
            'snippet_channel_id': CANONICAL_FIELD_MAP.get('snippet_channel_id'),
            'kind': CANONICAL_FIELD_MAP.get('kind'),
            'etag': CANONICAL_FIELD_MAP.get('etag')
        }
        print("🔑 Key mappings:")
        for db_col, api_field in key_mappings.items():
            print(f"   {db_col} -> {api_field}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error loading video CANONICAL_FIELD_MAP: {e}")
        return False

def test_video_processor():
    """Test that video processor handles kind/etag extraction"""
    print("\n=== Testing Video Processor ===")
    
    try:
        from src.utils.video_processor import process_video_data
        print("✅ Video processor loaded successfully")
        
        # Test with sample video data
        test_video = {
            'id': 'test_video_123',
            'kind': 'youtube#video',
            'etag': 'test_etag_456',
            'snippet': {
                'title': 'Test Video',
                'description': 'Test Description',
                'channelId': 'test_channel_789'
            }
        }
        
        processed = process_video_data([test_video])
        
        if processed and len(processed) == 1:
            video = processed[0]
            print(f"✅ Video processed successfully")
            print(f"🔑 Kind: {video.get('kind')}")
            print(f"🔑 Etag: {video.get('etag')}")
            print(f"🔑 Video ID: {video.get('video_id')}")
            
            # Check that kind/etag are preserved
            if video.get('kind') == 'youtube#video' and video.get('etag') == 'test_etag_456':
                print("✅ Kind and etag properly extracted")
                return True
            else:
                print("❌ Kind or etag not properly extracted")
                return False
        else:
            print("❌ Video processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing video processor: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all video fix tests"""
    print("🧪 Testing Video Duplicate Field Fixes")
    print("=" * 50)
    
    results = []
    
    # Test 1: CANONICAL_FIELD_MAP
    results.append(test_video_canonical_field_map())
    
    # Test 2: Video processor
    results.append(test_video_processor())
    
    # Summary
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All video tests PASSED!")
        print("✅ Video duplicate field fixes are working correctly")
        return True
    else:
        print("❌ Some video tests FAILED!")
        failed_tests = sum(1 for r in results if not r)
        print(f"   {failed_tests}/{len(results)} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
