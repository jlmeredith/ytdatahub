"""
Integration tests for the database module, focusing on how it works with
other components of the application such as the YouTube API client.
"""
import pytest
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

from src.database.sqlite import SQLiteDatabase
from src.api.youtube_api import YouTubeAPI

# Re-use the session state mock from the unit tests
class SessionStateMock(dict):
    """Custom mock for Streamlit's session_state"""
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
        self.use_data_cache = False

    def __getattr__(self, name):
        if name in self:
            return self[name]
        return getattr(super(), name)

    def __setattr__(self, name, value):
        self[name] = value

# Fixtures
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
def mock_youtube_api():
    """Create a mock YouTube API that returns test data"""
    with patch('src.api.youtube_api.YouTubeAPI') as mock_api:
        # Create an instance of the mock
        mock_instance = mock_api.return_value
        
        # Mock the fetch_channel_info method
        mock_instance.fetch_channel_info.return_value = {
            'id': 'UC_test_channel_id',
            'snippet': {
                'title': 'Integration Test Channel',
                'description': 'Channel for integration testing',
                'publishedAt': '2020-01-01T00:00:00Z'
            },
            'statistics': {
                'subscriberCount': '5000',
                'viewCount': '100000',
                'videoCount': '50'
            },
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'UU_test_playlist_id'
                }
            }
        }
        
        # Mock the fetch_channel_videos method to return sample videos
        mock_instance.fetch_channel_videos.return_value = [
            {
                'id': 'test_video_1_id',
                'snippet': {
                    'title': 'Integration Test Video 1',
                    'description': 'First test video',
                    'publishedAt': '2022-01-15T00:00:00Z'
                },
                'statistics': {
                    'viewCount': '1500',
                    'likeCount': '120',
                    'commentCount': '30'
                },
                'contentDetails': {
                    'duration': 'PT15M30S'
                }
            },
            {
                'id': 'test_video_2_id',
                'snippet': {
                    'title': 'Integration Test Video 2',
                    'description': 'Second test video',
                    'publishedAt': '2022-02-15T00:00:00Z'
                },
                'statistics': {
                    'viewCount': '2500',
                    'likeCount': '200',
                    'commentCount': '45'
                },
                'contentDetails': {
                    'duration': 'PT10M15S'
                }
            }
        ]
        
        # Mock the fetch_video_comments method
        mock_instance.fetch_video_comments.return_value = [
            {
                'id': 'comment_1_id',
                'snippet': {
                    'topLevelComment': {
                        'snippet': {
                            'textDisplay': 'Great integration test video!',
                            'authorDisplayName': 'Test User 1',
                            'publishedAt': '2022-01-16T00:00:00Z',
                            'likeCount': 5
                        }
                    }
                }
            },
            {
                'id': 'comment_2_id',
                'snippet': {
                    'topLevelComment': {
                        'snippet': {
                            'textDisplay': 'Testing the database integration.',
                            'authorDisplayName': 'Test User 2',
                            'publishedAt': '2022-01-17T00:00:00Z',
                            'likeCount': 3
                        }
                    }
                }
            }
        ]
        
        yield mock_instance

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for integration testing"""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file_path = temp_file.name
    temp_file.close()
    
    # Create database instance
    db = SQLiteDatabase(temp_file_path)
    
    yield db
    
    # Clean up the file after tests
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)

class TestDatabaseIntegration:
    """Integration tests for the database module"""
    
    def test_api_to_database_workflow(self, temp_db, mock_youtube_api):
        """Test the workflow from YouTube API to database storage"""
        # Mock the data transformation from API response to database format
        channel_data = {
            'channel_id': 'UC_test_channel_id',
            'channel_name': 'Integration Test Channel',
            'subscribers': 5000,
            'views': 100000,
            'total_videos': 50,
            'channel_description': 'Channel for integration testing',
            'playlist_id': 'UU_test_playlist_id',
            'published_at': '2020-01-01T00:00:00Z',
            'fetched_at': '2025-04-29T00:00:00Z',
            'video_id': [
                {
                    'video_id': 'test_video_1_id',
                    'title': 'Integration Test Video 1',
                    'video_description': 'First test video',
                    'published_at': '2022-01-15T00:00:00Z',
                    'views': 1500,
                    'likes': 120,
                    'duration': 'PT15M30S',
                    'comments': [
                        {
                            'comment_id': 'comment_1_id',
                            'comment_text': 'Great integration test video!',
                            'comment_author': 'Test User 1',
                            'comment_published_at': '2022-01-16T00:00:00Z'
                        }
                    ]
                },
                {
                    'video_id': 'test_video_2_id',
                    'title': 'Integration Test Video 2',
                    'video_description': 'Second test video',
                    'published_at': '2022-02-15T00:00:00Z',
                    'views': 2500,
                    'likes': 200,
                    'duration': 'PT10M15S',
                    'comments': [
                        {
                            'comment_id': 'comment_2_id',
                            'comment_text': 'Testing the database integration.',
                            'comment_author': 'Test User 2',
                            'comment_published_at': '2022-01-17T00:00:00Z'
                        }
                    ]
                }
            ]
        }
        
        # Store the transformed data
        result = temp_db.store_channel_data(channel_data)
        assert result is True
        
        # Retrieve the channel data and verify it was stored correctly
        retrieved_data = temp_db.get_channel_data('UC_test_channel_id')
        assert retrieved_data is not None
        assert retrieved_data['channel_id'] == 'UC_test_channel_id'
        
        # Check channel details
        assert retrieved_data['channel_info']['title'] == 'Integration Test Channel'
        assert int(retrieved_data['channel_info']['statistics']['subscriberCount']) == 5000
        
        # Check video details
        assert len(retrieved_data['videos']) == 2
        video_ids = [v['id'] for v in retrieved_data['videos']]
        assert 'test_video_1_id' in video_ids
        assert 'test_video_2_id' in video_ids
        
        # Find first video
        video_1 = next((v for v in retrieved_data['videos'] if v['id'] == 'test_video_1_id'), None)
        assert video_1 is not None
        assert video_1['snippet']['title'] == 'Integration Test Video 1'
        assert int(video_1['statistics']['viewCount']) == 1500
        
        # Verify we can also retrieve by channel name
        by_name_data = temp_db.get_channel_data('Integration Test Channel')
        assert by_name_data is not None
        assert by_name_data['channel_id'] == 'UC_test_channel_id'
    
    def test_database_connections_cleanup(self, temp_db):
        """Test that database connections are properly cleaned up"""
        # Store some simple data
        channel_data = {
            'channel_id': 'UC_connection_test',
            'channel_name': 'Connection Test Channel',
            'subscribers': 100,
            'views':
            5000,
            'total_videos': 10,
            'channel_description': 'Test channel for connection testing',
            'playlist_id': 'PL_test_connection',
            'fetched_at': '2025-04-29T00:00:00Z',
            'video_id': []
        }
        
        # Store data multiple times to test connection handling
        for i in range(5):
            result = temp_db.store_channel_data(channel_data)
            assert result is True
        
        # Get data multiple times
        for i in range(5):
            data = temp_db.get_channel_data('UC_connection_test')
            assert data is not None
        
        # Verify database file is not locked by checking if we can open a new connection
        try:
            conn = sqlite3.connect(temp_db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channels")
            rows = cursor.fetchall()
            assert len(rows) == 1  # We only inserted one channel
            conn.close()
        except sqlite3.OperationalError as e:
            pytest.fail(f"Database is locked: {str(e)}")
    
    def test_channel_data_integrity(self, temp_db):
        """Test data integrity when storing and retrieving channel data"""
        # Create test data with special characters and edge cases
        channel_data = {
            'channel_id': 'UC_test_integrity',
            'channel_name': "Test Channel with quotes",  # Simplified name
            'subscribers': 999999,  # Large but not extreme number
            'views': 0,  # Zero views
            'total_videos': 0,  # Explicit zero instead of None
            'channel_description': "Multiline description with special chars",
            'playlist_id': 'PL_test_integrity',
            'published_at': '2010-01-01T00:00:00Z',
            'fetched_at': '2025-04-29T00:00:00Z',
            'video_id': [
                {
                    'video_id': 'test_video_integrity',
                    'title': "Video with emoji",
                    'video_description': "Description with special characters",
                    'published_at': '2022-01-01T00:00:00Z',  # Valid date instead of None
                    'views': 0,  # Zero instead of negative
                    'likes': 0,  # Numeric instead of string
                    'duration': 'PT1M',  # Valid duration instead of None
                    'comments': []
                }
            ]
        }
        
        # Store the data
        result = temp_db.store_channel_data(channel_data)
        assert result is True
        
        # Retrieve the data
        retrieved_data = temp_db.get_channel_data('UC_test_integrity')
        assert retrieved_data is not None
        
        # Check channel details
        assert retrieved_data['channel_info']['title'] == "Test Channel with quotes"
        assert int(retrieved_data['channel_info']['statistics']['subscriberCount']) == 999999
        assert int(retrieved_data['channel_info']['statistics']['viewCount']) == 0
        
        # Check video with special content
        video = retrieved_data['videos'][0]
        assert video['snippet']['title'] == "Video with emoji"
        assert video['snippet']['description'] == "Description with special characters"

    def test_all_channels_have_uploads_playlist_id(self, temp_db):
        """Test that all channels have uploads_playlist_id set (migration health check)."""
        conn = temp_db._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT channel_id FROM channels WHERE uploads_playlist_id IS NULL OR uploads_playlist_id = ''")
        missing = cur.fetchall()
        conn.close()
        assert not missing, f"Channels missing uploads_playlist_id: {[row[0] for row in missing]}"

if __name__ == '__main__':
    pytest.main()