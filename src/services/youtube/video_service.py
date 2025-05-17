"""
Service for handling YouTube video operations.
Provides methods for fetching and processing video data.
"""
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.api.youtube_api import YouTubeAPI, YouTubeAPIError
from src.utils.helpers import debug_log
from src.services.youtube.base_service import BaseService

class VideoService(BaseService):
    """
    Service for managing YouTube video operations.
    """
    
    def __init__(self, api_key=None, api_client=None, quota_service=None):
        """
        Initialize the video service.
        
        Args:
            api_key (str, optional): YouTube API key
            api_client (obj, optional): Existing API client to use
            quota_service (QuotaService, optional): Service for quota management
        """
        super().__init__(api_key, api_client)
        self.api = api_client if api_client else (YouTubeAPI(api_key) if api_key else None)
        self.quota_service = quota_service
        self.logger = logging.getLogger(__name__)
    
    def collect_channel_videos(self, channel_data: Dict, max_results: int = 0, optimize_quota: bool = False) -> Dict:
        """
        Fetch and populate videos for the channel.
        
        Args:
            channel_data: Dictionary containing channel data with playlist_id
            max_results: Maximum number of videos to retrieve (0 for all)
            optimize_quota: Whether to optimize quota usage
            
        Returns:
            dict: Updated channel data with videos
        """
        channel_id = channel_data.get('channel_id')
        if not channel_id:
            debug_log("No channel ID available to fetch videos")
            return channel_data
            
        debug_log(f"Fetching videos for channel: {channel_id}, max_results: {max_results}, optimize_quota: {optimize_quota}")
        
        try:
            # Track quota if quota service is provided
            if self.quota_service:
                self.quota_service.track_quota_usage('playlistItems.list')
                
            # Request videos from the channel
            videos_response = self.api.get_channel_videos(channel_data, max_videos=max_results, optimize_quota=optimize_quota)
            
            if not videos_response:
                debug_log("Failed to retrieve videos or channel has no videos")
                return channel_data
                
            # Extract videos from the response
            if 'video_id' in videos_response:
                # Check if video_id is a list or another structure
                if isinstance(videos_response['video_id'], list):
                    # Direct assignment of the video list
                    videos_list = videos_response['video_id']
                    channel_data['video_id'] = videos_list
                    debug_log(f"Collected {len(videos_list)} videos for channel")
                else:
                    # Handle case where video_id might be a dictionary or other structure
                    debug_log(f"Warning: video_id is not a list, but {type(videos_response['video_id'])}")
                    # Special handling for tests where video_id might be a special structure
                    if not channel_data.get('video_id'):
                        channel_data['video_id'] = []
                    # Try to extract videos if possible
                    videos_list = None
                    if 'video_id' in videos_response:
                        videos_list = videos_response['video_id']
                        channel_data['video_id'] = videos_list
                        debug_log(f"Extracted {len(videos_list) if isinstance(videos_list, list) else 'unknown'} videos from special structure")
            else:
                debug_log("No 'video_id' field found in the API response")
                
            # Preserve videos_unavailable field if present in response
            if 'videos_unavailable' in videos_response:
                channel_data['videos_unavailable'] = videos_response['videos_unavailable']
                debug_log(f"Preserved videos_unavailable count: {videos_response['videos_unavailable']}")
                
            # Also preserve videos_fetched field if present
            if 'videos_fetched' in videos_response:
                channel_data['videos_fetched'] = videos_response['videos_fetched']
                debug_log(f"Preserved videos_fetched count: {videos_response['videos_fetched']}")
                
            # Process videos that might have errors (like unavailable videos)
            self._process_video_details(channel_data)
            
            return channel_data
            
        except YouTubeAPIError as e:
            # Special handling for quota exceeded errors
            if e.status_code == 403 and getattr(e, 'error_type', '') == 'quotaExceeded':
                channel_data['error_videos'] = f"Quota exceeded: {str(e)}"
                debug_log(f"Quota exceeded error handled gracefully: {channel_id}")
            else:
                # Handle other errors
                debug_log(f"Error collecting videos: {str(e)}")
                channel_data['error_videos'] = f"Error: {str(e)}"
            
            return channel_data
            
        except Exception as e:
            debug_log(f"Unexpected error collecting videos: {str(e)}")
            channel_data['error_videos'] = f"Unexpected error: {str(e)}"
            return channel_data
            
    def _process_video_details(self, channel_data: Dict) -> None:
        """
        Process video details and handle errors for individual videos.
        
        Args:
            channel_data: Channel data dictionary with videos
        """
        if 'video_id' in channel_data and isinstance(channel_data['video_id'], list):
            # Check if any video has an error
            for video in channel_data['video_id']:
                video_id = video.get('video_id')
                if not video_id:
                    continue
                
                try:
                    # Try to get video details if the API supports it
                    if hasattr(self.api, 'get_video_info'):
                        details = self.api.get_video_info(video_id)
                        # Update video with details
                        if details:
                            video.update(details)
                except YouTubeAPIError as e:
                    # If the video is unavailable, mark it with error info
                    if e.status_code == 404 or e.error_type == "videoNotFound":
                        video['error'] = f"Video unavailable: {str(e)}"
                        debug_log(f"Marked video {video_id} as unavailable")
                    else:
                        # For other errors, also record them
                        video['error'] = f"Error fetching video: {str(e)}"
                        debug_log(f"Error fetching details for video {video_id}: {str(e)}")

    def get_video_details_batch(self, video_ids: List[str]) -> Dict:
        """
        Get detailed information about a batch of videos.
        
        Args:
            video_ids: List of video IDs
            
        Returns:
            dict: Video details response
        """
        if not video_ids:
            return None
            
        debug_log(f"Getting details for {len(video_ids)} videos in batch")
        
        try:
            # Track quota if quota service is provided
            if self.quota_service:
                self.quota_service.track_quota_usage('videos.list')
                
            # Request video details
            return self.api.get_video_details_batch(video_ids)
        except Exception as e:
            debug_log(f"Error getting video details batch: {str(e)}")
            raise

    def refresh_video_details(self, channel_data: Dict) -> Dict:
        """
        Refresh video details for videos in the channel data.
        
        Args:
            channel_data: Dictionary containing channel data with videos
            
        Returns:
            dict: Updated channel data with refreshed video details
        """
        if not channel_data or 'video_id' not in channel_data or not isinstance(channel_data['video_id'], list):
            return channel_data
            
        debug_log(f"Refreshing video details for {len(channel_data['video_id'])} videos")
        
        try:
            # Extract all video IDs from existing data
            all_video_ids = []
            for video in channel_data.get('video_id', []):
                if isinstance(video, dict) and 'video_id' in video:
                    all_video_ids.append(video['video_id'])
                    
            # Process in batches of 50 (YouTube API limit)
            batch_size = 50
            for i in range(0, len(all_video_ids), batch_size):
                batch = all_video_ids[i:i + batch_size]
                
                # Get details for this batch of videos
                details_response = self.get_video_details_batch(batch)
                
                if details_response and 'items' in details_response:
                    # Create lookup map for efficiency
                    details_map = {}
                    for item in details_response['items']:
                        details_map[item['id']] = item
                    
                    # Update videos with details
                    for video in channel_data['video_id']:
                        if 'video_id' in video and video['video_id'] in details_map:
                            item = details_map[video['video_id']]
                            
                            # Update from snippet
                            if 'snippet' in item:
                                for field in ['title', 'description', 'publishedAt']:
                                    if field in item['snippet']:
                                        # Convert publishedAt to published_at to match our schema
                                        dest_field = 'published_at' if field == 'publishedAt' else field
                                        video[dest_field] = item['snippet'][field]
                            
                            # Update from statistics
                            if 'statistics' in item:
                                video['views'] = item['statistics'].get('viewCount', video.get('views', '0'))
                                video['likes'] = item['statistics'].get('likeCount', video.get('likes', '0'))
                                video['comment_count'] = item['statistics'].get('commentCount', video.get('comment_count', '0'))
                                
                                # Also store statistics object for consistency with new channel flow
                                video['statistics'] = item['statistics']
            
            # Apply video formatter to ensure consistent data structure
            from src.utils.video_formatter import fix_missing_views
            channel_data['video_id'] = fix_missing_views(channel_data['video_id'])
            
            return channel_data
            
        except Exception as e:
            debug_log(f"Error refreshing video details: {str(e)}")
            channel_data['error_videos'] = f"Error refreshing videos: {str(e)}"
            return channel_data
