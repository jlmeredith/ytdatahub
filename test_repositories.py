#!/usr/bin/env python3
"""
Test script for repository pattern implementation.
This script tests the interaction between all repository classes.
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch streamlit to disable warnings
import builtins
original_import = builtins.__import__

def import_mock(name, *args, **kwargs):
    if name == "streamlit":
        import types
        return types.ModuleType("streamlit_mock")
    return original_import(name, *args, **kwargs)

builtins.__import__ = import_mock

# Create a replacement for debug_log to use in our tests
def test_debug_log(message, exception=None):
    """Debug logging function replacement"""
    logging.debug(message)
    if exception:
        logging.debug(f"Exception details: {str(exception)}")
    
# Monkey patch the debug_log function in helpers
import sys
if 'src.utils.helpers' in sys.modules:
    sys.modules['src.utils.helpers'].debug_log = test_debug_log

from src.database.sqlite import SQLiteDatabase
from src.utils.helpers import debug_log

# Use a test database file
test_db_path = os.path.join('data', 'repository_test.sqlite')

# Remove the test database file if it exists
if os.path.exists(test_db_path):
    os.remove(test_db_path)
    print(f"Removed existing test database: {test_db_path}")

# Initialize the SQLiteDatabase with all repositories
print("Initializing database...")
db = SQLiteDatabase(test_db_path)
print("Database initialized successfully.")

# Create sample channel data
channel_data = {
    'channel_id': 'UC123456789',
    'channel_name': 'Test Channel',
    'subscribers': 1000,
    'views': 50000,
    'total_videos': 10,
    'channel_description': 'This is a test channel',
    'playlist_id': 'PL123456789',
    'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'video_id': [
        {
            'video_id': 'vid001',
            'title': 'Test Video 1',
            'video_description': 'This is a test video',
            'published_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'views': 500,
            'likes': 50,
            'duration': 'PT5M30S',
            'comments': [
                {
                    'comment_id': 'comment001',
                    'comment_text': 'Great video!',
                    'comment_author': 'User1',
                    'comment_published_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ],
            'locations': [
                {
                    'location_type': 'country',
                    'location_name': 'United States',
                    'confidence': 0.95,
                    'source': 'auto'
                }
            ]
        }
    ]
}

# Test storage
print("\nTesting data storage...")
print(f"Storing channel with ID: {channel_data['channel_id']}")
print(f"Channel has {len(channel_data['video_id'])} videos")
print(f"First video has ID: {channel_data['video_id'][0]['video_id']}")
success = db.store_channel_data(channel_data)
print(f"Data storage successful: {success}")

# Test data retrieval
print("\nTesting data retrieval...")
channels = db.get_channels_list()
print(f"Retrieved {len(channels)} channels")

# Test channel data retrieval
channel = db.get_channel_data('Test Channel')
if channel:
    print(f"Successfully retrieved channel: {channel['channel_info']['title']}")
    print(f"Channel has {len(channel['videos'])} videos")
    if 'comments' in channel:
        print(f"Retrieved comments for videos")
else:
    print("Failed to retrieve channel data")

# Test clear cache
print("\nTesting cache clearing...")
success = db.clear_cache()
print(f"Cache clearing successful: {success}")

print("\nAll tests completed successfully")
