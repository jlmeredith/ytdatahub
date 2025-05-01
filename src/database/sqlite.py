"""
SQLite database module for the YouTube scraper application.
"""
import sqlite3
import streamlit as st
import pandas as pd
import os
from pathlib import Path

from src.utils.helpers import debug_log

class SQLiteDatabase:
    """SQLite database connector for the YouTube scraper application."""
    
    def __init__(self, db_path):
        """Initialize the SQLite database with the given path."""
        self.db_path = db_path
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # Initialize the database tables
        self.initialize_db()
    
    def initialize_db(self):
        """Create the necessary tables in SQLite if they don't exist"""
        debug_log("Creating SQLite tables if needed")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create the channels table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE NOT NULL,
                title TEXT,
                subscriber_count INTEGER,
                video_count INTEGER,
                view_count INTEGER,
                description TEXT,
                custom_url TEXT,
                published_at TEXT,
                country TEXT,
                default_language TEXT,
                privacy_status TEXT,
                is_linked BOOLEAN,
                long_uploads_status TEXT,
                made_for_kids BOOLEAN,
                hidden_subscriber_count BOOLEAN,
                thumbnail_default TEXT,
                thumbnail_medium TEXT,
                thumbnail_high TEXT,
                keywords TEXT,
                topic_categories TEXT,
                fetched_at TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploads_playlist_id TEXT,
                local_thumbnail_medium TEXT,
                local_thumbnail_default TEXT,
                local_thumbnail_high TEXT,
                updated_at TEXT
            )
            ''')
            
            # Create the videos table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE NOT NULL,
                channel_id INTEGER,
                title TEXT,
                description TEXT,
                published_at TEXT,
                view_count INTEGER,
                like_count INTEGER,
                dislike_count INTEGER,
                favorite_count INTEGER,
                comment_count INTEGER,
                duration TEXT,
                dimension TEXT,
                definition TEXT,
                caption BOOLEAN,
                licensed_content BOOLEAN,
                projection TEXT,
                privacy_status TEXT,
                license TEXT,
                embeddable BOOLEAN,
                public_stats_viewable BOOLEAN,
                made_for_kids BOOLEAN,
                thumbnail_default TEXT,
                thumbnail_medium TEXT,
                thumbnail_high TEXT,
                tags TEXT,
                category_id INTEGER,
                live_broadcast_content TEXT,
                fetched_at TEXT,
                updated_at TEXT,
                local_thumbnail_default TEXT,
                local_thumbnail_medium TEXT,
                local_thumbnail_high TEXT,
                FOREIGN KEY (channel_id) REFERENCES channels (id)
            )
            ''')
            
            # Create the video_locations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                location_type TEXT NOT NULL,
                location_name TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                source TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
            )
            ''')
            
            # Create the comments table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE NOT NULL,
                video_id INTEGER NOT NULL,
                text TEXT,
                author_display_name TEXT,
                author_profile_image_url TEXT,
                author_channel_id TEXT,
                like_count INTEGER,
                published_at TEXT,
                updated_at TEXT,
                parent_id INTEGER,
                is_reply BOOLEAN DEFAULT FALSE,
                fetched_at TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES comments (id) ON DELETE CASCADE
            )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_channels_youtube_id ON channels(youtube_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_youtube_id ON videos(youtube_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_locations_video_id ON video_locations(video_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_locations_location ON video_locations(location_type, location_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments(parent_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_channels_id ON channels(id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_id ON videos(id)')
            
            # Commit the changes and close the connection
            conn.commit()
            conn.close()
            
            debug_log("SQLite tables created or already exist")
            return True
        except Exception as e:
            st.error(f"Error creating SQLite tables: {str(e)}")
            debug_log(f"Exception in initialize_db: {str(e)}", e)
            return False
    
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
            
            # Extract and insert video data
            videos = data.get('video_id', [])
            for video in videos:
                youtube_id = video.get('video_id')
                title = video.get('title')
                description = video.get('video_description', '')
                published_at = video.get('published_at')
                view_count = int(video.get('views', 0))
                like_count = int(video.get('likes', 0))
                duration = video.get('duration')
                
                # Extract new fields from video data
                dislike_count = int(video.get('dislike_count', 0))
                favorite_count = int(video.get('favorite_count', 0))
                comment_count = int(video.get('comment_count', 0))
                dimension = video.get('dimension', '')
                definition = video.get('definition', '')
                caption = video.get('caption_status', False)
                licensed_content = video.get('licensed_content', False)
                projection = video.get('projection', '')
                privacy_status = video.get('privacy_status', '')
                license_type = video.get('license', '')
                embeddable = video.get('embeddable', True)
                public_stats_viewable = video.get('public_stats_viewable', True)
                made_for_kids = video.get('made_for_kids', False)
                
                # Thumbnail URLs
                thumbnail_default = video.get('thumbnail_default', '')
                thumbnail_medium = video.get('thumbnail_medium', '')
                thumbnail_high = video.get('thumbnails', '') or video.get('thumbnail_high', '')
                
                # Additional metadata
                tags = ','.join(video.get('tags', [])) if isinstance(video.get('tags', []), list) else video.get('tags', '')
                category_id = video.get('category_id', '')
                live_broadcast_content = video.get('live_broadcast_content', '')
                video_fetched_at = video.get('fetched_at', fetched_at)  # Use video's fetched_at or default to channel's
                updated_at = video.get('updated_at', video_fetched_at)  # Use video's updated_at or default to fetched_at
                
                # Insert or update video data with all new fields
                cursor.execute('''
                INSERT OR REPLACE INTO videos (
                    youtube_id, channel_id, title, description, published_at,
                    view_count, like_count, dislike_count, favorite_count, 
                    comment_count, duration, dimension, definition,
                    caption, licensed_content, projection, privacy_status, 
                    license, embeddable, public_stats_viewable, made_for_kids,
                    thumbnail_default, thumbnail_medium, thumbnail_high,
                    tags, category_id, live_broadcast_content, 
                    fetched_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    youtube_id, channel_db_id, title, description, published_at,
                    view_count, like_count, dislike_count, favorite_count,
                    comment_count, duration, dimension, definition,
                    caption, licensed_content, projection, privacy_status,
                    license_type, embeddable, public_stats_viewable, made_for_kids,
                    thumbnail_default, thumbnail_medium, thumbnail_high,
                    tags, category_id, live_broadcast_content,
                    video_fetched_at, updated_at
                ))
                
                # Get the id of the inserted video
                cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
                video_db_id = cursor.fetchone()[0]
                
                # Extract and insert comment data
                comments = video.get('comments', [])
                for comment in comments:
                    comment_id = comment.get('comment_id')
                    text = comment.get('comment_text', '')
                    author_display_name = comment.get('comment_author', '')
                    published_at = comment.get('comment_published_at', '')
                    
                    # Insert or update comment data - fixed column names
                    cursor.execute('''
                    INSERT OR REPLACE INTO comments (
                        comment_id, video_id, text, author_display_name, published_at,
                        fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        comment_id, video_db_id, text, author_display_name, published_at,
                        fetched_at
                    ))
                
                # Extract and insert location data
                locations = video.get('locations', [])
                for location in locations:
                    location_type = location.get('location_type', '')
                    location_name = location.get('location_name', '')
                    confidence = float(location.get('confidence', 0.0))
                    source = location.get('source', 'auto')
                    created_at = location.get('created_at', '')
                    
                    # Use current timestamp if created_at is not provided
                    if not created_at:
                        from datetime import datetime
                        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Insert location data
                    cursor.execute('''
                    INSERT INTO video_locations (
                        video_id, location_type, location_name, confidence, source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        video_db_id, location_type, location_name, confidence, source, created_at
                    ))
            
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
            
            # Get all channel names - updating column name from 'channel_name' to 'title'
            cursor.execute("SELECT title FROM channels")
            channels = [row[0] for row in cursor.fetchall()]
            
            # Close the connection
            conn.close()
            
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
        try:
            # First check if this is a channel title or ID
            is_id = channel_identifier.startswith('UC')
            
            # Check if we have this channel data cached in session state
            cache_key = f"channel_data_{channel_identifier}"
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached data for channel: {channel_identifier}")
                return st.session_state[cache_key]
            
            debug_log(f"Loading data for channel: {channel_identifier} from database")
            
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get channel info - using either ID or title depending on what was provided
            if is_id:
                # Query by YouTube channel ID (preferred method)
                cursor.execute("""
                    SELECT id, youtube_id, title, subscriber_count, view_count, 
                           video_count, description, uploads_playlist_id 
                    FROM channels 
                    WHERE youtube_id = ?
                """, (channel_identifier,))
            else:
                # Query by channel title (fallback method)
                cursor.execute("""
                    SELECT id, youtube_id, title, subscriber_count, view_count, 
                           video_count, description, uploads_playlist_id 
                    FROM channels 
                    WHERE title = ?
                """, (channel_identifier,))
            
            channel_row = cursor.fetchone()
            if not channel_row:
                # If not found and it's not an ID, try a partial match on title
                if not is_id:
                    cursor.execute("""
                        SELECT id, youtube_id, title, subscriber_count, view_count, 
                               video_count, description, uploads_playlist_id 
                        FROM channels 
                        WHERE title LIKE ?
                    """, (f"%{channel_identifier}%",))
                    channel_row = cursor.fetchone()
                
                if not channel_row:
                    conn.close()
                    debug_log(f"No channel found for identifier: {channel_identifier}")
                    return None
            
            channel_db_id = channel_row[0]
            channel_youtube_id = channel_row[1]  # Store the actual YouTube ID
            uploads_playlist_id = channel_row[7]  # Get the uploads_playlist_id
            
            debug_log(f"Found channel with database ID: {channel_db_id}, YouTube ID: {channel_youtube_id}")
            
            # Create channel data dictionary
            channel_info = {
                'id': channel_youtube_id,  # Always use the actual YouTube ID
                'title': channel_row[2],
                'statistics': {
                    'subscriberCount': channel_row[3],
                    'viewCount': channel_row[4],
                    'videoCount': channel_row[5]  # Explicitly include videoCount here
                },
                'description': channel_row[6],
                'uploads_playlist_id': uploads_playlist_id  # Add uploads_playlist_id to channel_info
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
                'channel_id': channel_youtube_id,  # Include the channel ID at the root level
                'uploads_playlist_id': uploads_playlist_id,  # Also add it at the root level for compatibility
                'videos': []  # Changed from 'video_id' to 'videos'
            }
            
            # Get videos for this channel
            cursor.execute("""
                SELECT id, youtube_id, title, description, published_at, view_count, 
                       like_count, duration, thumbnail_high, caption
                FROM videos 
                WHERE channel_id = ?
            """, (channel_db_id,))
            
            videos = cursor.fetchall()
            debug_log(f"DEBUG: Found {len(videos)} videos for channel {channel_identifier}")
            
            # Add each video to the channel data
            for video_row in videos:
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
                
                # Get locations for this video
                cursor.execute("""
                    SELECT location_type, location_name, confidence, source, created_at
                    FROM video_locations
                    WHERE video_id = ?
                """, (video_db_id,))
                
                locations = cursor.fetchall()
                
                # Add locations to the video data
                for location_row in locations:
                    location_data = {
                        'location_type': location_row[0],
                        'location_name': location_row[1],
                        'confidence': location_row[2],
                        'source': location_row[3],
                        'created_at': location_row[4]
                    }
                    video_data['locations'].append(location_data)
                
                # Get comments for this video
                cursor.execute("""
                    SELECT comment_id, text, author_display_name, published_at
                    FROM comments 
                    WHERE video_id = ?
                """, (video_db_id,))
                
                comments = cursor.fetchall()
                
                # Count comments and add them to statistics
                video_data['statistics']['commentCount'] = len(comments)
                
                # Create a dictionary to store comments for this video
                video_comments = []
                
                # Add each comment to the video data
                for comment_row in comments:
                    comment_data = {
                        'id': comment_row[0],
                        'snippet': {
                            'topLevelComment': {
                                'snippet': {
                                    'textDisplay': comment_row[1],
                                    'authorDisplayName': comment_row[2],
                                    'publishedAt': comment_row[3],
                                    'likeCount': 0
                                }
                            }
                        }
                    }
                    video_comments.append(comment_data)
                
                # Add the video to channel data
                channel_data['videos'].append(video_data)
            
            # If we have comments, add them to the channel data
            if any(v['statistics']['commentCount'] > 0 for v in channel_data['videos']):
                channel_data['comments'] = {}
                
                # Add comments organized by video
                for video in channel_data['videos']:
                    if video['statistics']['commentCount'] > 0:
                        cursor.execute("""
                            SELECT comment_id, text, author_display_name, published_at
                            FROM comments 
                            WHERE video_id = ?
                        """, (video['db_id'],))
                        
                        comments = cursor.fetchall()
                        if comments:
                            channel_data['comments'][video['id']] = []
                            
                            for comment_row in comments:
                                comment_data = {
                                    'id': comment_row[0],
                                    'snippet': {
                                        'topLevelComment': {
                                            'snippet': {
                                                'textDisplay': comment_row[1],
                                                'authorDisplayName': comment_row[2],
                                                'publishedAt': comment_row[3],
                                                'likeCount': 0
                                            }
                                        }
                                    }
                                }
                                channel_data['comments'][video['id']].append(comment_data)
            
            # Cache the result in session state if caching is enabled
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = channel_data
                debug_log(f"Cached data for channel: {channel_identifier}")
                
                # Also cache by YouTube ID if we found the channel by title
                if not is_id and channel_youtube_id:
                    id_cache_key = f"channel_data_{channel_youtube_id}"
                    st.session_state[id_cache_key] = channel_data
                    debug_log(f"Also cached data by YouTube ID: {channel_youtube_id}")
            
            # Close the connection
            conn.close()
            
            # Final debug verification of channel data structure
            if channel_data and 'channel_info' in channel_data:
                debug_log(f"DEBUG: Final channel info structure: {list(channel_data['channel_info'].keys())}")
                if 'statistics' in channel_data['channel_info']:
                    stats = channel_data['channel_info']['statistics']
                    debug_log(f"DEBUG: Final statistics: {list(stats.keys())} - videoCount={stats.get('videoCount', 'MISSING')}")
                debug_log(f"DEBUG: Final uploads_playlist_id: {channel_data.get('uploads_playlist_id', 'MISSING')}")
                if 'contentDetails' in channel_data['channel_info']:
                    debug_log(f"DEBUG: Final contentDetails structure: {channel_data['channel_info']['contentDetails']}")
            
            return channel_data
        except Exception as e:
            debug_log(f"Exception in get_channel_data: {str(e)}", e)
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
                c.channel_name,
                c.channel_id,
                c.subscribers,
                c.views,
                c.total_videos,
                COUNT(v.video_id) as fetched_videos,
                CASE 
                    WHEN COUNT(v.video_id) > 0 THEN c.views / COUNT(v.video_id)
                    ELSE 0
                END as avg_views_per_video
            FROM 
                channels c
            LEFT JOIN 
                videos v ON c.channel_id = v.channel_id
            GROUP BY 
                c.channel_id
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
    
    def display_videos_data(self):
        """Display all videos from SQLite database in a Streamlit interface"""
        debug_log("Loading videos from SQLite")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            
            # Query for videos data with channel names
            query = '''
            SELECT 
                c.channel_name,
                c.channel_id,
                v.video_id,
                v.title,
                v.published_at,
                v.views,
                v.likes,
                v.duration,
                CASE 
                    WHEN v.views > 0 THEN CAST(v.likes AS FLOAT) / v.views
                    ELSE 0
                END as engagement
            FROM 
                videos v
            JOIN 
                channels c ON v.channel_id = c.channel_id
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
            st.error(f"Error loading videos from SQLite: {str(e)}")
            debug_log(f"Exception in display_videos_data: {str(e)}", e)
            return False

    def clear_cache(self):
        """
        Clear any database caches or temporary data
        
        This method:
        1. Releases any connection pools
        2. Runs VACUUM to optimize the database
        3. Clears any prepared statement caches
        
        Returns:
            bool: True if successful, False otherwise
        """
        debug_log("Clearing database caches")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Run PRAGMA statements to clear SQLite's internal caches
            cursor.execute("PRAGMA cache_size = 0")  # Clear page cache
            cursor.execute("PRAGMA cache_size = -2000")  # Reset to default
            
            # Run VACUUM to optimize the database and reclaim space
            cursor.execute("VACUUM")
            
            # Execute a checkpoint to ensure all changes are written to disk
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            debug_log("Database caches cleared successfully")
            return True
        except Exception as e:
            debug_log(f"Error clearing database caches: {str(e)}", e)
            return False

    def continue_iteration(self, channel_id, max_iterations=3, time_threshold_days=7):
        """
        Determine if data collection should continue for a given channel.
        
        Args:
            channel_id (str): The YouTube channel ID to check
            max_iterations (int): Maximum number of iterations allowed for a channel
            time_threshold_days (int): Number of days to consider for recent iterations
            
        Returns:
            bool: True if iteration should continue, False otherwise
        """
        debug_log(f"Checking if data collection should continue for channel: {channel_id}")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if the iteration_history table exists
            cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='iteration_history'
            ''')
            
            if not cursor.fetchone():
                # Create the iteration_history table if it doesn't exist
                cursor.execute('''
                CREATE TABLE iteration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    iteration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    metrics_changed BOOLEAN DEFAULT FALSE
                )
                ''')
                conn.commit()
                debug_log("Created iteration_history table")
            
            # Get current timestamp in SQLite format
            import datetime
            current_time = datetime.datetime.now()
            time_threshold = current_time - datetime.timedelta(days=time_threshold_days)
            threshold_timestamp = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
            
            # Count recent iterations for this channel
            cursor.execute('''
            SELECT COUNT(*) FROM iteration_history
            WHERE channel_id = ? AND iteration_date > ?
            ''', (channel_id, threshold_timestamp))
            
            recent_iterations = cursor.fetchone()[0]
            
            # Record this iteration attempt
            cursor.execute('''
            INSERT INTO iteration_history (channel_id)
            VALUES (?)
            ''', (channel_id,))
            
            # Get the ID of the newly inserted record
            iteration_id = cursor.lastrowid
            
            # Commit the changes
            conn.commit()
            
            # Check if we should continue
            should_continue = recent_iterations < max_iterations
            
            # Update the status if we're not continuing
            if not should_continue:
                cursor.execute('''
                UPDATE iteration_history
                SET status = 'skipped - max iterations reached'
                WHERE id = ?
                ''', (iteration_id,))
                conn.commit()
                debug_log(f"Skipping iteration for channel {channel_id} - maximum iterations reached")
            
            # Close the connection
            conn.close()
            
            return should_continue
            
        except Exception as e:
            debug_log(f"Exception in continue_iteration: {str(e)}", e)
            # Default to False on error to be safe
            return False

    def get_channel_id_by_title(self, channel_title):
        """Get the YouTube channel ID for a given channel title"""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query the database for the channel ID by title
            cursor.execute("SELECT youtube_id FROM channels WHERE title = ?", (channel_title,))
            result = cursor.fetchone()
            
            # Close the connection
            conn.close()
            
            # Return the channel ID if found, otherwise None
            return result[0] if result else None
        except Exception as e:
            debug_log(f"Exception in get_channel_id_by_title: {str(e)}", e)
            return None

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

    def clear_all_data(self):
        """
        Clear all data from the database by dropping and recreating all tables.
        
        This is a destructive operation and should be used with caution,
        primarily for testing purposes.
        
        Returns:
            bool: True if successful, False otherwise
        """
        debug_log("WARNING: Clearing all data from the database")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, back up the database
            import shutil
            from datetime import datetime
            
            # Create backup filename with timestamp
            backup_path = f"{self.db_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            
            # Close connection to allow backup
            conn.close()
            
            # Create backup
            shutil.copy2(self.db_path, backup_path)
            debug_log(f"Created database backup at: {backup_path}")
            
            # Reconnect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Drop all tables in the correct order to respect foreign keys
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # First drop tables with foreign key dependencies
            tables_to_drop = [
                "comments", 
                "video_locations", 
                "videos", 
                "channels",
                "iteration_history"
            ]
            
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    debug_log(f"Dropped table: {table}")
                except Exception as e:
                    debug_log(f"Error dropping table {table}: {str(e)}")
            
            # Commit changes
            conn.commit()
            
            # Re-initialize the database tables
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.close()
            
            # Recreate all tables
            success = self.initialize_db()
            
            if success:
                debug_log("All data cleared and tables recreated successfully")
                return True
            else:
                debug_log("Error recreating tables after clearing data")
                return False
                
        except Exception as e:
            debug_log(f"Error clearing database: {str(e)}", e)
            return False

    def _get_connection(self):
        """
        Get a direct SQLite database connection.
        This is useful for performing custom queries.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            debug_log(f"Error connecting to database: {str(e)}")
            return None

# Keep the original functions for backward compatibility, but delegate to the class
def create_sqlite_tables():
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.initialize_db()

def save_to_sqlite(data):
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.store_channel_data(data)

def get_sqlite_channels_data():
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.display_channels_data()

def get_sqlite_videos_data():
    # Use default path from config
    from src.config import SQLITE_DB_PATH
    db = SQLiteDatabase(SQLITE_DB_PATH)
    return db.display_videos_data()