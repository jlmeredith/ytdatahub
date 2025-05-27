"""
Unit tests for the repository pattern implementation.
"""
import os
import sys
import sqlite3
import unittest
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.channel_repository import ChannelRepository
from src.database.video_repository import VideoRepository
from src.database.comment_repository import CommentRepository
from src.database.location_repository import LocationRepository
from src.database.database_utility import DatabaseUtility

class TestRepositories(unittest.TestCase):
    """Test case for repository classes."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_db_path = os.path.join('data', 'test_db.sqlite')
        
        # Remove test database if it exists
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            
        self.create_test_db()
        
        # Initialize repositories
        self.channel_repo = ChannelRepository(self.test_db_path)
        self.video_repo = VideoRepository(self.test_db_path)
        self.comment_repo = CommentRepository(self.test_db_path)
        self.location_repo = LocationRepository(self.test_db_path)
        self.db_util = DatabaseUtility(self.test_db_path)
        
    def tearDown(self):
        """Clean up after test."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            
    def create_test_db(self):
        """Create test database with schema."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create the channels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT UNIQUE NOT NULL,
            title TEXT,
            subscriber_count INTEGER,
            video_count INTEGER,
            view_count INTEGER,
            description TEXT,
            custom_url TEXT,
            published_at TEXT,
            country TEXT,
            default_language TEXT,
            privacy_status TEXT,
            is_linked BOOLEAN,
            long_uploads_status TEXT,
            made_for_kids BOOLEAN,
            hidden_subscriber_count BOOLEAN,
            thumbnail_default TEXT,
            thumbnail_medium TEXT,
            thumbnail_high TEXT,
            keywords TEXT,
            topic_categories TEXT,
            fetched_at TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploads_playlist_id TEXT,
            local_thumbnail_medium TEXT,
            local_thumbnail_default TEXT,
            local_thumbnail_high TEXT,
            updated_at TEXT
        )
        ''')
        
        # Create the videos table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT UNIQUE NOT NULL,
            channel_id INTEGER,
            title TEXT,
            description TEXT,
            published_at TEXT,
            view_count INTEGER,
            like_count INTEGER,
            dislike_count INTEGER,
            favorite_count INTEGER,
            comment_count INTEGER,
            duration TEXT,
            dimension TEXT,
            definition TEXT,
            caption BOOLEAN,
            licensed_content BOOLEAN,
            projection TEXT,
            privacy_status TEXT,
            license TEXT,
            embeddable BOOLEAN,
            public_stats_viewable BOOLEAN,
            made_for_kids BOOLEAN,
            thumbnail_default TEXT,
            thumbnail_medium TEXT,
            thumbnail_high TEXT,
            tags TEXT,
            category_id INTEGER,
            live_broadcast_content TEXT,
            fetched_at TEXT,
            updated_at TEXT,
            local_thumbnail_default TEXT,
            local_thumbnail_medium TEXT,
            local_thumbnail_high TEXT,
            FOREIGN KEY (channel_id) REFERENCES channels (id)
        )
        ''')
        
        # Create the video_locations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            location_type TEXT NOT NULL,
            location_name TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            source TEXT DEFAULT 'auto',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
        )
        ''')
        
        # Create the comments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id TEXT UNIQUE NOT NULL,
            video_id INTEGER NOT NULL,
            text TEXT,
            author_display_name TEXT,
            author_profile_image_url TEXT,
            author_channel_id TEXT,
            like_count INTEGER,
            published_at TEXT,
            updated_at TEXT,
            parent_id INTEGER,
            is_reply BOOLEAN DEFAULT FALSE,
            fetched_at TEXT,
            FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES comments (id) ON DELETE CASCADE
        )
        ''')
        
        # Create the comments_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id TEXT,
            fetched_at TEXT,
            raw_comment_info TEXT
        )
        ''')
        
        # Insert test data
        # Channel
        cursor.execute('''
        INSERT INTO channels (youtube_id, title, subscriber_count, video_count, view_count, description, uploads_playlist_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('UC123456789', 'Test Channel', 1000, 10, 50000, 'Test channel description', 'PL123456789'))
        
        # Get the channel ID
        cursor.execute("SELECT id FROM channels WHERE youtube_id = ?", ('UC123456789',))
        channel_db_id = cursor.fetchone()[0]
        
        # Video
        cursor.execute('''
        INSERT INTO videos (youtube_id, channel_id, title, description, published_at, view_count, like_count, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('vid001', channel_db_id, 'Test Video', 'Test video description', 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 500, 50, 'PT5M30S'))
        
        # Get the video ID
        cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", ('vid001',))
        video_db_id = cursor.fetchone()[0]
        
        # Comment
        cursor.execute('''
        INSERT INTO comments (comment_id, video_id, text, author_display_name, published_at)
        VALUES (?, ?, ?, ?, ?)
        ''', ('comment001', video_db_id, 'Great video!', 'User1', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        # Location
        cursor.execute('''
        INSERT INTO video_locations (video_id, location_type, location_name, confidence)
        VALUES (?, ?, ?, ?)
        ''', (video_db_id, 'country', 'United States', 0.95))
        
        conn.commit()
        conn.close()
        
    def test_channel_get_by_id(self):
        """Test get_by_id method for ChannelRepository."""
        # Get channel id from database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM channels LIMIT 1")
        channel_id = cursor.fetchone()[0]
        conn.close()
        
        # Test get_by_id
        channel = self.channel_repo.get_by_id(channel_id)
        self.assertIsNotNone(channel)
        self.assertEqual(channel['youtube_id'], 'UC123456789')
        self.assertEqual(channel['title'], 'Test Channel')
        
    def test_video_get_by_id(self):
        """Test get_by_id method for VideoRepository."""
        # Get video id from database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM videos LIMIT 1")
        video_id = cursor.fetchone()[0]
        conn.close()
        
        # Test get_by_id
        video = self.video_repo.get_by_id(video_id)
        self.assertIsNotNone(video)
        self.assertEqual(video['youtube_id'], 'vid001')
        self.assertEqual(video['title'], 'Test Video')
        
    def test_comment_get_by_id(self):
        """Test get_by_id method for CommentRepository."""
        # Get comment id from database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM comments LIMIT 1")
        comment_id = cursor.fetchone()[0]
        conn.close()
        
        # Test get_by_id
        comment = self.comment_repo.get_by_id(comment_id)
        self.assertIsNotNone(comment)
        self.assertEqual(comment['comment_id'], 'comment001')
        self.assertEqual(comment['text'], 'Great video!')
        
    def test_location_get_by_id(self):
        """Test get_by_id method for LocationRepository."""
        # Get location id from database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM video_locations LIMIT 1")
        location_id = cursor.fetchone()[0]
        conn.close()
        
        # Test get_by_id
        location = self.location_repo.get_by_id(location_id)
        self.assertIsNotNone(location)
        self.assertEqual(location['location_type'], 'country')
        self.assertEqual(location['location_name'], 'United States')
        
    def test_database_utility_get_by_id(self):
        """Test get_by_id method for DatabaseUtility."""
        # For DatabaseUtility, get_by_id should always return None
        result = self.db_util.get_by_id(1)
        self.assertIsNone(result)
        
    def test_end_to_end_comment_ingestion(self):
        """Test full pipeline: insert video, store comments, verify DB and analytics."""
        # Insert a new test video
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO videos (youtube_id, title, fetched_at, updated_at) VALUES (?, ?, datetime('now'), datetime('now'))", ('test_vid_123', 'End-to-End Test Video'))
        conn.commit()
        cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", ('test_vid_123',))
        video_db_id = cursor.fetchone()[0]
        conn.close()
        # Simulate fetched comments
        comments = [
            {
                'comment_id': f'cmt_{i}',
                'comment_text': f'Test comment {i}',
                'comment_author': f'User{i}',
                'comment_published_at': '2024-01-01T00:00:00Z',
                'like_count': str(i),
                'parent_id': '',
                'is_reply': False,
                'author_profile_image_url': '',
                'author_channel_id': f'chan_{i}',
            } for i in range(5)
        ]
        # Store comments
        self.comment_repo.create_comment_ingestion_stats_table()
        self.comment_repo.store_comments(comments, video_db_id=video_db_id)
        self.comment_repo.log_comment_ingestion_stats(video_db_id, len(comments), len(comments))
        # Verify comments in DB
        stored_comments = self.comment_repo.get_video_comments(video_db_id)
        self.assertEqual(len(stored_comments), 5)
        # Verify analytics
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fetched_count, stored_count FROM comment_ingestion_stats WHERE video_id = ?", (video_db_id,))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 5)
        self.assertEqual(row[1], 5)
        
if __name__ == '__main__':
    unittest.main()
