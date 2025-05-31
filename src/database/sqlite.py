"""
SQLite database module for the YouTube scraper application.
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

from src.utils.debug_utils import debug_log
from src.database.channel_repository import ChannelRepository
from src.database.video_repository import VideoRepository
from src.database.comment_repository import CommentRepository
from src.database.location_repository import LocationRepository
from src.database.database_utility import DatabaseUtility

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

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
        # Always initialize the database tables (for each DB instance)
        self.initialize_db()
    
    def initialize_db(self):
        """Create the necessary tables in SQLite if they don't exist (full schema, with historical tables for all major objects)."""
        db_file_existed = os.path.exists(self.db_path)
        if not db_file_existed:
            debug_log("Creating SQLite tables (full schema, zero state)")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Create the channels table (no duplicate fields - only normalized columns)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_title TEXT,
                uploads_playlist_id TEXT,
                subscriber_count INTEGER,
                view_count INTEGER,
                video_count INTEGER,
                kind TEXT,
                etag TEXT,
                snippet_description TEXT,
                snippet_customUrl TEXT,
                snippet_publishedAt TEXT,
                snippet_defaultLanguage TEXT,
                snippet_country TEXT,
                snippet_thumbnails_default_url TEXT,
                snippet_thumbnails_medium_url TEXT,
                snippet_thumbnails_high_url TEXT,
                statistics_hiddenSubscriberCount BOOLEAN,
                brandingSettings_channel_keywords TEXT,
                status_privacyStatus TEXT,
                status_isLinked BOOLEAN,
                status_longUploadsStatus TEXT,
                status_madeForKids BOOLEAN,
                topicDetails_topicCategories TEXT,
                localizations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            # Create the channel_history table (for full JSON/time series)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                raw_channel_info TEXT NOT NULL
            )
            ''')
            # Create the playlists table (full schema)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id TEXT PRIMARY KEY,
                type TEXT DEFAULT 'uploads',
                kind TEXT,
                etag TEXT,
                snippet_publishedAt TEXT,
                snippet_channelId TEXT,
                snippet_title TEXT,
                snippet_description TEXT,
                snippet_thumbnails TEXT,
                snippet_channelTitle TEXT,
                snippet_defaultLanguage TEXT,
                snippet_localized_title TEXT,
                snippet_localized_description TEXT,
                status_privacyStatus TEXT,
                contentDetails_itemCount INTEGER,
                player_embedHtml TEXT,
                localizations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (snippet_channelId) REFERENCES channels (channel_id)
            )
            ''')
            # Create the videos table (full public YouTube API schema for non-owners)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE NOT NULL,
                kind TEXT,
                etag TEXT,
                snippet_title TEXT,
                snippet_description TEXT,
                published_at TEXT,
                snippet_channel_id TEXT,
                snippet_channel_title TEXT,
                snippet_tags TEXT, -- JSON array
                snippet_category_id TEXT,
                snippet_live_broadcast_content TEXT,
                snippet_default_language TEXT,
                snippet_localized_title TEXT,
                snippet_localized_description TEXT,
                snippet_default_audio_language TEXT,
                -- Thumbnails (all sizes as JSON)
                snippet_thumbnails_default TEXT,
                snippet_thumbnails_medium TEXT,
                snippet_thumbnails_high TEXT,
                snippet_thumbnails_standard TEXT,
                snippet_thumbnails_maxres TEXT,
                -- contentDetails
                content_details_duration TEXT,
                content_details_dimension TEXT,
                content_details_definition TEXT,
                content_details_caption TEXT,
                content_details_licensed_content BOOLEAN,
                content_details_region_restriction_allowed TEXT, -- JSON array
                content_details_region_restriction_blocked TEXT, -- JSON array
                content_details_content_rating TEXT, -- JSON object
                content_details_projection TEXT,
                content_details_has_custom_thumbnail BOOLEAN,
                -- status
                status_upload_status TEXT,
                status_failure_reason TEXT,
                status_rejection_reason TEXT,
                status_privacy_status TEXT,
                status_publish_at TEXT,
                status_license TEXT,
                status_embeddable BOOLEAN,
                status_public_stats_viewable BOOLEAN,
                status_made_for_kids BOOLEAN,
                -- statistics
                statistics_view_count INTEGER,
                statistics_like_count INTEGER,
                statistics_comment_count INTEGER,
                -- player
                player_embed_html TEXT,
                player_embed_height INTEGER,
                player_embed_width INTEGER,
                -- topicDetails
                topic_details_topic_ids TEXT, -- JSON array
                topic_details_relevant_topic_ids TEXT, -- JSON array
                topic_details_topic_categories TEXT, -- JSON array
                -- liveStreamingDetails
                live_streaming_details_actual_start_time TEXT,
                live_streaming_details_actual_end_time TEXT,
                live_streaming_details_scheduled_start_time TEXT,
                live_streaming_details_scheduled_end_time TEXT,
                live_streaming_details_concurrent_viewers INTEGER,
                live_streaming_details_active_live_chat_id TEXT,
                -- localizations
                localizations TEXT, -- JSON object
                fetched_at TEXT,
                updated_at TEXT
            )
            ''')
            # Create the comments table (full schema)
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
            # Create the video_locations table (full schema)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                location_type TEXT NOT NULL,
                location_name TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                source TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(video_id) REFERENCES videos(id)
            )
            ''')
            # Create the videos_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                raw_video_info TEXT NOT NULL
            )
            ''')
            # Create the comments_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                raw_comment_info TEXT NOT NULL
            )
            ''')
            # Create the playlists_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                raw_playlist_info TEXT NOT NULL
            )
            ''')
            # Create the video_locations_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_locations_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                raw_location_info TEXT NOT NULL
            )
            ''')
            # Create index on channel_id
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_channels_channel_id ON channels(channel_id)
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            debug_log(f"Error initializing SQLite DB: {str(e)}")
    
    def store_channel_data(self, data):
        """Save channel data to SQLite database - delegated to ChannelRepository"""
        try:
            abs_db_path = os.path.abspath(self.db_path)
            debug_log(f"[DB] Using database at: {abs_db_path}")
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
        except Exception as e:
            import traceback
            debug_log(f"Exception in SQLiteDatabase.store_channel_data: {str(e)}\n{traceback.format_exc()}")
            return {"error": str(e)}
    
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

    def get_channel(self, channel_identifier):
        """
        Get channel data by ID or title - delegated to ChannelRepository.get_channel_data
        
        Args:
            channel_identifier (str): Either a YouTube channel ID (UC...) or a channel title
            
        Returns:
            dict or None: Channel data or None if not found
        """
        debug_log(f"SQLiteDatabase: get_channel called with identifier: {channel_identifier}")
        # This is an alias for get_channel_data to maintain compatibility with the API
        return self.get_channel_data(channel_identifier)

    def flatten_dict(self, d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def store_playlist_data(self, playlist: dict) -> bool:
        """
        Save playlist data to SQLite database and insert full API response into playlists_history.
        Delegated to PlaylistRepository for improved field mapping.
        
        Args:
            playlist: Dictionary containing playlist data (must include playlist_id and channel_id)
        Returns:
            bool: True if successful, False otherwise
        """
        from src.database.playlist_repository import PlaylistRepository
        playlist_repo = PlaylistRepository(self.db_path)
        return playlist_repo.store_playlist_data(playlist)

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
