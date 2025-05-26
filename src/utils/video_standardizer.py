"""
Video Data Standardization Utility

This module provides functions to ensure consistent video data structure
across the application regardless of where the data came from.
"""
from src.utils.helpers import debug_log
from src.utils.video_processor import process_video_data
from src.utils.video_formatter import fix_missing_views

def standardize_video_data(videos_data):
    """
    One-stop function to ensure video data is consistently structured.
    This should be called before storing videos in session state or displaying them.
    
    Args:
        videos_data (list): List of video dictionaries from any source
        
    Returns:
        list: List with standardized video data
    """
    if not videos_data:
        debug_log("standardize_video_data: No videos provided")
        return []
    
    debug_log(f"standardize_video_data: Standardizing {len(videos_data) if isinstance(videos_data, list) else '1 non-list item'} videos")
    debug_log(f"standardize_video_data: Input data type: {type(videos_data)}")
    
    # Log initial sample for diagnostic purposes
    if isinstance(videos_data, list) and len(videos_data) > 0:
        first_video = videos_data[0]
        debug_log(f"standardize_video_data: First video data BEFORE processing: {str(first_video)[:500]}...")
        if isinstance(first_video, dict):
            debug_log(f"standardize_video_data: First video keys: {list(first_video.keys())}")
    
    # Handle non-list input (single video)
    if not isinstance(videos_data, list):
        debug_log(f"standardize_video_data: Input is not a list, converting from type {type(videos_data)}")
        if isinstance(videos_data, dict):
            videos_data = [videos_data]
        else:
            debug_log(f"standardize_video_data: Cannot standardize non-dict/non-list input: {type(videos_data)}")
            return []
    
    # First apply the process_video_data function to extract all fields to top level
    processed_videos = process_video_data(videos_data)
    
    # Then fix any missing views
    fixed_videos = fix_missing_views(processed_videos)
    
    debug_log(f"standardize_video_data: After processing and fixing views - have {len(fixed_videos) if isinstance(fixed_videos, list) else 'non-list'} videos")
    if isinstance(fixed_videos, list) and len(fixed_videos) > 0:
        first_fixed = fixed_videos[0]
        debug_log(f"standardize_video_data: First video AFTER fixing views - type: {type(first_fixed)}")
        if isinstance(first_fixed, dict):
            debug_log(f"standardize_video_data: First video keys AFTER fixing views: {list(first_fixed.keys())}")
            debug_log(f"standardize_video_data: First video data sample AFTER fixing views: {str(first_fixed)[:300]}...")
    
    # Additional normalization to ensure all required fields exist with proper types
    standardized_videos = []
    for video in fixed_videos:
        if not isinstance(video, dict):
            debug_log(f"standardize_video_data: Skipping non-dict video item of type {type(video)}")
            continue
            
        video_id = video.get('video_id', video.get('id', ''))
        if not video_id:
            # Try to extract from other possible locations
            if isinstance(video.get('contentDetails'), dict) and 'videoId' in video['contentDetails']:
                video_id = video['contentDetails']['videoId']
            elif isinstance(video.get('snippet'), dict) and 'resourceId' in video['snippet']:
                if isinstance(video['snippet']['resourceId'], dict) and 'videoId' in video['snippet']['resourceId']:
                    video_id = video['snippet']['resourceId']['videoId']
            elif isinstance(video.get('id'), dict) and 'videoId' in video['id']:
                video_id = video['id']['videoId']
                
        if not video_id:
            debug_log("Skipping video with no ID")
            continue
        
        # Make a copy to avoid modifying the original
        std_video = video.copy()
        
        # Ensure required fields exist
        std_video['video_id'] = video_id
        std_video['title'] = video.get('title', video.get('snippet', {}).get('title', 'Untitled'))
        
        # Ensure metrics are strings to prevent type errors
        for metric in ['views', 'likes', 'comment_count']:
            # Convert to string if not already
            if metric in std_video:
                std_video[metric] = str(std_video[metric])
            else:
                std_video[metric] = '0'
                
        # Normalize published date
        if 'published_at' not in std_video:
            # Try multiple paths for published date
            if 'snippet' in std_video and 'publishedAt' in std_video['snippet']:
                std_video['published_at'] = std_video['snippet']['publishedAt']
            elif 'published' in std_video:
                std_video['published_at'] = std_video['published']
                
        # Normalize thumbnail
        if 'thumbnail_url' not in std_video:
            # Try all possible thumbnail paths
            
            # Path 1: snippet.thumbnails (YouTube API standard)
            if 'snippet' in std_video and 'thumbnails' in std_video['snippet']:
                thumbnails = std_video['snippet']['thumbnails']
                if 'medium' in thumbnails and 'url' in thumbnails['medium']:
                    std_video['thumbnail_url'] = thumbnails['medium']['url']
                elif 'default' in thumbnails and 'url' in thumbnails['default']:
                    std_video['thumbnail_url'] = thumbnails['default']['url']
                elif 'high' in thumbnails and 'url' in thumbnails['high']:
                    std_video['thumbnail_url'] = thumbnails['high']['url']
            
            # Path 2: Direct thumbnails property
            elif 'thumbnails' in std_video:
                thumbnails = std_video['thumbnails']
                if isinstance(thumbnails, dict):
                    if 'medium' in thumbnails and 'url' in thumbnails['medium']:
                        std_video['thumbnail_url'] = thumbnails['medium']['url']
                    elif 'default' in thumbnails and 'url' in thumbnails['default']:
                        std_video['thumbnail_url'] = thumbnails['default']['url']
                    elif 'high' in thumbnails and 'url' in thumbnails['high']:
                        std_video['thumbnail_url'] = thumbnails['high']['url']
            
            # Path 3: thumbnail property
            elif 'thumbnail' in std_video:
                if isinstance(std_video['thumbnail'], str):
                    std_video['thumbnail_url'] = std_video['thumbnail']
                    
            # Path 4: Construct from video ID as last resort
            if 'thumbnail_url' not in std_video and video_id:
                std_video['thumbnail_url'] = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                debug_log(f"Generated thumbnail URL for video {video_id}")
                    
        standardized_videos.append(std_video)
        
    debug_log(f"standardize_video_data: Returning {len(standardized_videos)} standardized videos")
    return standardized_videos


def extract_standardized_videos(response_data):
    """
    Extract videos from an API response and standardize them.
    
    Args:
        response_data (dict): API response data that might contain videos
        
    Returns:
        list: List of standardized video objects
    """
    videos = []
    
    debug_log(f"extract_standardized_videos: Processing response data of type {type(response_data)}")
    debug_log(f"extract_standardized_videos: Raw response data structure: {str(response_data)[:500]}...")
    
    # Handle different response data types/shapes
    if not response_data:
        debug_log("extract_standardized_videos: Empty response data")
        return []
        
    # First try the video_id field (most common)
    if isinstance(response_data, dict) and 'video_id' in response_data:
        videos = response_data['video_id']
        debug_log(f"extract_standardized_videos: Found {len(videos) if isinstance(videos, list) else 'non-list'} videos in video_id field")
    # Try items field (from direct API responses)
    elif isinstance(response_data, dict) and 'items' in response_data:
        videos = response_data['items']
        debug_log(f"extract_standardized_videos: Found {len(videos) if isinstance(videos, list) else 'non-list'} videos in items field")
    # Try videos field (some legacy responses)
    elif isinstance(response_data, dict) and 'videos' in response_data:
        videos = response_data['videos']
        debug_log(f"extract_standardized_videos: Found {len(videos) if isinstance(videos, list) else 'non-list'} videos in videos field")
    # Try channel_info field (embedded in some responses)
    elif isinstance(response_data, dict) and 'channel_info' in response_data and isinstance(response_data['channel_info'], dict):
        if 'video_id' in response_data['channel_info']:
            videos = response_data['channel_info']['video_id']
            debug_log(f"extract_standardized_videos: Found {len(videos) if isinstance(videos, list) else 'non-list'} videos in channel_info.video_id field")
        elif 'videos' in response_data['channel_info']:
            videos = response_data['channel_info']['videos']
            debug_log(f"extract_standardized_videos: Found {len(videos) if isinstance(videos, list) else 'non-list'} videos in channel_info.videos field")
    # Maybe it's already a list of videos
    elif isinstance(response_data, list):
        videos = response_data
        debug_log(f"extract_standardized_videos: Input appears to be a direct list of {len(videos)} videos")
        
    # If videos is not a list at this point, make it one
    if not isinstance(videos, list):
        debug_log(f"extract_standardized_videos: Converting non-list videos to list: {type(videos)}")
        if videos:  # If it's not empty/None
            videos = [videos]
        else:
            videos = []
            
    debug_log(f"extract_standardized_videos: Sending {len(videos)} videos to standardizer")
    return standardize_video_data(videos)
