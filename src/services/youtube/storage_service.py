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

class StorageService(BaseService):
    """
    Service for managing storage operations for YouTube data.
    """
    
    def __init__(self, db=None):
        """
        Initialize the storage service.
        
        Args:
            db (object, optional): Database connection
        """
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._db_channel_saved = {}  # Track channels saved to DB
        
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
            storage = StorageFactory.get_storage(storage_type, config)
            result = storage.save_channel(channel_data)
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
            storage = StorageFactory.get_storage(storage_type, config)
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
            storage = StorageFactory.get_storage(storage_type, config)
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
