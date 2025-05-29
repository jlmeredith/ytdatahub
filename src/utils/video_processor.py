"""
Helper functions for processing YouTube video data consistently
Extracts both views and comment counts in a unified way
"""
from src.utils.debug_utils import debug_log

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
    
    videos_with_views = 0
    videos_with_comments = 0
    
    for i, video in enumerate(videos_data):
        if not isinstance(video, dict):
            continue
            
        # Get video ID - handle different formats with robust extraction
        video_id = (
            video.get('video_id') or
            video.get('youtube_id') or
            video.get('id') if isinstance(video.get('id'), str) else None or
            (video.get('id', {}).get('videoId') if isinstance(video.get('id'), dict) else None) or
            (video.get('contentDetails', {}).get('videoId') if isinstance(video.get('contentDetails'), dict) else None) or
            (video.get('snippet', {}).get('resourceId', {}).get('videoId') if isinstance(video.get('snippet', {}).get('resourceId'), dict) else None) or
            f"video_{i}"
        )
        
        # Always ensure video_id is set
        if video_id and video_id != f"video_{i}":
            video['video_id'] = video_id
        elif not video.get('video_id'):
            video['video_id'] = f"video_{i}"
            debug_log(f"WARNING: No valid video ID found, using fallback: video_{i}")
        
        debug_log(f"Processing video {video_id}")
        
        # Store original values for diagnostic purposes
        orig_views = video.get('views')
        orig_comment_count = video.get('comment_count')
        
        # First try to normalize data structure (title, etc)
        # If video has snippet, but no direct title field, copy it
        if 'title' not in video and 'snippet' in video and isinstance(video['snippet'], dict):
            if 'title' in video['snippet']:
                video['title'] = video['snippet']['title']
                
        # Handle published_at field
        if 'published_at' not in video and 'snippet' in video and 'publishedAt' in video['snippet']:
            video['published_at'] = video['snippet']['publishedAt']
        
        # First pass - extract data from statistics objects
        if 'statistics' in video and isinstance(video['statistics'], dict):
            # Extract view count
            if 'viewCount' in video['statistics']:
                if 'views' not in video or not video['views'] or video['views'] == '0' or str(video['views']).strip() == '':
                    video['views'] = video['statistics']['viewCount']
                    debug_log(f"Set views from statistics.viewCount: {video['statistics']['viewCount']} for {video_id}")
                    
            # Extract comment count - ALWAYS do this regardless of existing comment_count
            if 'commentCount' in video['statistics']:
                video['comment_count'] = video['statistics']['commentCount']
                debug_log(f"Set comment_count from statistics.commentCount: {video['statistics']['commentCount']} for {video_id}")
                
            # Extract likes count
            if 'likeCount' in video['statistics']:
                if 'likes' not in video or not video['likes'] or video['likes'] == '0':
                    video['likes'] = video['statistics']['likeCount']
                    debug_log(f"Set likes from statistics.likeCount: {video['statistics']['likeCount']} for {video_id}")
                    
        # Second pass - handle other video data locations and edge cases
        if 'views' not in video or not video['views'] or str(video['views']) == '0' or str(video['views']).strip() == '':
            # Try to find views in alternative locations if not already set
            # ContentDetails
            if 'contentDetails' in video and isinstance(video['contentDetails'], dict) and 'statistics' in video['contentDetails']:
                if isinstance(video['contentDetails']['statistics'], dict) and 'viewCount' in video['contentDetails']['statistics']:
                    video['views'] = video['contentDetails']['statistics']['viewCount'] 
                    debug_log(f"Set views from contentDetails.statistics.viewCount: {video['views']} for {video_id}")
            
            # If still not found, set default
            if 'views' not in video or not video['views'] or str(video['views']).strip() == '':
                video['views'] = '0'
                debug_log(f"No view data found, set default '0' for {video_id}")
                
        # Ensure these fields are present even if empty
        if 'views' not in video:
            video['views'] = '0'
        if 'likes' not in video:
            video['likes'] = '0'
        if 'comment_count' not in video:
            video['comment_count'] = '0'
        
        # Count videos with actual data
        if video['views'] and video['views'] != '0':
            videos_with_views += 1
            
        # Log changes
        if orig_views != video.get('views'):
            debug_log(f"Updated views for {video_id}: {orig_views} -> {video['views']}")
        if orig_comment_count != video.get('comment_count'):
            debug_log(f"Updated comment_count for {video_id}: {orig_comment_count} -> {video['comment_count']}")
        
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
