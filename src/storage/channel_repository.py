"""
Channel repository implementation for channel data storage operations.
"""
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from src.storage.base_repository import BaseRepository
from src.storage.factory import StorageFactory

class ChannelRepository(BaseRepository):
    """
    Repository for YouTube channel data.
    Implements the repository pattern for channel data storage operations.
    """
    
    REQUIRED_FIELDS = ['channel_id', 'channel_name']
    
    def __init__(self, storage_type: str = "SQLite Database", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the channel repository with a storage provider.
        
        Args:
            storage_type: The type of storage to use (default: SQLite)
            config: Configuration for the storage provider
        """
        storage_provider = StorageFactory.get_storage_provider(storage_type, config)
        super().__init__(storage_provider)
        self.logger = logging.getLogger(__name__)
    
    def get_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a channel by ID.
        
        Args:
            channel_id: The ID of the channel to retrieve
            
        Returns:
            dict: The channel data or None if not found
        """
        try:
            if hasattr(self.storage, 'get_channel_data'):
                return self.storage.get_channel_data(channel_id)
            elif hasattr(self.storage, 'get_entity'):
                return self.storage.get_entity('channel', channel_id)
            else:
                self.log_error("Storage provider does not support get_channel_data or get_entity")
                return None
        except Exception as e:
            self.log_error(f"Error retrieving channel {channel_id}", e)
            return None
    
    def save(self, channel: Dict[str, Any]) -> bool:
        """
        Save a channel.
        
        Args:
            channel: The channel data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.validate_entity(channel, self.REQUIRED_FIELDS):
            self.log_error(f"Invalid channel data: missing required fields {self.REQUIRED_FIELDS}")
            return False
            
        try:
            # Add timestamp if not present
            if 'fetched_at' not in channel:
                channel['fetched_at'] = datetime.now().isoformat()
                
            if hasattr(self.storage, 'store_channel_data'):
                return self.storage.store_channel_data(channel)
            elif hasattr(self.storage, 'save_entity'):
                return self.storage.save_entity('channel', channel['channel_id'], channel)
            else:
                self.log_error("Storage provider does not support store_channel_data or save_entity")
                return False
        except Exception as e:
            self.log_error(f"Error saving channel {channel.get('channel_id', 'unknown')}", e)
            return False
    
    def delete(self, channel_id: str) -> bool:
        """
        Delete a channel.
        
        Args:
            channel_id: The ID of the channel to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if hasattr(self.storage, 'delete_channel_data'):
                return self.storage.delete_channel_data(channel_id)
            elif hasattr(self.storage, 'delete_entity'):
                return self.storage.delete_entity('channel', channel_id)
            else:
                self.log_error("Storage provider does not support delete_channel_data or delete_entity")
                return False
        except Exception as e:
            self.log_error(f"Error deleting channel {channel_id}", e)
            return False
    
    def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all channels.
        
        Args:
            limit: Maximum number of channels to return
            offset: Number of channels to skip
            
        Returns:
            list: List of channel data
        """
        try:
            if hasattr(self.storage, 'list_channels'):
                return self.storage.list_channels(limit, offset)
            elif hasattr(self.storage, 'list_entities'):
                return self.storage.list_entities('channel', limit, offset)
            else:
                self.log_error("Storage provider does not support list_channels or list_entities")
                return []
        except Exception as e:
            self.log_error("Error listing channels", e)
            return []
    
    def find_by_field(self, field_name: str, field_value: Any) -> List[Dict[str, Any]]:
        """
        Find channels by field value.
        
        Args:
            field_name: The field to search
            field_value: The value to search for
            
        Returns:
            list: List of matching channel data
        """
        try:
            if hasattr(self.storage, 'find_channels_by'):
                return self.storage.find_channels_by(field_name, field_value)
            elif hasattr(self.storage, 'find_entities_by'):
                return self.storage.find_entities_by('channel', field_name, field_value)
            else:
                self.log_error("Storage provider does not support find_channels_by or find_entities_by")
                return []
        except Exception as e:
            self.log_error(f"Error finding channels by {field_name}={field_value}", e)
            return []
    
    def get_channel_metrics(self, channel_id: str) -> Dict[str, Any]:
        """
        Get metrics for a channel.
        
        Args:
            channel_id: The ID of the channel
            
        Returns:
            dict: Channel metrics
        """
        try:
            if hasattr(self.storage, 'get_channel_metrics'):
                return self.storage.get_channel_metrics(channel_id)
            else:
                # Try to build metrics from channel data
                channel = self.get_by_id(channel_id)
                if channel:
                    return {
                        'subscribers': channel.get('subscribers', 0),
                        'views': channel.get('views', 0),
                        'video_count': channel.get('total_videos', 0)
                    }
                return {}
        except Exception as e:
            self.log_error(f"Error getting metrics for channel {channel_id}", e)
            return {}
    
    def update_field(self, channel_id: str, field_name: str, field_value: Any) -> bool:
        """
        Update a single field for a channel.
        
        Args:
            channel_id: The ID of the channel
            field_name: The field to update
            field_value: The new value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if hasattr(self.storage, 'update_channel_field'):
                return self.storage.update_channel_field(channel_id, field_name, field_value)
            else:
                # Get the channel, update the field, and save it back
                channel = self.get_by_id(channel_id)
                if channel:
                    channel[field_name] = field_value
                    return self.save(channel)
                return False
        except Exception as e:
            self.log_error(f"Error updating field {field_name} for channel {channel_id}", e)
            return False 