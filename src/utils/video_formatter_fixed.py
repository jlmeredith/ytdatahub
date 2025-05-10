"""
Helper functions for formatting and fixing video data
"""
from src.utils.helpers import debug_log

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
        if 'statistics' in video and isinstance(video['statistics'], dict) and 'commentCount' in video['statistics']:
            if 'comment_count' not in video or not video['comment_count']:
                video['comment_count'] = video['statistics']['commentCount']
                debug_log(f"Setting comment_count from statistics.commentCount: {video['statistics']['commentCount']}")
        
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
                import json
                stats_dict = json.loads(video['statistics'])
                if 'viewCount' in stats_dict:
                    views = str(stats_dict['viewCount']).strip()
                    video['views'] = views  # Save it back to the video object for future use
                    debug_log(f"Using parsed statistics string for {video_id}: {views}")
            except:
                debug_log(f"Failed to parse statistics string for {video_id}")
        
        # Path 3: statistics.viewCount (YouTube API standard location)
        if not views and 'statistics' in video and isinstance(video['statistics'], dict):
            # Check if statistics is empty
            if not video['statistics']:
                debug_log(f"WARNING: Video {video_id} has empty statistics dictionary")
                views = '0'
                video['views'] = views  # Save it back for consistency
            elif 'viewCount' in video['statistics']:
                views = str(video['statistics']['viewCount']).strip()
                video['views'] = views  # Save it back for consistency
                debug_log(f"Using statistics.viewCount for {video_id}: {views}")
        
        # Path 4: contentDetails.statistics.viewCount (alternative nested location)
        if not views and 'contentDetails' in video:
            debug_log(f"Video {video_id} contentDetails keys: {list(video['contentDetails'].keys()) if isinstance(video['contentDetails'], dict) else 'Not a dict'}")
            if isinstance(video['contentDetails'], dict) and 'statistics' in video['contentDetails']:
                if isinstance(video['contentDetails']['statistics'], dict) and 'viewCount' in video['contentDetails']['statistics']:
                    views = str(video['contentDetails']['statistics']['viewCount']).strip()
                    video['views'] = views  # Save it back for consistency
                    debug_log(f"Using contentDetails.statistics.viewCount for {video_id}: {views}")
        
        # Path 5: Check if views is in snippet (some API responses)
        if not views and 'snippet' in video:
            if isinstance(video['snippet'], dict) and 'statistics' in video['snippet']:
                if isinstance(video['snippet']['statistics'], dict) and 'viewCount' in video['snippet']['statistics']:
                    views = str(video['snippet']['statistics']['viewCount']).strip()
                    video['views'] = views  # Save it back for consistency
                    debug_log(f"Using snippet.statistics.viewCount for {video_id}: {views}")
        
        # Path 6: Try to find any property with 'view' in the name
        if not views:
            for key in video.keys():
                if 'view' in key.lower() and video[key] and str(video[key]) != '0':
                    views = str(video[key]).strip()
                    video['views'] = views  # Save it back for consistency
                    debug_log(f"Found view data in field '{key}' for {video_id}: {views}")
                    break
        
        # Default to 0 if no valid data found
        if not views:
            views = '0'
            video['views'] = '0'  # Save it back for consistency
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

def fix_missing_views(videos_data):
    """
    Advanced function to diagnose and fix missing view data in videos
    
    Args:
        videos_data (list): List of video dictionaries
        
    Returns:
        list: The same list with updated view data
    """
    if not videos_data or not isinstance(videos_data, list):
        return videos_data
        
    debug_log(f"Running fix_missing_views on {len(videos_data)} videos")
    
    for i, video in enumerate(videos_data):
        if not isinstance(video, dict):
            continue
            
        video_id = video.get('video_id', f"video_{i}")
        
        # Check if this video has valid views
        has_valid_views = ('views' in video and video['views'] and str(video['views']) != '0')
        
        # Skip videos that already have valid view data
        if has_valid_views:
            debug_log(f"Video {video_id} already has valid views: {video['views']}")
            # Even if we have valid views, make sure comment_count is consistent
            if 'statistics' in video and isinstance(video['statistics'], dict) and 'commentCount' in video['statistics']:
                if 'comment_count' not in video or not video['comment_count']:
                    video['comment_count'] = video['statistics']['commentCount']
                    debug_log(f"Added missing comment_count from statistics.commentCount: {video['statistics']['commentCount']}")
            continue
            
        debug_log(f"Attempting to fix missing views for video {video_id}")            # First try direct access to statistics.viewCount
            # This is the most common location in the YouTube API
            if 'statistics' in video and isinstance(video['statistics'], dict):
                # Handle empty statistics dictionary
                if not video['statistics']:
                    debug_log(f"Video {video_id} has empty statistics dictionary, using '0'")
                    video['views'] = '0'
                elif 'viewCount' in video['statistics']:
                    video['views'] = video['statistics']['viewCount']
                    debug_log(f"Fixed views for {video_id} from statistics.viewCount: {video['statistics']['viewCount']}")
                
                # Always check for comment count regardless of view count status
                if 'commentCount' in video['statistics']:
                    video['comment_count'] = video['statistics']['commentCount']
                    debug_log(f"Fixed comment_count for {video_id} from statistics.commentCount: {video['statistics']['commentCount']}")
                
                # If we've fixed the views, continue to the next video - but make sure we've handled comment count first
                if 'views' in video and video['views'] and str(video['views']) != '0':
                    continue
                
        # Next, attempt to parse from raw API response
        # Sometimes the API returns statistics as a string or in different nested structures
        raw_video_str = str(video)
        import re
        
        # Look for viewCount in raw string using regex
        viewcount_pattern = r'"viewCount":\s*"?(\d+)"?'
        match = re.search(viewcount_pattern, raw_video_str)
        if match:
            view_count = match.group(1)
            video['views'] = view_count
            debug_log(f"Extracted views for {video_id} using regex: {view_count}")
            
            # Also look for commentCount while we're at it
            commentcount_pattern = r'"commentCount":\s*"?(\d+)"?'
            comment_match = re.search(commentcount_pattern, raw_video_str)
            if comment_match and ('comment_count' not in video or not video['comment_count']):
                comment_count = comment_match.group(1)
                video['comment_count'] = comment_count
                debug_log(f"Extracted comment_count for {video_id} using regex: {comment_count}")
            
            continue
            
        # If we still don't have views, try additional locations
        # Check contentDetails.statistics.viewCount
        if 'contentDetails' in video and isinstance(video['contentDetails'], dict):
            if 'statistics' in video['contentDetails'] and isinstance(video['contentDetails']['statistics'], dict):
                if 'viewCount' in video['contentDetails']['statistics']:
                    video['views'] = video['contentDetails']['statistics']['viewCount']
                    debug_log(f"Fixed views for {video_id} from contentDetails.statistics.viewCount")
                if 'commentCount' in video['contentDetails']['statistics'] and ('comment_count' not in video or not video['comment_count']):
                    video['comment_count'] = video['contentDetails']['statistics']['commentCount']
                    debug_log(f"Fixed comment_count for {video_id} from contentDetails.statistics.commentCount")
                continue
        
        # Look for any field containing 'view' in its name (case insensitive)
        view_related_fields = [k for k in video.keys() if 'view' in k.lower() and k.lower() != 'preview']
        for field in view_related_fields:
            if video[field] and str(video[field]) != '0':
                video['views'] = str(video[field])
                debug_log(f"Found view data in field '{field}' for {video_id}: {video['views']}")
                break
        
        # As a last resort, examine all properties for viewCount
        for key, value in video.items():
            if isinstance(value, dict) and 'viewCount' in value:
                video['views'] = value['viewCount']
                debug_log(f"Found viewCount in property {key} for {video_id}")
                # Also look for commentCount in the same property
                if 'commentCount' in value and ('comment_count' not in video or not video['comment_count']):
                    video['comment_count'] = value['commentCount']
                    debug_log(f"Found commentCount in property {key} for {video_id}")
                break
            
            # Look in dict values for anything containing view-related keywords 
            if isinstance(value, dict):
                for k, v in value.items():
                    if 'view' in k.lower() and str(v) != '0':
                        video['views'] = str(v)
                        debug_log(f"Found view data in nested property {key}.{k} for {video_id}: {v}")
                        break
        
        # If we still don't have views, set to '0'
        # All YouTube videos should have at least one view from the uploader
        if not has_valid_views and ('views' not in video or not video['views'] or video['views'] == '0'):
            video['views'] = '0'
            # Remove views_display if it exists, we want to use '0' consistently
            if 'views_display' in video:
                video.pop('views_display', None)
            debug_log(f"Could not find any view data for {video_id}, using '0'")
    
    # Count how many videos were fixed
    fixed_count = 0
    comment_count = 0
    for video in videos_data:
        if isinstance(video, dict) and 'views' in video and video['views'] and str(video['views']) != '0':
            fixed_count += 1
        if isinstance(video, dict) and 'comment_count' in video and video['comment_count']:
            comment_count += 1
            
    debug_log(f"Views extraction complete: {fixed_count}/{len(videos_data)} videos have valid view counts")
    debug_log(f"Comment count extraction complete: {comment_count}/{len(videos_data)} videos have valid comment counts")
    
    return videos_data
