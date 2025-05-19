"""
Validation utilities for the YouTube Data Hub application.
"""
import re
from typing import Tuple, Union, Dict, Any, Optional

def validate_api_key(api_key: str) -> bool:
    """
    Basic validation for YouTube API key format
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if the key format appears valid
    """
    if not api_key:
        return False
        
    # API key format validation
    # Google API keys are typically 39 characters long
    # and contain alphanumeric characters plus may contain _-
    api_key = api_key.strip()
    
    # Basic format check
    if len(api_key) < 30 or len(api_key) > 50:
        return False
        
    # Check character set
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
    return all(c in allowed_chars for c in api_key)

def validate_channel_id(input_string: str) -> Tuple[bool, str]:
    """
    Validate a channel ID and extract it from various formats
    
    Args:
        input_string: String that might contain a channel ID or URL
        
    Returns:
        Tuple of (is_valid, channel_id)
    """
    if not input_string:
        return False, ""
        
    input_string = input_string.strip()
    
    # Direct channel ID
    direct_match = re.match(r'^UC[\w-]{22}$', input_string)
    if direct_match:
        return True, input_string
        
    # From URL - youtube.com/channel/UC...
    channel_match = re.search(r'youtube\.com/channel/(UC[\w-]{22})', input_string)
    if channel_match:
        return True, channel_match.group(1)
        
    # From URL - youtube.com/c/... (doesn't contain channel ID)
    c_match = re.search(r'youtube\.com/c/(\w+)', input_string)
    if c_match:
        return False, f"Custom URL: {c_match.group(1)} (needs resolution)"
        
    # From URL - youtube.com/@... (handle)
    handle_match = re.search(r'youtube\.com/@([\w.-]+)', input_string)
    if handle_match:
        return False, f"Handle: @{handle_match.group(1)} (needs resolution)"
        
    # Not recognized
    return False, ""

# Keep the old function for backward compatibility
def validate_channel_id_old(channel_id: str) -> bool:
    """
    Basic validation for YouTube channel ID format (legacy function)
    
    Args:
        channel_id: The channel ID to validate
        
    Returns:
        True if the channel ID format appears valid
    """
    if not channel_id:
        return False
        
    # Channel ID should start with UC and be followed by 22 characters
    channel_id = channel_id.strip()
    return bool(re.match(r'^UC[\w-]{22}$', channel_id))

def estimate_quota_usage(fetch_channel: bool = True, 
                         fetch_videos: bool = False, 
                         fetch_comments: bool = False,
                         video_count: int = 0,
                         comments_count: int = 0) -> int:
    """
    Estimate the YouTube API quota units needed for an operation
    
    Args:
        fetch_channel: Whether channel data is being fetched
        fetch_videos: Whether videos are being fetched
        fetch_comments: Whether comments are being fetched
        video_count: Number of videos to fetch
        comments_count: Average number of comments per video
        
    Returns:
        Estimated quota units
    """
    # Initialize quota count
    quota = 0
    
    # Add channel data quota (1 unit for channel list)
    if fetch_channel:
        quota += 1
        
    # Add video list quota (each video list request costs 1 unit)
    # About 50 videos per request, so calculate requests needed
    if fetch_videos and video_count > 0:
        # Each page of video results costs 1 unit and contains up to 50 videos
        video_requests = max(1, math.ceil(video_count / 50))
        quota += video_requests
        
        # Each video details request costs 1 unit for up to 50 videos
        video_detail_requests = max(1, math.ceil(video_count / 50))
        quota += video_detail_requests
        
    # Add comments quota (each comment thread request costs 1 unit)
    # About 100 comments per request, so calculate requests needed
    if fetch_comments and fetch_videos and video_count > 0:
        # Estimated number of comment requests based on video count and comments per video
        total_comments = video_count * comments_count
        comment_requests = max(1, math.ceil(total_comments / 100))
        quota += comment_requests
        
    return quota

import math  # Needed for ceiling function in estimate_quota_usage
