"""
Pytest configuration and fixtures for YTDataHub tests.
"""
import os
import json
import pytest
from unittest.mock import MagicMock, patch

# Create a Streamlit session state mock that behaves like a proper object
class SessionStateMock(dict):
    """A mock for streamlit.session_state that allows attribute access"""
    def __getattr__(self, name):
        if name not in self:
            self[name] = False
        return self[name]
    
    def __setattr__(self, name, value):
        self[name] = value


@pytest.fixture
def mock_youtube_api():
    """
    Fixture that provides a mock YouTube API object
    """
    mock_api = MagicMock()
    
    # Set up mock return values for common methods
    mock_api.get_channel_info.return_value = {
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': '10000',
        'views': '5000000',
        'total_videos': '250',
        'channel_description': 'This is a test channel',
        'playlist_id': 'PL_test_playlist',
    }
    
    # Mock video data
    mock_api.get_channel_videos.return_value = {
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': '10000',
        'views': '5000000',
        'total_videos': '250',
        'channel_description': 'This is a test channel',
        'playlist_id': 'PL_test_playlist',
        'video_id': [
            {
                'video_id': 'video123',
                'title': 'Test Video 1',
                'video_description': 'Test video description',
                'published_at': '2025-04-01T12:00:00Z',
                'published_date': '2025-04-01',
                'views': '15000',
                'likes': '1200',
                'comment_count': '300',
                'duration': 'PT10M30S',
                'thumbnails': 'https://example.com/thumb1.jpg',
                'comments': []
            },
            {
                'video_id': 'video456',
                'title': 'Test Video 2',
                'video_description': 'Another test video',
                'published_at': '2025-04-15T15:30:00Z',
                'published_date': '2025-04-15',
                'views': '25000',
                'likes': '2000',
                'comment_count': '500',
                'duration': 'PT15M45S',
                'thumbnails': 'https://example.com/thumb2.jpg',
                'comments': []
            }
        ],
        'videos_fetched': 2,
        'videos_unavailable': 0
    }
    
    # Mock comment data
    mock_api.get_video_comments.return_value = {
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': '10000',
        'views': '5000000',
        'total_videos': '250',
        'channel_description': 'This is a test channel',
        'playlist_id': 'PL_test_playlist',
        'video_id': [
            {
                'video_id': 'video123',
                'title': 'Test Video 1',
                'video_description': 'Test video description',
                'published_at': '2025-04-01T12:00:00Z',
                'published_date': '2025-04-01',
                'views': '15000',
                'likes': '1200',
                'comment_count': '300',
                'duration': 'PT10M30S',
                'thumbnails': 'https://example.com/thumb1.jpg',
                'comments': [
                    {
                        'comment_id': 'comment123',
                        'comment_text': 'Great video!',
                        'comment_author': 'Test User 1',
                        'comment_published_at': '2025-04-02T10:00:00Z',
                        'like_count': '50'
                    },
                    {
                        'comment_id': 'comment456',
                        'comment_text': 'Very informative',
                        'comment_author': 'Test User 2',
                        'comment_published_at': '2025-04-03T14:30:00Z',
                        'like_count': '30'
                    }
                ]
            },
            {
                'video_id': 'video456',
                'title': 'Test Video 2',
                'video_description': 'Another test video',
                'published_at': '2025-04-15T15:30:00Z',
                'published_date': '2025-04-15',
                'views': '25000',
                'likes': '2000',
                'comment_count': '500',
                'duration': 'PT15M45S',
                'thumbnails': 'https://example.com/thumb2.jpg',
                'comments': [
                    {
                        'comment_id': 'comment789',
                        'comment_text': 'Nice content!',
                        'comment_author': 'Test User 3',
                        'comment_published_at': '2025-04-16T09:15:00Z',
                        'like_count': '45'
                    }
                ]
            }
        ],
        'videos_fetched': 2,
        'videos_unavailable': 0,
        'comment_stats': {
            'total_comments': 3,
            'videos_with_comments': 2,
            'videos_with_disabled_comments': 0,
            'videos_with_errors': 0
        }
    }
    
    # Mock for resolving channel URLs
    mock_api.resolve_custom_channel_url.return_value = 'UC_test_channel'
    
    return mock_api


@pytest.fixture
def mock_sqlite_db():
    """
    Fixture that provides a mock SQLite database
    """
    mock_db = MagicMock()
    
    # Set up mock return values for common methods
    mock_db.get_channel_list.return_value = [
        {'name': 'Test Channel 1', 'id': 'UC_test_channel1'},
        {'name': 'Test Channel 2', 'id': 'UC_test_channel2'}
    ]
    
    mock_db.get_channel_data.return_value = {
        'channel_info': {
            'id': 'UC_test_channel',
            'title': 'Test Channel',
            'subscribers': '10000',
            'viewCount': '5000000',
            'videoCount': '250',
            'description': 'This is a test channel'
        },
        'videos': [
            {
                'id': 'video123',
                'snippet': {
                    'title': 'Test Video 1',
                    'description': 'Test video description',
                    'publishedAt': '2025-04-01T12:00:00Z'
                },
                'statistics': {
                    'viewCount': '15000',
                    'likeCount': '1200',
                    'commentCount': '300'
                },
                'contentDetails': {
                    'duration': 'PT10M30S'
                }
            }
        ]
    }
    
    # Mock save methods to return True (success)
    mock_db.save_channel_data.return_value = True
    mock_db.save_channel.return_value = True
    mock_db.save_video.return_value = True
    mock_db.save_comments.return_value = True
    
    return mock_db


@pytest.fixture
def sample_channel_data():
    """
    Fixture providing sample channel data for testing
    """
    return {
        'channel_id': 'UC_test_channel',
        'channel_name': 'Test Channel',
        'subscribers': '10000',
        'views': '5000000',
        'total_videos': '250',
        'channel_description': 'This is a test channel',
        'playlist_id': 'PL_test_playlist',
        'video_id': [
            {
                'video_id': 'video123',
                'title': 'Test Video 1',
                'video_description': 'Test video description',
                'published_at': '2025-04-01T12:00:00Z',
                'published_date': '2025-04-01',
                'views': '15000',
                'likes': '1200',
                'comment_count': '300',
                'duration': 'PT10M30S',
                'thumbnails': 'https://example.com/thumb1.jpg',
                'comments': [
                    {
                        'comment_id': 'comment123',
                        'comment_text': 'Great video!',
                        'comment_author': 'Test User 1',
                        'comment_published_at': '2025-04-02T10:00:00Z',
                        'like_count': '50'
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_collection_options():
    """
    Fixture providing sample collection options for testing
    """
    return {
        'fetch_channel_data': True,
        'fetch_videos': True,
        'fetch_comments': True,
        'max_videos': 50,
        'max_comments_per_video': 10
    }


# Create a better patch for streamlit to prevent st.xxx commands from failing in tests
@pytest.fixture(autouse=True)
def mock_streamlit():
    """
    Fixture to mock all streamlit functions to prevent failures during testing
    """
    # Create a session state mock that behaves like an object
    session_state_mock = SessionStateMock()
    session_state_mock.debug_mode = False
    
    # We'll use a context manager with fewer nested patches to avoid syntax error
    with patch('streamlit.text', return_value=None):
        with patch('streamlit.write', return_value=None):
            with patch('streamlit.title', return_value=None):
                with patch('streamlit.header', return_value=None):
                    with patch('streamlit.subheader', return_value=None):
                        with patch('streamlit.sidebar', return_value=MagicMock()):
                            with patch('streamlit.session_state', session_state_mock):
                                with patch('streamlit.progress', return_value=MagicMock()):
                                    with patch('streamlit.spinner', return_value=MagicMock().__enter__.return_value):
                                        with patch('streamlit.error', return_value=None):
                                            with patch('streamlit.warning', return_value=None):
                                                with patch('streamlit.info', return_value=None):
                                                    with patch('streamlit.success', return_value=None):
                                                        with patch('streamlit.empty', return_value=MagicMock()):
                                                            yield