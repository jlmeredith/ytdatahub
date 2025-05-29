"""
YouTube Channel API client implementation
"""
import logging
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.api.youtube.base import YouTubeBaseClient
from src.utils.debug_utils import debug_log, clean_channel_id

class YouTubeChannelClient(YouTubeBaseClient):
    """Client for YouTube Channel API operations"""
    
    def get_channel_info(self, channel_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information from YouTube
        
        Args:
            channel_identifier: Channel ID, URL, or handle
            
        Returns:
            Dict with channel information or None if not found
        """
        debug_log(f"Getting channel info for: {channel_identifier}")
        channel_id = clean_channel_id(channel_identifier)
        
        # Update API call status for debug panel
        if hasattr(st, 'session_state'):
            st.session_state.api_call_status = f"Fetching channel info for: {channel_id}"
        
        # Check if API is initialized
        if not self.is_initialized():
            debug_log("API client not initialized. Cannot fetch channel info.")
            if hasattr(st, 'session_state'):
                st.session_state.api_last_error = "API client not initialized"
            return None
        
        # Check if we have this channel in cache
        cache_key = f"channel_info_{channel_id}"
        cached_info = self.get_from_cache(cache_key)
        if cached_info:
            debug_log(f"Found cached channel info for {channel_id}")
            return cached_info
            
        debug_log(f"Making API request for channel ID: {channel_id}")
        
        try:
            # Get the channel data from YouTube API
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics,brandingSettings,status,topicDetails,localizations",
                id=channel_id
            )
            
            # Execute the request and capture response
            response = request.execute()
            
            # For debugging purposes, store the raw response
            if hasattr(st, 'session_state'):
                st.session_state.api_last_response = response
                st.session_state.api_call_status = "API call completed successfully"
            
            debug_log(f"API response received: {response}")
            
            # Process the response to extract channel data
            if 'items' in response and len(response['items']) > 0:
                channel_item = response['items'][0]
                
                # Extract basic channel info
                snippet = channel_item.get('snippet', {})
                statistics = channel_item.get('statistics', {})
                content_details = channel_item.get('contentDetails', {})
                uploads_playlist_id = content_details.get('relatedPlaylists', {}).get('uploads', '')
                
                # Build a more complete channel info structure
                channel_info = {
                    'raw_channel_info': channel_item,
                    'channel_id': channel_item.get('id'),
                    'channel_name': snippet.get('title', 'Unknown Channel'),
                    'channel_description': snippet.get('description', ''),
                    'custom_url': snippet.get('customUrl', ''),
                    'published_at': snippet.get('publishedAt', ''),
                    'country': snippet.get('country', ''),
                    'subscribers': statistics.get('subscriberCount', '0'),
                    'views': statistics.get('viewCount', '0'),
                    'total_videos': statistics.get('videoCount', '0'),
                    'playlist_id': uploads_playlist_id,
                    'uploads_playlist_id': uploads_playlist_id,
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'fetched_at': datetime.now().isoformat()
                }
                
                # Store in cache
                self.store_in_cache(cache_key, channel_info)
                
                debug_log(f"Channel info processed successfully for: {channel_info['channel_name']}")
                return channel_info
            else:
                debug_log(f"No channel found with ID: {channel_id}. Full response: {response}")
                if hasattr(st, 'session_state'):
                    st.session_state.api_call_status = f"No channel found with ID: {channel_id}"
                    st.session_state.api_last_error = f"No channel found. API response: {response}"
                return None
                
        except Exception as e:
            debug_log(f"Exception in get_channel_info: {str(e)}")
            if hasattr(st, 'session_state'):
                st.session_state.api_last_error = str(e)
            self._handle_api_error(e, f"get_channel_info({channel_id})")
            return None

    def get_channel_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get channel by username/handle
        
        Args:
            username: The channel username or handle (@name)
            
        Returns:
            Dict with channel information or None if not found
        """
        debug_log(f"Getting channel info for username: {username}")
        
        # Remove @ symbol if present
        if username.startswith('@'):
            username = username[1:]
            
        # Update API call status for debug panel
        if hasattr(st, 'session_state'):
            st.session_state.api_call_status = f"Fetching channel info for username: {username}"
        
        # Check if we have this channel in cache
        cache_key = f"channel_username_{username}"
        cached_info = self.get_from_cache(cache_key)
        if cached_info:
            debug_log(f"Found cached channel info for username {username}")
            return cached_info
            
        try:
            # Make API request for channel by username
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics,brandingSettings,status,topicDetails,localizations",
                forUsername=username
            )
            
            # Execute the request
            response = request.execute()
            
            # For debugging purposes, store the raw response
            if hasattr(st, 'session_state'):
                st.session_state.api_last_response = response
                st.session_state.api_call_status = "API call completed successfully"
            
            debug_log(f"API response received. Items count: {len(response.get('items', []))}")
            
            # Process the response
            if 'items' in response and len(response['items']) > 0:
                channel_item = response['items'][0]
                channel_id = channel_item['id']
                
                # Build the channel info dictionary with standardized structure
                channel_info = {
                    'channel_id': channel_id,
                    'channel_info': channel_item,  # Store the full API response
                    'channel_name': channel_item.get('snippet', {}).get('title', 'Unknown Channel'),
                    'channel_description': channel_item.get('snippet', {}).get('description', ''),
                    'subscribers': channel_item.get('statistics', {}).get('subscriberCount', '0'),
                    'views': channel_item.get('statistics', {}).get('viewCount', '0'),
                    'total_videos': channel_item.get('statistics', {}).get('videoCount', '0'),
                }
                
                # Extract the uploads playlist ID for fetching videos later
                if 'contentDetails' in channel_item and 'relatedPlaylists' in channel_item['contentDetails']:
                    channel_info['playlist_id'] = channel_item['contentDetails']['relatedPlaylists'].get('uploads', '')
                
                # Cache the result under both username and channel ID
                self.store_in_cache(cache_key, channel_info)
                self.store_in_cache(f"channel_info_{channel_id}", channel_info)
                
                debug_log(f"Channel info processed successfully. Name: {channel_info['channel_name']}, ID: {channel_id}")
                return channel_info
            else:
                debug_log(f"No channel found with username: {username}")
                if hasattr(st, 'session_state'):
                    st.session_state.api_call_status = f"No channel found with username: {username}"
                    st.session_state.api_last_error = "Channel not found by username"
                return None
                
        except Exception as e:
            self._handle_api_error(e, f"get_channel_by_username({username})")
            return None

    def search_channel(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for channels by keyword
        
        Args:
            query: The search query
            
        Returns:
            List of channel information dictionaries
        """
        debug_log(f"Searching for channels with query: {query}")
        
        # Update API call status for debug panel
        if hasattr(st, 'session_state'):
            st.session_state.api_call_status = f"Searching for channels: {query}"
        
        try:
            # Make API request to search for channels
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="channel",
                maxResults=5  # Limit to 5 to conserve quota
            )
            
            # Execute the request
            response = request.execute()
            
            # For debugging purposes, store the raw response
            if hasattr(st, 'session_state'):
                st.session_state.api_last_response = response
                st.session_state.api_call_status = "API call completed successfully"
            
            debug_log(f"Search API response received. Items count: {len(response.get('items', []))}")
            
            # Process the results
            channels = []
            for item in response.get('items', []):
                channel_id = item['id']['channelId']
                
                # Get detailed channel info for each result
                channel_info = self.get_channel_info(channel_id)
                if channel_info:
                    channels.append(channel_info)
            
            debug_log(f"Found {len(channels)} channels matching query: {query}")
            return channels
            
        except Exception as e:
            self._handle_api_error(e, f"search_channel({query})")
            return []