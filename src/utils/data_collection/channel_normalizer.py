"""
Channel data normalization utilities.

This module provides functions to normalize channel data before save operations
to ensure consistent format between different data collection workflows.
"""
from datetime import datetime
import json
import logging

# Set up simple logging
logger = logging.getLogger(__name__)

def normalize_channel_data_for_save(channel_data, workflow_type="unknown"):
    """
    Normalize channel data to a consistent format before saving to database.
    
    This function ensures that both new channel and refresh channel workflows
    save data in identical format, eliminating spurious deltas.
    
    Args:
        channel_data (dict): Channel data to normalize
        workflow_type (str): "new_channel" or "refresh_channel" for debugging
        
    Returns:
        dict: Normalized channel data ready for saving
    """
    if not channel_data:
        logger.warning(f"normalize_channel_data_for_save ({workflow_type}): Empty data provided")
        return {}
    
    logger.info(f"normalize_channel_data_for_save ({workflow_type}): Starting normalization")
    
    # Start with a clean copy to avoid modifying the original
    normalized = {}
    
    # --- Core channel identification fields ---
    normalized['channel_id'] = _extract_channel_id(channel_data)
    normalized['channel_name'] = _extract_channel_name(channel_data)
    normalized['playlist_id'] = _extract_playlist_id(channel_data)
    
    # --- API metadata fields ---
    normalized['kind'] = _extract_kind(channel_data)
    normalized['etag'] = _extract_etag(channel_data)
    
    # --- Statistics (ensure integer type and consistent defaults) ---
    normalized['subscribers'] = _normalize_integer_field(channel_data, ['subscribers', 'subscriber_count', 'statistics_subscriberCount'], 0)
    normalized['views'] = _normalize_integer_field(channel_data, ['views', 'view_count', 'statistics_viewCount'], 0)
    normalized['total_videos'] = _normalize_integer_field(channel_data, ['total_videos', 'video_count', 'statistics_videoCount'], 0)
    
    # --- Metadata fields ---
    normalized['channel_description'] = _extract_channel_description(channel_data)
    normalized['custom_url'] = _extract_custom_url(channel_data)
    normalized['published_at'] = _extract_published_at(channel_data)
    normalized['country'] = _extract_country(channel_data)
    normalized['default_language'] = _extract_default_language(channel_data)
    
    # --- Content and status fields ---
    normalized['privacy_status'] = _extract_privacy_status(channel_data)
    normalized['is_linked'] = _normalize_boolean_field(channel_data, ['is_linked', 'status_isLinked'], False)
    normalized['long_uploads_status'] = _extract_long_uploads_status(channel_data)
    normalized['made_for_kids'] = _normalize_boolean_field(channel_data, ['made_for_kids', 'status_madeForKids'], False)
    normalized['hidden_subscriber_count'] = _normalize_boolean_field(channel_data, ['hidden_subscriber_count', 'statistics_hiddenSubscriberCount'], False)
    
    # --- Thumbnail URLs ---
    normalized['thumbnail_default'] = _extract_thumbnail_url(channel_data, 'default')
    normalized['thumbnail_medium'] = _extract_thumbnail_url(channel_data, 'medium')
    normalized['thumbnail_high'] = _extract_thumbnail_url(channel_data, 'high')
    
    # --- Additional metadata ---
    normalized['keywords'] = _extract_keywords(channel_data)
    normalized['topic_categories'] = _extract_topic_categories(channel_data)
    
    # --- Timestamps (normalize format) ---
    normalized['fetched_at'] = _normalize_timestamp(channel_data.get('fetched_at') or datetime.now().isoformat())
    normalized['updated_at'] = _normalize_timestamp(datetime.now().isoformat())
    
    # --- Video data (simple handling without external dependencies) ---
    videos = _extract_videos(channel_data)
    if videos:
        normalized['video_id'] = _standardize_videos_simple(videos)
        logger.info(f"normalize_channel_data_for_save ({workflow_type}): Normalized {len(normalized['video_id'])} videos")
    else:
        normalized['video_id'] = []
        logger.info(f"normalize_channel_data_for_save ({workflow_type}): No videos to normalize")
    
    # --- Remove any non-persistent/session fields that should not be saved ---
    _remove_non_persistent_fields(normalized)
    
    logger.info(f"normalize_channel_data_for_save ({workflow_type}): Normalization complete. Fields: {list(normalized.keys())}")
    
    return normalized

def _extract_channel_id(data):
    """Extract channel_id from various possible locations."""
    return (
        data.get('channel_id') or
        data.get('id') or
        data.get('raw_channel_info', {}).get('id') or
        data.get('channel_info', {}).get('id') or
        ''
    )

def _extract_channel_name(data):
    """Extract channel_name from various possible locations."""
    return (
        data.get('channel_name') or
        data.get('channel_title') or
        data.get('title') or
        data.get('raw_channel_info', {}).get('snippet', {}).get('title') or
        data.get('channel_info', {}).get('snippet', {}).get('title') or
        data.get('channel_info', {}).get('title') or
        'Unknown Channel'
    )

def _extract_playlist_id(data):
    """Extract uploads playlist_id from various possible locations."""
    return (
        data.get('playlist_id') or
        data.get('uploads_playlist_id') or
        data.get('raw_channel_info', {}).get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads') or
        data.get('channel_info', {}).get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads') or
        data.get('contentDetails_relatedPlaylists_uploads') or
        ''
    )

def _extract_kind(data):
    """Extract kind from various possible locations."""
    return (
        data.get('kind') or
        data.get('raw_channel_info', {}).get('kind') or
        data.get('channel_info', {}).get('kind') or
        ''
    )

def _extract_etag(data):
    """Extract etag from various possible locations."""
    return (
        data.get('etag') or
        data.get('raw_channel_info', {}).get('etag') or
        data.get('channel_info', {}).get('etag') or
        ''
    )

def _extract_channel_description(data):
    """Extract channel description from various possible locations."""
    return (
        data.get('channel_description') or
        data.get('description') or
        data.get('raw_channel_info', {}).get('snippet', {}).get('description') or
        data.get('channel_info', {}).get('snippet', {}).get('description') or
        data.get('snippet_description') or
        ''
    )

def _extract_custom_url(data):
    """Extract custom URL from various possible locations."""
    return (
        data.get('custom_url') or
        data.get('raw_channel_info', {}).get('snippet', {}).get('customUrl') or
        data.get('channel_info', {}).get('snippet', {}).get('customUrl') or
        data.get('snippet_customUrl') or
        ''
    )

def _extract_published_at(data):
    """Extract published_at timestamp from various possible locations."""
    return (
        data.get('published_at') or
        data.get('raw_channel_info', {}).get('snippet', {}).get('publishedAt') or
        data.get('channel_info', {}).get('snippet', {}).get('publishedAt') or
        data.get('snippet_publishedAt') or
        ''
    )

def _extract_country(data):
    """Extract country from various possible locations."""
    return (
        data.get('country') or
        data.get('raw_channel_info', {}).get('snippet', {}).get('country') or
        data.get('channel_info', {}).get('snippet', {}).get('country') or
        data.get('snippet_country') or
        ''
    )

def _extract_default_language(data):
    """Extract default language from various possible locations."""
    return (
        data.get('default_language') or
        data.get('raw_channel_info', {}).get('snippet', {}).get('defaultLanguage') or
        data.get('channel_info', {}).get('snippet', {}).get('defaultLanguage') or
        data.get('snippet_defaultLanguage') or
        ''
    )

def _extract_privacy_status(data):
    """Extract privacy status from various possible locations."""
    return (
        data.get('privacy_status') or
        data.get('raw_channel_info', {}).get('status', {}).get('privacyStatus') or
        data.get('channel_info', {}).get('status', {}).get('privacyStatus') or
        data.get('status_privacyStatus') or
        ''
    )

def _extract_long_uploads_status(data):
    """Extract long uploads status from various possible locations."""
    return (
        data.get('long_uploads_status') or
        data.get('raw_channel_info', {}).get('status', {}).get('longUploadsStatus') or
        data.get('channel_info', {}).get('status', {}).get('longUploadsStatus') or
        data.get('status_longUploadsStatus') or
        ''
    )

def _extract_keywords(data):
    """Extract keywords from various possible locations."""
    keywords = (
        data.get('keywords') or
        data.get('raw_channel_info', {}).get('brandingSettings', {}).get('channel', {}).get('keywords') or
        data.get('channel_info', {}).get('brandingSettings', {}).get('channel', {}).get('keywords') or
        data.get('brandingSettings_channel_keywords') or
        ''
    )
    # Ensure keywords is a string
    if isinstance(keywords, list):
        keywords = ', '.join(keywords)
    return str(keywords)

def _extract_topic_categories(data):
    """Extract topic categories from various possible locations."""
    categories = (
        data.get('topic_categories') or
        data.get('raw_channel_info', {}).get('topicDetails', {}).get('topicCategories') or
        data.get('channel_info', {}).get('topicDetails', {}).get('topicCategories') or
        data.get('topicDetails_topicCategories') or
        []
    )
    # Ensure topic_categories is a string
    if isinstance(categories, list):
        categories = ', '.join(categories)
    return str(categories)

def _extract_thumbnail_url(data, size):
    """Extract thumbnail URL for a specific size."""
    # Try raw_channel_info first
    raw_info = data.get('raw_channel_info', {})
    if 'snippet' in raw_info and 'thumbnails' in raw_info['snippet']:
        thumbnails = raw_info['snippet']['thumbnails']
        if size in thumbnails and 'url' in thumbnails[size]:
            return thumbnails[size]['url']
    
    # Try channel_info
    channel_info = data.get('channel_info', {})
    if 'snippet' in channel_info and 'thumbnails' in channel_info['snippet']:
        thumbnails = channel_info['snippet']['thumbnails']
        if size in thumbnails and 'url' in thumbnails[size]:
            return thumbnails[size]['url']
    
    # Try direct fields
    field_name = f'thumbnail_{size}'
    return data.get(field_name, '')

def _extract_videos(data):
    """Extract video data from various possible locations."""
    # Try different field names where videos might be stored
    videos = (
        data.get('video_id') or
        data.get('videos') or
        data.get('video_data') or
        []
    )
    
    # Ensure it's a list
    if not isinstance(videos, list):
        videos = [videos] if videos else []
    
    return videos

def _standardize_videos_simple(videos):
    """Simple video standardization without external dependencies."""
    if not videos:
        return []
    
    # If it's already a list of video IDs, return as-is
    if all(isinstance(v, str) for v in videos):
        return videos
    
    # If it's a list of video objects, extract IDs
    video_ids = []
    for video in videos:
        if isinstance(video, dict):
            video_id = (
                video.get('video_id') or
                video.get('id') or
                video.get('snippet', {}).get('resourceId', {}).get('videoId') or
                ''
            )
            if video_id:
                video_ids.append(video_id)
        elif isinstance(video, str):
            video_ids.append(video)
    
    return video_ids

def _normalize_integer_field(data, field_names, default=0):
    """Extract and normalize an integer field from various possible locations."""
    value = None
    
    # Try each field name in order
    for field_name in field_names:
        if field_name in data:
            value = data[field_name]
            break
    
    # Try nested paths in raw_channel_info
    if value is None:
        raw_info = data.get('raw_channel_info', {})
        if 'statistics' in raw_info:
            stats = raw_info['statistics']
            for field_name in field_names:
                # Map field names to API statistics field names
                api_field = _map_to_api_field(field_name)
                if api_field in stats:
                    value = stats[api_field]
                    break
    
    # Try nested paths in channel_info
    if value is None:
        channel_info = data.get('channel_info', {})
        if 'statistics' in channel_info:
            stats = channel_info['statistics']
            for field_name in field_names:
                api_field = _map_to_api_field(field_name)
                if api_field in stats:
                    value = stats[api_field]
                    break
    
    # Convert to integer
    if value is not None:
        try:
            return int(str(value).replace(',', ''))
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value '{value}' to integer, using default {default}")
    
    return default

def _normalize_boolean_field(data, field_names, default=False):
    """Extract and normalize a boolean field from various possible locations."""
    value = None
    
    # Try each field name in order
    for field_name in field_names:
        if field_name in data:
            value = data[field_name]
            break
    
    # Try nested paths
    if value is None:
        raw_info = data.get('raw_channel_info', {})
        for section in ['status', 'statistics']:
            if section in raw_info:
                section_data = raw_info[section]
                for field_name in field_names:
                    api_field = _map_to_api_field(field_name)
                    if api_field in section_data:
                        value = section_data[api_field]
                        break
                if value is not None:
                    break
    
    # Convert to boolean
    if value is not None:
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(value, (int, float)):
            return bool(value)
    
    return default

def _map_to_api_field(field_name):
    """Map internal field names to YouTube API field names."""
    mapping = {
        'subscribers': 'subscriberCount',
        'subscriber_count': 'subscriberCount',
        'views': 'viewCount',
        'view_count': 'viewCount',
        'total_videos': 'videoCount',
        'video_count': 'videoCount',
        'hidden_subscriber_count': 'hiddenSubscriberCount',
        'is_linked': 'isLinked',
        'made_for_kids': 'madeForKids',
    }
    return mapping.get(field_name, field_name)

def _normalize_timestamp(timestamp_str):
    """Normalize timestamp to consistent ISO format."""
    if not timestamp_str:
        return datetime.now().isoformat()
    
    try:
        # If it's already a proper ISO format, return as-is
        if 'T' in timestamp_str and ('Z' in timestamp_str or '+' in timestamp_str):
            return timestamp_str
        
        # Try to parse and reformat
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.isoformat()
    except Exception:
        # If parsing fails, return current timestamp
        logger.warning(f"Could not parse timestamp '{timestamp_str}', using current time")
        return datetime.now().isoformat()

def _remove_non_persistent_fields(data):
    """Remove fields that should not be persisted to database."""
    non_persistent_fields = [
        # Session/temporary fields
        '_comparison_options',
        '_delta_options',
        '_existing_data',
        'delta',
        'raw_channel_info',  # This is already processed into normalized fields
        'data_source',
        'debug_info',
        'ui_state',
        'session_id',
        'request_id',
        
        # Internal processing fields
        'processing_status',
        'validation_errors',
        'api_response_raw',
        'temp_data',
        'workflow_step',
        'collection_step'
    ]
    
    for field in non_persistent_fields:
        if field in data:
            del data[field]
            logger.info(f"Removed non-persistent field: {field}")
