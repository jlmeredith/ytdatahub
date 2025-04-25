"""
Utility helper functions for the YouTube scraper application.
"""
import re
import os
import json
import shutil
import streamlit as st
from datetime import datetime
from typing import Any, Dict, Optional, List

def debug_log(message: str, data: Any = None):
    """Log debug messages to Streamlit if debug mode is enabled"""
    if st.session_state.debug_mode:
        current_time = datetime.now().strftime("%H:%M:%S")
        
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
            
            st.text(f"[DEBUG {current_time}] {message}:\n{data_str}")
        else:
            st.text(f"[DEBUG {current_time}] {message}")

def estimate_quota_usage():
    """Estimates YouTube API quota points that will be used with current settings"""
    # Base quota for channel info
    quota = 1 if st.session_state.fetch_channel_data else 0
    
    # Quota for video list
    # Each page of playlist items costs 1 unit, each page has 50 videos
    if st.session_state.fetch_videos:
        video_pages = (st.session_state.max_videos + 49) // 50  # Ceiling division
        quota += video_pages
        
        # Each batch of 50 videos costs 1 unit for details
        video_batches = (st.session_state.max_videos + 49) // 50
        quota += video_batches
        
        # Comments cost 1 unit per video
        if st.session_state.fetch_comments:
            quota += st.session_state.max_videos
    
    return quota

def duration_to_seconds(duration):
    """Convert YouTube duration format (PT1H2M3S) to seconds"""
    duration = duration[2:]  # Remove the 'PT' prefix
    seconds = 0

    # Check for hours
    if 'H' in duration:
        hours, duration = duration.split('H')
        seconds += int(hours) * 3600

    # Check for minutes
    if 'M' in duration:
        minutes, duration = duration.split('M')
        seconds += int(minutes) * 60

    # Check for seconds
    if 'S' in duration:
        seconds = duration.split('S')[0]

    return int(seconds)

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
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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

def validate_channel_id(channel_id: str) -> bool:
    """Basic validation for YouTube channel ID format"""
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