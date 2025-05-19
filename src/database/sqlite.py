"""
SQLite database module for the YouTube scraper application.
"""
import sqlite3
import streamlit as st
import pandas as pd
import os
from pathlib import Path

from src.utils.helpers import debug_log
from src.database.channel_repository import ChannelRepository
from src.database.video_repository import VideoRepository
from src.database.comment_repository import CommentRepository
from src.database.location_repository import LocationRepository
from src.database.database_utility import DatabaseUtility

class SQLiteDatabase:
    """SQLite database connector for the YouTube scraper application."""
    
    def __init__(self, db_path):
        """Initialize the SQLite database with the given path."""
        self.db_path = db_path
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # Initialize repository classes
        self.channel_repository = ChannelRepository(db_path)
        self.video_repository = VideoRepository(db_path)
        self.comment_repository = CommentRepository(db_path)
        self.location_repository = LocationRepository(db_path)
        self.database_utility = DatabaseUtility(db_path)
        # Initialize the database tables
        self.initialize_db()
    
    def initialize_db(self):
        """Create the necessary tables in SQLite if they don't exist"""
        debug_log("Creating SQLite tables if needed")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
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
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_channels_youtube_id ON channels(youtube_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_youtube_id ON videos(youtube_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_locations_video_id ON video_locations(video_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_locations_location ON video_locations(location_type, location_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments(parent_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_channels_id ON channels(id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_id ON videos(id)')
            
            # Commit the changes and close the connection
            conn.commit()
            conn.close()
            
            debug_log("SQLite tables created or already exist")
            return True
        except Exception as e:
            st.error(f"Error creating SQLite tables: {str(e)}")
            debug_log(f"Exception in initialize_db: {str(e)}", e)
            return False
    
    def store_channel_data(self, data):
        """Save channel data to SQLite database - delegated to ChannelRepository"""
        debug_log("SQLiteDatabase: Delegating store_channel_data to ChannelRepository")
        # Check if data contains comments before delegating
        videos = data.get('video_id', [])
        comment_count = 0
        for video in videos:
            comments = video.get('comments', [])
            comment_count += len(comments)
        debug_log(f"SQLiteDatabase: Data contains {len(videos)} videos with {comment_count} total comments")
        
        # Add debugging log to trace data flow
        result = self.channel_repository.store_channel_data(data)
        
        # Verify comments were stored
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM comments")
            stored_comments = cursor.fetchone()[0]
            debug_log(f"SQLiteDatabase: After storage, database contains {stored_comments} comments")
            conn.close()
        except Exception as e:
            debug_log(f"SQLiteDatabase: Error checking comment count: {str(e)}")
            
        return result
    
    def get_channels_list(self):
        """Get a list of all channel names from the database - delegated to ChannelRepository"""
        return self.channel_repository.get_channels_list()
    
    def get_channel_data(self, channel_identifier):
        """Get full data for a specific channel including videos, comments, and locations - delegated to ChannelRepository
        
        Args:
            channel_identifier (str): Either a YouTube channel ID (UC...) or a channel title
            
        Returns:
            dict or None: Channel data or None if not found
        """
        return self.channel_repository.get_channel_data(channel_identifier)
    
    def display_channels_data(self):
        """Display all channels from SQLite database in a Streamlit interface - delegated to ChannelRepository"""
        return self.channel_repository.display_channels_data()
    
    def display_videos_data(self):
        """Display all videos from SQLite database in a Streamlit interface - delegated to VideoRepository"""
        return self.video_repository.display_videos_data()
    
    def list_channels(self):
        """
        Get a list of all channels from the database with their IDs and titles - delegated to ChannelRepository
        
        Returns:
            list: List of tuples containing (youtube_id, title) for each channel
        """
        return self.channel_repository.list_channels()

    def clear_cache(self):
        """
        Clear any database caches or temporary data - delegated to DatabaseUtility
        
        This method:
        1. Releases any connection pools
        2. Runs VACUUM to optimize the database
        3. Clears any prepared statement caches
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.database_utility.clear_cache()

    def continue_iteration(self, channel_id, max_iterations=3, time_threshold_days=7):
        """
        Determine if data collection should continue for a given channel - delegated to DatabaseUtility
        
        Args:
            channel_id (str): The YouTube channel ID to check
            max_iterations (int): Maximum number of iterations allowed for a channel
            time_threshold_days (int): Number of days to consider for recent iterations
            
        Returns:
            bool: True if iteration should continue, False otherwise
        """
        return self.database_utility.continue_iteration(channel_id, max_iterations, time_threshold_days)

    def clear_all_data(self):
        """
        Clear all data from the database by dropping and recreating all tables - delegated to DatabaseUtility
        
        This is a destructive operation and should be used with caution,
        primarily for testing purposes.
        
        Returns:
            bool: True if successful, False otherwise
        """
        success = self.database_utility.clear_all_data()
        
        if success:
            # Recreate all tables
            success = self.initialize_db()
            
        return success

    def _get_connection(self):
        """
        Get a direct SQLite database connection - delegated to DatabaseUtility
        This is useful for performing custom queries.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        return self.database_utility.get_connection()

    def get_channel_id_by_title(self, title):
        """Get the YouTube channel ID for a given channel title - delegated to ChannelRepository"""
        return self.channel_repository.get_channel_id_by_title(title)
        
    def get_channels(self):
        """
        Get a list of all channels in the database - delegates to channel_repository.get_channels_list
        
        Returns:
            list: List of channel IDs/names
        """
        return self.channel_repository.get_channels_list()

# Keep the original functions for backward compatibility, but delegate to the class
def create_sqlite_tables():
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.initialize_db()

def save_to_sqlite(data):
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.store_channel_data(data)

def get_sqlite_channels_data():
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.display_channels_data()

def get_sqlite_videos_data():
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.display_videos_data()
