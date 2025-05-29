"""
Channel repository module for interacting with YouTube channel data in the SQLite database.
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
            debug_log(f"[DB DEBUG] flat_api_underscore: {flat_api_underscore}")
            # --- Get all columns in the channels table ---
            cursor.execute("PRAGMA table_info(channels)")
            existing_cols = set(row[1] for row in cursor.fetchall())
            # --- Prepare columns and values for insert/update ---
            columns = []
            values = []
            for col in existing_cols:
                if col in ['id', 'created_at', 'updated_at']:
                    continue
                api_key = CANONICAL_FIELD_MAP.get(col, col)
                v = flat_api_underscore.get(api_key, None)
                values.append(serialize_for_sqlite(v))
                columns.append(col)
            debug_log(f"[DB INSERT] Final channel insert columns: {columns}")
            debug_log(f"[DB INSERT] Final channel insert values: {values}")
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

    def get_channel_db_id(self, channel_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM channels WHERE channel_id = ?", (channel_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def get_channels_list(self):
        """Get a list of all channel names from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT channel_id, channel_title FROM channels ORDER BY channel_title")
            rows = cursor.fetchall()
            channels = [{'channel_id': row[0], 'channel_name': row[1]} for row in rows]
            conn.close()
            debug_log(f"Retrieved {len(channels)} channels from database")
            return channels
        except Exception as e:
            debug_log(f"Exception in get_channels_list: {str(e)}")
            return []
    
    def get_channel_data(self, channel_identifier):
        """Get full data for a specific channel, including all API fields from raw_channel_info if present."""
        conn = None
        try:
            abs_db_path = os.path.abspath(self.db_path)
            debug_log(f"[DB] Using database at: {abs_db_path}")
            is_id = channel_identifier.startswith('UC')
            debug_log(f"Loading data for channel: {channel_identifier} from database")
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Get channel info - using either ID or title depending on what was provided
            if is_id:
                cursor.execute("""
                    SELECT * FROM channels WHERE channel_id = ?
                """, (channel_identifier,))
            else:
                cursor.execute("""
                    SELECT * FROM channels WHERE channel_title = ?
                """, (channel_identifier,))
            row = cursor.fetchone()
            if not row:
                debug_log(f"Channel not found in database: {channel_identifier}")
                return None
            record = dict(row)
            # Load full API response if present
            cursor.execute("PRAGMA table_info(channels)")
            columns = [r[1] for r in cursor.fetchall()]
            raw_info = None
            if 'raw_channel_info' in columns:
                cursor.execute("SELECT raw_channel_info FROM channels WHERE id = ?", (record['id'],))
                raw_info_row = cursor.fetchone()
                if raw_info_row and raw_info_row[0]:
                    try:
                        import json
                        raw_info = json.loads(raw_info_row[0])
                    except Exception as e:
                        debug_log(f"Error loading raw_channel_info JSON: {str(e)}")
            # Fetch uploads playlist from playlists table
            cursor.execute("SELECT playlist_id FROM playlists WHERE channel_id = ? AND type = 'uploads'", (record['channel_id'],))
            playlist_row = cursor.fetchone()
            uploads_playlist_id = playlist_row[0] if playlist_row else record.get('uploads_playlist_id', '')
            # Always set playlist_id from uploads_playlist_id if present
            record['uploads_playlist_id'] = uploads_playlist_id
            record['playlist_id'] = uploads_playlist_id
            record['raw_channel_info'] = raw_info
            debug_log(f"[DB] get_channel_data returning: {record}")
            return record
        except Exception as e:
            debug_log(f"Exception in get_channel_data: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_channel_id_by_title(self, title):
        """Get the YouTube channel ID for a given channel title."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT channel_id FROM channels WHERE channel_title = ?", (title,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            debug_log(f"Exception in get_channel_id_by_title: {str(e)}")
            return None

    def display_channels_data(self):
        """Display all channels from SQLite database in a Streamlit interface"""
        debug_log("Loading channels from SQLite")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            
            # Query for channels data with video counts
            query = '''
            SELECT 
                c.title as channel_name,
                c.channel_id as channel_id,
                c.subscriber_count as subscribers,
                c.view_count as views,
                c.video_count as total_videos,
                COUNT(v.id) as fetched_videos,
                CASE 
                    WHEN COUNT(v.id) > 0 THEN c.view_count / COUNT(v.id)
                    ELSE 0
                END as avg_views_per_video
            FROM 
                channels c
            LEFT JOIN 
                videos v ON v.channel_id = c.id
            GROUP BY 
                c.id
            '''
            
            # Execute query and convert to DataFrame
            df = pd.read_sql_query(query, conn)
            
            # Close the connection
            conn.close()
            
            # Display the data
            if not df.empty:
                st.dataframe(df)
            else:
                st.info("No channels found in SQLite database.")
                
            return True
        except Exception as e:
            debug_log(f"Error loading data from SQLite: {str(e)}")
            return False
    
    def list_channels(self):
        """
        Get a list of all channels from the database with their IDs and titles.
        
        Returns:
            list: List of tuples containing (channel_id, title) for each channel
        """
        debug_log("Fetching list of all channels")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query all channels, returning both ID and title
            cursor.execute("SELECT channel_id, channel_title FROM channels ORDER BY channel_title")
            channels = cursor.fetchall()
            
            # Close the connection
            conn.close()
            
            debug_log(f"Retrieved {len(channels)} channels from database")
            return channels
        except Exception as e:
            debug_log(f"Exception in list_channels: {str(e)}")
            return []

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a channel by its database ID.
        
        Args:
            id: The database ID of the channel
            
        Returns:
            Optional[Dict[str, Any]]: The channel data as a dictionary, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use Row to access by column name
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM channels WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            debug_log(f"Error retrieving channel by ID {id}: {str(e)}", e)
            return None

    def get_uploads_playlist_id(self, channel_id):
        """Fetch the uploads playlist ID for a channel from the playlists table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT playlist_id FROM playlists WHERE channel_id = ? AND type = 'uploads'", (channel_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                debug_log(f"Found uploads playlist_id for channel_id={channel_id}: {row[0]}")
                return row[0]
            debug_log(f"No uploads playlist_id found for channel_id={channel_id}")
            return ''
        except Exception as e:
            debug_log(f"Exception in get_uploads_playlist_id: {str(e)}")
            return ''

# ... existing code ...

CANONICAL_FIELD_MAP = {
    # Basic channel info
    'channel_id': 'channel_id',
    'channel_title': 'channel_title',
    'uploads_playlist_id': 'uploads_playlist_id',
    
    # Kind and etag
    'kind': 'kind',
    'etag': 'etag',
    
    # Snippet fields
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
    
    # Content details
    'contentDetails_relatedPlaylists_uploads': 'contentDetails_relatedPlaylists_uploads',
    'contentDetails_relatedPlaylists_likes': 'contentDetails_relatedPlaylists_likes',
    'contentDetails_relatedPlaylists_favorites': 'contentDetails_relatedPlaylists_favorites',
    
    # Statistics (with backward compatibility)
    'subscriber_count': 'statistics_subscriberCount',
    'view_count': 'statistics_viewCount', 
    'video_count': 'statistics_videoCount',
    'statistics_viewCount': 'statistics_viewCount',
    'statistics_subscriberCount': 'statistics_subscriberCount',
    'statistics_hiddenSubscriberCount': 'statistics_hiddenSubscriberCount',
    'statistics_videoCount': 'statistics_videoCount',
    
    # Branding settings
    'brandingSettings_channel_title': 'brandingSettings_channel_title',
    'brandingSettings_channel_description': 'brandingSettings_channel_description',
    'brandingSettings_channel_keywords': 'brandingSettings_channel_keywords',
    'brandingSettings_channel_country': 'brandingSettings_channel_country',
    'brandingSettings_image_bannerExternalUrl': 'brandingSettings_image_bannerExternalUrl',
    
    # Status
    'status_privacyStatus': 'status_privacyStatus',
    'status_isLinked': 'status_isLinked',
    'status_longUploadsStatus': 'status_longUploadsStatus',
    'status_madeForKids': 'status_madeForKids',
    
    # Topic details
    'topicDetails_topicIds': 'topicDetails_topicIds',
    'topicDetails_topicCategories': 'topicDetails_topicCategories',
    
    # Localizations
    'localizations': 'localizations',
    
    # Legacy/simplified field mappings for application compatibility
    'channel_name': 'channel_title',
    'channel_description': 'snippet_description',
    'description': 'snippet_description',
    'custom_url': 'snippet_customUrl',
    'published_at': 'snippet_publishedAt',
    'country': 'snippet_country',
    'default_language': 'snippet_defaultLanguage',
    'thumbnail_default': 'snippet_thumbnails_default_url',
    'thumbnail_medium': 'snippet_thumbnails_medium_url',
    'thumbnail_high': 'snippet_thumbnails_high_url',
    'subscribers': 'statistics_subscriberCount',
    'views': 'statistics_viewCount',
    'total_videos': 'statistics_videoCount',
    'privacy_status': 'status_privacyStatus',
    'is_linked': 'status_isLinked',
    'long_uploads_status': 'status_longUploadsStatus',
    'made_for_kids': 'status_madeForKids',
    'hidden_subscriber_count': 'statistics_hiddenSubscriberCount',
    'keywords': 'brandingSettings_channel_keywords',
    'topic_categories': 'topicDetails_topicCategories',
    'playlist_id': 'uploads_playlist_id',
}
