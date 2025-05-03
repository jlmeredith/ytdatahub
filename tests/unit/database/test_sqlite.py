"""
Unit tests for the SQLite database operations, focusing on data persistence
and retrieval functionality.
"""
import pytest
import os
import sqlite3
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

from src.database.sqlite import SQLiteDatabase

class SessionStateMock(dict):
    """Custom mock for Streamlit's session_state to handle attribute access and assignment"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_mode = False
        self.log_level = 30  # WARNING level
        self.performance_timers = {}
        self.performance_metrics = {}
        self.ui_freeze_thresholds = {
            'warning': 1.0,
            'critical': 3.0,
            'ui_blocking': 0.5
        }

    def __getattr__(self, name):
        # For attribute access like st.session_state.debug_mode
        if name in self:
            return self[name]
        return getattr(super(), name)

    def __setattr__(self, name, value):
        # For attribute assignment like st.session_state.debug_mode = False
        self[name] = value

# Create a patch for the debug_log function to prevent Streamlit session_state errors
@pytest.fixture(autouse=True)
def mock_debug_log():
    """Mock the debug_log function to prevent session_state errors"""
    with patch('src.utils.helpers.debug_log') as mock:
        yield mock

# Create a patch for Streamlit to prevent st.error and other UI calls
@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock streamlit to prevent UI calls during testing"""
    session_state_mock = SessionStateMock()
    
    with patch('streamlit.error') as mock_error, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.write') as mock_write, \
         patch('streamlit.dataframe') as mock_df, \
         patch('streamlit.session_state', session_state_mock):
        yield {
            'error': mock_error,
            'info': mock_info,
            'write': mock_write,
            'dataframe': mock_df,
            'session_state': session_state_mock
        }

@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing"""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file_path = temp_file.name
    temp_file.close()
    
    yield temp_file_path
    
    # Clean up the file after tests
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)

@pytest.fixture
def sqlite_db(temp_db_path):
    """Create an instance of SQLiteDatabase with a temporary database file"""
    db = SQLiteDatabase(temp_db_path)
    return db

@pytest.fixture
def sample_channel_data():
    """Sample channel data structure for testing database storage"""
    return {
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': 1000,
        'views': 50000,
        'total_videos': 25,
        'channel_description': 'This is a test channel for unit tests',
        'playlist_id': 'PL_test_playlist',
        'published_at': '2020-01-01T12:00:00Z',
        'fetched_at': '2025-04-29T15:00:00Z',
        'video_id': [
            {
                'video_id': 'test_video_1',
                'title': 'Test Video 1',
                'video_description': 'Description for test video 1',
                'published_at': '2020-01-15T12:00:00Z',
                'views': 1000,
                'likes': 100,
                'duration': 'PT10M30S',
                'comments': [
                    {
                        'comment_id': 'comment_1_1',
                        'comment_text': 'Great video!',
                        'comment_author': 'Commenter 1',
                        'comment_published_at': '2020-01-16T12:00:00Z'
                    },
                    {
                        'comment_id': 'comment_1_2',
                        'comment_text': 'Nice content',
                        'comment_author': 'Commenter 2',
                        'comment_published_at': '2020-01-17T12:00:00Z'
                    }
                ]
            },
            {
                'video_id': 'test_video_2',
                'title': 'Test Video 2',
                'video_description': 'Description for test video 2',
                'published_at': '2020-02-15T12:00:00Z',
                'views': 2000,
                'likes': 200,
                'duration': 'PT15M45S',
                'comments': [
                    {
                        'comment_id': 'comment_2_1',
                        'comment_text': 'Interesting!',
                        'comment_author': 'Commenter 3',
                        'comment_published_at': '2020-02-16T12:00:00Z'
                    }
                ]
            }
        ]
    }


class TestSQLiteDatabase:
    """Tests for SQLite database operations"""
    
    def test_initialization(self, sqlite_db, temp_db_path):
        """Test database initialization and table creation"""
        # Verify the database file was created
        assert os.path.exists(temp_db_path)
        
        # Connect to check if tables were created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Verify required tables exist
        assert 'channels' in tables
        assert 'videos' in tables
        assert 'comments' in tables
        assert 'video_locations' in tables
        
        # Check if indexes were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Verify at least some indexes exist
        assert len(indexes) > 0
        assert 'idx_channels_youtube_id' in indexes
        assert 'idx_videos_youtube_id' in indexes
        
        # Close connection
        conn.close()
    
    def test_store_channel_data(self, sqlite_db, sample_channel_data):
        """Test storing channel data to the database"""
        # Store the sample data
        result = sqlite_db.store_channel_data(sample_channel_data)
        
        # Verify the operation was successful
        assert result is True
        
        # Connect to check if data was stored
        conn = sqlite3.connect(sqlite_db.db_path)
        cursor = conn.cursor()
        
        # Check if channel was inserted
        cursor.execute("SELECT youtube_id FROM channels WHERE youtube_id = ?", 
                      (sample_channel_data['channel_id'],))
        channel = cursor.fetchone()
        assert channel is not None
        
        # Check if videos were inserted
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        assert video_count == 2  # We had 2 videos in the sample data
        
        # Check if comments were inserted
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
        assert comment_count == 3  # We had 3 comments total in the sample data
        
        # Close connection
        conn.close()
    
    def test_get_channels_list(self, sqlite_db, sample_channel_data):
        """Test retrieving the list of channel names"""
        # First store some data
        sqlite_db.store_channel_data(sample_channel_data)
        
        # Get the list of channels
        channels = sqlite_db.get_channels_list()
        
        # Verify the list contains our test channel
        assert len(channels) == 1
        
        # Verify the format of the returned data (should be a list of dictionaries)
        assert isinstance(channels[0], dict)
        assert 'channel_id' in channels[0]
        assert 'channel_name' in channels[0]
        
        # Verify the content matches our sample data
        assert channels[0]['channel_id'] == sample_channel_data['channel_id']
        assert channels[0]['channel_name'] == sample_channel_data['channel_name']
    
    def test_get_channel_data(self, sqlite_db, sample_channel_data):
        """Test retrieving full channel data by ID"""
        # First store some data
        sqlite_db.store_channel_data(sample_channel_data)
        
        # Get the channel data by ID
        channel_data = sqlite_db.get_channel_data(sample_channel_data['channel_id'])
        
        # Verify the returned data
        assert channel_data is not None
        assert channel_data['channel_id'] == sample_channel_data['channel_id']
        assert 'channel_info' in channel_data
        assert channel_data['channel_info']['title'] == sample_channel_data['channel_name']
        
        # Check if videos were retrieved
        assert 'videos' in channel_data
        assert len(channel_data['videos']) == 2
        
        # Check if video details are correct
        video_ids = [v['id'] for v in channel_data['videos']]
        assert 'test_video_1' in video_ids
        assert 'test_video_2' in video_ids
    
    def test_get_channel_data_by_title(self, sqlite_db, sample_channel_data):
        """Test retrieving channel data by title instead of ID"""
        # First store some data
        sqlite_db.store_channel_data(sample_channel_data)
        
        # Get the channel data by title
        channel_data = sqlite_db.get_channel_data(sample_channel_data['channel_name'])
        
        # Verify the returned data
        assert channel_data is not None
        assert channel_data['channel_id'] == sample_channel_data['channel_id']
    
    def test_clear_cache(self, sqlite_db):
        """Test clearing database caches"""
        # Clear cache should return True on success
        result = sqlite_db.clear_cache()
        assert result is True
    
    def test_get_channel_id_by_title(self, sqlite_db, sample_channel_data):
        """Test retrieving a channel ID by title"""
        # First store some data
        sqlite_db.store_channel_data(sample_channel_data)
        
        # Get the channel ID by title
        channel_id = sqlite_db.get_channel_id_by_title(sample_channel_data['channel_name'])
        
        # Verify the returned ID
        assert channel_id == sample_channel_data['channel_id']
    
    def test_list_channels(self, sqlite_db, sample_channel_data):
        """Test listing all channels with their IDs and titles"""
        # First store some data
        sqlite_db.store_channel_data(sample_channel_data)
        
        # Get the list of channels
        channels = sqlite_db.list_channels()
        
        # Verify the returned list
        assert len(channels) == 1
        assert channels[0][0] == sample_channel_data['channel_id']
        assert channels[0][1] == sample_channel_data['channel_name']
    
    def test_factory_with_sqlite_shortname(self, temp_db_path, sample_channel_data, monkeypatch):
        """Test that the StorageFactory can handle the 'sqlite' shortname"""
        from src.storage.factory import StorageFactory
        from src.config import SQLITE_DB_PATH
        
        # Store some data for testing
        db = SQLiteDatabase(temp_db_path)
        db.store_channel_data(sample_channel_data)
        
        # Patch the SQLITE_DB_PATH to use our test database
        monkeypatch.setattr("src.config.SQLITE_DB_PATH", temp_db_path)
        
        # Get storage provider using 'sqlite' (lowercase, no "Database") as in the UI code
        storage_provider = StorageFactory.get_storage_provider("sqlite")
        
        # Verify it returns an instance of SQLiteDatabase
        assert isinstance(storage_provider, SQLiteDatabase)
        
        # Verify it works with the shortname
        channels = storage_provider.get_channels_list()
        
        # Check that we can get channels with the correct format
        assert len(channels) == 1
        assert isinstance(channels[0], dict)
        assert 'channel_id' in channels[0]
        assert 'channel_name' in channels[0]


if __name__ == '__main__':
    pytest.main()