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
            
            # Extract video data
            videos = data.get('video_id', [])
            debug_log(f"Processing {len(videos)} videos")
            
            # Store videos directly using SQL for better control
            for video in videos:
                video_id = video.get('video_id')
                title = video.get('title')
                description = video.get('video_description', '')
                published_at = video.get('published_at')
                
                try:
                    view_count = int(video.get('views', 0))
                except (ValueError, TypeError):
                    view_count = 0
                
                try:
                    like_count = int(video.get('likes', 0))
                except (ValueError, TypeError):
                    like_count = 0
                
                duration = video.get('duration', '')
                
                # Insert the video directly
                debug_log(f"Directly inserting video {video_id} into database")
                try:
                    cursor.execute('''
                    INSERT OR REPLACE INTO videos (
                        youtube_id, channel_id, title, description, published_at,
                        view_count, like_count, duration
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        video_id, channel_db_id, title, description, published_at,
                        view_count, like_count, duration
                    ))
                    
                    # Get the video ID
                    cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", (video_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        video_db_id = result[0]
                        debug_log(f"Inserted video {video_id} with DB ID: {video_db_id}")
                        
                        # Store comments for this video if we have a valid ID
                        comments = video.get('comments', [])
                        if comments and len(comments) > 0:
                            debug_log(f"Found {len(comments)} comments for video {video_id}, DB ID: {video_db_id}")
                            debug_log(f"Sample comment data: {comments[0]}")
                            
                            # DIRECT STORAGE: Instead of delegating to video_repository, 
                            # we'll directly insert the comments here to ensure they're stored
                            for i, comment in enumerate(comments):
                                try:
                                    # Ensure comment_id exists
                                    comment_id = comment.get('comment_id')
                                    if not comment_id:
                                        comment_id = f"generated_id_{video_db_id}_{i}_{hash(str(comment))}"
                                    
                                    # Extract comment fields with fallbacks
                                    text = comment.get('comment_text', comment.get('text', ''))
                                    author = comment.get('comment_author', comment.get('author_display_name', ''))
                                    published = comment.get('comment_published_at', comment.get('published_at', ''))
                                    author_profile_image_url = comment.get('author_profile_image_url', '')
                                    author_channel_id = comment.get('author_channel_id', '')
                                    
                                    # Handle like_count
                                    try:
                                        like_count = int(comment.get('like_count', 0))
                                    except (ValueError, TypeError):
                                        like_count = 0
                                        
                                    updated_at = comment.get('updated_at', published)
                                    parent_id = comment.get('parent_id', None)
                                    is_reply = bool(comment.get('is_reply', False))
                                    
                                    # Direct SQL insert - bypass VideoRepository 
                                    cursor.execute('''
                                    INSERT OR REPLACE INTO comments (
                                        comment_id, video_id, text, author_display_name, author_profile_image_url,
                                        author_channel_id, like_count, published_at, updated_at, parent_id,
                                        is_reply, fetched_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        comment_id, video_db_id, text, author, author_profile_image_url,
                                        author_channel_id, like_count, published, updated_at, parent_id,
                                        is_reply, fetched_at
                                    ))
                                    debug_log(f"ChannelRepository: Inserted comment {comment_id}")
                                except Exception as e:
                                    debug_log(f"ChannelRepository: Error inserting comment {i}: {str(e)}")
                                    
                            # Also try delegating through the repository as a backup
                            try:
                                result = self.video_repository.store_comments(comments, video_db_id, fetched_at)
                                debug_log(f"ChannelRepository: Video repository comment storage result: {result}")
                            except Exception as e:
                                debug_log(f"ChannelRepository: Error delegating comment storage: {str(e)}")
                            
                            # Verify comments were stored
                            try:
                                cursor.execute("SELECT COUNT(*) FROM comments WHERE video_id = ?", (video_db_id,))
                                comment_count = cursor.fetchone()[0]
                                debug_log(f"ChannelRepository: Verified {comment_count} comments stored for video DB ID {video_db_id}")
                            except Exception as e:
                                debug_log(f"ChannelRepository: Error verifying comments: {str(e)}", e)
                        
                        # Store locations for this video
                        locations = video.get('locations', [])
                        if locations and len(locations) > 0:
                            debug_log(f"Storing {len(locations)} locations for video")
                            self.video_repository.store_video_locations(locations, video_db_id)
                    else:
                        debug_log(f"Failed to get ID for inserted video {video_id}")
                except Exception as e:
                    debug_log(f"Error inserting video {video_id}: {str(e)}", e)
            
            # Commit the changes and close the connection
            conn.commit()
            debug_log("Committed all changes to database")
            
            # Verify videos were stored
            cursor.execute("SELECT COUNT(*) FROM videos WHERE channel_id = ?", (channel_db_id,))
            count = cursor.fetchone()[0]
            debug_log(f"Verified {count} videos stored for channel {youtube_id}")
            
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
            
            # Add video_id field for backward compatibility with tests
            channel_data['video_id'] = videos
            
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
