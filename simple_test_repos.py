#!/usr/bin/env python3
"""
Simple test script for repository pattern implementation.
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test database path
test_db_path = os.path.join('data', 'simple_test.sqlite')

# Remove the test database if it exists
if os.path.exists(test_db_path):
    os.remove(test_db_path)
    logger.info(f"Removed existing test database: {test_db_path}")

# Create database tables manually
def create_tables():
    conn = sqlite3.connect(test_db_path)
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
    
    conn.commit()
    conn.close()
    logger.info("Database tables created")

# Import repositories
from src.database.channel_repository import ChannelRepository
from src.database.video_repository import VideoRepository
from src.database.comment_repository import CommentRepository
from src.database.location_repository import LocationRepository

# Create tables
create_tables()

# Initialize repositories
channel_repo = ChannelRepository(test_db_path)
video_repo = VideoRepository(test_db_path)
comment_repo = CommentRepository(test_db_path)
location_repo = LocationRepository(test_db_path)

logger.info("Repositories initialized")

# Create a test channel
conn = sqlite3.connect(test_db_path)
cursor = conn.cursor()
cursor.execute('''
INSERT INTO channels (youtube_id, title, subscriber_count, video_count, view_count, description, uploads_playlist_id)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('UC123456789', 'Test Channel', 1000, 10, 50000, 'Test channel description', 'PL123456789'))
conn.commit()

# Get the channel ID
cursor.execute("SELECT id FROM channels WHERE youtube_id = ?", ('UC123456789',))
channel_db_id = cursor.fetchone()[0]
logger.info(f"Created test channel with ID: {channel_db_id}")

# Create a test video
cursor.execute('''
INSERT INTO videos (youtube_id, channel_id, title, description, published_at, view_count, like_count, duration)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', ('vid001', channel_db_id, 'Test Video', 'Test video description', 
      datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 500, 50, 'PT5M30S'))
conn.commit()

# Get the video ID
cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", ('vid001',))
video_db_id = cursor.fetchone()[0]
logger.info(f"Created test video with ID: {video_db_id}")

# Add a comment
comment_id = 'comment001'
cursor.execute('''
INSERT INTO comments (comment_id, video_id, text, author_display_name, published_at)
VALUES (?, ?, ?, ?, ?)
''', (comment_id, video_db_id, 'Great video!', 'User1', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
conn.commit()
logger.info(f"Added comment with ID: {comment_id}")

# Add a location
cursor.execute('''
INSERT INTO video_locations (video_id, location_type, location_name, confidence)
VALUES (?, ?, ?, ?)
''', (video_db_id, 'country', 'United States', 0.95))
conn.commit()
logger.info(f"Added location for video")

# Close connection
conn.close()

# Test repository retrieval methods
logger.info("\nTesting repository methods:")

# Test channel retrieval
channels = channel_repo.get_channels_list()
logger.info(f"Retrieved {len(channels)} channels: {channels}")

# Test video retrieval
videos = video_repo.get_videos_by_channel(channel_db_id)
logger.info(f"Retrieved {len(videos)} videos for channel")

# Test comment retrieval
comments = comment_repo.get_video_comments(video_db_id)
logger.info(f"Retrieved {len(comments)} comments for video")

# Test location retrieval
locations = location_repo.get_video_locations(video_db_id)
logger.info(f"Retrieved {len(locations)} locations for video")

logger.info("\nAll tests completed successfully")
