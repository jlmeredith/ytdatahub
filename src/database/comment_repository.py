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
        """Save comments to SQLite database, mapping every API field (recursively) to a column, and insert full JSON into comments_history only."""
        abs_db_path = os.path.abspath(self.db_path)
        debug_log(f"[DB] Using database at: {abs_db_path}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        expected_fields = {
            'comment_id': '',
            'comment_text': '',
            'comment_author': '',
            'comment_published_at': '',
            'like_count': '0',
            'parent_id': '',
            'is_reply': False,
            'author_profile_image_url': '',
            'author_channel_id': '',
            'video_id': video_db_id if video_db_id else '',
            'fetched_at': fetched_at or datetime.utcnow().isoformat(),
        }
        for comment in comments:
            api = comment.get('comment_info', comment)
            # Standardize comment fields
            for field, default in expected_fields.items():
                if field not in api or api[field] is None:
                    api[field] = default
                    debug_log(f"store_comments: Field '{field}' missing in comment {api.get('comment_id', '')}, defaulting to {repr(default)}")
            flat_api = self.flatten_dict(api)
            cursor.execute("PRAGMA table_info(comments)")
            existing_cols = set(row[1] for row in cursor.fetchall())
            columns = []
            values = []
            flat_api_underscore = {k.replace('.', '_'): v for k, v in flat_api.items()}
            for col in existing_cols:
                if col == 'id' or col == 'created_at' or col == 'updated_at':
                    continue
                if col in flat_api_underscore:
                    columns.append(col)
                    values.append(flat_api_underscore[col])
            if video_db_id and 'video_id' in existing_cols:
                columns.append('video_id')
                values.append(video_db_id)
            debug_log(f"[DB INSERT] Final comment insert columns: {columns}")
            debug_log(f"[DB INSERT] Final comment insert values: {values}")
            if not columns:
                debug_log("[DB WARNING] No columns to insert for comment.")
                continue
            placeholders = ','.join(['?'] * len(columns))
            update_clause = ','.join([f'{col}=excluded.{col}' for col in columns])
            cursor.execute(f'''
                INSERT INTO comments ({','.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(comment_id) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP
            ''', values)
            debug_log(f"Inserted/updated comment: {flat_api.get('comment_id') or flat_api.get('id')}")
            # --- Insert full JSON into comments_history only ---
            fetched_at_val = fetched_at or datetime.utcnow().isoformat()
            raw_comment_info = json.dumps(api)
            cursor.execute('''
                INSERT INTO comments_history (comment_id, fetched_at, raw_comment_info) VALUES (?, ?, ?)
            ''', (flat_api.get('comment_id') or flat_api.get('id'), fetched_at_val, raw_comment_info))
        conn.commit()
        conn.close()
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
