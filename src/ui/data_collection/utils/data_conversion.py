"""
Data conversion utilities for the data collection UI.
"""
from src.utils.helpers import debug_log

def convert_db_to_api_format(db_data):
    """
    Convert database-format channel data to API format for consistent processing.
    
    Args:
        db_data (dict): Channel data from the database
        
    Returns:
        dict: Data converted to API-compatible format
    """
    # Create a new dict for the API format
    api_format = {}
    
    # Mark the data source even if data is empty
    api_format['data_source'] = 'database'
    
    # If no data provided, return minimal structure
    if not db_data:
        debug_log("Empty data provided to convert_db_to_api_format, returning minimal structure")
        api_format['video_id'] = []
        return api_format
        
    # Extract channel info if available
    if 'channel_info' in db_data:
        channel_info = db_data['channel_info']
        
        # Extract basic channel info
        if 'id' in channel_info:
            api_format['channel_id'] = channel_info['id']
        
        if 'title' in channel_info:
            api_format['channel_name'] = channel_info['title']
            
        if 'description' in channel_info:
            api_format['channel_description'] = channel_info['description']
            
        # Extract statistics if available
        if 'statistics' in channel_info:
            stats = channel_info['statistics']
            
            if 'subscriberCount' in stats:
                try:
                    api_format['subscribers'] = int(stats['subscriberCount'])
                except (ValueError, TypeError):
                    api_format['subscribers'] = stats['subscriberCount']
                
            if 'viewCount' in stats:
                try:
                    api_format['views'] = int(stats['viewCount'])
                except (ValueError, TypeError):
                    api_format['views'] = stats['viewCount']
                
            if 'videoCount' in stats:
                try:
                    api_format['total_videos'] = int(stats['videoCount'])
                except (ValueError, TypeError):
                    api_format['total_videos'] = stats['videoCount']
        
        # Extract playlist info if available
        if 'contentDetails' in channel_info and 'relatedPlaylists' in channel_info['contentDetails']:
            playlists = channel_info['contentDetails']['relatedPlaylists']
            if 'uploads' in playlists:
                api_format['playlist_id'] = playlists['uploads']
    
    # Handle partial data - ensure at least these fields exist with defaults
    if 'channel_info' in db_data and 'id' in db_data['channel_info']:
        # If we have a channel ID but missing other fields, set defaults
        if 'channel_id' not in api_format:
            api_format['channel_id'] = db_data['channel_info']['id']
            
        if 'channel_name' not in api_format and 'title' in db_data['channel_info']:
            api_format['channel_name'] = db_data['channel_info']['title']
    
    # Convert video data if present
    if 'videos' in db_data and isinstance(db_data['videos'], list):
        api_format['video_id'] = []
        
        for video in db_data['videos']:
            video_item = {}
            
            # Extract video ID
            if 'id' in video:
                video_item['video_id'] = video['id']
                
            # Extract video snippet info
            if 'snippet' in video:
                snippet = video['snippet']
                
                if 'title' in snippet:
                    video_item['title'] = snippet['title']
                
                if 'description' in snippet:
                    video_item['video_description'] = snippet['description']
                
                if 'publishedAt' in snippet:
                    video_item['published_at'] = snippet['publishedAt']
                    
                    # Add a simplified date field (no time)
                    try:
                        # Just take the date part (YYYY-MM-DD)
                        video_item['published_date'] = snippet['publishedAt'].split('T')[0]
                    except (IndexError, AttributeError):
                        pass
            
            # Extract video statistics
            if 'statistics' in video:
                stats = video['statistics']
                
                if 'viewCount' in stats:
                    video_item['views'] = stats['viewCount']
                
                if 'likeCount' in stats:
                    video_item['likes'] = stats['likeCount']
                
                if 'commentCount' in stats:
                    video_item['comment_count'] = stats['commentCount']
            
            # Extract content details
            if 'contentDetails' in video and 'duration' in video['contentDetails']:
                video_item['duration'] = video['contentDetails']['duration']
                
            # Add thumbnails if available
            if 'snippet' in video and 'thumbnails' in video['snippet']:
                # Use the highest quality thumbnail available
                thumbs = video['snippet']['thumbnails']
                if 'maxres' in thumbs:
                    video_item['thumbnails'] = thumbs['maxres'].get('url', '')
                elif 'high' in thumbs:
                    video_item['thumbnails'] = thumbs['high'].get('url', '')
                elif 'medium' in thumbs:
                    video_item['thumbnails'] = thumbs['medium'].get('url', '')
                elif 'default' in thumbs:
                    video_item['thumbnails'] = thumbs['default'].get('url', '')
            
            # Add the video to the list
            api_format['video_id'].append(video_item)
        
        debug_log(f"Converted {len(api_format['video_id'])} videos from database format.")
    elif 'video_id' in db_data and isinstance(db_data['video_id'], list):
        # Video data is already in the right format
        api_format['video_id'] = db_data['video_id']
        debug_log(f"Video data already in correct format. Found {len(api_format['video_id'])} videos.")
    else:
        # Add empty video list if missing
        api_format['video_id'] = []
        debug_log("No videos found in data, added empty video list.")
        
    return api_format

def format_number(num):
    """
    Format a number with thousands separators.
    
    Args:
        num (int or float): Number to format
        
    Returns:
        str: Formatted number string
    """
    try:
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)