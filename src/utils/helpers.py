"""
Utility helper functions for the YouTube scraper application.
"""
import re
import os
import json
import shutil
import logging
import streamlit as st
from datetime import datetime
from typing import Any, Dict, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def debug_log(message: str, data: Any = None):
    """Log debug messages to server console if debug mode is enabled"""
    if st.session_state.debug_mode:
        if data is not None:
            # Format data for display
            if isinstance(data, dict) or isinstance(data, list):
                try:
                    data_str = json.dumps(data, indent=2)
                except:
                    data_str = str(data)
            else:
                data_str = str(data)
            
            # Truncate if too long
            if len(data_str) > 1000:
                data_str = data_str[:1000] + "... [truncated]"
            
            logging.debug(f"{message}:\n{data_str}")
        else:
            logging.debug(message)

def estimate_quota_usage(fetch_channel=None, fetch_videos=None, fetch_comments=None, 
                         video_count=None, comments_count=None):
    """
    Estimates YouTube API quota points that will be used with current settings
    
    Args:
        fetch_channel: Whether to fetch channel data (defaults to session state if None)
        fetch_videos: Whether to fetch videos (defaults to session state if None)
        fetch_comments: Whether to fetch comments (defaults to session state if None)
        video_count: Number of videos to fetch (defaults to session state if None)
        comments_count: Number of comments per video (default 10 if None)
    
    Returns:
        int: Estimated quota usage
    """
    # Use parameters if provided, otherwise fall back to session state
    fetch_channel = fetch_channel if fetch_channel is not None else st.session_state.fetch_channel_data
    fetch_videos = fetch_videos if fetch_videos is not None else st.session_state.fetch_videos
    fetch_comments = fetch_comments if fetch_comments is not None else st.session_state.fetch_comments
    video_count = video_count if video_count is not None else st.session_state.max_videos
    comments_count = comments_count if comments_count is not None else 10
    
    # Base quota for channel info
    quota = 1 if fetch_channel else 0
    
    # Quota for video list
    # Each page of playlist items costs 1 unit, each page has 50 videos
    if fetch_videos:
        video_pages = (video_count + 49) // 50  # Ceiling division
        quota += video_pages
        
        # Each batch of 50 videos costs 1 unit for details
        video_batches = (video_count + 49) // 50
        quota += video_batches
        
        # Comments cost 1 unit per video
        if fetch_comments:
            quota += video_count
    
    return quota

def duration_to_seconds(duration):
    """Convert YouTube duration format (PT1H2M3S) to seconds"""
    if not duration or not isinstance(duration, str):
        return 0
        
    # Use regex to properly extract all components
    hours = re.search(r'(\d+)H', duration)
    minutes = re.search(r'(\d+)M', duration)
    seconds = re.search(r'(\d+)S', duration)
    
    # Convert to seconds
    total_seconds = 0
    if hours:
        total_seconds += int(hours.group(1)) * 3600
    if minutes:
        total_seconds += int(minutes.group(1)) * 60
    if seconds:
        total_seconds += int(seconds.group(1))
    
    return total_seconds

def parse_duration_with_regex(duration_str: str) -> int:
    """
    Parse YouTube duration string (ISO 8601) to seconds using regex
    Example: 'PT1H2M3S' -> 3723 seconds
    """
    if not duration_str:
        return 0
    
    # Extract hours, minutes, and seconds with regex
    hours = re.search(r'(\d+)H', duration_str)
    minutes = re.search(r'(\d+)M', duration_str)
    seconds = re.search(r'(\d+)S', duration_str)
    
    # Convert to seconds
    total_seconds = 0
    if hours:
        total_seconds += int(hours.group(1)) * 3600
    if minutes:
        total_seconds += int(minutes.group(1)) * 60
    if seconds:
        total_seconds += int(seconds.group(1))
    
    return total_seconds

def format_duration(seconds):
    """Format seconds as HH:MM:SS or MM:SS depending on length"""
    if seconds is None or seconds <= 0:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    # For videos under an hour, use MM:SS format
    if hours == 0:
        return f"{minutes:02d}:{secs:02d}"
    
    # For longer videos, use HH:MM:SS format
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_duration_human_friendly(seconds):
    """
    Format seconds into a human-friendly duration string.
    Examples: "3 hours 42 minutes", "5 minutes 17 seconds", "2 hours 1 minute", etc.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds is None or seconds <= 0:
        return "0 seconds"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    
    # Add hours if present
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    
    # Add minutes if present
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    # Add seconds if present, or if it's the only component
    if secs > 0 or (hours == 0 and minutes == 0):
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    
    # Join the parts based on how many we have
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:  # len(parts) == 3
        return f"{parts[0]}, {parts[1]}, and {parts[2]}"

def format_number(num: int) -> str:
    """Format large numbers in human-readable form"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)

def validate_api_key(api_key: str) -> bool:
    """Basic validation for YouTube API key format"""
    # API keys should be about 39 characters long and contain alphanumeric chars
    if not api_key or len(api_key) < 30:
        return False
    
    # Check if it has valid characters (alphanumeric and some special chars)
    if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
        return False
    
    return True

def validate_channel_id(input_string: str) -> tuple[bool, str]:
    """
    Validate and extract YouTube channel ID from either a direct ID or channel URL.
    
    Args:
        input_string: Either a channel ID or a channel URL
        
    Returns:
        Tuple of (is_valid, channel_id)
    """
    # Clean the input string
    cleaned_input = input_string.strip()
    
    # Case 1: Direct channel ID (e.g., 'UCxxx...')
    if cleaned_input.startswith('UC') and len(cleaned_input) >= 20:
        # Check if it only contains valid characters
        if re.match(r'^[A-Za-z0-9_-]+$', cleaned_input):
            return True, cleaned_input
    
    # Case 2: Channel URL formats
    # Handle common YouTube channel URL formats:
    
    # Format: https://www.youtube.com/channel/UCxxx...
    channel_pattern = r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([a-zA-Z0-9_-]+)'
    channel_match = re.match(channel_pattern, cleaned_input)
    if channel_match:
        channel_id = channel_match.group(1)
        if channel_id.startswith('UC') and len(channel_id) >= 20:
            return True, channel_id
    
    # Format: https://www.youtube.com/c/ChannelName or /user/UserName
    # These require an API call to resolve, which we'll handle in the YouTube service
    custom_pattern = r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/(?:c|user)\/([a-zA-Z0-9_-]+)'
    custom_match = re.match(custom_pattern, cleaned_input)
    if custom_match:
        # We'll return a special signal that this needs to be resolved
        # The YouTube service will need to look up the actual channel ID
        return False, f"resolve:{custom_match.group(1)}"
    
    # Format: https://www.youtube.com/@username
    handle_pattern = r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)'
    handle_match = re.match(handle_pattern, cleaned_input)
    if handle_match:
        # Also needs API resolution
        return False, f"resolve:@{handle_match.group(1)}"
    
    # Not a valid channel ID or URL format
    return False, ""

# Keep the old function for backward compatibility
def validate_channel_id_old(channel_id: str) -> bool:
    """Basic validation for YouTube channel ID format (legacy function)"""
    # Channel IDs typically start with 'UC' and are about 24 chars long
    if not channel_id or len(channel_id) < 20:
        return False
    
    # Most channel IDs start with 'UC'
    if not channel_id.startswith('UC'):
        return False
    
    # Channel IDs contain only alphanumeric chars and a few special chars
    if not re.match(r'^[A-Za-z0-9_-]+$', channel_id):
        return False
    
    return True

def clear_cache(clear_api_cache: bool = True, clear_python_cache: bool = True, 
                clear_db_cache: bool = True, verbose: bool = True) -> Dict[str, Any]:
    """
    Clear all caches in the application
    
    Args:
        clear_api_cache: Whether to clear the Streamlit session state API cache
        clear_python_cache: Whether to clear Python __pycache__ directories
        clear_db_cache: Whether to clear any database caches
        verbose: Whether to log detailed information about cache clearing
        
    Returns:
        A dictionary with information about what was cleared
    """
    results = {
        "api_cache_cleared": False,
        "python_cache_cleared": False,
        "db_cache_cleared": False,
        "python_cache_dirs_removed": [],
        "total_items_cleared": 0
    }
    
    # Clear API cache from session state
    if clear_api_cache and hasattr(st, 'session_state') and hasattr(st.session_state, 'api_cache'):
        cache_size = len(st.session_state.api_cache)
        st.session_state.api_cache = {}
        results["api_cache_cleared"] = True
        results["total_items_cleared"] += cache_size
        
        if verbose:
            debug_log(f"Cleared {cache_size} items from API cache")
    
    # Clear Python __pycache__ directories
    if clear_python_cache:
        # Get the root directory of the application
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        # Find and remove all __pycache__ directories
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if '__pycache__' in dirnames:
                pycache_path = os.path.join(dirpath, '__pycache__')
                try:
                    # Count files before removing
                    file_count = len(os.listdir(pycache_path))
                    results["total_items_cleared"] += file_count
                    
                    # Remove the directory
                    shutil.rmtree(pycache_path)
                    results["python_cache_dirs_removed"].append(pycache_path)
                    
                    if verbose:
                        debug_log(f"Removed __pycache__ directory: {pycache_path} ({file_count} files)")
                except Exception as e:
                    if verbose:
                        debug_log(f"Error removing __pycache__ directory {pycache_path}: {str(e)}")
        
        results["python_cache_cleared"] = len(results["python_cache_dirs_removed"]) > 0
    
    # Clear database cache if needed
    if clear_db_cache:
        try:
            # Import here to avoid circular imports
            from src.database.sqlite import SQLiteDatabase
            
            # Get a database instance and clear its cache
            db = SQLiteDatabase()
            db.clear_cache()
            
            results["db_cache_cleared"] = True
            
            if verbose:
                debug_log("Database cache cleared")
        except Exception as e:
            if verbose:
                debug_log(f"Error clearing database cache: {str(e)}")
    
    # Display summary if verbose
    if verbose:
        debug_log(f"Cache clearing complete. Total items cleared: {results['total_items_cleared']}")
    
    return results