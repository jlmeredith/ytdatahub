"""
Initialization file for the YouTube API modules.
Exports the main YouTubeAPI class and individual clients.
"""
from src.api.youtube.base import YouTubeBaseClient
from src.api.youtube.channel import ChannelClient
from src.api.youtube.video import VideoClient
from src.api.youtube.comment import CommentClient
from src.api.youtube.resolver import ChannelResolver

__all__ = [
    'YouTubeAPI',
    'YouTubeBaseClient',
    'ChannelClient',
    'VideoClient',
    'CommentClient',
    'ChannelResolver'
]

class YouTubeAPI:
    """
    Main YouTube API client that combines functionality from all specialized clients.
    This class maintains backward compatibility with the original YouTubeAPI.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the YouTube API client with specialized sub-clients
        
        Args:
            api_key: YouTube Data API key
        """
        self.api_key = api_key
        self.channel_client = ChannelClient(api_key)
        self.video_client = VideoClient(api_key)
        self.comment_client = CommentClient(api_key)
        
        # For backward compatibility
        self.youtube = self.channel_client.youtube if self.channel_client.is_initialized() else None
    
    def is_initialized(self) -> bool:
        """Check if the API client is properly initialized"""
        return self.channel_client.is_initialized()
    
    # Delegate methods to specialized clients
    def get_channel_info(self, channel_id):
        """Get channel information by channel ID"""
        return self.channel_client.get_channel_info(channel_id)
    
    def get_channel_videos(self, channel_info, max_videos=0):
        """Get videos from a channel's uploads playlist"""
        return self.video_client.get_channel_videos(channel_info, max_videos)
    
    def get_videos_details(self, video_ids):
        """Get detailed information for a batch of videos by their IDs"""
        return self.video_client.get_videos_details(video_ids)
    
    def get_video_comments(self, channel_info, max_comments_per_video=10):
        """Get comments for each video in the channel"""
        return self.comment_client.get_video_comments(channel_info, max_comments_per_video)
    
    def resolve_custom_channel_url(self, custom_url_or_handle):
        """Resolve a custom URL or handle (@username) to a channel ID"""
        return self.channel_client.resolver.resolve_custom_channel_url(custom_url_or_handle)
    
    def test_connection(self):
        """
        Test the API connection with a simple request
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Try a simple API call to confirm the API key works
            # This performs a search with minimal quota use
            if not self.is_initialized():
                return False
                
            # Simple test using a channel search (costs 1 unit)
            # We only need to know if it succeeds, not the actual results
            self.youtube.search().list(
                part="snippet",
                maxResults=1,
                type="channel",
                q="YouTube"
            ).execute()
            
            return True
        except Exception as e:
            from src.utils.helpers import debug_log
            debug_log(f"API test connection failed: {str(e)}")
            return False