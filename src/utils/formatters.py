"""
Formatting utilities for the YouTube Data Hub application.
"""
import re
from typing import Optional, Union, Dict, Any
from datetime import timedelta

# Import duration formatting utilities
from src.utils.duration_utils import (
    duration_to_seconds,
    format_duration,
    format_duration_human_friendly
)

# Re-export for backward compatibility
__all__ = [
    'format_number',
    'format_duration',
    'duration_to_seconds',
    'format_duration_human_friendly',
    'format_timedelta',
    'get_thumbnail_url',
    'get_location_display'
]

def format_number(num: Union[int, str, float, None]) -> str:
    """
    Format large numbers in human-readable form
    
    Args:
        num: The number to format
        
    Returns:
        Formatted string representation (e.g. 1K, 1.5M)
    """
    try:
        if num is None:
            return "0"
        
        # Convert string to number if needed
        if isinstance(num, str):
            num = float(num)
        
        # Format the number
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B".replace(".0", "")
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M".replace(".0", "")
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K".replace(".0", "")
        else:
            return str(int(num))
    except:
        return str(num)

def format_duration(duration_str: Optional[str]) -> str:
    """
    Format YouTube duration string into human-readable format
    
    Args:
        duration_str: YouTube duration string (e.g. PT1H30M20S)
        
    Returns:
        Formatted duration string (e.g. 1:30:20)
    """
    if not duration_str:
        return "0:00"
        
    # Extract hours, minutes, and seconds
    hours_match = re.search(r'(\d+)H', duration_str)
    minutes_match = re.search(r'(\d+)M', duration_str)
    seconds_match = re.search(r'(\d+)S', duration_str)
    
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    # Format the duration
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def duration_to_seconds(duration_str: Optional[str]) -> int:
    """
    Convert YouTube duration string to seconds
    
    Args:
        duration_str: YouTube duration string (e.g. PT1H30M20S)
        
    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0
        
    # Extract hours, minutes, and seconds
    hours_match = re.search(r'(\d+)H', duration_str)
    minutes_match = re.search(r'(\d+)M', duration_str)
    seconds_match = re.search(r'(\d+)S', duration_str)
    
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    # Convert to seconds
    return hours * 3600 + minutes * 60 + seconds

def format_timedelta(delta: timedelta) -> str:
    """
    Format a timedelta object into a human-readable string
    
    Args:
        delta: A timedelta object
        
    Returns:
        Formatted string (e.g. "2 days ago", "5 hours ago")
    """
    seconds = int(delta.total_seconds())
    
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''} ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"

def get_thumbnail_url(video_data: Dict[str, Any]) -> str:
    """
    Extract thumbnail URL from video data with fallback options
    
    Args:
        video_data: Video data dictionary from YouTube API or database
        
    Returns:
        URL string to the best available thumbnail
    """
    # Handle different data formats for thumbnails
    try:
        if isinstance(video_data, dict):
            # Check for thumbnails in snippet or directly in video data
            thumbnails = video_data.get('snippet', {}).get('thumbnails', video_data.get('thumbnails', {}))
            
            # If we have thumbnails, get the best quality available (in descending order)
            if thumbnails:
                for size in ['maxres', 'standard', 'high', 'medium', 'default']:
                    if size in thumbnails and thumbnails[size].get('url'):
                        return thumbnails[size]['url']
                
        # If we have a direct thumbnail URL
        if isinstance(video_data, dict) and 'thumbnail_url' in video_data:
            return video_data['thumbnail_url']
            
    except Exception as e:
        # Default to YouTube placeholder image if an error occurs
        pass
        
    # Default placeholder thumbnail
    return "https://i.ytimg.com/vi/default/hqdefault.jpg"

def get_location_display(video_data: Dict[str, Any]) -> str:
    """
    Format location information from video data
    
    Args:
        video_data: Video data dictionary
        
    Returns:
        Formatted location string or empty string if no location
    """
    location = ""
    
    try:
        # Check if recording details and location data exist
        recording_details = video_data.get('recordingDetails', {})
        
        if not recording_details:
            # Try alternative location in different formats
            location_data = video_data.get('location', {})
            
            if location_data:
                lat = location_data.get('latitude')
                lng = location_data.get('longitude')
                
                if lat and lng:
                    return f"📍 {round(lat, 2)}, {round(lng, 2)}"
            
            return ""
            
        # Extract location data
        location_data = recording_details.get('location', {})
        if not location_data:
            return ""
            
        # Format latitude and longitude if available
        lat = location_data.get('latitude')
        lng = location_data.get('longitude')
        
        if lat and lng:
            location = f"📍 {round(lat, 2)}, {round(lng, 2)}"
            
        # Add location description if available
        location_description = recording_details.get('locationDescription')
        if location_description:
            if location:
                location += f" ({location_description})"
            else:
                location = f"📍 {location_description}"
                
    except Exception:
        return ""
        
    return location
