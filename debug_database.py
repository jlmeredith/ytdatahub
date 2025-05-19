"""
Script to debug database video storage and retrieval issues.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from src.database.sqlite import SQLiteDatabase
from src.database.video_repository import VideoRepository
from src.database.channel_repository import ChannelRepository

def debug_video_storage():
    """Debug video storage and retrieval issues"""
    # Path to the SQLite database file
    db_path = os.path.join(project_root, "data", "youtube_data.db")
    print(f"Using database at: {db_path}")
    
    # Create an instance of the SQLiteDatabase
    db = SQLiteDatabase(db_path)
    
    # Create a sample channel with videos
    sample_data = {
        'channel_id': 'UC_test_debug',
        'channel_name': 'Debug Test Channel',
        'subscribers': 1000,
        'views': 50000,
        'total_videos': 2,
        'channel_description': 'This is a debug test channel',
        'playlist_id': 'PL_test_debug',
        'published_at': '2020-01-01T12:00:00Z',
        'fetched_at': '2025-05-18T15:00:00Z',
        'video_id': [
            {
                'video_id': 'debug_video_1',
                'title': 'Debug Video 1',
                'video_description': 'Description for debug video 1',
                'published_at': '2020-01-15T12:00:00Z',
                'views': 1000,
                'likes': 100,
                'duration': 'PT10M30S',
                'comments': []
            },
            {
                'video_id': 'debug_video_2',
                'title': 'Debug Video 2',
                'video_description': 'Description for debug video 2',
                'published_at': '2020-02-15T12:00:00Z',
                'views': 2000,
                'likes': 200,
                'duration': 'PT15M45S',
                'comments': []
            }
        ]
    }
    
    # Store the channel data
    print("Storing sample channel data...")
    result = db.store_channel_data(sample_data)
    print(f"Store result: {result}")
    
    # Connect directly to the database to check if videos were stored
    print("\nChecking database for videos directly...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the database ID of the channel
    cursor.execute("SELECT id FROM channels WHERE youtube_id = ?", ('UC_test_debug',))
    channel_row = cursor.fetchone()
    
    if channel_row:
        channel_db_id = channel_row[0]
        print(f"Channel DB ID: {channel_db_id}")
        
        # Check if videos were stored for this channel
        cursor.execute("SELECT COUNT(*) FROM videos WHERE channel_id = ?", (channel_db_id,))
        video_count = cursor.fetchone()[0]
        print(f"Videos in database for this channel: {video_count}")
        
        if video_count > 0:
            cursor.execute("SELECT youtube_id, title FROM videos WHERE channel_id = ?", (channel_db_id,))
            videos = cursor.fetchall()
            print("\nVideos found in database:")
            for i, video in enumerate(videos):
                print(f"  {i+1}. ID: {video[0]}, Title: {video[1]}")
    
    # Retrieve the channel data using the repository
    print("\nRetrieving channel data using repository...")
    channel_data = db.get_channel_data('UC_test_debug')
    
    # Log the retrieved data
    if channel_data:
        print(f"Channel ID: {channel_data['channel_id']}")
        print(f"Channel Title: {channel_data['channel_info']['title']}")
        print(f"Number of videos: {len(channel_data['videos'])}")
        for i, video in enumerate(channel_data['videos']):
            print(f"\nVideo {i+1}:")
            print(f"  ID: {video['id']}")
            print(f"  Title: {video['snippet']['title']}")
            print(f"  Views: {video['statistics']['viewCount']}")
    else:
        print("Failed to retrieve channel data")

    # Now check the get_videos_by_channel method directly
    print("\nTesting get_videos_by_channel directly...")
    video_repo = VideoRepository(db_path)
    
    if channel_row:
        channel_db_id = channel_row[0]
        print(f"Channel DB ID: {channel_db_id}")
        
        # Inspect the SQL directly
        print("\nSQL that would be executed:")
        sql = """
            SELECT id, youtube_id, title, description, published_at, view_count, 
                   like_count, duration, thumbnail_high, caption
            FROM videos 
            WHERE channel_id = ?
        """
        print(sql)
        
        # Execute the SQL directly
        print("\nExecuting SQL directly:")
        cursor.execute(sql, (channel_db_id,))
        videos_rows = cursor.fetchall()
        print(f"Found {len(videos_rows)} videos directly")
        for i, video_row in enumerate(videos_rows):
            print(f"  {i+1}. ID: {video_row[0]}, YouTube ID: {video_row[1]}, Title: {video_row[2]}")
        
        # Now use the repository method
        print("\nUsing repository method:")
        videos = video_repo.get_videos_by_channel(channel_db_id)
        print(f"Found {len(videos)} videos using repository")
        for i, video in enumerate(videos):
            if video:
                print(f"  {i+1}. ID: {video.get('id')}, Title: {video.get('snippet', {}).get('title')}")
    
    conn.close()

if __name__ == "__main__":
    debug_video_storage()
