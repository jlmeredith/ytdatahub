"""
Comment repository module for interacting with YouTube comment data in the SQLite database.
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union
import json
from datetime import datetime
import os

from src.utils.debug_utils import debug_log
from src.database.base_repository import BaseRepository

def handle_missing_api_field(field_name: str, column_type: str = 'TEXT') -> Any:
    """
    Handle missing API fields by returning appropriate default values for comments table.
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
        'author_channel_url', 'author_channel_id', 'can_rate', 
        'viewer_rating', 'moderation_status', 'parent_id',
        'can_reply', 'total_reply_count', 'is_public'
    }
    
    if field_name in api_provided_fields:
        return "NOT_PROVIDED_BY_API"
    elif column_type == 'INTEGER':
        return None
    elif column_type == 'BOOLEAN':
        return False
    else:
        return None

# Define a canonical mapping of database columns to API fields
CANONICAL_FIELD_MAP = {
    # Basic comment info - Comments use a consistent field naming approach
    # without the duplicate field problem found in videos and playlists
    'comment_id': 'id',
    'video_id': 'video_id',  # This comes from the parameter
    'text': 'snippet_textDisplay',
    'author_display_name': 'snippet_authorDisplayName',
    'author_profile_image_url': 'snippet_authorProfileImageUrl',
    'author_channel_url': 'snippet_authorChannelUrl',
    'author_channel_id': 'snippet_authorChannelId_value',
    'like_count': 'snippet_likeCount',
    'published_at': 'snippet_publishedAt',
    'updated_at': 'snippet_updatedAt',
    'parent_id': 'snippet_parentId',
    'is_reply': 'is_reply',
    'fetched_at': 'fetched_at',  # This comes from the parameter
    
    # Additional fields that might be missing from API
    'can_rate': 'snippet_canRate',
    'viewer_rating': 'snippet_viewerRating',
    'moderation_status': 'snippet_moderationStatus',
    'can_reply': 'snippet_canReply',
    'total_reply_count': 'snippet_totalReplyCount',
    'is_public': 'snippet_isPublic',
    'etag': 'etag'
}

class CommentRepository(BaseRepository):
    """Repository for managing YouTube comment data in the SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the repository with the database path."""
        self.db_path = db_path
        
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a comment by its database ID.
        
        Args:
            id: The database ID of the comment
            
        Returns:
            Optional[Dict[str, Any]]: The comment data as a dictionary, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use Row to access by column name
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM comments WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            debug_log(f"Error retrieving comment by ID {id}: {str(e)}", e)
            return None
    
    def flatten_dict(self, d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def store_comment(self, comment, video_db_id=None, fetched_at=None):
        """
        Save a single comment to SQLite database.
        
        Args:
            comment: Comment data dictionary
            video_db_id: The database ID of the video this comment belongs to
            fetched_at: Timestamp when the data was fetched
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.store_comments([comment], video_db_id, fetched_at)
        
    def store_comments(self, comments, video_db_id=None, fetched_at=None):
        """Save comments to SQLite database with proper field mapping and handling of missing API data."""
        abs_db_path = os.path.abspath(self.db_path)
        debug_log(f"[DB] Using database at: {abs_db_path}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get column information for the comments table
                cursor.execute("PRAGMA table_info(comments)")
                table_info = cursor.fetchall()
                existing_cols = set(row[1] for row in table_info)
                column_types = {row[1]: row[2] for row in table_info}
                
                for comment in comments:
                    # Get the raw API data
                    raw_api = comment.get('comment_info', comment)
                    
                    # Flatten the API response using dot notation
                    flat_api = self.flatten_dict(raw_api)
                    
                    # Convert dot notation to underscore for direct mapping
                    flat_api_underscore = {k.replace('.', '_'): v for k, v in flat_api.items()}
                    
                    db_row = {}
                    
                    # Map each database column to the correct flattened API field
                    for col in existing_cols:
                        if col == 'id':
                            continue
                        
                        # Get the corresponding flattened API field from canonical mapping
                        api_field = CANONICAL_FIELD_MAP.get(col)
                        value = None
                        
                        if api_field and api_field in flat_api_underscore:
                            # Found the field in API response
                            value = flat_api_underscore[api_field]
                            debug_log(f"[DB MAPPING] {col} -> {api_field} = {str(value)[:100]}")
                        elif col == 'video_id' and video_db_id:
                            # Special handling for video_id which comes from parameter
                            value = video_db_id
                        elif col == 'fetched_at':
                            # Special handling for fetched_at timestamp
                            value = fetched_at or datetime.utcnow().isoformat()
                        else:
                            # Field not found in API response
                            value = handle_missing_api_field(col, column_types.get(col, 'TEXT'))
                            if value == "NOT_PROVIDED_BY_API":
                                debug_log(f"[DB MISSING] {col} not provided by API")
                            else:
                                debug_log(f"[DB DEFAULT] {col} using default: {value}")
                        
                        db_row[col] = value
                    
                    # Prepare for database insertion
                    columns = [col for col in existing_cols if col != 'id']
                    values = [db_row.get(col) for col in columns]
                    
                    debug_log(f"[DB INSERT] Comment {comment.get('comment_id') or comment.get('id')} with {len(columns)} fields")
                    
                    # Insert or update
                    placeholders = ','.join(['?'] * len(columns))
                    update_clause = ','.join([f'{col}=excluded.{col}' for col in columns])
                    
                    cursor.execute(f'''
                        INSERT INTO comments ({','.join(columns)})
                        VALUES ({placeholders})
                        ON CONFLICT(comment_id) DO UPDATE SET {update_clause}
                    ''', values)
                    
                    # Store in history table
                    comment_id = comment.get('comment_id') or comment.get('id')
                    raw_comment_info = json.dumps(raw_api)
                    cursor.execute('''
                        INSERT INTO comments_history (comment_id, fetched_at, raw_comment_info) 
                        VALUES (?, ?, ?)
                        ON CONFLICT(comment_id, fetched_at) DO UPDATE SET raw_comment_info=excluded.raw_comment_info
                    ''', (comment_id, fetched_at or datetime.utcnow().isoformat(), raw_comment_info))
                    
                    debug_log(f"[DB SUCCESS] Stored comment: {comment_id}")
                
                conn.commit()
                return True
                
        except Exception as e:
            debug_log(f"[DB ERROR] Failed to store comments: {str(e)}", e)
            return False
        return True
    
    def get_video_comments(self, video_db_id: int) -> List[Dict[str, Any]]:
        """
        Get comments for a specific video.
        
        Args:
            video_db_id: The database ID of the video
            
        Returns:
            list: A list of comment data dictionaries
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get comments for this video
            cursor.execute("""
                SELECT comment_id, text, author_display_name, published_at, author_profile_image_url,
                       author_channel_id, like_count, updated_at, parent_id, is_reply
                FROM comments 
                WHERE video_id = ?
            """, (video_db_id,))
            
            comments_rows = cursor.fetchall()
            
            comments = []
            for comment_row in comments_rows:
                comment_data = {
                    'id': comment_row[0],
                    'snippet': {
                        'topLevelComment': {
                            'snippet': {
                                'textDisplay': comment_row[1],
                                'authorDisplayName': comment_row[2],
                                'publishedAt': comment_row[3],
                                'authorProfileImageUrl': comment_row[4],
                                'authorChannelId': comment_row[5],
                                'likeCount': comment_row[6],
                                'updatedAt': comment_row[7]
                            }
                        }
                    }
                }
                
                # If this is a reply, add parent ID
                if comment_row[9]:  # is_reply
                    comment_data['snippet']['parentId'] = comment_row[8]  # parent_id
                
                comments.append(comment_data)
            
            conn.close()
            
            return comments
        except Exception as e:
            debug_log(f"Error getting video comments: {str(e)}", e)
            return []

    def get_by_channel_id(self, channel_id: str) -> List[Dict[str, Any]]:
        """
        Get all comments for all videos belonging to a specific channel.
        
        Args:
            channel_id: The YouTube channel ID
            
        Returns:
            list: A list of all comment data dictionaries for the channel
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all comments for videos in this channel using JOIN
            cursor.execute("""
                SELECT c.comment_id, c.text, c.author_display_name, c.published_at, 
                       c.author_profile_image_url, c.author_channel_id, c.like_count, c.updated_at, 
                       c.parent_id, c.is_reply, v.youtube_id
                FROM comments c
                JOIN videos v ON c.video_id = v.id
                JOIN channels ch ON v.channel_id = ch.id
                WHERE ch.channel_id = ?
            """, (channel_id,))
            
            comments_rows = cursor.fetchall()
            
            comments = []
            for comment_row in comments_rows:
                comment_data = {
                    'comment_id': comment_row[0],
                    'comment_text': comment_row[1],
                    'comment_author': comment_row[2],
                    'comment_published_at': comment_row[3],
                    'author_profile_image_url': comment_row[4],
                    'author_channel_id': comment_row[5],
                    'like_count': comment_row[6],
                    'updated_at': comment_row[7],
                    'parent_id': comment_row[8],
                    'is_reply': comment_row[9],
                    'video_id': comment_row[10]
                }
                comments.append(comment_data)
            
            conn.close()
            
            return comments
        except Exception as e:
            debug_log(f"Error getting comments by channel ID {channel_id}: {str(e)}", e)
            return []

    def get_by_video_id(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get comments for a specific video using YouTube video ID.
        
        Args:
            video_id: The YouTube video ID
            
        Returns:
            list: A list of comment data dictionaries
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get comments for this video using YouTube video ID
            cursor.execute("""
                SELECT c.comment_id, c.text, c.author_display_name, c.published_at, 
                       c.author_profile_image_url, c.author_channel_id, c.like_count, c.updated_at, 
                       c.parent_id, c.is_reply
                FROM comments c
                JOIN videos v ON c.video_id = v.id
                WHERE v.youtube_id = ?
            """, (video_id,))
            
            comments_rows = cursor.fetchall()
            
            comments = []
            for comment_row in comments_rows:
                comment_data = {
                    'comment_id': comment_row[0],
                    'comment_text': comment_row[1],
                    'comment_author': comment_row[2],
                    'comment_published_at': comment_row[3],
                    'author_profile_image_url': comment_row[4],
                    'author_channel_id': comment_row[5],
                    'like_count': comment_row[6],
                    'updated_at': comment_row[7],
                    'parent_id': comment_row[8],
                    'is_reply': comment_row[9]
                }
                comments.append(comment_data)
            
            conn.close()
            
            return comments
        except Exception as e:
            debug_log(f"Error getting comments by video ID {video_id}: {str(e)}", e)
            return []

    def create_comment_ingestion_stats_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comment_ingestion_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                fetched_count INTEGER,
                stored_count INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(video_id) REFERENCES videos(id)
            )
        ''')
        conn.commit()
        conn.close()

    def log_comment_ingestion_stats(self, video_id, fetched_count, stored_count):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO comment_ingestion_stats (video_id, fetched_count, stored_count)
            VALUES (?, ?, ?)
        ''', (video_id, fetched_count, stored_count))
        conn.commit()
        conn.close()
