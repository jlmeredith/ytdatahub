"""
YouTube API client for video-related operations.
"""
import streamlit as st
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

import googleapiclient.errors

from src.utils.helpers import debug_log
from src.api.youtube.base import YouTubeBaseClient

class VideoClient(YouTubeBaseClient):
    """YouTube Data API client focused on video operations"""
    
    def get_channel_videos(self, channel_info, max_videos=25, page_token=None):
        """
        Get videos for a channel using the uploads playlist ID
        
        Args:
            channel_info: Dictionary with channel information
            max_videos: Maximum number of videos to fetch
            page_token: Token for pagination
            
        Returns:
            Updated channel_info dictionary with videos
        """
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return channel_info
        
        # Get the uploads playlist ID
        playlist_id = channel_info.get('playlist_id', '')
        if not playlist_id:
            debug_log("No uploads playlist ID found in channel info. Attempting to find it...")
            
            # Check if it might be in channel_info structure (needed for update scenario)
            if 'channel_info' in channel_info and isinstance(channel_info['channel_info'], dict):
                if 'contentDetails' in channel_info['channel_info'] and 'relatedPlaylists' in channel_info['channel_info']['contentDetails']:
                    playlist_id = channel_info['channel_info']['contentDetails']['relatedPlaylists'].get('uploads', '')
                    if playlist_id:
                        debug_log(f"Found uploads playlist ID in channel_info structure: {playlist_id}")
                        channel_info['playlist_id'] = playlist_id
            
            # If still no playlist ID, check for uploads_playlist_id at the root level
            if not playlist_id and 'uploads_playlist_id' in channel_info:
                playlist_id = channel_info['uploads_playlist_id']
                debug_log(f"Found uploads playlist ID as uploads_playlist_id: {playlist_id}")
                channel_info['playlist_id'] = playlist_id
        
        if not playlist_id:
            debug_log("ERROR: Failed to find uploads playlist ID, cannot fetch videos")
            st.error("No uploads playlist ID found in channel info. Videos cannot be fetched.")
            return channel_info
        
        debug_log(f"[WORKFLOW] Using playlist_id={playlist_id} to fetch videos for channel_id={channel_info.get('channel_id','?')}")
        
        debug_log(f"[DIAG] API key starts with: {self.api_key[:6]}... (masked)")
        debug_log(f"[DIAG] YouTube client initialized: {self.is_initialized()}")
        debug_log(f"[DIAG] Using playlist_id: {playlist_id}")
        
        debug_log(f"Fetching videos for channel using playlist ID: {playlist_id}")
        
        # Initialize variables
        total_videos_fetched = 0
        total_videos_unavailable = 0
        videos_with_comments_disabled = 0
        next_page_token = None
        
        # Initialize video_id list if it doesn't exist
        if 'video_id' not in channel_info:
            channel_info['video_id'] = []
        
        # Keep track of existing video IDs to avoid duplicates (for update scenario)
        existing_video_ids = {v['video_id'] for v in channel_info['video_id']} if 'video_id' in channel_info else set()
        debug_log(f"Found {len(existing_video_ids)} existing videos in channel data")
        
        # Save original video count for delta reporting
        original_video_count = len(channel_info['video_id'])
        
        # Additional tracking for delta reporting
        updated_videos = 0
        new_videos = 0
        unchanged_videos = 0
        
        # For quota optimization, we'll collect video IDs first, then batch request their details
        all_video_ids = []
        
        try:
            # Start fetching video IDs from the uploads playlist
            while True:
                # Configure the request to get videos from the playlist
                playlist_request = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,  # Maximum allowed by API
                    pageToken=next_page_token
                )
                
                playlist_response = playlist_request.execute()
                debug_log(f"[DIAG] Raw playlistItems API response: {json.dumps(playlist_response)[:1000]}")
                if 'error' in playlist_response:
                    debug_log(f"[DIAG] API error in playlistItems response: {playlist_response['error']}")
                    channel_info['error_videos'] = f"YouTube API error: {playlist_response['error']}"
                    return channel_info
                if not playlist_response.get('items'):
                    debug_log(f"[DIAG] No items returned in playlistItems response for playlist_id {playlist_id}")
                    channel_info['error_videos'] = f"No videos found in playlist {playlist_id}. API response: {json.dumps(playlist_response)[:500]}"
                    return channel_info
                
                # Extract video IDs from playlist items
                for item in playlist_response.get('items', []):
                    # Get the video ID from the playlist item
                    video_id = item['contentDetails']['videoId']
                    
                    # Skip if we already have this video (for update scenario)
                    if video_id in existing_video_ids:
                        continue
                    
                    # Add to our batch processing list
                    all_video_ids.append(video_id)
                
                # Get the next page token if available
                next_page_token = playlist_response.get('nextPageToken')
                
                # Check if we've reached our maximum videos or there are no more pages
                if not next_page_token or (max_videos > 0 and len(all_video_ids) + len(existing_video_ids) >= max_videos):
                    break
            
            debug_log(f"Found {len(all_video_ids)} new video IDs from playlist, processing details...")
            
            # Now fetch the actual video details in batches
            batch_size = 50  # Maximum allowed by API for video.list
            for i in range(0, len(all_video_ids), batch_size):
                # Get the current batch of IDs
                batch_ids = all_video_ids[i:i+batch_size]
                
                # Break if we've reached the maximum video count
                if max_videos > 0 and total_videos_fetched + len(existing_video_ids) >= max_videos:
                    break
                
                # Request detailed video information
                video_request = self.youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(batch_ids)
                )
                
                video_response = video_request.execute()
                
                # Track how many videos we actually get back vs requested
                videos_expected = len(batch_ids)
                videos_returned = len(video_response.get('items', []))
                if videos_expected > videos_returned:
                    total_videos_unavailable += (videos_expected - videos_returned)
                    debug_log(f"Warning: {videos_expected - videos_returned} videos were unavailable.")
                
                # Process each video
                for video in video_response.get('items', []):
                    if max_videos > 0 and total_videos_fetched + len(existing_video_ids) >= max_videos:
                        break
                        
                    # Get video ID for tracking
                    video_id = video['id']                            # Build video data with improved view and comment handling
                    video_data = {
                        'video_id': video_id,
                        'title': video['snippet'].get('title', ''),
                        'video_description': video['snippet'].get('description', ''),
                        'published_at': video['snippet'].get('publishedAt', ''),
                        'published_date': video['snippet'].get('publishedAt', '')[:10] if video['snippet'].get('publishedAt', '') else '',
                        'views': video['statistics'].get('viewCount', '0'),
                        'likes': video['statistics'].get('likeCount', '0'),
                        'comment_count': video['statistics'].get('commentCount', '0'),
                        'duration': video['contentDetails'].get('duration', ''),
                        'thumbnails': video['snippet'].get('thumbnails', {}).get('high', {}).get('url', ''),
                        'comments': []
                    }
                    
                    # Store the full statistics object for later reference and ensure consistent data
                    video_data['statistics'] = video.get('statistics', {})
                    
                    # Double-check comment_count is correctly populated from statistics
                    if 'commentCount' in video_data['statistics'] and (not video_data['comment_count'] or video_data['comment_count'] == '0'):
                        video_data['comment_count'] = video_data['statistics']['commentCount']
                        debug_log(f"Set comment_count to {video_data['comment_count']} from statistics for video {video_id}")
                    
                    # Track if comments are disabled
                    if video['contentDetails'].get('commentStatus') == 'disabled':
                        video_data['comments_disabled'] = True
                        videos_with_comments_disabled += 1
                    
                    # Attach the full API response for this video
                    video_data['raw_api_response'] = video
                    
                    # Add the video to the channel data
                    channel_info['video_id'].append(video_data)
                    total_videos_fetched += 1
                    new_videos += 1
                
                # Add a slight delay to avoid hitting rate limits
                time.sleep(0.1)
            
            # Update summary statistics for the channel
            channel_info['videos_fetched'] = total_videos_fetched + len(existing_video_ids)
            channel_info['videos_unavailable'] = total_videos_unavailable
            
            if videos_with_comments_disabled > 0:
                channel_info['videos_with_comments_disabled'] = videos_with_comments_disabled
            
            # Add delta reporting data
            channel_info['update_stats'] = {
                'original_video_count': original_video_count,
                'new_videos': new_videos,
                'updated_videos': updated_videos,
                'unchanged_videos': unchanged_videos
            }
            
            debug_log(f"Delta reporting stats: {channel_info['update_stats']}")
            
            debug_log(f"Successfully fetched {total_videos_fetched} videos for the channel. "
                     f"Total videos in collection: {len(channel_info['video_id'])}")
            
            # Add comment counts for later tracking
            comment_counts = {
                'total_comment_count': sum(int(v.get('comment_count', 0)) for v in channel_info['video_id']),
                'videos_with_comments': sum(1 for v in channel_info['video_id'] if int(v.get('comment_count', 0)) > 0)
            }
            channel_info['comment_counts'] = comment_counts
            
            debug_log(f"Comment counts from metadata: {comment_counts}")
            return channel_info
            
        except Exception as e:
            self._handle_api_error(e, "get_channel_videos")
            return channel_info
    
    def get_videos_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed information for a batch of videos by their IDs
        
        Args:
            video_ids: List of YouTube video IDs to fetch details for
            
        Returns:
            List of video detail dictionaries
        """
        if not video_ids:
            return []
        
        try:
            # Join IDs with commas for the API request
            video_ids_str = ','.join(video_ids)
            
            # Check cache first
            cache_key = f"video_details_{video_ids_str}"
            cached_data = self.get_from_cache(cache_key)
            if cached_data:
                debug_log(f"Using cached video details for {len(video_ids)} videos")
                return cached_data
            
            # Request video details with more parts to get additional fields
            video_request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics,status,topicDetails,player,liveStreamingDetails",
                id=video_ids_str
            )
            video_response = video_request.execute()
            
            # Store in cache
            result = video_response.get('items', [])
            self.store_in_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            self._handle_api_error(e, "get_videos_details")
            return []

    # Alias for test compatibility: patching get_video_details_batch will patch get_videos_details
    get_video_details_batch = get_videos_details

    def get_playlist_info(self, playlist_id: str) -> dict:
        """
        Fetch full playlist info from the YouTube Data API for a given playlist_id.
        Args:
            playlist_id (str): The playlist ID to fetch
        Returns:
            dict: Playlist info dict or None if not found
        """
        debug_log(f"[API] get_playlist_info called with playlist_id: {playlist_id}")
        if not self.is_initialized():
            debug_log("YouTube API client not initialized. Cannot fetch playlist info.")
            return None
        try:
            request = self.youtube.playlists().list(
                part="snippet,contentDetails,status,player,localizations",
                id=playlist_id
            )
            response = request.execute()
            debug_log(f"[API] Playlist API response: {str(response)[:500]}")
            if 'items' in response and len(response['items']) > 0:
                return response['items'][0]
            else:
                debug_log(f"No playlist found with ID: {playlist_id}")
                return None
        except Exception as e:
            debug_log(f"[API][ERROR] Exception in get_playlist_info: {str(e)}")
            return None