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
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                subscribers INTEGER,
                views INTEGER,
                total_videos INTEGER,
                channel_description TEXT,
                playlist_id TEXT
            )
            ''')
            
            # Create the videos table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                channel_id TEXT,
                title TEXT,
                video_description TEXT,
                published_at TEXT,
                views INTEGER,
                likes INTEGER,
                duration TEXT,
                thumbnails TEXT,
                caption_status TEXT,
                FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
            )
            ''')
            
            # Create the comments table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                comment_id TEXT PRIMARY KEY,
                video_id TEXT,
                comment_text TEXT,
                comment_author TEXT,
                comment_published_at TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
            ''')
            
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
            channel_id = data.get('channel_id')
            channel_name = data.get('channel_name')
            subscribers = int(data.get('subscribers', 0))
            views = int(data.get('views', 0))  # Changed from total_views to views
            total_videos = int(data.get('total_videos', 0))
            channel_description = data.get('channel_description', '')
            playlist_id = data.get('playlist_id', '')
            
            # Insert or update channel data
            cursor.execute('''
            INSERT OR REPLACE INTO channels (
                channel_id, channel_name, subscribers, views, 
                total_videos, channel_description, playlist_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                channel_id, channel_name, subscribers, views,
                total_videos, channel_description, playlist_id
            ))
            
            # Extract and insert video data
            videos = data.get('video_id', [])
            for video in videos:
                video_id = video.get('video_id')
                title = video.get('title')
                description = video.get('video_description', '')
                published_at = video.get('published_at')
                views = int(video.get('views', 0))
                likes = int(video.get('likes', 0))
                duration = video.get('duration')
                thumbnail_url = video.get('thumbnails', '')
                caption_status = video.get('caption_status', '')
                
                # Insert or update video data
                cursor.execute('''
                INSERT OR REPLACE INTO videos (
                    video_id, channel_id, title, video_description, published_at,
                    views, likes, duration, thumbnails, caption_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_id, channel_id, title, description, published_at,
                    views, likes, duration, thumbnail_url, caption_status
                ))
                
                # Extract and insert comment data
                comments = video.get('comments', [])
                for comment in comments:
                    comment_id = comment.get('comment_id')
                    comment_text = comment.get('comment_text', '')
                    author_name = comment.get('comment_authorc', '')
                    comment_published_at = comment.get('comment_published_at', '')
                    
                    # Insert or update comment data
                    cursor.execute('''
                    INSERT OR REPLACE INTO comments (
                        comment_id, video_id, comment_text, comment_author, comment_published_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        comment_id, video_id, comment_text, author_name, comment_published_at
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
            
            # Get all channel names
            cursor.execute("SELECT channel_name FROM channels")
            channels = [row[0] for row in cursor.fetchall()]
            
            # Close the connection
            conn.close()
            
            return channels
        except Exception as e:
            debug_log(f"Exception in get_channels_list: {str(e)}", e)
            return []
    
    def get_channel_data(self, channel_name):
        """Get full data for a specific channel including videos and comments"""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get channel info
            cursor.execute("""
                SELECT channel_id, channel_name, subscribers, views, 
                       total_videos, channel_description, playlist_id 
                FROM channels 
                WHERE channel_name = ?
            """, (channel_name,))
            
            channel_row = cursor.fetchone()
            if not channel_row:
                conn.close()
                return None
            
            # Create channel data dictionary
            channel_info = {
                'title': channel_row[1],
                'statistics': {
                    'subscriberCount': channel_row[2],
                    'viewCount': channel_row[3]
                },
                'description': channel_row[5]
            }
            
            channel_data = {
                'channel_info': channel_info,
                'videos': []  # Changed from 'video_id' to 'videos'
            }
            
            # Get videos for this channel
            cursor.execute("""
                SELECT video_id, title, video_description, published_at, views, 
                       likes, duration, thumbnails, caption_status
                FROM videos 
                WHERE channel_id = ?
            """, (channel_row[0],))
            
            videos = cursor.fetchall()
            
            # Add each video to the channel data
            for video_row in videos:
                video_data = {
                    'id': video_row[0],  # Changed from 'video_id' to 'id'
                    'snippet': {
                        'title': video_row[1],
                        'description': video_row[2],
                        'publishedAt': video_row[3]
                    },
                    'statistics': {
                        'viewCount': video_row[4],
                        'likeCount': video_row[5],
                        'commentCount': 0  # Default value
                    },
                    'contentDetails': {
                        'duration': video_row[6]
                    }
                }
                
                # Get comments for this video
                cursor.execute("""
                    SELECT comment_id, comment_text, comment_author, comment_published_at
                    FROM comments 
                    WHERE video_id = ?
                """, (video_row[0],))
                
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
            if any(len(cursor.execute("""SELECT 1 FROM comments WHERE video_id = ?""",
                                   (v['id'],)).fetchall()) > 0 
                  for v in channel_data['videos']):
                channel_data['comments'] = {}
                
                # Add comments organized by video
                for video in channel_data['videos']:
                    cursor.execute("""
                        SELECT comment_id, comment_text, comment_author, comment_published_at
                        FROM comments 
                        WHERE video_id = ?
                    """, (video['id'],))
                    
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
            
            # Close the connection
            conn.close()
            
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