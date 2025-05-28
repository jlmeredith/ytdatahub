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
    api_format = {}
    api_format['data_source'] = 'database'
    if not db_data:
        debug_log("Empty data provided to convert_db_to_api_format, returning minimal structure")
        api_format['video_id'] = []
        return api_format

    # --- Robust channel_id mapping ---
    channel_id = (
        db_data.get('channel_id') or
        db_data.get('id') or
        db_data.get('channel_info', {}).get('id')
    )
    if channel_id:
        api_format['channel_id'] = channel_id
        debug_log(f"Mapped channel_id: {channel_id}")

    # --- Robust channel_name mapping ---
    channel_name = (
        db_data.get('channel_name') or
        db_data.get('channel_title') or
        db_data.get('snippet_title') or
        db_data.get('channel_info', {}).get('title')
    )
    if channel_name:
        api_format['channel_name'] = channel_name
        debug_log(f"Mapped channel_name: {channel_name}")

    # --- Robust playlist_id mapping ---
    playlist_id = (
        db_data.get('playlist_id') or
        db_data.get('uploads_playlist_id') or
        db_data.get('contentDetails_relatedPlaylists_uploads') or
        db_data.get('channel_info', {}).get('uploads_playlist_id') or
        db_data.get('channel_info', {}).get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
    )
    if playlist_id:
        api_format['playlist_id'] = playlist_id
        debug_log(f"Mapped playlist_id: {playlist_id}")
    else:
        debug_log("No playlist_id found in DB record.")

    # --- Robust subscriber/view/video count mapping ---
    subscribers = (
        db_data.get('subscribers') or
        db_data.get('subscriber_count') or
        db_data.get('statistics_subscriberCount') or
        db_data.get('channel_info', {}).get('statistics', {}).get('subscriberCount')
    )
    if subscribers is not None:
        try:
            api_format['subscribers'] = int(subscribers)
        except Exception:
            api_format['subscribers'] = subscribers
        debug_log(f"Mapped subscribers: {api_format['subscribers']}")

    views = (
        db_data.get('views') or
        db_data.get('view_count') or
        db_data.get('statistics_viewCount') or
        db_data.get('channel_info', {}).get('statistics', {}).get('viewCount')
    )
    if views is not None:
        try:
            api_format['views'] = int(views)
        except Exception:
            api_format['views'] = views
        debug_log(f"Mapped views: {api_format['views']}")

    total_videos = (
        db_data.get('total_videos') or
        db_data.get('video_count') or
        db_data.get('statistics_videoCount') or
        db_data.get('channel_info', {}).get('statistics', {}).get('videoCount')
    )
    if total_videos is not None:
        try:
            api_format['total_videos'] = int(total_videos)
        except Exception:
            api_format['total_videos'] = total_videos
        debug_log(f"Mapped total_videos: {api_format['total_videos']}")

    # --- Robust channel_description mapping ---
    channel_description = (
        db_data.get('channel_description') or
        db_data.get('snippet_description') or
        db_data.get('channel_info', {}).get('description')
    )
    if channel_description:
        api_format['channel_description'] = channel_description

    # --- Nested channel_info fallback (legacy) ---
    if 'channel_info' in db_data:
        channel_info = db_data['channel_info']
        if 'id' in channel_info and 'channel_id' not in api_format:
            api_format['channel_id'] = channel_info['id']
        if 'title' in channel_info and 'channel_name' not in api_format:
            api_format['channel_name'] = channel_info['title']
        if 'description' in channel_info and 'channel_description' not in api_format:
            api_format['channel_description'] = channel_info['description']
        if 'statistics' in channel_info:
            stats = channel_info['statistics']
            if 'subscriberCount' in stats and 'subscribers' not in api_format:
                try:
                    api_format['subscribers'] = int(stats['subscriberCount'])
                except Exception:
                    api_format['subscribers'] = stats['subscriberCount']
            if 'viewCount' in stats and 'views' not in api_format:
                try:
                    api_format['views'] = int(stats['viewCount'])
                except Exception:
                    api_format['views'] = stats['viewCount']
            if 'videoCount' in stats and 'total_videos' not in api_format:
                try:
                    api_format['total_videos'] = int(stats['videoCount'])
                except Exception:
                    api_format['total_videos'] = stats['videoCount']
        # Playlist ID from nested contentDetails
        if 'contentDetails' in channel_info and 'relatedPlaylists' in channel_info['contentDetails']:
            playlists = channel_info['contentDetails']['relatedPlaylists']
            if 'uploads' in playlists and 'playlist_id' not in api_format:
                api_format['playlist_id'] = playlists['uploads']
                debug_log(f"Mapped playlist_id from nested channel_info: {playlists['uploads']}")

    # --- Video data mapping (unchanged) ---
    if 'videos' in db_data and isinstance(db_data['videos'], list):
        api_format['video_id'] = []
        for video in db_data['videos']:
            video_item = {}
            if 'id' in video:
                video_item['video_id'] = video['id']
            if 'snippet' in video:
                snippet = video['snippet']
                if 'title' in snippet:
                    video_item['title'] = snippet['title']
                if 'description' in snippet:
                    video_item['video_description'] = snippet['description']
                if 'publishedAt' in snippet:
                    video_item['published_at'] = snippet['publishedAt']
                    try:
                        video_item['published_date'] = snippet['publishedAt'].split('T')[0]
                    except (IndexError, AttributeError):
                        pass
            if 'statistics' in video:
                stats = video['statistics']
                if 'viewCount' in stats:
                    video_item['views'] = stats['viewCount']
                if 'likeCount' in stats:
                    video_item['likes'] = stats['likeCount']
                if 'commentCount' in stats:
                    video_item['comment_count'] = stats['commentCount']
            if 'contentDetails' in video and 'duration' in video['contentDetails']:
                video_item['duration'] = video['contentDetails']['duration']
            if 'snippet' in video and 'thumbnails' in video['snippet']:
                thumbs = video['snippet']['thumbnails']
                if 'maxres' in thumbs:
                    video_item['thumbnails'] = thumbs['maxres'].get('url', '')
                elif 'high' in thumbs:
                    video_item['thumbnails'] = thumbs['high'].get('url', '')
                elif 'medium' in thumbs:
                    video_item['thumbnails'] = thumbs['medium'].get('url', '')
                elif 'default' in thumbs:
                    video_item['thumbnails'] = thumbs['default'].get('url', '')
            api_format['video_id'].append(video_item)
        debug_log(f"Converted {len(api_format['video_id'])} videos from database format.")
    elif 'video_id' in db_data and isinstance(db_data['video_id'], list):
        api_format['video_id'] = db_data['video_id']
        debug_log(f"Video data already in correct format. Found {len(api_format['video_id'])} videos.")
    else:
        api_format['video_id'] = []
        debug_log("No videos found in data, added empty video list.")
    return api_format

def format_number(num, short=False):
    """
    Format a number with thousands separators or short form (e.g., 1K, 1.2M).
    
    Args:
        num (int or float): Number to format
        short (bool): If True, use short form (e.g., 1K, 1.2M)
        
    Returns:
        str: Formatted number string
    """
    try:
        n = int(num)
        if short:
            if n >= 1_000_000_000:
                return f"{n/1_000_000_000:.1f}B".rstrip("0.") + "B"
            elif n >= 1_000_000:
                return f"{n/1_000_000:.1f}M".rstrip("0.") + "M"
            elif n >= 1_000:
                return f"{n/1_000:.0f}K"
        return f"{n:,}"
    except (ValueError, TypeError):
        return str(num)