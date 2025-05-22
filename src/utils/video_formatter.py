"""
Helper functions for formatting and fixing video data
"""
from src.utils.helpers import debug_log
import json

def ensure_views_data(video_data):
    """
    Ensures that video data has views information properly set
    
    Args:
        video_data (list): List of video dictionaries
        
    Returns:
        list: List of videos with views properly set
    """
    if not video_data:
        return video_data
        
    for video in video_data:
        if not isinstance(video, dict):
            continue
            
        # Debug log all keys for first video
        video_id = video.get('video_id', 'unknown')
        debug_log(f"Video {video_id} keys: {list(video.keys())}")
        debug_log(f"Video {video_id} raw data: {str(video)[:200]}...")
        
        # Log current view value 
        debug_log(f"Video {video_id} current views value: '{video.get('views', 'Not present')}'")
        
        # Special handling for videos with string "0" views (likely placeholder)
        if 'views' in video and video['views'] == "0":
            debug_log(f"Video {video_id} has placeholder '0' string value, will try to find real view count")
            # Force it to try other paths by temporarily removing the "0" value
            video['original_views'] = video['views']  # Keep the original 
            video.pop('views', None)

        # Check for views data and ensure it's set properly
        if 'views' not in video or not video['views']:
            # Try to extract from statistics if available
            if 'statistics' in video and isinstance(video['statistics'], dict) and 'viewCount' in video['statistics']:
                debug_log(f"Setting views from statistics.viewCount: {video['statistics']['viewCount']}")
                video['views'] = video['statistics']['viewCount']
            elif 'contentDetails' in video and 'statistics' in video['contentDetails'] and 'viewCount' in video['contentDetails']['statistics']:
                debug_log(f"Setting views from contentDetails.statistics.viewCount: {video['contentDetails']['statistics']['viewCount']}")
                video['views'] = video['contentDetails']['statistics']['viewCount']
            else:
                # Try to recover view count from other possible locations
                if 'original_views' in video and video['original_views'] != "0":
                    video['views'] = video['original_views']
                    debug_log(f"Restored original views value: {video['views']}")
                else:
                    # Default to zero if no views data can be found
                    debug_log(f"No views data found for video {video_id}, setting to 0")
                    video['views'] = '0'
        
        # Additional step: Check for comment_count in statistics and make sure it's copied to the base level
        # This ensures consistency between the new channel and refresh flows
        if 'statistics' in video and isinstance(video['statistics'], dict):
            # Handle comment count
            if 'commentCount' in video['statistics']:
                if 'comment_count' not in video or not video['comment_count']:
                    video['comment_count'] = video['statistics']['commentCount']
                    debug_log(f"Setting comment_count from statistics.commentCount: {video['statistics']['commentCount']}")
            
            # Handle likes
            if 'likeCount' in video['statistics']:
                if 'likes' not in video or not video['likes']:
                    video['likes'] = video['statistics']['likeCount']
                    debug_log(f"Setting likes from statistics.likeCount: {video['statistics']['likeCount']}")
        
        # Clean up temporary field
        if 'original_views' in video:
            video.pop('original_views', None)
                
    return video_data

def extract_video_views(video, format_func=None):
    """
    Extracts views from a video object using a consistent approach
    
    Args:
        video (dict): A dictionary containing video data
        format_func (function, optional): A function to format the view count
        
    Returns:
        str: Formatted view count or '0' if not found
    """
    if not isinstance(video, dict):
        return '0'
        
    video_id = video.get('video_id', video.get('id', 'unknown'))
    views = None
    
    # Log detailed debugging info to help identify the problem
    debug_log(f"Video {video_id} extract_video_views() - all keys: {list(video.keys()) if isinstance(video, dict) else 'Not a dict'}")
    
    # Look for raw json string data if debugging
    raw_data = str(video)[:300]
    if "viewCount" in raw_data:
        debug_log(f"Found viewCount in raw string data: {raw_data}")
    else:
        debug_log(f"viewCount NOT found in raw string data sample")
    
    # Log specific nested structure inspection to diagnose the issue
    debug_log(f"Video {video_id} has 'statistics'?: {('statistics' in video)}")
    if 'statistics' in video:
        debug_log(f"Video {video_id} statistics type: {type(video['statistics'])}")
        debug_log(f"Video {video_id} statistics value: {video['statistics']}")
        if isinstance(video['statistics'], dict):
            debug_log(f"Video {video_id} statistics keys: {list(video['statistics'].keys())}")
    
    # Try all possible paths to find views data with detailed logging
    try:
        # Path 1: Direct views field - handle all formats and validate non-zero values
        if 'views' in video:
            raw_views = video['views']
            if raw_views is not None and raw_views != '' and str(raw_views) != '0':
                views = str(raw_views).strip()
                debug_log(f"Using non-zero direct views field for {video_id}: {views}")
            else:
                debug_log(f"Found invalid value '{raw_views}' in direct views field, trying other sources")
        
        # Path 2: Check if statistics is a string (API sometimes returns serialized JSON)
        if not views and 'statistics' in video and isinstance(video['statistics'], str):
            try:
                stats_dict = json.loads(video['statistics'])
                if 'viewCount' in stats_dict:
                    views = str(stats_dict['viewCount']).strip()
                    video['views'] = views
                    debug_log(f"Using parsed statistics string for {video_id}: {views}")
            except:
                debug_log(f"Failed to parse statistics string for {video_id}")
        
        # Path 3: statistics.viewCount (YouTube API standard location)
        if not views and 'statistics' in video and isinstance(video['statistics'], dict):
            # Check if statistics is empty (like in the case of the screenshot)
            if not video['statistics']:
                debug_log(f"WARNING: Video {video_id} has empty statistics dictionary")
                views = '0'
                video['views'] = views
            elif 'viewCount' in video['statistics']:
                views = str(video['statistics']['viewCount']).strip()
                # Also store in standard location for consistency
                video['views'] = views
                debug_log(f"Using statistics.viewCount for {video_id}: {views}")
        
        # Path 4: contentDetails.statistics.viewCount (alternative nested location)
        if not views and 'contentDetails' in video:
            debug_log(f"Video {video_id} contentDetails keys: {list(video['contentDetails'].keys()) if isinstance(video['contentDetails'], dict) else 'Not a dict'}")
            if isinstance(video['contentDetails'], dict) and 'statistics' in video['contentDetails']:
                if isinstance(video['contentDetails']['statistics'], dict) and 'viewCount' in video['contentDetails']['statistics']:
                    views = str(video['contentDetails']['statistics']['viewCount']).strip()
                    # Also store in standard location for consistency
                    video['views'] = views
                    debug_log(f"Using contentDetails.statistics.viewCount for {video_id}: {views}")
        
        # Path 5: Check if views is in snippet (some API responses)
        if not views and 'snippet' in video:
            if isinstance(video['snippet'], dict) and 'statistics' in video['snippet']:
                if isinstance(video['snippet']['statistics'], dict) and 'viewCount' in video['snippet']['statistics']:
                    views = str(video['snippet']['statistics']['viewCount']).strip()
                    video['views'] = views
                    debug_log(f"Using snippet.statistics.viewCount for {video_id}: {views}")
        
        # Path 6: Try to find any property with 'view' in the name
        if not views:
            for key in video.keys():
                if 'view' in key.lower() and video[key] and str(video[key]) != '0':
                    views = str(video[key]).strip()
                    video['views'] = views
                    debug_log(f"Found view data in field '{key}' for {video_id}: {views}")
                    break
        
        # Default to 0 if no valid data found
        if not views:
            views = '0'
            debug_log(f"No valid views data found for video {video_id}, using '0'")
        
        # Apply formatting if requested
        if format_func and callable(format_func):
            try:
                # Even if we find 0 views, format it consistently
                # This ensures we always display '0' in the UI instead of 'Not Available'
                if views == '0':
                    debug_log(f"WARNING: Found 0 views for video {video_id} - likely API or extraction issue")
                    return format_func('0')  # Format the '0' value for consistent display
                return format_func(views)
            except Exception as e:
                debug_log(f"Error formatting views for {video_id}: {str(e)}")
                return views
        
        return views
        
    except Exception as e:
        debug_log(f"Error extracting views for video {video_id}: {str(e)}")
        return '0'

def fix_missing_views(videos):
    """Fix missing views data in video list"""
    if not videos:
        return videos
    for video in videos:
        # Only set default if missing
        if 'views' not in video:
            video['views'] = '0'
        if 'likes' not in video:
            video['likes'] = '0'
        if 'comment_count' not in video:
            video['comment_count'] = '0'
        # Try to get statistics from various locations
        stats = None
        if isinstance(video.get('statistics'), dict):
            stats = video['statistics']
        elif isinstance(video.get('statistics'), str):
            try:
                stats = json.loads(video['statistics'])
            except:
                pass
        elif isinstance(video.get('contentDetails', {}).get('statistics'), dict):
            stats = video['contentDetails']['statistics']
        elif isinstance(video.get('snippet', {}).get('statistics'), dict):
            stats = video['snippet']['statistics']
        if stats:
            # Only set if not already present or is '0'
            if ('views' not in video or video['views'] == '0') and 'viewCount' in stats:
                video['views'] = str(stats.get('viewCount', '0'))
            if ('likes' not in video or video['likes'] == '0') and 'likeCount' in stats:
                video['likes'] = str(stats.get('likeCount', '0'))
            if ('comment_count' not in video or video['comment_count'] == '0') and 'commentCount' in stats:
                video['comment_count'] = str(stats.get('commentCount', '0'))
    return videos
