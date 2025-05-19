"""
Utility functions for handling and formatting time durations.
"""
import re

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

def duration_to_seconds(duration):
    """Convert YouTube duration format (PT1H2M3S) to seconds"""
    return parse_duration_with_regex(duration)

def format_duration(duration):
    """Format seconds as HH:MM:SS or MM:SS depending on length"""
    # Check if duration is a string (e.g., ISO 8601 format like 'PT1H2M3S')
    if isinstance(duration, str):
        if not duration:
            return "0:00"  # Handle empty string case
        # Convert ISO 8601 duration to seconds
        seconds = parse_duration_with_regex(duration)
    elif duration is None:
        return "0:00"  # Use consistent format for null/empty values
    else:
        # Assume it's already in seconds
        seconds = duration
        
    # Now handle formatting with numeric seconds
    if seconds <= 0:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    # For videos under an hour, use M:SS format (no leading zero for minutes if less than 10 minutes)
    if hours == 0:
        return f"{minutes}:{secs:02d}"
    
    # For longer videos, use H:MM:SS format (no leading zero for hours)
    return f"{hours}:{minutes:02d}:{secs:02d}"

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
