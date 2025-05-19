#!/usr/bin/env python
"""
Debug script to troubleshoot comment storage in the SQLite database.
"""
import os
import sqlite3
from pathlib import Path
import tempfile
from src.database.sqlite import SQLiteDatabase
from src.utils.helpers import debug_log

def setup_test_db():
    """Create a test database and return the path"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file_path = temp_file.name
    temp_file.close()
    return temp_file_path

def create_sample_data():
    """Create sample channel data similar to what's in the tests"""
    return {
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': 1000,
        'views': 50000,
        'total_videos': 25,
        'channel_description': 'This is a test channel for unit tests',
        'playlist_id': 'PL_test_playlist',
        'published_at': '2020-01-01T12:00:00Z',
        'fetched_at': '2025-04-29T15:00:00Z',
        'video_id': [
            {
                'video_id': 'test_video_1',
                'title': 'Test Video 1',
                'video_description': 'Description for test video 1',
                'published_at': '2020-01-15T12:00:00Z',
                'views': 1000,
                'likes': 100,
                'duration': 'PT10M30S',
                'comments': [
                    {
                        'comment_id': 'comment_1_1',
                        'comment_text': 'Great video!',
                        'comment_author': 'Commenter 1',
                        'comment_published_at': '2020-01-16T12:00:00Z'
                    },
                    {
                        'comment_id': 'comment_1_2',
                        'comment_text': 'Nice content',
                        'comment_author': 'Commenter 2',
                        'comment_published_at': '2020-01-17T12:00:00Z'
                    }
                ]
            },
            {
                'video_id': 'test_video_2',
                'title': 'Test Video 2',
                'video_description': 'Description for test video 2',
                'published_at': '2020-02-15T12:00:00Z',
                'views': 2000,
                'likes': 200,
                'duration': 'PT15M45S',
                'comments': [
                    {
                        'comment_id': 'comment_2_1',
                        'comment_text': 'Interesting!',
                        'comment_author': 'Commenter 3',
                        'comment_published_at': '2020-02-16T12:00:00Z'
                    }
                ]
            }
        ]
    }

def debug_video_repository_store_comments(db_path):
    """Debug the VideoRepository.store_comments method"""
    from src.database.video_repository import VideoRepository
    
    # Create a database connection and initialize tables
    db = SQLiteDatabase(db_path)
    
    # Get the video repository
    video_repo = VideoRepository(db_path)
    
    # Create a test video in the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert a test channel
    cursor.execute('''
    INSERT INTO channels (youtube_id, title) 
    VALUES ('test_channel', 'Test Channel')
    ''')
    conn.commit()
    
    # Get the channel ID
    cursor.execute("SELECT id FROM channels WHERE youtube_id = 'test_channel'")
    channel_id = cursor.fetchone()[0]
    
    # Insert a test video
    cursor.execute('''
    INSERT INTO videos (youtube_id, channel_id, title)
    VALUES ('test_video', ?, 'Test Video')
    ''', (channel_id,))
    conn.commit()
    
    # Get the video ID
    cursor.execute("SELECT id FROM videos WHERE youtube_id = 'test_video'")
    video_id = cursor.fetchone()[0]
    
    # Create some test comments
    test_comments = [
        {
            'comment_id': 'test_comment_1',
            'comment_text': 'This is a test comment',
            'comment_author': 'Test User',
            'comment_published_at': '2025-05-18T12:00:00Z'
        },
        {
            'comment_id': 'test_comment_2',
            'comment_text': 'Another test comment',
            'comment_author': 'Another User',
            'comment_published_at': '2025-05-18T13:00:00Z'
        }
    ]
    
    # Test the store_comments method
    print(f"Testing VideoRepository.store_comments with {len(test_comments)} comments")
    result = video_repo.store_comments(test_comments, video_id, '2025-05-18T14:00:00Z')
    
    # Print the result
    print(f"store_comments result: {result}")
    
    # Check if comments were stored
    cursor.execute("SELECT COUNT(*) FROM comments WHERE video_id = ?", (video_id,))
    count = cursor.fetchone()[0]
    print(f"Number of comments in database: {count}")
    
    # Print all comments for debugging
    cursor.execute("""
    SELECT comment_id, text, author_display_name, published_at 
    FROM comments
    """)
    print("All comments in database:")
    for row in cursor.fetchall():
        print(f"  {row}")
        
    conn.close()

def debug_channel_repository_store_channel_data(db_path):
    """Debug the ChannelRepository.store_channel_data method"""
    # Create a database connection and initialize tables
    db = SQLiteDatabase(db_path)
    
    # Create sample data
    sample_data = create_sample_data()
    
    # Store the data
    print("Storing sample channel data...")
    result = db.store_channel_data(sample_data)
    
    # Print the result
    print(f"store_channel_data result: {result}")
    
    # Check what was stored
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check channels
    cursor.execute("SELECT youtube_id, title FROM channels")
    print("Channels in database:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # Check videos
    cursor.execute("SELECT youtube_id, title FROM videos")
    print("Videos in database:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # Check comments
    cursor.execute("SELECT comment_id, text FROM comments")
    print("Comments in database:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    conn.close()

def main():
    """Main function for the debug script"""
    print("Starting debug script for comment storage")
    
    # Setup a test database
    db_path = setup_test_db()
    print(f"Created test database at {db_path}")
    
    # Debug the VideoRepository
    print("\n--- Debugging VideoRepository.store_comments ---")
    debug_video_repository_store_comments(db_path)
    
    # Setup another test database for the channel repository
    db_path2 = setup_test_db()
    
    # Debug the ChannelRepository
    print("\n--- Debugging ChannelRepository.store_channel_data ---")
    debug_channel_repository_store_channel_data(db_path2)
    
    # Cleanup
    try:
        os.unlink(db_path)
        os.unlink(db_path2)
    except:
        pass
    
    print("Debug script completed")

if __name__ == "__main__":
    main()
