"""
Pytest fixtures for integration tests in the YouTube Data Hub application.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure project root is on path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import local utilities
from tests.utils.session_state_helper import fix_session_state_for_tests

@pytest.fixture(autouse=True)
def setup_session_state():
    """Automatically fix session state for all integration tests"""
    fix_session_state_for_tests()

# Import the YouTube API and other services
try:
    from src.api.youtube_api import YouTubeAPI
    from src.database.sqlite import SQLiteDatabase
except ImportError as e:
    print(f"Warning: Failed to import modules in conftest: {e}")


@pytest.fixture
def mock_youtube_api():
    """Create a mock YouTube API object."""
    # Create a mock without spec to avoid attribute errors
    mock_api = MagicMock()
    
    # Configure mock API to return standard test data
    mock_api.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
    
    # Mock channel data response
    mock_api.get_channel_info = MagicMock(return_value={
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': '10000',
        'views': '5000000',
        'total_videos': '50'
    })
    
    # Mock video data response
    mock_api.get_channel_videos = MagicMock(return_value={
        'channel_id': 'UC_test_channel',
        'video_id': [
            {
                'video_id': 'video123',
                'title': 'Test Video 1',
                'views': '15000',
                'published_at': '2023-01-01T00:00:00Z'
            },
            {
                'video_id': 'video456',
                'title': 'Test Video 2',
                'views': '25000',
                'published_at': '2023-01-02T00:00:00Z'
            }
        ]
    })
    
    # Mock comment data response
    mock_api.get_video_comments = MagicMock(return_value={
        'video_id': 'video123',
        'comments': [
            {
                'comment_id': 'comment1',
                'text': 'This is a test comment',
                'author': 'Test User',
                'likes': '10'
            }
        ]
    })
    
    return mock_api


@pytest.fixture
def mock_sqlite_db():
    """Create a mock SQLite database object."""
    # Create a mock without spec to avoid attribute errors
    mock_db = MagicMock()
    mock_db.store_channel_data = MagicMock(return_value=True)
    mock_db.store_video_data = MagicMock(return_value=True)
    mock_db.store_comment_data = MagicMock(return_value=True)
    return mock_db


@pytest.fixture
def mock_quota_service():
    """Create a mock quota service."""
    mock_quota = MagicMock()
    mock_quota.check_quota.return_value = True
    mock_quota.update_quota_usage.return_value = None
    return mock_quota


@pytest.fixture
def sample_channel_data():
    """Return sample channel data for testing."""
    return {
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': '10000',
        'views': '5000000',
        'total_videos': '50',
        'video_id': [
            {
                'video_id': 'video123',
                'title': 'Test Video 1',
                'views': '15000',
                'published_at': '2023-01-01T00:00:00Z',
                'comments': [
                    {
                        'comment_id': 'comment1',
                        'text': 'This is a test comment',
                        'author': 'Test User',
                        'likes': '10'
                    }
                ]
            }
        ]
    }
