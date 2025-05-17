"""
YouTube service module to handle business logic related to YouTube data operations.
This layer sits between the UI and the API/storage layers.

This is now a facade that delegates to the modular implementation in the youtube package.
"""
# Re-export YouTubeService class for backward compatibility
from src.services.youtube.youtube_service_patched import YouTubeService

# Re-export specialized services for direct use if needed
from src.services.youtube import (
    QuotaService,
    StorageService,
    ChannelService,
    VideoService,
    CommentService,
    DeltaService,
    YouTubeServiceImpl
)

# Re-export helper function for backward compatibility
from src.services.youtube.channel_service import ChannelService

# Define parse_channel_input for backward compatibility
def parse_channel_input(channel_input):
    """
    Parse channel input which could be a channel ID, URL, or custom handle.
    This is a wrapper around ChannelService.parse_channel_input for backward compatibility.
    
    Args:
        channel_input (str): Input that represents a YouTube channel
            
    Returns:
        str: Extracted channel ID or the original input if it appears to be a valid ID
    """
    # Create a temporary instance of ChannelService
    channel_service = ChannelService()
    return channel_service.parse_channel_input(channel_input)

# For backward compatibility with existing imports
__all__ = [
    'YouTubeService',
    'QuotaService',
    'StorageService',
    'ChannelService',
    'VideoService',
    'CommentService',
    'DeltaService',
    'YouTubeServiceImpl',
    'parse_channel_input'
]