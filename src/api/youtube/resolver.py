"""
YouTube channel URL and handle resolver module.
"""
import streamlit as st
from typing import Optional
import re

import googleapiclient.errors

from src.utils.helpers import debug_log
from src.api.youtube.base import YouTubeBaseClient

class ChannelResolver(YouTubeBaseClient):
    """Class for resolving YouTube channel handles and custom URLs to channel IDs"""
    
    def resolve_custom_channel_url(self, custom_url_or_handle: str) -> Optional[str]:
        """
        Resolve a custom URL or handle (@username) to a channel ID.
        
        Args:
            custom_url_or_handle (str): The custom URL, handle, or username to resolve
            
        Returns:
            str or None: The resolved channel ID or None if resolution failed
        """
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return None
            
        debug_log(f"Resolving custom URL or handle: {custom_url_or_handle}")
        
        # Clean up input
        query = custom_url_or_handle.strip()
        
        # Remove 'resolve:' prefix if present (internal format)
        if query.startswith('resolve:'):
            query = query[8:].strip()
        
        # Process based on URL format
        if query.startswith('@'):
            handle = query
            debug_log(f"Processing as channel handle: {handle}")
        elif '/' in query:
            # Extract the last part of the URL
            parts = query.strip('/').split('/')
            handle = parts[-1]
            if handle.startswith('@'):
                debug_log(f"Extracted handle from URL: {handle}")
            else:
                handle = '@' + handle
                debug_log(f"Converted URL part to handle format: {handle}")
        else:
            # If it doesn't have @ or /, add @ to make it a handle format
            handle = '@' + query
            debug_log(f"Added @ prefix to make it a handle: {handle}")
            
        try:
            # Try to resolve handle or custom URL using search endpoint
            search_request = self.youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=5
            )
            search_response = search_request.execute()
            
            # Check if we got any results
            if not search_response.get('items'):
                debug_log(f"No channels found for query: {handle}")
                return None
                
            # Find the best match by comparing titles and custom URLs
            best_match = None
            
            for item in search_response['items']:
                channel_id = item['id']['channelId']
                channel_title = item['snippet']['title']
                
                # Get more details about the channel to check custom URL
                channel_request = self.youtube.channels().list(
                    part="snippet",
                    id=channel_id
                )
                channel_response = channel_request.execute()
                
                if not channel_response.get('items'):
                    continue
                    
                channel_data = channel_response['items'][0]
                
                # Check if this is an exact match for handle or custom URL
                # CustomUrl field might not be available in all channel data
                channel_custom_url = channel_data['snippet'].get('customUrl', '')
                
                debug_log(f"Checking channel: ID={channel_id}, title='{channel_title}', customUrl='{channel_custom_url}'")
                
                # Match priority:
                # 1. Exact match on customUrl (without @)
                # 2. If we're searching for a handle (@username), match on username
                # 3. Exact match on title
                # 4. First result if nothing else matches
                
                # Clean handle for comparison by removing @ if present
                clean_handle = handle[1:] if handle.startswith('@') else handle
                
                if channel_custom_url and (
                    channel_custom_url.lower() == clean_handle.lower() or 
                    channel_custom_url.lower() == handle.lower()
                ):
                    debug_log(f"Found exact match on customUrl: {channel_custom_url}")
                    best_match = channel_id
                    break
                elif handle.startswith('@') and clean_handle.lower() in channel_custom_url.lower():
                    debug_log(f"Found handle match: @{clean_handle} in {channel_custom_url}")
                    best_match = channel_id
                    # Continue looking for exact matches
                elif clean_handle.lower() in channel_title.lower():
                    debug_log(f"Found channel with matching title for handle {handle}: {channel_id}")
                    if not best_match:  # Only set if we don't have a better match
                        best_match = channel_id
                elif not best_match:
                    debug_log(f"Setting initial match: {channel_title} ({channel_id})")
                    best_match = channel_id
            
            # Return the best match if found
            if best_match:
                debug_log(f"Resolved {query} to channel ID: {best_match}")
                return best_match
            
            # If we got items but didn't find a good match, use the first result
            if search_response.get('items'):
                first_result = search_response.get('items')[0]
                channel_id = first_result['id']['channelId']
                debug_log(f"No exact match found, using first search result for {handle}: {channel_id}")
                return channel_id
                
            debug_log(f"Failed to find a good match for: {query}")
            return None
            
        except Exception as e:
            self._handle_api_error(e, "resolve_custom_channel_url")
            return None