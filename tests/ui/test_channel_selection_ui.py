"""
Tests for channel selection interface in the data collection UI.
"""
import pytest
import streamlit as st
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure working directory is correct for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ui.data_collection import render_data_collection_tab
from src.database.sqlite import SQLiteDatabase
from src.services.youtube_service import YouTubeService


class TestChannelSelectionUI:
    """Tests for the channel selection UI components."""

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

    @pytest.fixture
    def mock_st(self):
        """Create a mock of the streamlit module with all needed functions for UI testing."""
        mock = MagicMock()
        
        # Create mock methods that we need for testing
        mock.container = MagicMock()
        mock.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
        mock.write = MagicMock()
        mock.markdown = MagicMock()
        mock.header = MagicMock()
        mock.metric = MagicMock()
        mock.expander = MagicMock()
        mock.button = MagicMock()
        mock.success = MagicMock()
        mock.error = MagicMock()
        mock.info = MagicMock()
        
        # Create a mock session_state
        mock.session_state = {}
        
        return mock

    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_channel_selection_ui(self, mock_sqlite_db_class, mock_sqlite_db, mock_channel_data):
        """Test the channel selection UI workflow."""
        # Configure the mock database
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        
        # Set up Streamlit session state and mock out the Streamlit components
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
        st.session_state.collection_mode = "new_channel"
        st.session_state.debug_mode = True
        
        # Mock the API key - replacing st.text_input
        user_api_key = "mock_api_key"
        
        # Create a mock return value for convert_db_to_api_format
        api_formatted_data = {
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
        
        # Mock the specific UI components and database calls
        with patch("streamlit.text_input", return_value=user_api_key), \
             patch("streamlit.selectbox", return_value=("UC_test_channel", "Test Channel")), \
             patch("streamlit.button", return_value=True), \
             patch("src.ui.data_collection.convert_db_to_api_format", return_value=api_formatted_data), \
             patch("src.ui.data_collection.YouTubeService") as mock_service_class, \
             patch("streamlit.spinner"), \
             patch("streamlit.success"), \
             patch("streamlit.rerun"):
            # Test implementation would be here
            pass

    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.YouTubeService")
    def test_update_channel_tab_displays_channels(self, mock_youtube_service_class, mock_sqlite_db_class):
        """Test that the update channel tab properly displays the available channels."""
        # Configure mocks for the database and YouTube service
        mock_db = MagicMock()
        mock_sqlite_db_class.return_value = mock_db
        
        # Set up channel list in the mock database
        channel_list = [
            ("UC_test_channel", "Test Channel"),
            ("UC_another_channel", "Another Test Channel"),
            ("UC_third_channel", "Third Test Channel")
        ]
        mock_db.list_channels.return_value = channel_list
        
        # Set up streamlit session state for testing
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.debug_mode = True
        
        # Mock UI components that would be interacted with
        with patch("streamlit.text_input", return_value="mock_api_key"), \
             patch("streamlit.selectbox", return_value=channel_list[0]), \
             patch("streamlit.button", return_value=True), \
             patch("streamlit.error"), \
             patch("streamlit.success"), \
             patch("streamlit.info"), \
             patch("streamlit.rerun"):
            # Test implementation would be here
            pass
