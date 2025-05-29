"""
Fixed Channel Repository with proper field mapping and missing value handling.
This addresses the missing YouTube API fields issue by:
1. Correctly mapping database columns to flattened API field names
2. Adding proper handling for missing API fields vs mapping issues
3. Adding enhanced logging for debugging
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union
import json
import os

import pandas as pd
import streamlit as st

from src.utils.debug_utils import debug_log
from src.database.base_repository import BaseRepository

def flatten_dict(d, parent_key='', sep='.'):
    """Recursively flattens a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def safe_int(val, field_name):
    """Safely convert a value to int, or return None if not possible. Log a warning if conversion fails."""
    try:
        if val is None or val == '':
            return None
        return int(val)
    except Exception as e:
        debug_log(f"[DB WARNING] Could not convert {field_name} value '{val}' to int: {str(e)}")
        return None

def serialize_for_sqlite(val):
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    return val

def handle_missing_api_field(field_name, column_type=None):
    """
    Handle missing API fields by returning appropriate default values
    based on the database column type and field semantics.
    
    Args:
        field_name: The name of the missing field
        column_type: The database column type
    
    Returns:
        Appropriate default value or special marker for missing data
    """
    # For fields that should explicitly indicate "not provided by API"
    # These are optional fields that may not be present in API response
    if field_name in [
        'snippet_defaultLanguage',
        'snippet_country',
        'brandingSettings_channel_keywords',
        'brandingSettings_channel_country',
        'brandingSettings_image_bannerExternalUrl'
    ]:
        return "NOT_PROVIDED_BY_API"
    
    # For fields that should be null when not available
    # These represent optional nested data
    if field_name in [
        'snippet_localized_title',
        'snippet_localized_description', 
        'contentDetails_relatedPlaylists_likes',
        'contentDetails_relatedPlaylists_favorites',
        'topicDetails_topicIds'
    ]:
        return None
    
    # For complex fields that should be empty objects/arrays
    if field_name in ['localizations']:
        return "{}"  # Empty JSON object
    
    # Default handling based on column type
    if column_type == 'BOOLEAN':
        return False
    elif column_type == 'INTEGER':
        return 0
    else:  # TEXT
        return None

class ChannelRepository(BaseRepository):
    """Repository for managing YouTube channel data in the SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the repository with the database path."""
        self.db_path = db_path
        self._video_repository = None
    
    @property
    def video_repository(self):
        """Lazy initialization of VideoRepository to avoid circular imports""" 
        if self._video_repository is None:
            from src.database.video_repository import VideoRepository
            self._video_repository = VideoRepository(self.db_path)
        return self._video_repository
    
    def store_channel_data(self, data):
        """Save channel data to SQLite database, mapping every API field (recursively) to a column, and insert full JSON into channel_history only."""
        try:
            abs_db_path = os.path.abspath(self.db_path)
            debug_log(f"[DB] Using database at: {abs_db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # --- Flatten the actual raw API response ---
            raw_api = data.get('raw_channel_info') or data.get('channel_info', data)
            flat_api = flatten_dict(raw_api)
            
            # --- Merge in extra fields from the wrapper dict (e.g., channel_id, channel_title) ---
            extra_fields = {k: v for k, v in data.items() if k not in ['raw_channel_info', 'channel_info']}
            flat_api.update(extra_fields)
            
            # --- Map dot notation to underscores for DB columns ---
            flat_api_underscore = {k.replace('.', '_'): v for k, v in flat_api.items()}
            
            # --- Get all columns in the channels table ---
            cursor.execute("PRAGMA table_info(channels)")
            column_info = cursor.fetchall()
            existing_cols = set(row[1] for row in column_info)
            column_types = {row[1]: row[2] for row in column_info}  # column_name -> column_type
            
            # Track missing fields for debugging
            missing_fields = []
            mapped_fields = []
            
            # --- Prepare columns and values for insert/update ---
            columns = []
            values = []
            for col in existing_cols:
                if col in ['id', 'created_at', 'updated_at']:
                    continue
                    
                api_key = CANONICAL_FIELD_MAP.get(col, col)
                v = flat_api_underscore.get(api_key, None)
                
                if v is None:
                    # Field is missing from API response - use appropriate default
                    v = handle_missing_api_field(col, column_types.get(col))
                    missing_fields.append(f"{col} (API field: {api_key})")
                else:
                    mapped_fields.append(f"{col} -> {api_key}")
                
                values.append(serialize_for_sqlite(v))
                columns.append(col)
            
            # Enhanced logging for debugging field mapping
            debug_log(f"[DB FIELD MAPPING] Channel ID: {flat_api.get('channel_id') or flat_api.get('id')}")
            debug_log(f"[DB FIELD MAPPING] Successfully mapped {len(mapped_fields)} fields")
            if missing_fields:
                debug_log(f"[DB FIELD MAPPING] Missing from API response ({len(missing_fields)} fields): {missing_fields[:5]}{'...' if len(missing_fields) > 5 else ''}")
            debug_log(f"[DB DEBUG] Available API fields: {list(flat_api_underscore.keys())[:10]}{'...' if len(flat_api_underscore) > 10 else ''}")
            
            debug_log(f"[DB INSERT] Final channel insert columns: {columns}")
            debug_log(f"[DB INSERT] Final channel insert values (first 5): {values[:5]}{'...' if len(values) > 5 else ''}")
            
            if not columns:
                debug_log("[DB WARNING] No columns to insert for channel.")
                conn.close()
                return False
                
            placeholders = ','.join(['?'] * len(columns))
            update_clause = ','.join([f'{col}=excluded.{col}' for col in columns])
            cursor.execute(f'''
                INSERT INTO channels ({','.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(channel_id) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP
            ''', values)
            debug_log(f"Inserted/updated channel: {flat_api.get('channel_id') or flat_api.get('id')}")
            
            # --- Insert full JSON into channel_history only ---
            self._ensure_channel_history_table(cursor)
            import datetime, json
            fetched_at = datetime.datetime.utcnow().isoformat()
            raw_channel_info = json.dumps(raw_api)
            cursor.execute('''
                INSERT INTO channel_history (channel_id, fetched_at, raw_channel_info) VALUES (?, ?, ?)
            ''', (flat_api.get('channel_id') or flat_api.get('id'), fetched_at, raw_channel_info))
            
            conn.commit()
            
            # After commit, check if row exists
            cursor.execute("SELECT COUNT(*) FROM channels WHERE channel_id = ?", (flat_api.get('channel_id') or flat_api.get('id'),))
            row_count = cursor.fetchone()[0]
            debug_log(f"[DB] Row count for channel_id={flat_api.get('channel_id') or flat_api.get('id')} after save: {row_count}")
            conn.close()
            
            # Process and store videos if present in the data
            if 'video_id' in data and data['video_id']:
                videos = data['video_id']
                debug_log(f"[DB] Processing {len(videos)} videos for storage")
                videos_stored = 0
                for video in videos:
                    try:
                        video_store_result = self.video_repository.store_video_data(video)
                        debug_log(f"[DB] store_video_data result for video {video.get('video_id')}: {video_store_result}")
                        if video_store_result:
                            videos_stored += 1
                            # --- Store comments for this video if present ---
                            # Try both 'youtube_id' and 'video_id' for DB lookup
                            yt_id = video.get('youtube_id') or video.get('video_id') or video.get('id')
                            video_db_id = self.video_repository.get_video_db_id(yt_id)
                            comments = video.get('comments', [])
                            debug_log(f"[DB] Video: yt_id={yt_id}, db_id={video_db_id}, comments={len(comments)}")
                            if comments and video_db_id:
                                debug_log(f"[DB] First comment for video {yt_id}: {comments[0] if comments else 'None'}")
                                comment_store_result = self.video_repository.store_comments(comments, video_db_id, fetched_at=None)
                                debug_log(f"[DB] Stored {len(comments)} comments for video {yt_id}, result: {comment_store_result}")
                            elif comments and not video_db_id:
                                debug_log(f"[DB WARNING] Comments present but could not find DB ID for video {yt_id}")
                    except Exception as e:
                        debug_log(f"[DB ERROR] Failed to store video {video.get('video_id', 'unknown')}: {str(e)}")
                debug_log(f"[DB] Successfully stored {videos_stored} out of {len(videos)} videos")
            
            return True
        except Exception as e:
            import traceback
            debug_log(f"Exception in store_channel_data: {str(e)}\n{traceback.format_exc()}")
            return {"error": str(e)}

    def _ensure_channel_history_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                raw_channel_info TEXT NOT NULL
            )
        ''')

    def get_all_channels(self):
        """Get all channels from SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            debug_log(f"Error getting all channels: {str(e)}")
            return []

    def get_channel_by_id(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full data for a specific channel, including all API fields from raw_channel_info if present.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the main channel record first
            cursor.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            # Convert to dictionary
            record = dict(zip(columns, row))
            
            # Get the most recent raw API data for this channel from history
            try:
                cursor.execute("""
                    SELECT raw_channel_info 
                    FROM channel_history 
                    WHERE channel_id = ? 
                    ORDER BY fetched_at DESC 
                    LIMIT 1
                """, (channel_id,))
                history_row = cursor.fetchone()
                
                if history_row and history_row[0]:
                    raw_info = json.loads(history_row[0])
                    # Merge raw API data into the record, giving priority to DB values
                    record['raw_channel_info'] = raw_info
                    
                    # Add any additional fields from raw API that aren't in the DB
                    flattened_raw = flatten_dict(raw_info)
                    for key, value in flattened_raw.items():
                        db_key = key.replace('.', '_')
                        if db_key not in record and value is not None:
                            record[db_key] = value
                            
            except json.JSONDecodeError as e:
                debug_log(f"Error parsing raw_channel_info JSON for channel {channel_id}: {str(e)}")
            
            conn.close()
            return record
            
        except Exception as e:
            debug_log(f"Error getting channel by ID {channel_id}: {str(e)}")
            return None

    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel and all its associated data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, get all videos for this channel to delete their comments
            cursor.execute("SELECT id FROM videos WHERE channel_id = ?", (channel_id,))
            video_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete comments for all videos of this channel
            for video_id in video_ids:
                cursor.execute("DELETE FROM comments WHERE video_id = ?", (video_id,))
            
            # Delete videos for this channel
            cursor.execute("DELETE FROM videos WHERE channel_id = ?", (channel_id,))
            
            # Delete channel history
            cursor.execute("DELETE FROM channel_history WHERE channel_id = ?", (channel_id,))
            
            # Delete the channel itself
            cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
            
            conn.commit()
            conn.close()
            
            debug_log(f"Deleted channel {channel_id} and all associated data")
            return True
            
        except Exception as e:
            debug_log(f"Error deleting channel {channel_id}: {str(e)}")
            return False

    def get_channel_statistics(self) -> Dict[str, Any]:
        """Get statistics about channels in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total number of channels
            cursor.execute("SELECT COUNT(*) FROM channels")
            total_channels = cursor.fetchone()[0]
            
            # Get channels with most subscribers
            cursor.execute("""
                SELECT channel_id, channel_title, subscriber_count 
                FROM channels 
                WHERE subscriber_count IS NOT NULL 
                ORDER BY subscriber_count DESC 
                LIMIT 10
            """)
            top_channels = cursor.fetchall()
            
            # Get total videos and views across all channels
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(video_count), 0) as total_videos,
                    COALESCE(SUM(view_count), 0) as total_views
                FROM channels 
                WHERE video_count IS NOT NULL AND view_count IS NOT NULL
            """)
            totals = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_channels': total_channels,
                'total_videos': totals[0] if totals else 0,
                'total_views': totals[1] if totals else 0,
                'top_channels': [
                    {'channel_id': row[0], 'title': row[1], 'subscribers': row[2]}
                    for row in top_channels
                ]
            }
            
        except Exception as e:
            debug_log(f"Error getting channel statistics: {str(e)}")
            return {'total_channels': 0, 'total_videos': 0, 'total_views': 0, 'top_channels': []}

# Updated CANONICAL_FIELD_MAP - Maps database column names to their corresponding flattened API field names
CANONICAL_FIELD_MAP = {
    # Basic channel info
    'channel_id': 'id',  # API 'id' field maps to DB 'channel_id'
    'channel_title': 'snippet_title',
    'uploads_playlist_id': 'contentDetails_relatedPlaylists_uploads',
    
    # Kind and etag - direct mapping
    'kind': 'kind',
    'etag': 'etag',
    
    # Snippet fields - direct mapping to flattened API field names
    'snippet_title': 'snippet_title',
    'snippet_description': 'snippet_description', 
    'snippet_customUrl': 'snippet_customUrl',
    'snippet_publishedAt': 'snippet_publishedAt',
    'snippet_defaultLanguage': 'snippet_defaultLanguage',
    'snippet_country': 'snippet_country',
    'snippet_thumbnails_default_url': 'snippet_thumbnails_default_url',
    'snippet_thumbnails_medium_url': 'snippet_thumbnails_medium_url', 
    'snippet_thumbnails_high_url': 'snippet_thumbnails_high_url',
    'snippet_localized_title': 'snippet_localized_title',
    'snippet_localized_description': 'snippet_localized_description',
    
    # Content details - direct mapping
    'contentDetails_relatedPlaylists_uploads': 'contentDetails_relatedPlaylists_uploads',
    'contentDetails_relatedPlaylists_likes': 'contentDetails_relatedPlaylists_likes',
    'contentDetails_relatedPlaylists_favorites': 'contentDetails_relatedPlaylists_favorites',
    
    # Statistics - direct mapping plus backward compatibility
    'subscriber_count': 'statistics_subscriberCount',
    'view_count': 'statistics_viewCount', 
    'video_count': 'statistics_videoCount',
    'statistics_viewCount': 'statistics_viewCount',
    'statistics_subscriberCount': 'statistics_subscriberCount',
    'statistics_hiddenSubscriberCount': 'statistics_hiddenSubscriberCount',
    'statistics_videoCount': 'statistics_videoCount',
    
    # Branding settings - direct mapping
    'brandingSettings_channel_title': 'brandingSettings_channel_title',
    'brandingSettings_channel_description': 'brandingSettings_channel_description',
    'brandingSettings_channel_keywords': 'brandingSettings_channel_keywords',
    'brandingSettings_channel_country': 'brandingSettings_channel_country',
    'brandingSettings_image_bannerExternalUrl': 'brandingSettings_image_bannerExternalUrl',
    
    # Status - direct mapping
    'status_privacyStatus': 'status_privacyStatus',
    'status_isLinked': 'status_isLinked',
    'status_longUploadsStatus': 'status_longUploadsStatus',
    'status_madeForKids': 'status_madeForKids',
    
    # Topic details - direct mapping
    'topicDetails_topicIds': 'topicDetails_topicIds',
    'topicDetails_topicCategories': 'topicDetails_topicCategories',
    
    # Localizations - direct mapping
    'localizations': 'localizations',
}
