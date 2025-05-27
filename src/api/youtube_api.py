"""
YouTube API client implementation for the YouTube scraper application.
This module is maintained for backward compatibility and delegates
to the specialized modules in the youtube/ directory.
"""
from typing import Dict, List, Any, Optional, Tuple

from src.utils.helpers import debug_log
from src.api.youtube import YouTubeAPI as ModularYouTubeAPI

# Define the YouTubeAPIError class that was missing
class YouTubeAPIError(Exception):
    """
    Custom exception class for YouTube API errors.
    Provides structured error information with status code and error type.
    """
    def __init__(self, message, status_code=None, error_type=None, additional_info=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.additional_info = additional_info or {}
    
    def __str__(self):
        base_message = f"{self.message} (Status: {self.status_code}, Type: {self.error_type})"
        if self.additional_info:
            base_message += f" Additional info: {self.additional_info}"
        return base_message

# For backward compatibility
class YouTubeAPI(ModularYouTubeAPI):
    """
    YouTube Data API client for fetching channel and video data.
    This implementation delegates to the specialized YouTube API modules.
    """
    def get_channel_videos(self, channel_id, max_videos=50, page_token=None, next_page_token=None, optimize_quota=False):
        """
        Get videos for a specific YouTube channel.
        
        Args:
            channel_id (str): YouTube channel ID
            max_videos (int): Maximum number of videos to retrieve
            page_token (str, optional): Token for pagination (new parameter name)
            next_page_token (str, optional): Token for pagination (legacy support)
            optimize_quota (bool): Whether to optimize quota usage
            
        Returns:
            dict: Dictionary containing video information
        """
        from googleapiclient.errors import HttpError
        
        try:
            # Use page_token if provided, fall back to next_page_token for backward compatibility
            pagination_token = page_token if page_token is not None else next_page_token
            
            # Ensure channel_id is a string (handle case where channel_data dict is passed)
            if isinstance(channel_id, dict):
                channel_id = channel_id.get('channel_id')
                
            if not channel_id:
                return None
            
            # Get the channel's uploads playlist
            channel_response = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()
            
            if not channel_response.get("items"):
                return None
                
            # Get the uploads playlist ID
            uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Initialize container for all videos
            all_videos = []
            
            # Use provided pagination token or None for first request
            # (compatibility with both page_token and next_page_token parameters)
            token = pagination_token
            
            # Track if this is the first page (important for pagination error handling)
            is_first_page = pagination_token is None
            
            # Also track the pagination token we're using in case of errors
            current_page_token = token
            
            # Keep fetching videos until we reach the max or run out of pages
            while len(all_videos) < max_videos or max_videos == 0:
                try:
                    # Get current page of videos
                    playlist_response = self.youtube.playlistItems().list(
                        part="snippet,contentDetails",
                        playlistId=uploads_playlist_id,
                        maxResults=min(50, max_videos - len(all_videos)) if max_videos > 0 else 50,
                        pageToken=token
                    ).execute()
                    
                    # Extract videos from the response
                    videos = playlist_response.get("items", [])
                    
                    # Get the token for the next page, if available
                    next_page = playlist_response.get("nextPageToken")
                    
                    # Transform the video data into the expected format
                    for video in videos:
                        video_data = {
                            'video_id': video["contentDetails"]["videoId"],
                            'title': video["snippet"]["title"],
                            'published_at': video["snippet"]["publishedAt"],
                            # Note: We don't have views/likes/comments yet - those require a separate API call
                        }
                        all_videos.append(video_data)
                    
                    # Stop if there's no next page or we've reached the limit
                    if not next_page or (max_videos > 0 and len(all_videos) >= max_videos):
                        break
                        
                    # Otherwise, update the pagination token and continue
                    token = next_page
                    current_page_token = token
                    
                except HttpError as e:
                    # If this is not the first page, we have a pagination error
                    if not is_first_page:
                        # Add pagination context to the error
                        error = YouTubeAPIError(str(e), status_code=e.resp.status, error_type="serverError")
                        error.during_pagination = True
                        error.error_context = {'next_page_token': current_page_token}
                        raise error
                    else:
                        # If it's the first page, re-raise the original error
                        raise
            
            # Return the formatted response
            return {
                'channel_id': channel_id,
                'video_id': all_videos
            }
            
        except HttpError as e:
            # If we have some videos but get an error during pagination
            if all_videos and current_page_token:
                # Create a YouTubeAPIError that has pagination context
                error = YouTubeAPIError(str(e), status_code=e.resp.status, error_type="serverError")
                error.during_pagination = True
                error.error_context = {'next_page_token': current_page_token}
                
                # Still return the videos we have, along with the error
                result = {
                    'channel_id': channel_id,
                    'video_id': all_videos,
                    'pagination_error': str(error),
                    'next_page_token': current_page_token
                }
                
                # But also raise the error for proper test handling
                raise error
            else:
                # Regular error handling when we have no videos
                raise YouTubeAPIError(str(e), status_code=e.resp.status, error_type="serverError")
        
        except Exception as e:
            debug_log(f"Error getting channel videos: {str(e)}")
            # Convert general exceptions to YouTubeAPIError
            if isinstance(e, HttpError):
                raise YouTubeAPIError(str(e), status_code=e.resp.status, error_type="serverError")
            else:
                raise YouTubeAPIError(str(e), status_code=500, error_type="serverError")

    def get_video_details_batch(self, video_ids):
        """
        Get detailed information for a batch of videos
        
        Args:
            video_ids (list): List of video IDs
            
        Returns:
            dict: Response containing video details with 'items' containing the video data
        """
        from googleapiclient.errors import HttpError
        
        try:
            if not video_ids:
                debug_log("Warning: get_video_details_batch called with empty video_ids list")
                return {'items': []}
                
            # Log for debugging
            debug_log(f"Getting details for {len(video_ids)} videos in batch")
            debug_log(f"First few video IDs: {video_ids[:5]}")
                
            # The YouTube API can only handle 50 video IDs at once
            max_results_per_request = 50
            all_items = []
            
            # Process video IDs in batches of 50
            for i in range(0, len(video_ids), max_results_per_request):
                batch = video_ids[i:i + max_results_per_request]
                debug_log(f"Processing batch {i//max_results_per_request + 1} with {len(batch)} videos")
                
                # Call the videos.list API endpoint
                response = self.youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(batch)
                ).execute()
                
                # Check if we got any items
                items = response.get('items', [])
                debug_log(f"Received {len(items)} video details in response")
                
                # Add video results to our list
                all_items = []
                all_items.extend(response.get('items', []))
                
                # Handle API rate limiting if needed
                if i + max_results_per_request < len(video_ids):
                    import time
                    time.sleep(0.5)  # Add a small delay between requests to avoid quota issues
                    
            # Return a dict with 'items' key to match YouTube API structure
            return {'items': all_items}
            
        except HttpError as e:
            # Convert YouTube API errors to our custom format
            raise YouTubeAPIError(str(e), status_code=e.resp.status, error_type="serverError")
        except Exception as e:
            # Handle general exceptions
            raise YouTubeAPIError(str(e), status_code=500, error_type="serverError")

    def get_playlist_id_for_channel(self, channel_id: str) -> str:
        """
        Fetch the uploads playlist ID for a channel using the YouTube API.
        Returns the playlist ID string or empty string if not found or invalid.
        
        Args:
            channel_id (str): YouTube channel ID
            
        Returns:
            str: Uploads playlist ID or empty string if not found/invalid
        """
        try:
            debug_log(f"[API] Fetching uploads playlist ID for channel_id={channel_id}")
            
            response = self.youtube.channels().list(
                part="snippet,contentDetails,statistics,brandingSettings,status,topicDetails,localizations",
                id=channel_id
            ).execute()
            
            if response and 'items' in response and response['items']:
                playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                # Validate playlist_id: must not be channel_id and must start with 'UU'
                if not playlist_id or playlist_id == channel_id or not playlist_id.startswith('UU'):
                    debug_log(f"[API][ERROR] Invalid playlist_id fetched for channel_id={channel_id}: {playlist_id}")
                    return ''
                
                debug_log(f"[API] Found valid playlist_id={playlist_id} for channel_id={channel_id}")
                return playlist_id
            else:
                debug_log(f"[API] No playlist_id found for channel_id={channel_id}")
                return ''
        except Exception as e:
            debug_log(f"[API] Error fetching playlist_id for channel_id={channel_id}: {str(e)}")
            return ''

    def execute_api_request(self, operation, **kwargs):
        """
        Execute an API request with the given operation and parameters.
        This method is primarily used for quota tracking and optimization.
        
        Args:
            operation (str): The API operation to execute (e.g., 'channels.list')
            **kwargs: Additional parameters for the API request
            
        Returns:
            dict: The API response
        """
        # Track quota usage if we have a tracking method
        if hasattr(self, 'increment_quota_usage'):
            self.increment_quota_usage(operation)
            
        # In a real implementation, this would make the actual API call
        # For tests, this is mocked to return predetermined responses
        if operation == 'channels.list':
            return self.get_channel_info(kwargs.get('id', ''))
        elif operation == 'playlistItems.list':
            return self.get_channel_videos(kwargs.get('playlistId', ''))
        elif operation == 'videos.list':
            return self.get_video_details_batch(kwargs.get('id', []))
        elif operation == 'commentThreads.list':
            return self.get_video_comments(kwargs.get('videoId', []))
        
        # Default empty response
        return {}

# Maintain backward compatibility
__all__ = ['YouTubeAPI', 'YouTubeAPIError']