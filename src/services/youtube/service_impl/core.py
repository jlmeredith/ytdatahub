"""
Core implementation of the YouTubeServiceImpl class.
"""
from unittest.mock import MagicMock
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import logging

from src.api.youtube_api import YouTubeAPI
from src.services.youtube import StorageService, ChannelService, VideoService, CommentService
from src.services.youtube.delta_service_integration import integrate_delta_service

from .data_collection import DataCollectionMixin
from .data_refresh import DataRefreshMixin
from .data_processing import DataProcessingMixin
from .error_handling import ErrorHandlingMixin

class YouTubeServiceImpl(DataCollectionMixin, 
                        DataRefreshMixin, DataProcessingMixin, ErrorHandlingMixin):
    """
    Implementation of the YouTube service using specialized services.
    """
    
    def __init__(self, api_key):
        """
        Initialize the YouTube service implementation.
        
        Args:
            api_key (str): YouTube Data API key
        """
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        
        self.api = YouTubeAPI(api_key)
        
        # Initialize specialized services
        self.storage_service = StorageService()
        self.channel_service = ChannelService(api_key, api_client=self.api)
        self.video_service = VideoService(api_key, api_client=self.api)
        self.comment_service = CommentService(api_key, api_client=self.api)
        
        # Database connection for storage operations
        self.db = None
        
        # For comment tracking (store the last response)
        self._last_comments_response = None
        
        # Track channels saved to DB
        self._db_channel_saved = {}
        
        # Integrate delta service functionality
        integrate_delta_service(self)
    
    # Delegate to storage service
    def save_channel_data(self, channel_data, storage_type, config=None):
        """
        Save channel data to the specified storage provider.
        
        Args:
            channel_data (dict): The channel data to save
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
        
        Returns:
            bool: True if data was saved successfully, False otherwise
        """
        return self.storage_service.save_channel_data(channel_data, storage_type, config)
    
    def get_channels_list(self, storage_type, config=None):
        """
        Get list of channels from the specified storage provider.
        
        Args:
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
            
        Returns:
            list: List of channel IDs/names 
        """
        return self.storage_service.get_channels_list(storage_type, config)
    
    def get_channel_data(self, channel_id_or_name, storage_type, config=None):
        """
        Get channel data from the specified storage provider.
        
        Args:
            channel_id_or_name (str): Channel ID or name
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
            
        Returns:
            dict or None: The channel data or None if retrieval failed
        """
        return self.storage_service.get_channel_data(channel_id_or_name, storage_type, config)
    
    def save_channel(self, channel: Dict) -> bool:
        """Save a YouTube channel to the database"""
        # Update database reference in storage service
        self.storage_service.set_db(self.db)
        return self.storage_service.save_channel(channel)
    
    def save_video(self, video: Dict) -> bool:
        """Save a YouTube video to the database"""
        # Update database reference in storage service
        self.storage_service.set_db(self.db)
        return self.storage_service.save_video(video)
    
    def save_comments(self, comments: List[Dict], video_id: str) -> bool:
        """Save YouTube comments to the database"""
        # Update database reference in storage service
        self.storage_service.set_db(self.db)
        return self.storage_service.save_comments(comments, video_id)
    
    def save_video_analytics(self, analytics: Dict, video_id: str) -> bool:
        """Save video analytics to the database"""
        # Update database reference in storage service
        self.storage_service.set_db(self.db)
        return self.storage_service.save_video_analytics(analytics, video_id)
    
    # Delegate to channel service
    def validate_and_resolve_channel_id(self, channel_id):
        """
        Validate a channel ID and resolve custom URLs or handles if needed.
        
        Args:
            channel_id (str): The channel ID, custom URL, or handle to validate
            
        Returns:
            tuple: (is_valid, channel_id_or_message)
        """
        return self.channel_service.validate_and_resolve_channel_id(channel_id)
