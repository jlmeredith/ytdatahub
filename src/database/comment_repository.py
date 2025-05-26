"""
Comment repository module for interacting with YouTube comment data in the SQLite database.
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union
import json
from datetime import datetime
import os

from src.utils.helpers import debug_log
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
    
    def store_comments(self, comments, video_db_id=None, fetched_at=None):
        """Save comments to SQLite database, mapping every API field (recursively) to a column, and insert full JSON into comments_history only."""
        abs_db_path = os.path.abspath(self.db_path)
        debug_log(f"[DB] Using database at: {abs_db_path}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for comment in comments:
            api = comment.get('comment_info', comment)
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
            fetched_at = fetched_at or datetime.datetime.utcnow().isoformat()
            raw_comment_info = json.dumps(api)
            cursor.execute('''
                INSERT INTO comments_history (comment_id, fetched_at, raw_comment_info) VALUES (?, ?, ?)
            ''', (flat_api.get('comment_id') or flat_api.get('id'), fetched_at, raw_comment_info))
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
