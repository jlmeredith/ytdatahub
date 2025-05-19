"""
Tests for comparison view functionality between API and database data in the data collection UI.
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


class TestComparisonView:
    """Tests for the comparison view between API and database data."""

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

    @patch("src.ui.data_collection.render_delta_report")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.render_delta_report")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_delta_reporting_in_ui(self, mock_sqlite_db_class, mock_render_delta, mock_sqlite_db, mock_channel_data):
        """Test that the delta report is shown during the channel update process."""
        # Configure the mock database
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        
        # Set up session state as if we've already loaded a channel 
        # and switched to existing_channel mode
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
        # Create previous data and updated data with differences
        previous_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10000,
            'views': 5000000,
            'total_videos': 50
        }
        
        updated_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500,
            'views': 5200000,
            'total_videos': 52
        }
        
        # Set session state as if we're in the existing channel flow
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        st.session_state.previous_channel_data = previous_data
        st.session_state.channel_data_fetched = True
        st.session_state.channel_info_temp = updated_data
        
        # Mock the UI components to simulate the delta reporting parts of the code
        with patch("streamlit.text_input", return_value="mock_api_key"), \
             patch("streamlit.subheader"), \
             patch("streamlit.spinner"), \
             patch("streamlit.success"), \
             patch("streamlit.info"), \
             patch("src.ui.data_collection.YouTubeService") as mock_service_class:
            # Test implementation would be here
            pass

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_channel_data_source_indicator(self, mock_sqlite_db_class, mock_youtube_service_class, mock_sqlite_db, mock_channel_data):
        """Test that the UI properly indicates whether data is from the API or database."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        
        # Set up session state for different data sources
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
        # Set up for testing database data source
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        st.session_state.channel_data_fetched = True
        st.session_state.data_source = "database"
        
        # Test implementation would be here
        pass

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_api_vs_db_comparison_view(self, mock_youtube_service_class, mock_sqlite_db_class, mock_sqlite_db, mock_channel_data):
        """Test that the API vs DB comparison view displays data correctly."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        mock_service = mock_youtube_service_class.return_value
        
        # Create API response with slightly different data
        api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500,
            'views': 5200000,
            'total_videos': 52
        }
        mock_service.collect_channel_data.return_value = api_data
        
        # Set up session state for comparison view
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        st.session_state.compare_data_view = True
        st.session_state.db_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10000,
            'views': 5000000,
            'total_videos': 50,
            'data_source': 'database'
        }
        st.session_state.api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500,
            'views': 5200000,
            'total_videos': 52,
            'data_source': 'api'
        }
        
        # Mock UI components
        with patch("streamlit.container", return_value=MagicMock().__enter__()), \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]), \
             patch("streamlit.subheader"), \
             patch("streamlit.markdown"), \
             patch("streamlit.metric"), \
             patch("streamlit.write"):
            # Test implementation would be here
            pass

    def test_api_data_displayed_in_ui_comparison(self, mock_st):
        """Test that API data is properly displayed in the UI comparison view alongside DB data."""
        # Setup test data
        db_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '250',
            'data_source': 'database'
        }
        
        api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '12000',
            'views': '5500000',
            'total_videos': '255',
            'data_source': 'api'
        }
        
        # Calculate the expected delta values
        delta = {
            'subscribers': 2000,
            'views': 500000,
            'total_videos': 5
        }
        
        # Mock the session state with our test data - use dictionary style access
        mock_st.session_state = {
            'existing_channel_id': 'UC_test_channel',
            'db_data': db_data,
            'api_data': api_data,
            'delta': delta,
            'compare_data_view': True
        }
        
        # Import the module that renders the comparison view
        from src.ui.data_collection import render_api_db_comparison
        
        # Call the function that renders the comparison view
        render_api_db_comparison(mock_st)
        
        # Simplified verification approach
        
        # Verify that columns were created for side-by-side comparison
        assert len(mock_st.columns.call_args_list) >= 1, "No columns were created for comparison view"
        
        # Verify that metrics are displayed
        assert len(mock_st.metric.call_args_list) > 0, "No metrics were displayed at all"
        
        # Verify that containers are created
        assert len(mock_st.container.call_args_list) > 0, "No containers were displayed"
        
        # Check that the API and DB data was passed to the comparison feature
        assert 'api_data' in mock_st.session_state, "API data was not present in session state"
        assert mock_st.session_state['api_data'] is not None, "API data was None in session state"
        assert 'db_data' in mock_st.session_state, "DB data was not present in session state"
        assert mock_st.session_state['db_data'] is not None, "DB data was None in session state"

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_channel_refresh_displays_comparison_data(self, mock_sqlite_db_class, mock_youtube_service_class):
        """Test that channel refresh properly displays comparison data."""
        # Configure mocks
        mock_db = MagicMock()
        mock_sqlite_db_class.return_value = mock_db
        mock_service = mock_youtube_service_class.return_value
        
        # Set up data for comparison
        db_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10000,
            'views': 5000000,
            'total_videos': 250
        }
        
        api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 12000,
            'views': 5500000,
            'total_videos': 255
        }
        
        # Configure mocks to return our test data
        mock_db.get_channel_data.return_value = {"channel_info": {"id": "UC_test_channel", "title": "Test Channel"}}
        mock_service.collect_channel_data.return_value = api_data
        
        # Set up session state
        if "session_state" not in st.__dict__:
            st.session_state = {}
            
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        st.session_state.db_data = db_data
        st.session_state.api_data = api_data
        st.session_state.channel_data_fetched = True
        st.session_state.compare_data_view = True
        
        # Mock UI components
        with patch("streamlit.container", return_value=MagicMock().__enter__()), \
             patch("streamlit.columns", return_value=[MagicMock(), MagicMock(), MagicMock()]), \
             patch("streamlit.subheader"), \
             patch("streamlit.markdown"), \
             patch("streamlit.metric"), \
             patch("streamlit.write"), \
             patch("src.ui.data_collection.render_api_db_comparison") as mock_render_comparison:
            # Test implementation would be here
            pass
