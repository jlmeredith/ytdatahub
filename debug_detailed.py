"""
Script with more detailed logging to debug database video storage.
"""
import os
import sys
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('debug_video_storage')

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# We'll use our own simple debug log function
def my_debug_log(message, exception=None):
    """Simple debug log function"""
    logger.debug(message)
    if exception:
        logger.exception(exception)

from src.database.sqlite import SQLiteDatabase
from src.database.video_repository import VideoRepository
from src.database.channel_repository import ChannelRepository

class VideoStorageDebugger:
    """Class to debug video storage issues"""
    
    def __init__(self):
        self.db_path = os.path.join(project_root, "data", "youtube_data.db")
        logger.info(f"Using database at: {self.db_path}")
        self.db = SQLiteDatabase(self.db_path)
        self.channel_repo = ChannelRepository(self.db_path)
        self.video_repo = VideoRepository(self.db_path)
        
    def create_test_data(self):
        """Create test data for debugging"""
        return {
            'channel_id': 'UC_test_debug',
            'channel_name': 'Debug Test Channel',
            'subscribers': 1000,
            'views': 50000,
            'total_videos': 2,
            'channel_description': 'This is a debug test channel',
            'playlist_id': 'PL_test_debug',
            'published_at': '2020-01-01T12:00:00Z',
            'fetched_at': '2025-05-18T15:00:00Z',
            'video_id': [
                {
                    'video_id': 'debug_video_1',
                    'title': 'Debug Video 1',
                    'video_description': 'Description for debug video 1',
                    'published_at': '2020-01-15T12:00:00Z',
                    'views': 1000,
                    'likes': 100,
                    'duration': 'PT10M30S',
                    'comments': []
                },
                {
                    'video_id': 'debug_video_2',
                    'title': 'Debug Video 2',
                    'video_description': 'Description for debug video 2',
                    'published_at': '2020-02-15T12:00:00Z',
                    'views': 2000,
                    'likes': 200,
                    'duration': 'PT15M45S',
                    'comments': []
                }
            ]
        }
        
    def trace_video_storage(self):
        """Trace the video storage process with detailed logging"""
        # Store sample data
        logger.info("Creating sample channel data")
        sample_data = self.create_test_data()
        
        # Log what we're storing
        logger.info(f"Channel ID: {sample_data['channel_id']}")
        logger.info(f"Channel name: {sample_data['channel_name']}")
        logger.info(f"Number of videos to store: {len(sample_data['video_id'])}")
        for i, video in enumerate(sample_data['video_id']):
            logger.info(f"Video {i+1}: {video['video_id']} - {video['title']}")
        
        # Monkey patch the VideoRepository.store_video_data method to add more logging
        original_store_video_data = VideoRepository.store_video_data
        
        def patched_store_video_data(self, video, channel_db_id, fetched_at):
            """Patched store_video_data with additional logging"""
            logger.info(f"VideoRepository.store_video_data called for video: {video.get('video_id')}")
            logger.info(f"  channel_db_id: {channel_db_id}")
            logger.info(f"  video title: {video.get('title')}")
            
            try:
                result = original_store_video_data(self, video, channel_db_id, fetched_at)
                logger.info(f"  store_video_data returned: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in store_video_data: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        
        # Apply the monkey patch
        VideoRepository.store_video_data = patched_store_video_data
        
        # Store the data
        logger.info("Storing sample channel data...")
        result = self.db.store_channel_data(sample_data)
        logger.info(f"store_channel_data result: {result}")
        
        # Check database directly
        logger.info("\nChecking database for videos directly...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the database ID of the channel
        cursor.execute("SELECT id FROM channels WHERE youtube_id = ?", ('UC_test_debug',))
        channel_row = cursor.fetchone()
        
        if channel_row:
            channel_db_id = channel_row[0]
            logger.info(f"Channel DB ID: {channel_db_id}")
            
            # Check if videos were stored for this channel
            cursor.execute("SELECT COUNT(*) FROM videos WHERE channel_id = ?", (channel_db_id,))
            video_count = cursor.fetchone()[0]
            logger.info(f"Videos in database for this channel: {video_count}")
            
            if video_count > 0:
                cursor.execute("SELECT id, youtube_id, title, view_count FROM videos WHERE channel_id = ?", (channel_db_id,))
                videos = cursor.fetchall()
                logger.info("\nVideos found in database:")
                for i, video in enumerate(videos):
                    logger.info(f"  {i+1}. ID: {video[0]}, YouTube ID: {video[1]}, Title: {video[2]}, Views: {video[3]}")
            else:
                logger.warning("No videos found in the database for this channel.")
                
                # Check for any videos in the database
                cursor.execute("SELECT COUNT(*) FROM videos")
                total_videos = cursor.fetchone()[0]
                logger.info(f"Total videos in database: {total_videos}")
                
                # Get table definitions
                logger.info("\nChecking table definitions:")
                cursor.execute("PRAGMA table_info(videos)")
                columns = cursor.fetchall()
                logger.info("Videos table columns:")
                for column in columns:
                    logger.info(f"  {column}")
                
                # Try to insert a video directly using SQL
                logger.info("\nTrying direct SQL insertion:")
                try:
                    cursor.execute('''
                        INSERT INTO videos (
                            youtube_id, channel_id, title, description, published_at, 
                            view_count, like_count, duration
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        'direct_sql_test', channel_db_id, 'Direct SQL Test', 
                        'Test description', '2025-05-18T00:00:00Z',
                        500, 50, 'PT5M30S'
                    ))
                    conn.commit()
                    logger.info("Direct SQL insertion succeeded")
                    
                    cursor.execute("SELECT * FROM videos WHERE youtube_id = ?", ('direct_sql_test',))
                    direct_video = cursor.fetchone()
                    logger.info(f"Direct inserted video: {direct_video}")
                except Exception as e:
                    logger.error(f"Direct SQL insertion failed: {str(e)}")
                    conn.rollback()
        else:
            logger.error("Channel not found in database")
        
        # Restore original method
        VideoRepository.store_video_data = original_store_video_data
        
        # Close database connection
        conn.close()
        
        logger.info("Debug complete")

if __name__ == "__main__":
    debugger = VideoStorageDebugger()
    debugger.trace_video_storage()
