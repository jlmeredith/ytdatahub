#!/usr/bin/env python3
"""
Test script to verify the playlist duplicate field fixes work correctly.
"""

import tempfile
import os
import sys
sys.path.append('/Users/jamiemeredith/Projects/ytdatahub')

from src.database.playlist_repository import PlaylistRepository
from src.database.sqlite import SQLiteDatabase

def test_playlist_fixes():
    print("Testing playlist duplicate field fixes...")
    
    # Create a temporary database
    temp_db = tempfile.mktemp(suffix='.db')
    print(f"Using temporary database: {temp_db}")
    
    try:
        # Initialize database
        db = SQLiteDatabase(temp_db)
        db.initialize_db()
        print("✓ Database initialized successfully")
        
        # Create repository
        repo = PlaylistRepository(temp_db)
        
        # Test data that would have caused duplicate field issues before the fix
        test_playlist = {
            'id': 'PLtest123',
            'playlist_id': 'PLtest123',
            'kind': 'youtube#playlist',
            'etag': 'test_etag_123',
            'snippet': {
                'publishedAt': '2023-01-01T00:00:00Z',
                'channelId': 'UCtest456',
                'title': 'Test Playlist Title',
                'description': 'Test playlist description',
                'channelTitle': 'Test Channel Title',
                'thumbnails': {
                    'default': {'url': 'http://example.com/thumb.jpg'}
                }
            },
            'contentDetails': {
                'itemCount': 10
            },
            'status': {
                'privacyStatus': 'public'
            },
            'type': 'uploads'
        }
        
        # Store the playlist data
        result = repo.store_playlist_data(test_playlist)
        print(f"✓ Store playlist result: {result}")
        
        if not result:
            print("✗ Failed to store playlist data")
            return False
            
        # Retrieve by ID
        retrieved = repo.get_by_id('PLtest123')
        print(f"✓ Retrieved playlist: {retrieved is not None}")
        
        if retrieved:
            print(f"  - Title: {retrieved.get('snippet_title')}")
            print(f"  - Channel ID: {retrieved.get('snippet_channelId')}")
            print(f"  - Description: {retrieved.get('snippet_description')}")
            print(f"  - Item count: {retrieved.get('contentDetails_itemCount')}")
            
            # Verify no legacy duplicate fields are present
            legacy_fields = ['channel_id', 'title', 'description']
            for field in legacy_fields:
                if field in retrieved:
                    print(f"✗ ERROR: Legacy field '{field}' still present in database")
                    return False
            print("✓ No legacy duplicate fields found")
        
        # Test getting by channel ID
        channel_playlists = repo.get_by_channel_id('UCtest456')
        print(f"✓ Found {len(channel_playlists)} playlists for channel")
        
        # Test uploads playlist ID retrieval
        uploads_id = repo.get_uploads_playlist_id('UCtest456')
        print(f"✓ Uploads playlist ID: {uploads_id}")
        
        print("\n🎉 All playlist duplicate field fixes are working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(temp_db):
            os.unlink(temp_db)
            print(f"✓ Cleaned up temporary database")

if __name__ == "__main__":
    success = test_playlist_fixes()
    sys.exit(0 if success else 1)
