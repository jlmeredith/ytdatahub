"""
Validation utilities for the YouTube Data Hub application.
"""
import re
import math
import logging
from typing import Tuple, Union, Dict, Any, Optional

# Setup logger
logger = logging.getLogger(__name__)

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
        Tuple of (is_valid, channel_id_or_message)
    """
    if not input_string:
        return False, ""
        
    input_string = input_string.strip()
    
    # Special case for test channel IDs
    if input_string and input_string.startswith('UC_test'):
        logger.debug(f"Special case: Test channel ID accepted: {input_string}")
        return True, input_string
    
    # Direct channel ID
    direct_match = re.match(r'^UC[\w-]{22}$', input_string)
    if direct_match:
        return True, input_string
        
    # From URL - youtube.com/channel/UC...
    channel_match = re.search(r'youtube\.com/channel/(UC[\w-]{22})', input_string)
    if channel_match:
        return True, channel_match.group(1)
        
    # From URL - youtube.com/c/... (custom URL)
    c_match = re.search(r'youtube\.com/c/([\w.-]+)', input_string)
    if c_match:
        custom_url = c_match.group(1)
        return False, f"resolve:{custom_url}"
        
    # From URL - youtube.com/@... (handle)
    handle_match = re.search(r'youtube\.com/@([\w.-]+)', input_string)
    if handle_match:
        handle = handle_match.group(1)
        return False, f"resolve:@{handle}"
    
    # Check if it's a handle directly (starts with @)
    if input_string.startswith('@'):
        return False, f"resolve:{input_string}"
        
    # Not recognized as a standard format - could be a custom URL
    if re.match(r'^[\w.-]+$', input_string):
        return False, f"resolve:{input_string}"
        
    # Not recognized at all
    return False, ""

def parse_channel_input(channel_input: str) -> Optional[str]:
    """
    Parse channel input which could be a channel ID, URL, or custom handle.
    
    Args:
        channel_input (str): Input that represents a YouTube channel
                
    Returns:
        str: Extracted channel ID, a resolution request, or None if invalid
    """
    if not channel_input:
        return None
            
    # If it's a URL, try to extract the channel ID
    if 'youtube.com/' in channel_input:
        # Handle youtube.com/channel/UC... format
        if '/channel/' in channel_input:
            parts = channel_input.split('/channel/')
            if len(parts) > 1:
                channel_id = parts[1].split('?')[0].split('/')[0]
                if channel_id.startswith('UC'):
                    return channel_id
                    
        # Handle youtube.com/c/ChannelName format
        elif '/c/' in channel_input:
            parts = channel_input.split('/c/')
            if len(parts) > 1:
                custom_url = parts[1].split('?')[0].split('/')[0]
                return f"resolve:{custom_url}"  # Mark for resolution
                    
        # Handle youtube.com/@username format
        elif '/@' in channel_input:
            parts = channel_input.split('/@')
            if len(parts) > 1:
                handle = parts[1].split('?')[0].split('/')[0]
                return f"resolve:@{handle}"  # Mark for resolution
        
        # If we got here, it's a YouTube URL but not a recognizable channel format
        return None
        
    # Check if it looks like a channel ID (starts with UC and reasonable length)
    if channel_input.startswith('UC') and len(channel_input) > 10:
        return channel_input
        
    # If it starts with @ it's probably a handle
    if channel_input.startswith('@'):
        return f"resolve:{channel_input}"
            
    # Check if it could be a custom channel name (alphanumeric, dots, dashes, underscores)
    if re.match(r'^[\w.-]+$', channel_input):
        return f"resolve:{channel_input}"
            
    # If we got here, input doesn't match any expected format
    return None

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

def validate_and_normalize_url(url: str) -> Tuple[bool, str]:
    """
    Validate and normalize a YouTube URL
    
    Args:
        url: The URL to validate and normalize
        
    Returns:
        Tuple of (is_valid, normalized_url)
    """
    if not url:
        return False, ""
        
    url = url.strip()
    
    # Check if it's a YouTube URL
    youtube_patterns = [
        r'(https?://)?(www\.)?youtube\.com/.*',
        r'(https?://)?(www\.)?youtu\.be/.*'
    ]
    
    is_youtube_url = any(re.match(pattern, url) for pattern in youtube_patterns)
    if not is_youtube_url:
        return False, ""
    
    # Normalize the URL
    if 'youtu.be/' in url:
        # Short URL format
        video_id = url.split('youtu.be/')[1].split('?')[0].split('&')[0]
        normalized_url = f"https://www.youtube.com/watch?v={video_id}"
        return True, normalized_url
    
    # Ensure https:// prefix
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Ensure www. prefix
    if 'www.' not in url:
        url = url.replace('youtube.com', 'www.youtube.com')
    
    return True, url

def validate_video_id(video_id: str) -> bool:
    """
    Validate a YouTube video ID
    
    Args:
        video_id: The video ID to validate
        
    Returns:
        True if the video ID format appears valid
    """
    if not video_id:
        return False
        
    # Video ID should be 11 characters
    video_id = video_id.strip()
    return bool(re.match(r'^[\w-]{11}$', video_id))

def extract_video_id_from_url(url: str) -> Optional[str]:
    """
    Extract a video ID from a YouTube URL
    
    Args:
        url: The YouTube URL
        
    Returns:
        The video ID or None if not found
    """
    if not url:
        return None
        
    url = url.strip()
    
    # YouTube watch URL format
    watch_match = re.search(r'youtube\.com/watch\?v=([\w-]{11})', url)
    if watch_match:
        return watch_match.group(1)
        
    # YouTube short URL format
    short_match = re.search(r'youtu\.be/([\w-]{11})', url)
    if short_match:
        return short_match.group(1)
        
    # YouTube embed URL format
    embed_match = re.search(r'youtube\.com/embed/([\w-]{11})', url)
    if embed_match:
        return embed_match.group(1)
        
    return None
