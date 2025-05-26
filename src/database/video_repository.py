"""
Video repository module for interacting with YouTube video data in the SQLite database.
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json
import os

from src.utils.helpers import debug_log
from src.database.base_repository import BaseRepository

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
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use Row to access by column name
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM videos WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            conn.close()
            
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
    
    def store_video_data(self, data, channel_db_id=None, fetched_at=None):
        """Save video data to SQLite database, mapping every API field (recursively) to a column, and insert full JSON into videos_history only."""
        try:
            abs_db_path = os.path.abspath(self.db_path)
            debug_log(f"[DB] Using database at: {abs_db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            api = data.get('video_info', data)
            flat_api = self.flatten_dict(api)
            cursor.execute("PRAGMA table_info(videos)")
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
            if channel_db_id and 'channel_id' in existing_cols:
                columns.append('channel_id')
                values.append(channel_db_id)
            debug_log(f"[DB INSERT] Final video insert columns: {columns}")
            debug_log(f"[DB INSERT] Final video insert values: {values}")
            if not columns:
                debug_log("[DB WARNING] No columns to insert for video.")
                conn.close()
                return False
            placeholders = ','.join(['?'] * len(columns))
            update_clause = ','.join([f'{col}=excluded.{col}' for col in columns])
            cursor.execute(f'''
                INSERT INTO videos ({','.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT(youtube_id) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP
            ''', values)
            debug_log(f"Inserted/updated video: {flat_api.get('youtube_id') or flat_api.get('id')}")
            # --- Insert full JSON into videos_history only ---
            fetched_at = fetched_at or datetime.datetime.utcnow().isoformat()
            raw_video_info = json.dumps(api)
            cursor.execute('''
                INSERT INTO videos_history (video_id, fetched_at, raw_video_info) VALUES (?, ?, ?)
            ''', (flat_api.get('youtube_id') or flat_api.get('id'), fetched_at, raw_video_info))
            conn.commit()
            conn.close()
            return True
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
        debug_log(f"VideoRepository: Delegating {len(comments)} comments to CommentRepository for video_db_id={video_db_id}")
        
        # First check if the video exists in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM videos WHERE id = ?", (video_db_id,))
        video_exists = cursor.fetchone() is not None
        conn.close()
        
        if not video_exists:
            debug_log(f"VideoRepository: ERROR - Video ID {video_db_id} does not exist in database!")
            return False
        
        # Ensure we have a list of comments
        if not isinstance(comments, list):
            debug_log(f"VideoRepository: ERROR - Comments is not a list: {type(comments)}")
            return False
        
        # Validate and transform comments to ensure they have all required fields
        processed_comments = []
        
        for i, comment in enumerate(comments):
            processed_comment = comment.copy()  # Create a copy to avoid modifying original
            
            # Ensure comment_id exists - crucial for database storage
            if 'comment_id' not in processed_comment:
                debug_log(f"VideoRepository: Adding missing comment_id for comment {i}")
                processed_comment['comment_id'] = f"generated_id_{video_db_id}_{i}_{hash(str(comment))}"
            
            # Ensure text field exists
            if 'text' not in processed_comment and 'comment_text' in processed_comment:
                processed_comment['text'] = processed_comment['comment_text']
            elif 'text' not in processed_comment and 'comment_text' not in processed_comment:
                processed_comment['text'] = f"[No text content for comment {i}]"
                
            # Ensure author field exists
            if 'author_display_name' not in processed_comment and 'comment_author' in processed_comment:
                processed_comment['author_display_name'] = processed_comment['comment_author']
                
            # Ensure published_at field exists
            if 'published_at' not in processed_comment and 'comment_published_at' in processed_comment:
                processed_comment['published_at'] = processed_comment['comment_published_at']
                
            processed_comments.append(processed_comment)
        
        if processed_comments and len(processed_comments) > 0:
            debug_log(f"VideoRepository: Comment sample after validation: {processed_comments[0]}")
            
        result = self.comment_repository.store_comments(processed_comments, video_db_id, fetched_at)
        debug_log(f"VideoRepository: Comment storage result: {result}")
        
        # Verify comments were stored
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM comments WHERE video_id = ?", (video_db_id,))
        count = cursor.fetchone()[0]
        debug_log(f"VideoRepository: Verification shows {count} comments stored for video_db_id={video_db_id}")
        conn.close()
        
        return result
            
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
            
    def get_videos_by_channel(self, channel_db_id: int) -> List[Dict[str, Any]]:
        """
        Get all videos for a specific channel.
        
        Args:
            channel_db_id: The database ID of the channel
            
        Returns:
            list: A list of video data dictionaries
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First check if videos exist for this channel
            cursor.execute("SELECT COUNT(*) FROM videos WHERE channel_id = ?", (channel_db_id,))
            count = cursor.fetchone()[0]
            debug_log(f"Found {count} videos with channel_id = {channel_db_id}")
            
            # Get videos for this channel
            cursor.execute("""
                SELECT id, youtube_id, title, description, published_at, view_count, 
                       like_count, duration, thumbnail_high, caption
                FROM videos 
                WHERE channel_id = ?
            """, (channel_db_id,))
            
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
                        'commentCount': 0  # Default value
                    },
                    'contentDetails': {
                        'duration': video_row[7]
                    },
                    'locations': []  # Add locations array
                }
                
                # Get locations for this video using LocationRepository
                locations = self.location_repository.get_video_locations(video_db_id)
                video_data['locations'] = locations
                
                # Get comments count and update statistics
                comments = self.comment_repository.get_video_comments(video_db_id)
                video_data['statistics']['commentCount'] = len(comments)
                
                videos.append(video_data)
            
            conn.close()
            
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
        debug_log("Loading videos from SQLite")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            
            # Query for videos data with channel names
            query = '''
            SELECT 
                c.title as channel_name,
                c.youtube_id as channel_id,
                v.youtube_id as video_id,
                v.title,
                v.published_at,
                v.view_count as views,
                v.like_count as likes,
                v.duration,
                CASE 
                    WHEN v.view_count > 0 THEN CAST(v.like_count AS FLOAT) / v.view_count
                    ELSE 0
                END as engagement
            FROM 
                videos v
            JOIN 
                channels c ON v.channel_id = c.id
            '''
            
            # Execute query and convert to DataFrame
            df = pd.read_sql_query(query, conn)
            
            # Close the connection
            conn.close()
            
            # Add a date column for easier filtering
            if not df.empty:
                df['published_date'] = pd.to_datetime(df['published_at']).dt.date
                
                # Display the data
                st.write(f"Showing {len(df)} videos")
                st.dataframe(df)
            else:
                st.info("No videos found in SQLite database.")
            
            return True
        except Exception as e:
            print(f"Error loading videos from SQLite: {str(e)}")
            debug_log(f"Exception in display_videos_data: {str(e)}", e)
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
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM playlists WHERE playlist_id = ?', (playlist_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            debug_log(f"Error fetching playlist data for {playlist_id}: {str(e)}")
            return None
