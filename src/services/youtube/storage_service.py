"""
Service for handling storage operations for YouTube data.
Provides methods for saving and retrieving channel data.
"""
import logging
from typing import Dict, List, Optional, Union
import sqlite3

from src.database.sqlite import SQLiteDatabase
from src.storage.factory import StorageFactory
from src.services.youtube.base_service import BaseService
from src.utils.helpers import debug_log

class StorageService(BaseService):
    """
    Service for managing storage operations for YouTube data.
    """
    
    def __init__(self, db=None, db_path=None):
        """
        Initialize the storage service.
        
        Args:
            db (object, optional): Database connection
            db_path (str, optional): Path to the SQLite database file
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._db_channel_saved = {}  # Track channels saved to DB
        # Always set db_path for CLI/automation
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = 'data/youtube_data.db'
        if not self.db_path:
            debug_log("Warning: db_path is not set. Defaulting to 'data/youtube_data.db'.")
            self.db_path = 'data/youtube_data.db'
        
    def set_db(self, db):
        """
        Set the database connection.
        
        Args:
            db: Database connection object
        """
        self.db = db
        
    def save_channel_data(self, channel_data: Dict, storage_type: str, config=None) -> bool:
        """
        Save channel data to the specified storage provider.
        
        Args:
            channel_data (dict): The channel data to save
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
        
        Returns:
            bool: True if data was saved successfully, False otherwise
        """
        try:
            debug_log(f"[WORKFLOW] Attempting to save channel data: channel_id={channel_data.get('channel_id')}, videos={len(channel_data.get('video_id', [])) if 'video_id' in channel_data else 0}")
            # Ensure playlist_id is mapped to uploads_playlist_id
            if 'playlist_id' in channel_data:
                channel_data['uploads_playlist_id'] = channel_data['playlist_id']
                debug_log(f"[WORKFLOW] Mapped playlist_id to uploads_playlist_id for channel_id={channel_data.get('channel_id')}: {channel_data['uploads_playlist_id']}")
            storage = StorageFactory.get_storage_provider(storage_type, config)
            result = storage.store_channel_data(channel_data)
            debug_log(f"[WORKFLOW] Save result for channel_id={channel_data.get('channel_id')}: {result}")
            
            # Remove from the queue tracker if saved successfully
            if result and 'channel_id' in channel_data:
                from src.utils.queue_tracker import remove_from_queue
                remove_from_queue('channels', channel_data['channel_id'])
                
            return result
        except Exception as e:
            self.logger.error(f"Error saving channel data: {str(e)}")
            return False
    
    def get_channels_list(self, storage_type: str, config=None) -> List:
        """
        Get list of channels from the specified storage provider.
        
        Args:
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
            
        Returns:
            list: List of channel IDs/names 
        """
        try:
            storage = StorageFactory.get_storage_provider(storage_type, config)
            return storage.get_channels()
        except Exception as e:
            self.logger.error(f"Error retrieving channels list: {str(e)}")
            return []
    
    def get_channel_data(self, channel_id_or_name: str, storage_type: str, config=None) -> Optional[Dict]:
        """
        Get channel data from the specified storage provider.
        
        Args:
            channel_id_or_name (str): Channel ID or name
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
            
        Returns:
            dict or None: The channel data or None if retrieval failed
        """
        try:
            storage = StorageFactory.get_storage_provider(storage_type, config)
            return storage.get_channel(channel_id_or_name)
        except Exception as e:
            self.logger.error(f"Error retrieving channel data: {str(e)}")
            return None
            
    def save_channel(self, channel: Dict) -> bool:
        """
        Save a YouTube channel to the database.
        
        Args:
            channel: Dictionary with channel data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.db:
                self.logger.error("No database connection")
                return False
                
            channel_id = channel.get('channel_id')
            if not channel_id:
                self.logger.error("Missing channel_id in data")
                return False
                
            self.db.store_channel_data(channel)
            
            # Mark this channel as saved for quota management
            self._db_channel_saved[channel_id] = True
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving channel to database: {str(e)}")
            return False
            
    def save_video(self, video: Dict) -> bool:
        """
        Save a YouTube video to the database.
        
        Args:
            video: Dictionary with video data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.db:
                self.logger.error("No database connection")
                return False
                
            video_id = video.get('video_id')
            if not video_id:
                self.logger.error("Missing video_id in data")
                return False
                
            self.db.store_video_data(video)
            return True
        except Exception as e:
            self.logger.error(f"Error saving video to database: {str(e)}")
            return False
    
    def save_comments(self, comments: List[Dict], video_id: str) -> bool:
        """
        Save YouTube comments to the database.
        
        Args:
            comments: List of comment dictionaries
            video_id: ID of the video these comments belong to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.db:
                self.logger.error("No database connection")
                return False
                
            if not video_id:
                self.logger.error("Missing video_id")
                return False
                
            self.db.store_comments(comments, video_id)
            return True
        except Exception as e:
            self.logger.error(f"Error saving comments to database: {str(e)}")
            return False
    
    def save_video_analytics(self, analytics: Dict, video_id: str) -> bool:
        """
        Save video analytics to the database.
        
        Args:
            analytics: Dictionary with analytics data
            video_id: ID of the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.db:
                self.logger.error("No database connection")
                return False
                
            if not video_id:
                self.logger.error("Missing video_id")
                return False
                
            self.db.store_video_analytics(analytics, video_id)
            return True
        except Exception as e:
            self.logger.error(f"Error saving video analytics to database: {str(e)}")
            return False
    
    def has_saved_channel(self, channel_id: str) -> bool:
        """
        Check if a channel has already been saved to the database.
        
        Args:
            channel_id: Channel ID to check
            
        Returns:
            bool: True if the channel has been saved, False otherwise
        """
        return channel_id in self._db_channel_saved

    def update_channel_field(self, channel_id: str, field: str, value: str) -> bool:
        """
        Update a single field for a channel in the DB.
        """
        try:
            if not hasattr(self, 'db_path') or not self.db_path:
                debug_log(f"[WORKFLOW] WARNING: db_path is not set on StorageService. Defaulting to data/youtube_data.db")
                self.db_path = 'data/youtube_data.db'
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(f"UPDATE channels SET {field} = ? WHERE channel_id = ?", (value, channel_id))
            conn.commit()
            conn.close()
            debug_log(f"[WORKFLOW] Updated {field} for channel_id={channel_id} to {value}")
            return True
        except Exception as e:
            debug_log(f"[WORKFLOW] Failed to update {field} for channel_id={channel_id}: {str(e)}")
            return False

# Add a regression test for update_channel_field
if __name__ == "__main__":
    import tempfile
    import os
    import sqlite3
    # Create a temp DB
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        db_path = tf.name
    try:
        # Set up schema
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('''CREATE TABLE channels (id INTEGER PRIMARY KEY, channel_id TEXT UNIQUE, channel_title TEXT, uploads_playlist_id TEXT)''')
        cur.execute('''INSERT INTO channels (channel_id, channel_title, uploads_playlist_id) VALUES (?, ?, ?)''', ("UC123", "Test Channel", ""))
        conn.commit()
        conn.close()
        # Test update_channel_field
        svc = StorageService(db_path=db_path)
        result = svc.update_channel_field("UC123", "uploads_playlist_id", "UU123")
        assert result, "update_channel_field should return True"
        # Verify update
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT uploads_playlist_id FROM channels WHERE channel_id = ?", ("UC123",))
        row = cur.fetchone()
        assert row[0] == "UU123", f"Expected uploads_playlist_id to be 'UU123', got {row[0]}"
        print("Regression test for update_channel_field PASSED")
    finally:
        os.remove(db_path)
