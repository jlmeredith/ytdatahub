#!/usr/bin/env python
"""
Fix script to diagnose and repair comments storage issues in the SQLite database.
"""
import sqlite3
import os
import sys
from pathlib import Path

def diagnose_database(db_path):
    """Diagnose the state of the database tables and relationships"""
    print(f"Diagnosing database at {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file does not exist at {db_path}")
        return False
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables in database: {', '.join(tables)}")
    
    # Check channel count
    cursor.execute("SELECT COUNT(*) FROM channels")
    channel_count = cursor.fetchone()[0]
    print(f"Channel count: {channel_count}")
    
    # Check videos
    cursor.execute("SELECT COUNT(*) FROM videos")
    video_count = cursor.fetchone()[0]
    print(f"Video count: {video_count}")
    
    # Check comments
    cursor.execute("SELECT COUNT(*) FROM comments")
    comment_count = cursor.fetchone()[0]
    print(f"Comment count: {comment_count}")
    
    # Check comments schema
    cursor.execute("PRAGMA table_info(comments)")
    comment_columns = [row[1] for row in cursor.fetchall()]
    print(f"Comment table columns: {', '.join(comment_columns)}")
    
    # Check if there are any videos without comments
    cursor.execute("""
    SELECT v.id, v.youtube_id, v.title 
    FROM videos v 
    LEFT JOIN comments c ON v.id = c.video_id 
    WHERE c.id IS NULL
    """)
    videos_without_comments = cursor.fetchall()
    print(f"Videos without comments: {len(videos_without_comments)}")
    if videos_without_comments:
        for video in videos_without_comments[:5]:  # Show first 5
            print(f"  - Video ID {video[0]}: {video[1]} ({video[2]})")
    
    conn.close()
    return True

def direct_fix_missing_comments(db_path, sample_data):
    """Fix missing comments by directly inserting them into the database"""
    print(f"Attempting direct fix of comments in {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, get video IDs
    videos = sample_data.get('video_id', [])
    if not videos:
        print("ERROR: No videos in sample data")
        return False
    
    # Count total comments in sample data
    total_comments = sum(len(video.get('comments', [])) for video in videos)
    print(f"Sample data contains {len(videos)} videos with {total_comments} total comments")
    
    # For each video in the sample, find its DB ID and insert its comments
    comments_inserted = 0
    for video in videos:
        video_id = video.get('video_id')
        if not video_id:
            continue
            
        # Find the video's database ID
        cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", (video_id,))
        result = cursor.fetchone()
        if not result:
            print(f"ERROR: Could not find video {video_id} in database")
            continue
            
        video_db_id = result[0]
        print(f"Found video {video_id} with DB ID {video_db_id}")
        
        # Get comments for this video
        comments = video.get('comments', [])
        if not comments:
            print(f"Video {video_id} has no comments")
            continue
            
        print(f"Inserting {len(comments)} comments for video {video_id}")
        
        # Insert each comment
        for i, comment in enumerate(comments):
            comment_id = comment.get('comment_id')
            if not comment_id:
                comment_id = f"direct_fix_{video_db_id}_{i}"
                
            text = comment.get('comment_text', comment.get('text', ''))
            author = comment.get('comment_author', comment.get('author_display_name', ''))
            published = comment.get('comment_published_at', comment.get('published_at', ''))
            
            # Insert directly with minimal fields
            try:
                cursor.execute("""
                INSERT OR REPLACE INTO comments (
                    comment_id, video_id, text, author_display_name, published_at, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    comment_id, video_db_id, text, author, published, sample_data.get('fetched_at', '')
                ))
                comments_inserted += 1
            except Exception as e:
                print(f"Error inserting comment: {e}")
    
    # Commit and check results
    conn.commit()
    
    # Verify comments were inserted
    cursor.execute("SELECT COUNT(*) FROM comments")
    final_count = cursor.fetchone()[0]
    print(f"Final comment count: {final_count} (inserted {comments_inserted})")
    
    conn.close()
    return final_count > 0

def get_sample_data():
    """Create a simplified version of the test data"""
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

def main():
    """Main function to run the database fixes"""
    # Get database path from command line or use temporary one
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Create a temporary database for testing
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        db_path = temp_file.name
        temp_file.close()
        
        # Initialize the database schema
        from src.database.sqlite import SQLiteDatabase
        db = SQLiteDatabase(db_path)
        print(f"Created temporary database at {db_path}")
        
        # Store test data to set up the database
        sample_data = get_sample_data()
        result = db.store_channel_data(sample_data)
        print(f"Initial data storage result: {result}")
    
    # Diagnose current state
    print("\n--- Initial Database Diagnosis ---")
    diagnose_database(db_path)
    
    # Apply direct fixes
    print("\n--- Applying Direct Comment Fixes ---")
    sample_data = get_sample_data()
    direct_fix_missing_comments(db_path, sample_data)
    
    # Diagnose again to verify fixes
    print("\n--- Final Database Diagnosis ---")
    diagnose_database(db_path)
    
    print("\nFix script completed")

if __name__ == "__main__":
    main()
