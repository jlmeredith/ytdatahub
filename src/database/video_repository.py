"""
Video repository module for interacting with YouTube video data in the SQLite database.
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json
import os

import pandas as pd
import streamlit as st

from src.utils.debug_utils import debug_log
from src.database.base_repository import BaseRepository

def handle_missing_api_field(field_name: str, column_type: str = 'TEXT') -> Any:
    """
    Handle missing API fields by returning appropriate default values for videos table.
    This helps distinguish between fields that are truly missing from the API response
    vs. fields that are not being mapped correctly.
    
    Args:
        field_name: The database column name
        column_type: The SQLite column type (TEXT, INTEGER, BOOLEAN, etc.)
    
    Returns:
        Appropriate default value based on the field semantics
    """
    # Fields that should explicitly indicate "not provided by API"
    api_provided_fields = {
        'snippet_default_language', 'snippet_default_audio_language', 
        'snippet_category_id', 'snippet_localized_title', 'snippet_localized_description',
        'content_details_duration', 'content_details_dimension', 'content_details_definition',
        'content_details_caption', 'status_upload_status', 'status_failure_reason',
        'status_rejection_reason', 'status_privacy_status', 'status_license',
        'status_embeddable', 'status_public_stats_viewable', 'status_made_for_kids',
        'player_embed_html', 'topic_details_topic_ids', 'topic_details_relevant_topic_ids',
        'topic_details_topic_categories'
    }
    
    # Complex fields that should be empty objects/arrays when missing
    complex_fields = {
        'localizations': '{}',  # Empty JSON object
        'snippet_tags': '[]',  # Empty JSON array
        'content_details_region_restriction_allowed': '[]',
        'content_details_region_restriction_blocked': '[]',
        'content_details_content_rating': '{}',
        'topic_details_topic_ids': '[]',
        'topic_details_relevant_topic_ids': '[]',
        'topic_details_topic_categories': '[]'
    }
    
    if field_name in api_provided_fields:
        return "NOT_PROVIDED_BY_API"
    elif field_name in complex_fields:
        return complex_fields[field_name]
    elif column_type == 'INTEGER':
        return None
    elif column_type == 'BOOLEAN':
        return False
    else:
        return None

# Define a canonical mapping of database columns to API fields
CANONICAL_FIELD_MAP = {
    # Basic info - map DB columns to flattened API field names
    'youtube_id': 'id',
    'kind': 'kind',
    'etag': 'etag',
    
    # Snippet fields - Using only normalized prefixed field names (no duplicates)
    'snippet_title': 'snippet_title',
    'snippet_description': 'snippet_description',
    'snippet_channel_id': 'snippet_channelId',
    'snippet_channel_title': 'snippet_channelTitle',
    'published_at': 'snippet_publishedAt',
    'snippet_tags': 'snippet_tags',
    'snippet_category_id': 'snippet_categoryId',
    'snippet_live_broadcast_content': 'snippet_liveBroadcastContent',
    'snippet_default_language': 'snippet_defaultLanguage',
    'snippet_localized_title': 'snippet_localized_title',
    'snippet_localized_description': 'snippet_localized_description',
    'snippet_default_audio_language': 'snippet_defaultAudioLanguage',
    
    # Thumbnails - These come from snippet.thumbnails.{size}
    'snippet_thumbnails_default': 'snippet_thumbnails_default',
    'snippet_thumbnails_medium': 'snippet_thumbnails_medium',
    'snippet_thumbnails_high': 'snippet_thumbnails_high',
    'snippet_thumbnails_standard': 'snippet_thumbnails_standard',
    'snippet_thumbnails_maxres': 'snippet_thumbnails_maxres',
    
    # Content details
    'content_details_duration': 'contentDetails_duration',
    'content_details_dimension': 'contentDetails_dimension',
    'content_details_definition': 'contentDetails_definition',
    'content_details_caption': 'contentDetails_caption',
    'content_details_licensed_content': 'contentDetails_licensedContent',
    'content_details_region_restriction_allowed': 'contentDetails_regionRestriction_allowed',
    'content_details_region_restriction_blocked': 'contentDetails_regionRestriction_blocked',
    'content_details_content_rating': 'contentDetails_contentRating',
    'content_details_projection': 'contentDetails_projection',
    'content_details_has_custom_thumbnail': 'contentDetails_hasCustomThumbnail',
    
    # Status
    'status_upload_status': 'status_uploadStatus',
    'status_failure_reason': 'status_failureReason',
    'status_rejection_reason': 'status_rejectionReason',
    'status_privacy_status': 'status_privacyStatus',
    'status_publish_at': 'status_publishAt',
    'status_license': 'status_license',
    'status_embeddable': 'status_embeddable',
    'status_public_stats_viewable': 'status_publicStatsViewable',
    'status_made_for_kids': 'status_madeForKids',
    
    # Statistics
    'statistics_view_count': 'statistics_viewCount',
    'statistics_like_count': 'statistics_likeCount',
    'statistics_comment_count': 'statistics_commentCount',
    
    # Player
    'player_embed_html': 'player_embedHtml',
    'player_embed_height': 'player_embedHeight',
    'player_embed_width': 'player_embedWidth',
    
    # Topic details
    'topic_details_topic_ids': 'topicDetails_topicIds',
    'topic_details_relevant_topic_ids': 'topicDetails_relevantTopicIds',
    'topic_details_topic_categories': 'topicDetails_topicCategories',
    
    # Live streaming details
    'live_streaming_details_actual_start_time': 'liveStreamingDetails_actualStartTime',
    'live_streaming_details_actual_end_time': 'liveStreamingDetails_actualEndTime',
    'live_streaming_details_scheduled_start_time': 'liveStreamingDetails_scheduledStartTime',
    'live_streaming_details_scheduled_end_time': 'liveStreamingDetails_scheduledEndTime',
    'live_streaming_details_concurrent_viewers': 'liveStreamingDetails_concurrentViewers',
    'live_streaming_details_active_live_chat_id': 'liveStreamingDetails_activeLiveChatId',
    
    # Localizations
    'localizations': 'localizations',
    
    # Additional fields that might be missing
    'fetched_at': 'fetched_at',
    'updated_at': 'updated_at',
}

class VideoRepository(BaseRepository):
    """Repository for managing YouTube video data in the SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the repository with the database path."""
        self.db_path = db_path
        self._comment_repository = None
        self._location_repository = None
    
    @property
    def comment_repository(self):
        """Lazy initialization of CommentRepository to avoid circular imports"""
        if self._comment_repository is None:
            from src.database.comment_repository import CommentRepository
            self._comment_repository = CommentRepository(self.db_path)
        return self._comment_repository
    
    @property
    def location_repository(self):
        """Lazy initialization of LocationRepository to avoid circular imports"""
        if self._location_repository is None:
            from src.database.location_repository import LocationRepository
            self._location_repository = LocationRepository(self.db_path)
        return self._location_repository
        
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a video by its database ID.
        
        Args:
            id: The database ID of the video
            
        Returns:
            Optional[Dict[str, Any]]: The video data as a dictionary, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Use Row to access by column name
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM videos WHERE id = ?", (id,))
                row = cursor.fetchone()
                
            if row:
                return dict(row)
            return None
        except Exception as e:
            debug_log(f"Error retrieving video by ID {id}: {str(e)}", e)
            return None
    
    def flatten_dict(self, d, parent_key='', sep='.'):  # Add if not present
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def store_video_data(self, data, channel_db_id=None, fetched_at=None, retry_count=0):
        """
        Save video data to SQLite database with comprehensive field mapping.

        Args:
            data (dict): The full YouTube API response for a video
            channel_db_id (int, optional): The database ID of the channel this video belongs to
            fetched_at (str, optional): Timestamp when the data was fetched
            retry_count (int, optional): Internal use for retrying on DB lock

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Ensure youtube_id is present
                if 'youtube_id' not in data:
                    if 'video_id' in data:
                        data['youtube_id'] = data['video_id']
                    elif 'id' in data:
                        data['youtube_id'] = data['id']
                    else:
                        debug_log(f"[DB ERROR] Skipping video with no youtube_id: {data}")
                        return False

                # Flatten the raw API response
                raw_api = data.get('raw_api_response') or data.get('video_info', data)
                flat_api = self.flatten_dict(raw_api, sep='_')
                
                # Get all columns in the videos table
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(videos)")
                table_info = cursor.fetchall()
                existing_cols = set(row[1] for row in table_info)
                column_types = {row[1]: row[2] for row in table_info}
                
                db_row = {}
                
                # Map each database column to the correct API field
                for col in existing_cols:
                    if col == 'id':
                        continue
                        
                    # Special handling for thumbnail fields - extract directly from original structure
                    if col.startswith('snippet_thumbnails_'):
                        thumbnail_size = col.replace('snippet_thumbnails_', '')
                        
                        # Extract thumbnail data directly from original structure
                        value = None
                        if 'snippet' in raw_api and 'thumbnails' in raw_api['snippet']:
                            thumbnails = raw_api['snippet']['thumbnails']
                            if thumbnail_size in thumbnails and isinstance(thumbnails[thumbnail_size], dict):
                                value = json.dumps(thumbnails[thumbnail_size])
                                debug_log(f"[DB THUMBNAIL] {col} extracted from original: {value}")
                        
                        if not value:
                            value = handle_missing_api_field(col, column_types.get(col, 'TEXT'))
                            debug_log(f"[DB THUMBNAIL] {col} not found, using default: {value}")
                    else:
                        # Regular field mapping
                        api_field = CANONICAL_FIELD_MAP.get(col)
                        value = None
                        
                        if api_field and api_field in flat_api:
                            # Found the field in API response
                            value = flat_api[api_field]
                            debug_log(f"[DB MAPPING] {col} -> {api_field} = {str(value)[:100]}")
                        else:
                            # If no value found with canonical mapping, try direct column name
                            if api_field and api_field != col and col in flat_api:
                                value = flat_api[col]
                                debug_log(f"[DB MAPPING] {col} -> {col} (direct) = {str(value)[:100]}")
                            else:
                                # Field not found in API response
                                value = handle_missing_api_field(col, column_types.get(col, 'TEXT'))
                                if value == "NOT_PROVIDED_BY_API":
                                    debug_log(f"[DB MISSING] {col} not provided by API")
                                else:
                                    debug_log(f"[DB DEFAULT] {col} using default: {value}")
                        
                        # Handle JSON serialization for complex fields
                        if col in [
                            'snippet_tags', 'content_details_region_restriction_allowed', 'content_details_region_restriction_blocked',
                            'content_details_content_rating', 'topic_details_topic_ids', 'topic_details_relevant_topic_ids',
                            'topic_details_topic_categories', 'localizations'
                        ]:
                            if value is not None and not isinstance(value, str):
                                value = json.dumps(value)
                    
                    db_row[col] = value
                
                # Handle duplicate fields - ensure consistency
                # For fields that exist in both forms in the videos table:
                # - channel_id vs snippet_channel_id (both exist)
                # Note: title/description don't have snippet_ versions in videos table
                duplicate_mappings = {
                    ('channel_id', 'snippet_channel_id'): 'snippet_channelId',
                    ('published_at',): 'snippet_publishedAt'
                }
                
                # Sync duplicate fields to ensure consistency
                for field_group, api_source in duplicate_mappings.items():
                    if api_source in flat_api:
                        api_value = flat_api[api_source]
                        for field in field_group:
                            if field in existing_cols:
                                db_row[field] = api_value
                                debug_log(f"[DB SYNC] Set {field} = {str(api_value)[:50]}")
                
                # Also ensure title and description get their values from snippet API fields
                if 'title' in existing_cols and 'snippet_title' in flat_api:
                    db_row['title'] = flat_api['snippet_title']
                if 'description' in existing_cols and 'snippet_description' in flat_api:
                    db_row['description'] = flat_api['snippet_description']
                
                # Add metadata fields
                if channel_db_id:
                    db_row['channel_id'] = channel_db_id
                
                now = datetime.utcnow().isoformat()
                if 'fetched_at' in existing_cols:
                    db_row['fetched_at'] = fetched_at or now
                if 'updated_at' in existing_cols:
                    db_row['updated_at'] = now
                
                # Prepare for database insertion
                columns = [col for col in existing_cols if col != 'id']
                values = [db_row.get(col) for col in columns]
                
                debug_log(f"[DB INSERT] Video {data.get('youtube_id')} with {len(columns)} fields")
                debug_log(f"[DB DEBUG] Columns: {list(columns)}")
                debug_log(f"[DB DEBUG] youtube_id in columns: {'youtube_id' in columns}")
                debug_log(f"[DB DEBUG] youtube_id value: {db_row.get('youtube_id')}")
                debug_log(f"[DB DEBUG] Values: {values}")
                
                # Insert or update - using ON CONFLICT without column specification
                placeholders = ','.join(['?'] * len(columns))
                update_clause = ','.join([f'{col}=excluded.{col}' for col in columns])
                
                sql_query = f'''
                    INSERT INTO videos ({','.join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT DO UPDATE SET {update_clause}
                '''
                debug_log(f"[DB DEBUG] SQL Query: {sql_query}")
                
                cursor.execute(sql_query, values)
                
                # Store in history table
                video_id = data.get('youtube_id') or data.get('id')
                raw_video_info = json.dumps(raw_api)
                cursor.execute('''
                    INSERT INTO videos_history (video_id, fetched_at, raw_video_info) 
                    VALUES (?, ?, ?)
                    ON CONFLICT DO UPDATE SET raw_video_info=excluded.raw_video_info
                ''', (video_id, fetched_at or now, raw_video_info))
                
                conn.commit()
                debug_log(f"[DB SUCCESS] Stored video: {video_id}")
                
                # Save comments if present
                comments = data.get('comments', [])
                if comments:
                    debug_log(f"[DB] Saving {len(comments)} comments for video {video_id}")
                    comment_store_result = self.store_comments(comments, video_id, fetched_at or now)
                    debug_log(f"[DB] store_comments result: {comment_store_result}")
                
                return True
                
        except Exception as e:
            debug_log(f"[DB ERROR] Failed to store video: {str(e)}", e)
            return False
        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            # Handle database locked error with retries and exponential backoff
            if "database is locked" in error_msg and retry_count < 5:
                import time
                retry_count += 1
                wait_time = 0.5 * (2 ** retry_count)  # Exponential backoff
                debug_log(f"[DB ERROR] Database locked (attempt {retry_count}/5). Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                # Retry with increased wait time
                return self.store_video_data(data, channel_db_id, fetched_at, retry_count)
            elif "database is locked" in error_msg:
                # Max retries reached
                import traceback
                debug_log(f"[DB ERROR] Database locked - max retries reached: {str(e)}\n{traceback.format_exc()}")
                return {"error": f"Database locked after 5 retry attempts: {str(e)}"}
            else:
                # Other SQLite operational error
                import traceback
                debug_log(f"[DB ERROR] SQLite error in store_video_data: {str(e)}\n{traceback.format_exc()}")
                return {"error": str(e)}
        except Exception as e:
            import traceback
            debug_log(f"Exception in store_video_data: {str(e)}\n{traceback.format_exc()}")
            return {"error": str(e)}
            
    def store_comments(self, comments: List[Dict[str, Any]], video_db_id: int, fetched_at: str) -> bool:
        """
        Save comment data to SQLite database - delegated to CommentRepository
        
        Args:
            comments: List of comments for a video
            video_db_id: The database ID of the video these comments belong to
            fetched_at: Timestamp when the data was fetched
            
        Returns:
            bool: True if successful, False otherwise
        """
        debug_log(f"[DB] Storing {len(comments)} comments for video_db_id={video_db_id}")
        inserted = 0
        with sqlite3.connect(self.db_path) as conn:
            for comment in comments:
                debug_log(f"[DB] Inserting comment: {comment}")
                try:
                    # Ensure comment_id exists - crucial for database storage
                    if 'comment_id' not in comment:
                        debug_log(f"VideoRepository: Adding missing comment_id for comment")
                        comment['comment_id'] = f"generated_id_{video_db_id}_{inserted}_{hash(str(comment))}"
                    
                    # Ensure text field exists
                    if 'text' not in comment and 'comment_text' in comment:
                        comment['text'] = comment['comment_text']
                    elif 'text' not in comment and 'comment_text' not in comment:
                        comment['text'] = f"[No text content for comment {inserted}]"
                        
                    # Ensure author field exists
                    if 'author_display_name' not in comment and 'comment_author' in comment:
                        comment['author_display_name'] = comment['comment_author']
                        
                    # Ensure published_at field exists
                    if 'published_at' not in comment and 'comment_published_at' in comment:
                        comment['published_at'] = comment['comment_published_at']
                        
                    result = self.comment_repository.store_comment(comment, video_db_id, fetched_at)
                    inserted += 1
                except Exception as e:
                    debug_log(f"[DB ERROR] Failed to insert comment: {e}, comment={comment}")
        debug_log(f"[DB] Inserted {inserted} comments for video_db_id={video_db_id}")
        return inserted == len(comments)
            
    def store_video_locations(self, locations: List[Dict[str, Any]], video_db_id: int) -> bool:
        """
        Save video location data to SQLite database - delegated to LocationRepository
        
        Args:
            locations: List of locations for a video
            video_db_id: The database ID of the video these locations belong to
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.location_repository.store_video_locations(locations, video_db_id)
            
    def get_videos_by_channel(self, channel_identifier: Union[int, str]) -> List[Dict[str, Any]]:
        """
        Get all videos for a specific channel.
        
        Args:
            channel_identifier: Either the database ID (int) or YouTube channel ID (str) of the channel
            
        Returns:
            list: A list of video data dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Determine if we have a database ID or YouTube channel ID
                if isinstance(channel_identifier, int):
                    # If it's an integer, treat it as database ID and get the YouTube channel ID
                    cursor.execute("SELECT channel_id FROM channels WHERE id = ?", (channel_identifier,))
                    channel_row = cursor.fetchone()
                    if not channel_row:
                        debug_log(f"No channel found with database ID {channel_identifier}")
                        return []
                    youtube_channel_id = channel_row[0]
                    debug_log(f"Resolved database ID {channel_identifier} to YouTube channel ID {youtube_channel_id}")
                else:
                    # If it's a string, treat it as YouTube channel ID
                    youtube_channel_id = channel_identifier
                    debug_log(f"Using YouTube channel ID directly: {youtube_channel_id}")
                
                # First check if videos exist for this channel using YouTube channel ID
                cursor.execute("SELECT COUNT(*) FROM videos WHERE channel_id = ?", (youtube_channel_id,))
                count = cursor.fetchone()[0]
                debug_log(f"Found {count} videos with YouTube channel_id = {youtube_channel_id}")
                
                # Get videos for this channel using YouTube channel ID
                cursor.execute("""
                    SELECT id, youtube_id, title, description, published_at, statistics_view_count, 
                           statistics_like_count, statistics_comment_count, content_details_duration, snippet_thumbnails_high, content_details_caption
                    FROM videos 
                    WHERE channel_id = ?
                """, (youtube_channel_id,))
                
                videos_rows = cursor.fetchall()
                debug_log(f"Fetched {len(videos_rows)} video rows from database")
                
                # Check if ANY videos exist in the database
                cursor.execute("SELECT COUNT(*) FROM videos")
                total_count = cursor.fetchone()[0]
                debug_log(f"Total videos in database: {total_count}")
                
                # If no videos for this channel but we have videos in the db, list some examples
                if count == 0 and total_count > 0:
                    cursor.execute("SELECT id, youtube_id, channel_id FROM videos LIMIT 3")
                    examples = cursor.fetchall()
                    debug_log("Example videos in database:")
                    for ex in examples:
                        debug_log(f"  ID: {ex[0]}, YouTube ID: {ex[1]}, Channel ID: {ex[2]}")
                
                videos = []
                for video_row in videos_rows:
                    video_db_id = video_row[0]
                    video_id = video_row[1]
                    
                    video_data = {
                        'id': video_id,
                        'db_id': video_db_id,
                        'snippet': {
                            'title': video_row[2],
                            'description': video_row[3],
                            'publishedAt': video_row[4]
                        },
                        'statistics': {
                            'viewCount': video_row[5],
                            'likeCount': video_row[6],
                            'commentCount': video_row[7] or 0  # Use the actual comment count from DB
                        },
                        'contentDetails': {
                            'duration': video_row[8]  # Adjusted index due to added comment count
                        },
                        'locations': []  # Add locations array
                    }
                    
                    # Get locations for this video using LocationRepository
                    locations = self.location_repository.get_video_locations(video_db_id)
                    video_data['locations'] = locations
                    
                    # Note: commentCount is already set from statistics_comment_count in the database
                    # This represents the total comments available, not comments already downloaded
                    
                    videos.append(video_data)
            
            return videos
        except Exception as e:
            debug_log(f"Error getting videos by channel: {str(e)}", e)
            return []
    
    def get_video_comments(self, video_db_id: int) -> List[Dict[str, Any]]:
        """
        Get comments for a specific video - delegated to CommentRepository
        
        Args:
            video_db_id: The database ID of the video
            
        Returns:
            list: A list of comment data dictionaries
        """
        return self.comment_repository.get_video_comments(video_db_id)
    
    def display_videos_data(self) -> bool:
        """
        Display all videos from SQLite database in a Streamlit interface.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Query for videos data with channel names
                query = '''
                SELECT v.*, c.channel_name
                FROM videos v
                LEFT JOIN channels c ON v.channel_id = c.id
                '''
                # Execute query and convert to DataFrame
                df = pd.read_sql_query(query, conn)
                # Add a date column for easier filtering
                if 'published_at' in df.columns:
                    df['published_date'] = pd.to_datetime(df['published_at']).dt.date
                self._videos_df = df
            return True
        except Exception as e:
            debug_log(f"Error displaying videos data: {str(e)}")
            return False

    def get_playlist_data(self, playlist_id: str) -> dict:
        """
        Fetch a playlist record from the playlists table by playlist_id.
        Args:
            playlist_id (str): The playlist ID to fetch
        Returns:
            dict: Playlist record as a dict, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM playlists WHERE playlist_id = ?', (playlist_id,))
                row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            debug_log(f"Error fetching playlist data for {playlist_id}: {str(e)}")
            return None

    def get_video_db_id(self, youtube_id: str):
        """Return the DB primary key for a given YouTube video ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM videos WHERE youtube_id = ?",
                (youtube_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

# Comprehensive mapping from database column names to flattened YouTube API field names
VIDEO_CANONICAL_FIELD_MAP = {
    # Basic info
    'youtube_id': 'youtube_id',
    'title': 'snippet_title',
    'description': 'snippet_description',
    'published_at': 'snippet_publishedAt',
    'snippet_channel_id': 'snippet_channelId',
    'snippet_channel_title': 'snippet_channelTitle',
    'snippet_default_language': 'snippet_defaultLanguage',
    'snippet_default_audio_language': 'snippet_defaultAudioLanguage',
    'snippet_localized_title': 'snippet_localized_title',
    'snippet_localized_description': 'snippet_localized_description',
    
    # Thumbnails with dimensions
    'snippet_thumbnails_default_url': 'snippet_thumbnails_default_url',
    'snippet_thumbnails_default_width': 'snippet_thumbnails_default_width',
    'snippet_thumbnails_default_height': 'snippet_thumbnails_default_height',
    'snippet_thumbnails_medium_url': 'snippet_thumbnails_medium_url',
    'snippet_thumbnails_medium_width': 'snippet_thumbnails_medium_width',
    'snippet_thumbnails_medium_height': 'snippet_thumbnails_medium_height',
    'snippet_thumbnails_high_url': 'snippet_thumbnails_high_url',
    'snippet_thumbnails_high_width': 'snippet_thumbnails_high_width',
    'snippet_thumbnails_high_height': 'snippet_thumbnails_high_height',
    'snippet_thumbnails_standard_url': 'snippet_thumbnails_standard_url',
    'snippet_thumbnails_standard_width': 'snippet_thumbnails_standard_width',
    'snippet_thumbnails_standard_height': 'snippet_thumbnails_standard_height',
    'snippet_thumbnails_maxres_url': 'snippet_thumbnails_maxres_url',
    'snippet_thumbnails_maxres_width': 'snippet_thumbnails_maxres_width',
    'snippet_thumbnails_maxres_height': 'snippet_thumbnails_maxres_height',
    
    # Statistics
    'statistics_view_count': 'statistics_viewCount',
    'statistics_like_count': 'statistics_likeCount',
    'statistics_dislike_count': 'statistics_dislikeCount',
    'statistics_favorite_count': 'statistics_favoriteCount',
    'statistics_comment_count': 'statistics_commentCount',
    
    # Content details
    'content_details_duration': 'contentDetails_duration',
    'content_details_dimension': 'contentDetails_dimension',
    'content_details_definition': 'contentDetails_definition',
    'content_details_caption': 'contentDetails_caption',
    'content_details_licensed_content': 'contentDetails_licensedContent',
    'content_details_region_restriction_allowed': 'contentDetails_regionRestriction_allowed',
    'content_details_region_restriction_blocked': 'contentDetails_regionRestriction_blocked',
    'content_details_content_rating': 'contentDetails_contentRating',
    'content_details_projection': 'contentDetails_projection',
    'content_details_has_custom_thumbnail': 'contentDetails_hasCustomThumbnail',
    
    # Status
    'status_upload_status': 'status_uploadStatus',
    'status_failure_reason': 'status_failureReason',
    'status_rejection_reason': 'status_rejectionReason',
    'status_privacy_status': 'status_privacyStatus',
    'status_publish_at': 'status_publishAt',
    'status_license': 'status_license',
    'status_embeddable': 'status_embeddable',
    'status_public_stats_viewable': 'status_publicStatsViewable',
    'status_made_for_kids': 'status_madeForKids',
    'status_self_declared_made_for_kids': 'status_selfDeclaredMadeForKids',
    
    # Player
    'player_embed_html': 'player_embedHtml',
    'player_embed_height': 'player_embedHeight',
    'player_embed_width': 'player_embedWidth',
    
    # Topic details
    'topic_details_topic_ids': 'topicDetails_topicIds',
    'topic_details_relevant_topic_ids': 'topicDetails_relevantTopicIds',
    'topic_details_topic_categories': 'topicDetails_topicCategories',
    
    # Live streaming
    'live_streaming_details_actual_start_time': 'liveStreamingDetails_actualStartTime',
    'live_streaming_details_actual_end_time': 'liveStreamingDetails_actualEndTime',
    'live_streaming_details_scheduled_start_time': 'liveStreamingDetails_scheduledStartTime',
    'live_streaming_details_scheduled_end_time': 'liveStreamingDetails_scheduledEndTime',
    'live_streaming_details_concurrent_viewers': 'liveStreamingDetails_concurrentViewers',
    'live_streaming_details_active_live_chat_id': 'liveStreamingDetails_activeLiveChatId',
    
    # Legacy mappings for backward compatibility
    'view_count': 'statistics_viewCount',
    'like_count': 'statistics_likeCount',
    'dislike_count': 'statistics_dislikeCount',
    'favorite_count': 'statistics_favoriteCount',
    'comment_count': 'statistics_commentCount',
    'duration': 'contentDetails_duration',
    'dimension': 'contentDetails_dimension',
    'definition': 'contentDetails_definition',
    'caption': 'contentDetails_caption',
    'licensed_content': 'contentDetails_licensedContent',
    'projection': 'contentDetails_projection',
    'privacy_status': 'status_privacyStatus',
    'license': 'status_license',
    'embeddable': 'status_embeddable',
    'public_stats_viewable': 'status_publicStatsViewable',
    'made_for_kids': 'status_madeForKids',
    'tags': 'snippet_tags',
    'category_id': 'snippet_categoryId',
    'live_broadcast_content': 'snippet_liveBroadcastContent',
    
    # Localizations
    'localizations': 'localizations'
}
