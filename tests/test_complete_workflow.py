#!/usr/bin/env python3
"""
Complete end-to-end test of the "Add New Channel" workflow.
This script tests the entire pipeline from channel data collection to database persistence.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Settings
from services.youtube.service_impl.core import YouTubeService
from database.channel_repository import ChannelRepository
from utils.data_collection.channel_normalizer import ChannelNormalizer

def test_complete_workflow():
    """Test the complete Add New Channel workflow"""
    print("🧪 Starting Complete Workflow Test")
    print("=" * 50)
    
    # 1. Initialize components
    print("\n1️⃣ Initializing components...")
    settings = Settings()
    youtube_service = YouTubeService()
    channel_repo = ChannelRepository()
    normalizer = ChannelNormalizer()
    
    # Test channel (same as used in debug scripts)
    test_channel_id = "UCW0gH2G-cMKAEjEkI4YhnPA"  # Rootkid
    
    print(f"   ✓ Testing with channel ID: {test_channel_id}")
    print(f"   ✓ API Key configured: {'Yes' if settings.youtube_api_key else 'No'}")
    
    # 2. Collect channel data (simulating the UI workflow)
    print("\n2️⃣ Collecting channel data...")
    try:
        # This simulates the data collection step in the UI
        raw_channel_data = youtube_service.get_channel_info(test_channel_id)
        print(f"   ✓ Raw data collected: {len(raw_channel_data)} items")
        
        # Check if we got valid data
        if not raw_channel_data or not raw_channel_data.get('items'):
            print("   ❌ No channel data returned from API")
            return False
            
        channel_item = raw_channel_data['items'][0]
        print(f"   ✓ Channel title: {channel_item.get('snippet', {}).get('title', 'Unknown')}")
        
    except Exception as e:
        print(f"   ❌ Error collecting channel data: {e}")
        return False
    
    # 3. Normalize the data (simulating the normalization step)
    print("\n3️⃣ Normalizing channel data...")
    try:
        normalized_data = normalizer.normalize_channel_data(raw_channel_data)
        print(f"   ✓ Normalized data keys: {list(normalized_data.keys())}")
        
        # Check key normalized fields
        key_fields = ['channel_name', 'subscribers', 'views', 'total_videos']
        for field in key_fields:
            value = normalized_data.get(field, 'NOT_FOUND')
            print(f"   ✓ {field}: {value}")
            
    except Exception as e:
        print(f"   ❌ Error normalizing data: {e}")
        return False
    
    # 4. Save to database (the critical step that was failing)
    print("\n4️⃣ Saving to database...")
    try:
        # This is the exact call that was failing in the UI
        result = youtube_service.save_channel_data(
            normalized_data, 
            "SQLite Database",  # Fixed storage type parameter
            config=None
        )
        print(f"   ✓ Save operation result: {result}")
        
    except Exception as e:
        print(f"   ❌ Error saving to database: {e}")
        return False
    
    # 5. Verify data was saved correctly
    print("\n5️⃣ Verifying saved data...")
    try:
        # Connect directly to database to verify
        db_path = Path(__file__).parent / 'data' / 'youtube_data.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Query for our test channel
            cursor.execute("""
                SELECT channel_id, channel_title, subscriber_count, view_count, video_count
                FROM channels 
                WHERE channel_id = ?
                ORDER BY created_at DESC 
                LIMIT 1
            """, (test_channel_id,))
            
            row = cursor.fetchone()
            if row:
                channel_id, title, subscribers, views, videos = row
                print(f"   ✓ Channel found in database:")
                print(f"     - ID: {channel_id}")
                print(f"     - Title: {title}")
                print(f"     - Subscribers: {subscribers}")
                print(f"     - Views: {views}")
                print(f"     - Videos: {videos}")
                
                # Check for None values (the bug we fixed)
                if title is None or subscribers is None or views is None:
                    print("   ❌ Found None values in critical fields!")
                    return False
                else:
                    print("   ✅ All critical fields have valid data!")
                    
            else:
                print("   ❌ Channel not found in database")
                return False
                
    except Exception as e:
        print(f"   ❌ Error verifying database: {e}")
        return False
    
    # 6. Test video collection (optional but important)
    print("\n6️⃣ Testing video collection...")
    try:
        videos_data = youtube_service.get_videos_for_channel(test_channel_id, max_results=5)
        if videos_data and videos_data.get('items'):
            print(f"   ✓ Collected {len(videos_data['items'])} videos")
            
            # Test saving video data
            video_save_result = youtube_service.save_videos_data(
                videos_data,
                test_channel_id,
                "SQLite Database"
            )
            print(f"   ✓ Video save result: {video_save_result}")
        else:
            print("   ⚠️ No videos found (channel might have no public videos)")
            
    except Exception as e:
        print(f"   ⚠️ Video collection error (non-critical): {e}")
    
    print("\n🎉 Complete Workflow Test PASSED!")
    print("=" * 50)
    print("✅ All components are working correctly:")
    print("   - Channel data collection ✓")
    print("   - Data normalization ✓") 
    print("   - Database persistence ✓")
    print("   - Field mapping fixes ✓")
    print("   - Storage type parameter fixes ✓")
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    sys.exit(0 if success else 1)
