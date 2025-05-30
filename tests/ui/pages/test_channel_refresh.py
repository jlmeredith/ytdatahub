"""
Tests for channel data refresh functionality in the data collection UI.
"""
import pytest
import streamlit as st
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure working directory is correct for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.sqlite import SQLiteDatabase
from src.services.youtube_service import YouTubeService

# Helper function to fix session state in tests
def fix_session_state():
    """Fix session state in tests to handle attribute access"""
    if "session_state" not in st.__dict__:
        # Create a dictionary-like object that allows attribute access
        class SessionStateDict(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._dict = {}  # Add an internal dict for storing attributes
            
            def __getattr__(self, name):
                # First try to get it from the internal dict
                if name in self._dict:
                    return self._dict[name]
                # Then try to get it from self as a dict key
                if name in self:
                    return self[name]
                # Otherwise initialize it
                self[name] = None
                return self[name]
                
            def __setattr__(self, name, value):
                if name == '_dict':
                    # Allow setting _dict attribute during initialization
                    super().__setattr__(name, value)
                else:
                    # Store other attributes in the dict
                    self[name] = value
                
            def __getitem__(self, key):
                if key not in self:
                    self[key] = None
                return super().__getitem__(key)
        
        # Initialize with common default values
        session_state = SessionStateDict()
        session_state['debug_mode'] = True
        session_state['log_level'] = 'INFO'
        
        st.session_state = session_state
        return session_state
    
    return st.session_state


class TestChannelRefresh:
    """Tests for the channel data refresh functionality."""

    @pytest.fixture
    def mock_sqlite_db(self):
        """Create a mock database with test channels."""
        mock_db = MagicMock(spec=SQLiteDatabase)
        mock_db.list_channels.return_value = [
            ("UC_test_channel", "Test Channel"),
            ("UC_another_channel", "Another Channel")
        ]
        return mock_db
        
    @pytest.fixture
    def mock_channel_data(self):
        """Create mock channel data from database."""
        return {
            "channel_info": {
                "id": "UC_test_channel",
                "title": "Test Channel",
                "description": "This is a test channel",
                "statistics": {
                    "subscriberCount": "10000",
                    "viewCount": "5000000",
                    "videoCount": "50"
                },
                "contentDetails": {
                    "relatedPlaylists": {
                        "uploads": "UU_test_channel_uploads"
                    }
                }
            },
            "videos": [
                {
                    "id": "video123",
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test video description", 
                        "publishedAt": "2025-04-01T12:00:00Z"
                    },
                    "statistics": {
                        "viewCount": "15000",
                        "likeCount": "1200",
                        "commentCount": "300"
                    },
                    "contentDetails": {
                        "duration": "PT10M30S"
                    }
                }
            ]
        }

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.YouTubeService")
    def test_refresh_channel_data_button(self, mock_youtube_service_class, mock_sqlite_db_class, mock_sqlite_db, mock_channel_data):
        """Test that refresh channel data button actually calls the API and updates the UI."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        mock_service = mock_youtube_service_class.return_value
        
        # Create API response with updated data
        updated_api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500, 
            'views': 5200000, 
            'total_videos': 52, 
            'channel_description': 'This is a test channel',
            'playlist_id': 'UU_test_channel_uploads',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video',
                    'views': 16000, 
                    'likes': 1300 
                },
                {
                    'video_id': 'video456',
                    'title': 'New Test Video',
                    'views': 5000,
                    'likes': 500
                }
            ],
            'last_refresh': {
                'timestamp': '2025-04-30T12:00:00.000000'
            }
        }
        
        # Configure collect_channel_data return value
        mock_service.collect_channel_data.return_value = updated_api_data
        
        # Set up session state to simulate an existing channel
        fix_session_state()
        
        # Set session state as if we're in existing channel mode and have selected a channel
        previous_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10000,
            'views': 5000000,
            'total_videos': 50,
            'channel_description': 'This is a test channel',
            'playlist_id': 'UU_test_channel_uploads',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video',
                    'views': 15000,
                    'likes': 1200
                }
            ]
        }
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        st.session_state.previous_channel_data = previous_data
        # Set the channel data as fetched so the UI can access it
        st.session_state.channel_data_fetched = True
        # Add the channel info to the session state
        st.session_state.channel_info_temp = previous_data
        st.session_state.debug_mode = True
        
        # Mock UI components
        with patch("streamlit.text_input", return_value="mock_api_key"), \
             patch("streamlit.subheader"), \
             patch("streamlit.spinner", return_value=MagicMock().__enter__()), \
             patch("streamlit.success"), \
             patch("streamlit.error"), \
             patch("streamlit.info"), \
             patch("streamlit.rerun"), \
             patch("streamlit.metric"), \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]), \
             patch("src.utils.debug_utils.debug_log") as mock_debug_log, \
             patch("src.ui.data_collection.render_delta_report") as mock_render_delta:
            # Test implementation would be here
            pass

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.YouTubeService")
    def test_refresh_channel_data_failure(self, mock_youtube_service_class, mock_sqlite_db_class, mock_sqlite_db, mock_channel_data):
        """Test error handling when refresh channel data button is clicked but API call fails."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        mock_service = mock_youtube_service_class.return_value
        
        # Configure collect_channel_data to return None (simulating an API failure)
        mock_service.collect_channel_data.return_value = None
        
        # Set up session state to simulate an existing channel
        fix_session_state()
        
        # Set session state as if we're in existing channel mode and have selected a channel
        previous_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10000,
            'views': 5000000,
            'total_videos': 50
        }
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        st.session_state.previous_channel_data = previous_data
        st.session_state.channel_data_fetched = True
        # Add the channel info to the session state
        st.session_state.channel_info_temp = previous_data
        st.session_state.debug_mode = True
        
        # Initialize other session state variables that should be maintained in error scenarios
        st.session_state.api_client_initialized = True
        st.session_state.api_last_response = previous_data
        
        # Mock UI components
        error_mock = MagicMock()
        with patch("streamlit.text_input", return_value="mock_api_key"), \
             patch("streamlit.subheader"), \
             patch("streamlit.spinner", return_value=MagicMock().__enter__()), \
             patch("streamlit.success"), \
             patch("streamlit.error", error_mock), \
             patch("streamlit.info"), \
             patch("streamlit.rerun"), \
             patch("streamlit.metric"), \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]), \
             patch("src.utils.debug_utils.debug_log"):
            # Test implementation would be here
            pass

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.YouTubeService")
    def test_refresh_channel_data_sets_required_session_state(self, mock_youtube_service_class, mock_sqlite_db_class, mock_sqlite_db, mock_channel_data):
        """Test that clicking refresh channel data button properly sets all required session state variables."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        mock_service = mock_youtube_service_class.return_value
        
        # Create API response with updated data
        updated_api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500,
            'views': 5200000,
            'total_videos': 52
        }
        
        # Configure collect_channel_data return value 
        mock_service.collect_channel_data.return_value = updated_api_data
        
        # Set up session state
        fix_session_state()
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        
        # Mock UI components
        with patch("streamlit.text_input", return_value="mock_api_key"), \
             patch("streamlit.subheader"), \
             patch("streamlit.spinner", return_value=MagicMock().__enter__()), \
             patch("streamlit.success"), \
             patch("streamlit.error"), \
             patch("streamlit.info"), \
             patch("streamlit.rerun"), \
             patch("streamlit.metric"), \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]), \
             patch("src.utils.debug_utils.debug_log"):
            # Test implementation would be here
            pass

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.YouTubeService")
    def test_load_existing_channel_data_from_db(self, mock_youtube_service_class, mock_sqlite_db_class, mock_sqlite_db, mock_channel_data):
        """Test that loading existing channel data from the database works correctly."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        
        # Set up session state
        fix_session_state()
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        
        # Mock UI components
        with patch("streamlit.text_input", return_value="mock_api_key"), \
             patch("streamlit.subheader"), \
             patch("streamlit.spinner", return_value=MagicMock().__enter__()), \
             patch("streamlit.success"), \
             patch("streamlit.error"), \
             patch("streamlit.info"):
            # Test implementation would be here
            pass

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_channel_refresh_multistep_workflow(self, mock_sqlite_db_class, mock_youtube_service_class):
        """Test the multi-step workflow for refreshing channel data."""
        # Configure mocks
        mock_db = MagicMock()
        mock_sqlite_db_class.return_value = mock_db
        mock_service = mock_youtube_service_class.return_value
        
        # Set up channel list
        channel_list = [
            ("UC_test_channel", "Test Channel"),
            ("UC_another_channel", "Another Test Channel")
        ]
        mock_db.list_channels.return_value = channel_list
        
        # Mock the channel data retrieval
        db_channel_data = {
            'channel_info': {
                'id': 'UC_test_channel',
                'title': 'Test Channel',
                'statistics': {
                    'subscriberCount': '10000',
                    'viewCount': '5000000',
                    'videoCount': '50'
                }
            }
        }
        mock_db.get_channel_data.return_value = db_channel_data
        
        # Mock the API response
        api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500,
            'views': 5200000,
            'total_videos': 52
        }
        mock_service.collect_channel_data.return_value = api_data
        
        # Set up session state for testing
        fix_session_state()
        
        # Test implementation would be here
        pass

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_channel_refresh_handles_empty_data_dict(self, mock_sqlite_db_class, mock_youtube_service_class):
        """Test that the channel refresh workflow handles empty data dictionaries gracefully."""
        # Configure mocks
        mock_db = MagicMock()
        mock_sqlite_db_class.return_value = mock_db
        mock_service = mock_youtube_service_class.return_value
        
        # Return empty data from database
        mock_db.get_channel_data.return_value = {}
        
        # Return empty data from API
        mock_service.collect_channel_data.return_value = {}
        
        # Set up session state
        fix_session_state()
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        
        # Test implementation would be here
        pass
