"""
Channel repository module for interacting with YouTube channel data in the SQLite database.
"""
import sqlite3
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional, Any, Union

from src.utils.helpers import debug_log
from src.database.base_repository import BaseRepository

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
        """Save channel data to SQLite database"""
        debug_log("Saving data to SQLite")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract channel data
            youtube_id = data.get('channel_id')
            title = data.get('channel_name')
            subscriber_count = int(data.get('subscribers', 0))
            view_count = int(data.get('views', 0))
            video_count = int(data.get('total_videos', 0))
            description = data.get('channel_description', '')
            uploads_playlist_id = data.get('playlist_id', '')
            
            # Extract new fields from channel data
            custom_url = data.get('custom_url', '')
            published_at = data.get('published_at', '')
            country = data.get('country', '')
            default_language = data.get('default_language', '')
            privacy_status = data.get('privacy_status', '')
            is_linked = data.get('is_linked', False)
            long_uploads_status = data.get('long_uploads_status', '')
            made_for_kids = data.get('made_for_kids', False)
            hidden_subscriber_count = data.get('hidden_subscriber_count', False)
            thumbnail_default = data.get('thumbnail_default', '')
            thumbnail_medium = data.get('thumbnail_medium', '')
            thumbnail_high = data.get('thumbnail_high', '')
            keywords = data.get('keywords', '')
            topic_categories = data.get('topic_categories', '')
            fetched_at = data.get('fetched_at', '')
            
            # Insert or update channel data with all fields from the new schema
            cursor.execute('''
            INSERT OR REPLACE INTO channels (
                youtube_id, title, subscriber_count, video_count, 
                view_count, description, custom_url, published_at,
                country, default_language, privacy_status, is_linked,
                long_uploads_status, made_for_kids, hidden_subscriber_count,
                thumbnail_default, thumbnail_medium, thumbnail_high,
                keywords, topic_categories, fetched_at,
                uploads_playlist_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                youtube_id, title, subscriber_count, video_count, 
                view_count, description, custom_url, published_at,
                country, default_language, privacy_status, is_linked,
                long_uploads_status, made_for_kids, hidden_subscriber_count,
                thumbnail_default, thumbnail_medium, thumbnail_high,
                keywords, topic_categories, fetched_at,
                uploads_playlist_id
            ))
            
            # Get the id of the inserted channel
            cursor.execute("SELECT id FROM channels WHERE youtube_id = ?", (youtube_id,))
            channel_db_id = cursor.fetchone()[0]
            
            # Extract and insert video data using VideoRepository
            videos = data.get('video_id', [])
            debug_log(f"Processing {len(videos)} videos")
            
            for video in videos:
                # Store video data using VideoRepository
                video_db_id = self.video_repository.store_video_data(video, channel_db_id, fetched_at)
                debug_log(f"Stored video {video.get('video_id')} with DB ID: {video_db_id}")
                
                if video_db_id:
                    # Store comments for this video
                    comments = video.get('comments', [])
                    debug_log(f"Storing {len(comments)} comments for video")
                    self.video_repository.store_comments(comments, video_db_id, fetched_at)
                    
                    # Store locations for this video
                    locations = video.get('locations', [])
                    debug_log(f"Storing {len(locations)} locations for video")
                    self.video_repository.store_video_locations(locations, video_db_id)
            
            # Commit the changes and close the connection
            conn.commit()
            conn.close()
            
            debug_log("Data saved to SQLite successfully")
            return True
        except Exception as e:
            st.error(f"Error saving to SQLite: {str(e)}")
            debug_log(f"Exception in store_channel_data: {str(e)}", e)
            return False
    
    def get_channels_list(self):
        """Get a list of all channel names from the database"""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all channel IDs and titles
            cursor.execute("SELECT youtube_id, title FROM channels ORDER BY title")
            rows = cursor.fetchall()
            
            # Format as a list of dictionaries with channel_id and channel_name keys
            channels = [{'channel_id': row[0], 'channel_name': row[1]} for row in rows]
            
            # Close the connection
            conn.close()
            
            debug_log(f"Retrieved {len(channels)} channels from database")
            return channels
        except Exception as e:
            debug_log(f"Exception in get_channels_list: {str(e)}", e)
            return []
    
    def get_channel_data(self, channel_identifier):
        """Get full data for a specific channel including videos, comments, and locations
        
        Args:
            channel_identifier (str): Either a YouTube channel ID (UC...) or a channel title
            
        Returns:
            dict or None: Channel data or None if not found
        """
        conn = None
        try:
            # First check if this is a channel title or ID
            is_id = channel_identifier.startswith('UC')
            
            # Check if we have this channel data cached in session state
            cache_key = f"channel_data_{channel_identifier}"
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                # Cache handling code removed as it will depend on external state management
                pass
            
            debug_log(f"Loading data for channel: {channel_identifier} from database")
            
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get channel info - using either ID or title depending on what was provided
            if is_id:
                cursor.execute("""
                    SELECT id, youtube_id, title, subscriber_count, view_count, 
                           video_count, description, uploads_playlist_id 
                    FROM channels WHERE youtube_id = ?
                """, (channel_identifier,))
            else:
                cursor.execute("""
                    SELECT id, youtube_id, title, subscriber_count, view_count, 
                           video_count, description, uploads_playlist_id 
                    FROM channels WHERE title = ?
                """, (channel_identifier,))
            
            channel_row = cursor.fetchone()
            if not channel_row:
                debug_log(f"Channel not found in database: {channel_identifier}")
                return None
            
            channel_db_id = channel_row[0]
            channel_youtube_id = channel_row[1]  # Store the actual YouTube ID
            uploads_playlist_id = channel_row[7]  # Get the uploads_playlist_id
            
            debug_log(f"Found channel with database ID: {channel_db_id}, YouTube ID: {channel_youtube_id}")
            
            # Create channel data dictionary
            channel_info = {
                'id': channel_youtube_id,
                'title': channel_row[2],
                'statistics': {
                    'subscriberCount': channel_row[3],
                    'viewCount': channel_row[4],
                    'videoCount': channel_row[5]
                },
                'description': channel_row[6],
                'uploads_playlist_id': uploads_playlist_id
            }
            
            # For backwards compatibility, also add contentDetails structure if we have a playlist ID
            if uploads_playlist_id:
                channel_info['contentDetails'] = {
                    'relatedPlaylists': {
                        'uploads': uploads_playlist_id
                    }
                }
            
            # Add debug logging for statistics and uploads playlist ID
            debug_log(f"DEBUG: Channel statistics from database: subscribers={channel_row[3]}, views={channel_row[4]}, videoCount={channel_row[5]}")
            debug_log(f"DEBUG: Uploads playlist ID from database: {uploads_playlist_id}")
            
            channel_data = {
                'channel_info': channel_info,
                'channel_id': channel_youtube_id,
                'uploads_playlist_id': uploads_playlist_id,
                'videos': []
            }
            
            # Get videos for this channel using VideoRepository
            videos = self.video_repository.get_videos_by_channel(channel_db_id)
            debug_log(f"DEBUG: Found {len(videos)} videos for channel {channel_identifier}")
            
            # Add videos to channel data
            channel_data['videos'] = videos
            
            # If we have comments, add them to the channel data
            if any(v['statistics']['commentCount'] > 0 for v in channel_data['videos']):
                channel_data['comments'] = {}
                
                # Add comments organized by video
                for video in channel_data['videos']:
                    if video['statistics']['commentCount'] > 0:
                        # Get comments for this video
                        comments = self.video_repository.get_video_comments(video['db_id'])
                        if comments:
                            channel_data['comments'][video['id']] = comments
            
            # Final debug verification of channel data structure
            if channel_data and 'channel_info' in channel_data:
                debug_log(f"Successfully built channel data structure for {channel_identifier}")
            
            return channel_data
        except Exception as e:
            debug_log(f"Exception in get_channel_data: {str(e)}", e)
            return None
        finally:
            # Ensure connection is always closed
            if conn:
                conn.close()
    
    def get_channel_id_by_title(self, title):
        """Get the YouTube channel ID for a given channel title."""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get channel ID by title
            cursor.execute("SELECT youtube_id FROM channels WHERE title = ?", (title,))
            result = cursor.fetchone()
            
            # Close the connection
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            debug_log(f"Exception in get_channel_id_by_title: {str(e)}", e)
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
                c.youtube_id as channel_id,
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
            st.error(f"Error loading data from SQLite: {str(e)}")
            debug_log(f"Exception in display_channels_data: {str(e)}", e)
            return False
    
    def list_channels(self):
        """
        Get a list of all channels from the database with their IDs and titles.
        
        Returns:
            list: List of tuples containing (youtube_id, title) for each channel
        """
        debug_log("Fetching list of all channels")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query all channels, returning both ID and title
            cursor.execute("SELECT youtube_id, title FROM channels ORDER BY title")
            channels = cursor.fetchall()
            
            # Close the connection
            conn.close()
            
            debug_log(f"Retrieved {len(channels)} channels from database")
            return channels
        except Exception as e:
            debug_log(f"Exception in list_channels: {str(e)}", e)
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
