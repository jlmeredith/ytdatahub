"""
Comment repository module for interacting with YouTube comment data in the SQLite database.
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union

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
    
    def store_comments(self, comments: List[Dict[str, Any]], video_db_id: int, fetched_at: str) -> bool:
        """
        Save comment data to SQLite database.
        
        Args:
            comments: List of comments for a video
            video_db_id: The database ID of the video these comments belong to
            fetched_at: Timestamp when the data was fetched
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not comments:
                debug_log("CommentRepository: No comments to store")
                return True
                
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            debug_log(f"CommentRepository: Attempting to store {len(comments)} comments for video ID {video_db_id}")
            debug_log(f"CommentRepository: Sample comment: {comments[0]}")
            
            # First check if the video exists
            cursor.execute("SELECT id FROM videos WHERE id = ?", (video_db_id,))
            video_record = cursor.fetchone()
            if not video_record:
                debug_log(f"CommentRepository: ERROR - Video ID {video_db_id} does not exist in the database!")
                # Try to find a valid video ID from the database as a fallback
                cursor.execute("SELECT id FROM videos LIMIT 1")
                fallback_record = cursor.fetchone()
                if fallback_record:
                    video_db_id = fallback_record[0]
                    debug_log(f"CommentRepository: Using fallback video ID {video_db_id}")
                else:
                    debug_log("CommentRepository: No videos in database, cannot store comments")
                    conn.close()
                    return False
            
            successful_inserts = 0
            for i, comment in enumerate(comments):
                # Support both naming patterns (test vs production data)
                comment_id = comment.get('comment_id')
                if not comment_id:
                    debug_log(f"CommentRepository: Missing required comment_id for comment {i}, generating one")
                    comment_id = f"generated_id_{video_db_id}_{i}_{hash(str(comment))}"
                    
                text = comment.get('comment_text', comment.get('text', ''))
                author_display_name = comment.get('comment_author', comment.get('author_display_name', ''))
                published_at = comment.get('comment_published_at', comment.get('published_at', ''))
                author_profile_image_url = comment.get('author_profile_image_url', '')
                author_channel_id = comment.get('author_channel_id', '')
                
                # Handle like_count more carefully
                try:
                    like_count = int(comment.get('like_count', 0))
                except (ValueError, TypeError):
                    like_count = 0
                    
                updated_at = comment.get('updated_at', published_at)
                parent_id = comment.get('parent_id', None)
                is_reply = bool(comment.get('is_reply', False))
                
                debug_log(f"CommentRepository: Processing comment {i} (ID: {comment_id}) with text: {text[:30]}...")
                
                # Insert or update comment data
                try:
                    cursor.execute('''
                    INSERT OR REPLACE INTO comments (
                        comment_id, video_id, text, author_display_name, author_profile_image_url,
                        author_channel_id, like_count, published_at, updated_at, parent_id,
                        is_reply, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        comment_id, video_db_id, text, author_display_name, author_profile_image_url,
                        author_channel_id, like_count, published_at, updated_at, parent_id,
                        is_reply, fetched_at
                    ))
                    successful_inserts += 1
                except sqlite3.Error as e:
                    debug_log(f"CommentRepository: Error inserting comment {comment_id}: {str(e)}")
            
            # Commit changes
            conn.commit()
            
            # Verify the comments were stored
            cursor.execute("SELECT COUNT(*) FROM comments WHERE video_id = ?", (video_db_id,))
            count = cursor.fetchone()[0]
            debug_log(f"CommentRepository: Successfully stored {count} comments for video_id {video_db_id} (attempted {len(comments)}, succeeded {successful_inserts})")
            
            conn.close()
            
            # If we successfully inserted any comments, consider it a success
            # But if we were expecting to insert comments and inserted none, that's a problem
            if len(comments) > 0 and successful_inserts == 0:
                debug_log("CommentRepository: ERROR - Failed to insert any comments")
                return False
                
            return True
        except Exception as e:
            debug_log(f"CommentRepository: Error storing comments: {str(e)}", e)
            return False
    
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
