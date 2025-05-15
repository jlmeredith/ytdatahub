"""
Helper functions for processing YouTube video data consistently
Extracts both views and comment counts in a unified way
"""
from src.utils.helpers import debug_log

def process_video_data(videos_data):
    """
    Process video data to ensure consistency across all videos.
    Extracts both views and comment counts from various locations.
    
    Args:
        videos_data (list): List of video dictionaries
        
    Returns:
        list: The same list with updated view and comment count data
    """
    if not videos_data or not isinstance(videos_data, list):
        return videos_data
        
    debug_log(f"Processing {len(videos_data)} videos for views and comment counts")
    
    for i, video in enumerate(videos_data):
        if not isinstance(video, dict):
            continue
            
        video_id = video.get('video_id', f"video_{i}")
        debug_log(f"Processing video {video_id}")
        
        # First pass - extract data from statistics objects
        if 'statistics' in video and isinstance(video['statistics'], dict):
            # Extract view count
            if 'viewCount' in video['statistics']:
                if 'views' not in video or not video['views'] or video['views'] == '0':
                    video['views'] = video['statistics']['viewCount']
                    debug_log(f"Set views from statistics.viewCount: {video['statistics']['viewCount']} for {video_id}")
                    
            # Extract comment count - ALWAYS do this regardless of existing comment_count
            if 'commentCount' in video['statistics']:
                video['comment_count'] = video['statistics']['commentCount']
                debug_log(f"Set comment_count from statistics.commentCount: {video['statistics']['commentCount']} for {video_id}")
        
        # Second pass - handle other video data locations and edge cases
        if 'views' not in video or not video['views'] or video['views'] == '0':
            # Try to find views in alternative locations if not already set
            # ContentDetails
            if 'contentDetails' in video and isinstance(video['contentDetails'], dict) and 'statistics' in video['contentDetails']:
                if isinstance(video['contentDetails']['statistics'], dict) and 'viewCount' in video['contentDetails']['statistics']:
                    video['views'] = video['contentDetails']['statistics']['viewCount'] 
                    debug_log(f"Set views from contentDetails.statistics.viewCount: {video['views']} for {video_id}")
            
            # If still not found, set default
            if 'views' not in video or not video['views']:
                video['views'] = '0'
                debug_log(f"No view data found, set default '0' for {video_id}")
        
        # Ensure comment_count is always set
        if 'comment_count' not in video or not video['comment_count']:
            # Look in contentDetails first
            if 'contentDetails' in video and isinstance(video['contentDetails'], dict) and 'statistics' in video['contentDetails']:
                if isinstance(video['contentDetails']['statistics'], dict) and 'commentCount' in video['contentDetails']['statistics']:
                    video['comment_count'] = video['contentDetails']['statistics']['commentCount'] 
                    debug_log(f"Set comment_count from contentDetails.statistics.commentCount: {video['comment_count']} for {video_id}")
            
            # Try regex extraction as last resort
            if ('comment_count' not in video or not video['comment_count']) and 'statistics' in video:
                import re
                raw_str = str(video['statistics'])
                commentcount_pattern = r'"commentCount":\s*"?(\d+)"?'
                match = re.search(commentcount_pattern, raw_str)
                if match:
                    video['comment_count'] = match.group(1)
                    debug_log(f"Set comment_count via regex extraction: {video['comment_count']} for {video_id}")
    
    # Count processed videos
    view_count = sum(1 for v in videos_data if isinstance(v, dict) and 'views' in v and v['views'] and v['views'] != '0')
    comment_count = sum(1 for v in videos_data if isinstance(v, dict) and 'comment_count' in v and v['comment_count'])
    
    debug_log(f"Processed {view_count}/{len(videos_data)} videos with valid view counts")
    debug_log(f"Processed {comment_count}/{len(videos_data)} videos with valid comment counts")
    
    return videos_data
    
# Alias for backward compatibility
process_videos = process_video_data
