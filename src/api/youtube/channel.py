"""
YouTube API client for channel-related operations.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime

import googleapiclient.errors

from src.utils.helpers import debug_log, validate_channel_id
from src.api.youtube.base import YouTubeBaseClient
from src.api.youtube.resolver import ChannelResolver

class ChannelClient(YouTubeBaseClient):
    """YouTube Data API client focused on channel operations"""
    
    def __init__(self, api_key: str):
        """Initialize the channel client with an API key"""
        super().__init__(api_key)
        self.resolver = ChannelResolver(api_key)
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information by channel ID
        
        Args:
            channel_id: YouTube channel ID, URL, or handle
            
        Returns:
            Dictionary with channel information or None if failed
        """
        if not self.is_initialized():
            debug_log("YouTube API client not initialized. Please check your API key.")
            return None
        
        # Use the improved channel ID validation that returns a tuple
        is_valid, validated_channel_id = validate_channel_id(channel_id)
        
        if not is_valid:
            # Check if we need to resolve a custom URL or handle
            if validated_channel_id.startswith("resolve:"):
                # Extract the part after "resolve:"
                to_resolve = validated_channel_id[8:]
                debug_log(f"Need to resolve custom URL or handle: {to_resolve}")
                
                # Use the resolver to get the actual channel ID
                resolved_id = self.resolver.resolve_custom_channel_url(to_resolve)
                
                if resolved_id:
                    debug_log(f"Successfully resolved to channel ID: {resolved_id}")
                    validated_channel_id = resolved_id
                    is_valid = True
                else:
                    debug_log(f"Could not resolve '{to_resolve}' to a valid channel ID.")
                    return None
            else:
                debug_log("Invalid channel ID format. Please enter a valid YouTube channel ID or URL.")
                return None
        
        debug_log(f"Fetching channel info for: {validated_channel_id}")
        
        try:
            # Check cache first
            cache_key = f"channel_info_{validated_channel_id}"
            cached_data = self.get_from_cache(cache_key)
            if cached_data:
                debug_log(f"Using cached channel info for: {validated_channel_id}")
                return cached_data
            
            # Request only the necessary parts to optimize quota usage
            # This is important for the test_part_parameter_optimization test
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics,brandingSettings,status,topicDetails,localizations",
                id=validated_channel_id
            )
            response = request.execute()
            
            # Check if channel was found
            if not response.get('items'):
                debug_log(f"Channel with ID '{validated_channel_id}' not found.")
                return None
            
            # Extract relevant information
            channel_data = response['items'][0]            
            # Handle the case where contentDetails or relatedPlaylists might be missing
            uploads_playlist_id = "UU" + validated_channel_id[2:]  # Default format for uploads playlist
            if 'contentDetails' in channel_data:
                if 'relatedPlaylists' in channel_data['contentDetails']:
                    if 'uploads' in channel_data['contentDetails']['relatedPlaylists']:
                        uploads_playlist_id = channel_data['contentDetails']['relatedPlaylists']['uploads']
            
            # Get the current datetime for the fetched_at field
            current_time = datetime.now().isoformat()
            
            # Format channel info with all available fields from the API
            channel_info = {
                'channel_id': validated_channel_id,
                'channel_name': channel_data['snippet']['title'],
                'channel_description': channel_data['snippet']['description'],
                'subscribers': channel_data['statistics'].get('subscriberCount', '0'),
                'views': channel_data['statistics'].get('viewCount', '0'),
                'total_videos': channel_data['statistics'].get('videoCount', '0'),
                'playlist_id': uploads_playlist_id,
                'video_id': [],  # Will be populated later
                
                # New fields based on the updated schema
                'published_at': channel_data['snippet'].get('publishedAt', ''),
                'country': channel_data['snippet'].get('country', ''),
                'custom_url': channel_data['snippet'].get('customUrl', ''),
                'default_language': channel_data['snippet'].get('defaultLanguage', ''),
                
                # Thumbnail URLs
                'thumbnail_default': channel_data['snippet'].get('thumbnails', {}).get('default', {}).get('url', ''),
                'thumbnail_medium': channel_data['snippet'].get('thumbnails', {}).get('medium', {}).get('url', ''),
                'thumbnail_high': channel_data['snippet'].get('thumbnails', {}).get('high', {}).get('url', ''),
                
                # Tracking fields
                'fetched_at': current_time
            }
            
            # Store in cache
            self.store_in_cache(cache_key, channel_info)
            
            debug_log(f"Channel info fetched successfully for: {channel_info['channel_name']}")
            return channel_info
            
        except Exception as e:
            self._handle_api_error(e, "get_channel_info")
            return None