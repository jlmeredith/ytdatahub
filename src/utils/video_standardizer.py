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
    expected_fields = {
        'video_id': '',
        'title': '',
        'description': '',
        'duration': 'Unknown duration',
        'published_at': '',
        'likes': '0',
        'views': '0',
        'comment_count': '0',
        'thumbnail_url': '',
        'snippet': {},
        'statistics': {},
        'contentDetails': {},
    }
    for video in fixed_videos:
        if not isinstance(video, dict):
            debug_log(f"standardize_video_data: Skipping non-dict video item of type {type(video)}")
            continue
        # Robustly extract video_id from all possible locations
        video_id = (
            video.get('video_id') or
            video.get('youtube_id') or
            video.get('id') if isinstance(video.get('id'), str) else None or
            (video.get('id', {}).get('videoId') if isinstance(video.get('id'), dict) else None) or
            (video.get('contentDetails', {}).get('videoId') if isinstance(video.get('contentDetails'), dict) else None) or
            (video.get('snippet', {}).get('resourceId', {}).get('videoId') if isinstance(video.get('snippet', {}).get('resourceId'), dict) else None)
        )
        if not video_id:
            debug_log(f"standardize_video_data: Skipping video with no valid ID. Video keys: {list(video.keys())}")
            continue
        std_video = video.copy()
        std_video['video_id'] = video_id  # Always set video_id
        # Ensure all expected fields exist with sensible defaults
        for field, default in expected_fields.items():
            if field not in std_video or std_video[field] is None:
                std_video[field] = default
                debug_log(f"standardize_video_data: Field '{field}' missing in video {video_id}, defaulting to {repr(default)}")
        # Title
        std_video['title'] = video.get('title', video.get('snippet', {}).get('title', 'Untitled'))
        # Description
        std_video['description'] = video.get('description', video.get('snippet', {}).get('description', ''))
        # Duration
        if 'duration' not in std_video or not std_video['duration'] or std_video['duration'] == 'Unknown duration':
            if 'contentDetails' in std_video and isinstance(std_video['contentDetails'], dict):
                std_video['duration'] = std_video['contentDetails'].get('duration', 'Unknown duration')
            else:
                std_video['duration'] = 'Unknown duration'
        # Published at
        std_video['published_at'] = video.get('published_at', video.get('snippet', {}).get('publishedAt', ''))
        # Likes
        if 'likes' not in std_video or not std_video['likes']:
            if 'statistics' in std_video and isinstance(std_video['statistics'], dict):
                std_video['likes'] = str(std_video['statistics'].get('likeCount', '0'))
            else:
                std_video['likes'] = '0'
        # Views
        if 'views' not in std_video or not std_video['views']:
            if 'statistics' in std_video and isinstance(std_video['statistics'], dict):
                std_video['views'] = str(std_video['statistics'].get('viewCount', '0'))
            else:
                std_video['views'] = '0'
        # Comment count
        if 'comment_count' not in std_video or not std_video['comment_count']:
            if 'statistics' in std_video and isinstance(std_video['statistics'], dict):
                std_video['comment_count'] = str(std_video['statistics'].get('commentCount', '0'))
            else:
                std_video['comment_count'] = '0'
        # Thumbnail URL
        if not std_video['thumbnail_url']:
            # Try all possible thumbnail paths
            thumb_url = ''
            if 'snippet' in std_video and 'thumbnails' in std_video['snippet']:
                thumbnails = std_video['snippet']['thumbnails']
                for size in ['medium', 'default', 'high']:
                    if size in thumbnails and 'url' in thumbnails[size]:
                        thumb_url = thumbnails[size]['url']
                        break
            elif 'thumbnails' in std_video and isinstance(std_video['thumbnails'], dict):
                thumbnails = std_video['thumbnails']
                for size in ['medium', 'default', 'high']:
                    if size in thumbnails and 'url' in thumbnails[size]:
                        thumb_url = thumbnails[size]['url']
                        break
            elif 'thumbnail' in std_video and isinstance(std_video['thumbnail'], str):
                thumb_url = std_video['thumbnail']
            if not thumb_url and video_id:
                thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                debug_log(f"Generated thumbnail URL for video {video_id}")
            std_video['thumbnail_url'] = thumb_url
        # Nested fields: ensure dicts/arrays are not None
        for nested in ['snippet', 'statistics', 'contentDetails']:
            if std_video[nested] is None:
                std_video[nested] = {} if nested != 'tags' else []
        standardized_videos.append(std_video)
    debug_log(f"standardize_video_data: Returning {len(standardized_videos)} standardized videos")
    # Diagnostic: print first 3 video dicts and their video_id fields
    for i, v in enumerate(standardized_videos[:3]):
        debug_log(f"standardize_video_data: Video {i+1} video_id: {v.get('video_id')}, keys: {list(v.keys())}")
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
