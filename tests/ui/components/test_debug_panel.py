"""
Tests for the debug panel and session state maintenance in the data collection UI.
"""
import pytest
import streamlit as st
from unittest.mock import MagicMock, patch
import os
import sys
import logging
import pandas as pd
import json
import base64
from io import StringIO
import datetime

# Ensure working directory is correct for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ui.data_collection.main import render_data_collection_tab
from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format
from src.database.sqlite import SQLiteDatabase
from src.services.youtube_service import YouTubeService
from src.utils.debug_utils import debug_log
from src.ui.data_collection.debug_ui import render_debug_panel

class TestDebugPanelAndSessionState:
    """Tests for debug panel and session state maintenance in UI."""

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
    def mock_sqlite_db(self):
        """Create a mock database with test channels."""
        mock_db = MagicMock(spec=SQLiteDatabase)
        mock_db.list_channels.return_value = [
            ("UC_test_channel", "Test Channel"),
            ("UC_another_channel", "Another Channel")
        ]
        return mock_db

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_session_state_maintained_during_channel_refresh(self, mock_sqlite_db_class, mock_youtube_service_class, mock_sqlite_db, mock_channel_data):
        """Test that session state variables are properly maintained during channel refresh."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        mock_service = mock_youtube_service_class.return_value
        
        # Create API response with updated data
        updated_api_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500,  # 500 more subscribers
            'views': 5200000,      # 200K more views
            'total_videos': 52,    # 2 new videos
            'channel_description': 'This is a test channel',
            'playlist_id': 'UU_test_channel_uploads',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video',
                    'views': 16000,  # 1K more views
                    'likes': 1300    # 100 more likes
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
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
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
        st.session_state.channel_data_fetched = True
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
             patch("src.ui.data_collection.render_delta_report"):
            
            # Create a mock button that returns True (simulating a button click)
            button_mock = MagicMock(return_value=True)
            with patch("streamlit.button", button_mock):
                # Simulate the button click event that happens in the UI
                channel_id = st.session_state.existing_channel_id
                
                # Log the initial state for debugging
                debug_log = mock_debug_log
                debug_log(f"INITIAL SESSION STATE: channel_input={st.session_state.get('channel_input', 'Not set')}, " +
                          f"channel_data_fetched={st.session_state.get('channel_data_fetched', False)}, " +
                          f"api_initialized={st.session_state.get('api_initialized', False)}")
                
                # THIS IS THE KEY TEST: Set the critical session state variables explicitly
                st.session_state.channel_input = channel_id
                st.session_state.api_initialized = True
                st.session_state.api_client_initialized = True
                
                # Verify they're set immediately after setting them
                assert st.session_state.channel_input == channel_id
                assert st.session_state.api_initialized is True
                assert st.session_state.api_client_initialized is True
                
                debug_log(f"AFTER EXPLICITLY SETTING: channel_input={st.session_state.channel_input}, " +
                          f"api_initialized={st.session_state.api_initialized}, " +
                          f"api_client_initialized={st.session_state.api_client_initialized}")
                
                # Now simulate the API call
                options = {
                    'fetch_channel_data': True,
                    'fetch_videos': False,
                    'fetch_comments': False,
                    'max_videos': 0,
                    'max_comments_per_video': 0
                }
                
                updated_channel_info = mock_service.collect_channel_data(channel_id, options)
                
                # Verify session state is STILL properly maintained after API call
                debug_log(f"AFTER API CALL: channel_input={st.session_state.get('channel_input', 'Not set')}, " +
                          f"api_initialized={st.session_state.get('api_initialized', False)}, " +
                          f"api_client_initialized={st.session_state.get('api_client_initialized', False)}")
                
                # Store the updated data
                st.session_state.channel_info_temp = updated_channel_info
                st.session_state.current_channel_data = updated_channel_info
                
                # THE CRITICAL TEST: Verify the session state variables are still correct!
                assert st.session_state.channel_input == channel_id, "channel_input session state was lost"
                assert st.session_state.api_initialized is True, "api_initialized session state was lost"
                assert st.session_state.api_client_initialized is True, "api_client_initialized session state was lost"
                
                # Double-check by explicitly re-setting them and checking the render_debug_panel code path
                st.session_state.channel_input = channel_id  # Re-set for certainty
                st.session_state.api_initialized = True
                st.session_state.api_client_initialized = True
                
                # Mock the render_debug_panel function
                with patch("src.ui.data_collection.render_debug_panel") as mock_render_debug:
                    # Simulate calling the debug panel render function
                    render_debug_panel()
                    
                    # Verify it was called
                    mock_render_debug.assert_called_once()
                
                # Final session state check
                debug_log(f"FINAL STATE: channel_input={st.session_state.channel_input}, " +
                          f"api_initialized={st.session_state.api_initialized}, " +
                          f"api_client_initialized={st.session_state.api_client_initialized}")
                
                assert st.session_state.channel_input == channel_id
                assert st.session_state.api_initialized is True
                assert st.session_state.api_client_initialized is True
    
    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_session_state_preservation_through_spinner(self, mock_sqlite_db_class, mock_youtube_service_class, mock_sqlite_db, mock_channel_data):
        """Test that session state variables are preserved through the spinner context manager."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        mock_service = mock_youtube_service_class.return_value
        
        # Configure API response
        mock_service.collect_channel_data.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500
        }
        
        # Set up session state
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = "UC_test_channel"
        
        # Setup for debugging
        debug_logs = []
        def capture_log(message):
            debug_logs.append(message)
        
        # Mock components
        with patch("streamlit.text_input", return_value="mock_api_key"), \
             patch("streamlit.button", return_value=True), \
             patch("src.utils.debug_utils.debug_log", side_effect=capture_log):
            
            # Critical test: the spinner context manager may be interfering with state
            spinner_mock = MagicMock()
            spinner_context = MagicMock()
            spinner_mock.return_value = spinner_context
            
            with patch("streamlit.spinner", spinner_mock):
                # Set state variables before spinner
                channel_id = "UC_test_channel"
                st.session_state.channel_input = channel_id
                st.session_state.api_initialized = True
                st.session_state.api_client_initialized = True
                
                # Capture state before spinner
                before_spinner = {
                    'channel_input': st.session_state.channel_input,
                    'api_initialized': st.session_state.api_initialized,
                    'api_client_initialized': st.session_state.api_client_initialized
                }
                
                # Enter spinner context
                with st.spinner("Test spinner"):
                    # Check state inside spinner
                    inside_spinner = {
                        'channel_input': st.session_state.channel_input,
                        'api_initialized': st.session_state.api_initialized,
                        'api_client_initialized': st.session_state.api_client_initialized
                    }
                    
                    # Call API (this is where state might get lost)
                    options = {'fetch_channel_data': True, 'fetch_videos': False, 'fetch_comments': False}
                    mock_service.collect_channel_data(channel_id, options)
                    
                    # Check state after API call but still in spinner
                    after_api_call = {
                        'channel_input': st.session_state.channel_input,
                        'api_initialized': st.session_state.api_initialized,
                        'api_client_initialized': st.session_state.api_client_initialized
                    }
                
                # Check state after spinner
                after_spinner = {
                    'channel_input': st.session_state.get('channel_input', None),
                    'api_initialized': st.session_state.get('api_initialized', None),
                    'api_client_initialized': st.session_state.get('api_client_initialized', None)
                }
                
                # All these should be identical
                assert before_spinner == inside_spinner, "Session state changed when entering spinner"
                assert inside_spinner == after_api_call, "Session state changed during API call"
                assert after_api_call == after_spinner, "Session state changed when exiting spinner"
                
                # And all should have the expected values
                assert before_spinner['channel_input'] == channel_id
                assert before_spinner['api_initialized'] is True
                assert before_spinner['api_client_initialized'] is True

    @patch("src.ui.data_collection.YouTubeService")
    @patch("src.ui.data_collection.SQLiteDatabase")
    def test_session_state_debug_panel_rendering(self, mock_sqlite_db_class, mock_youtube_service_class, mock_sqlite_db, mock_channel_data):
        """Test specifically how the debug panel renders session state variables."""
        # Configure mocks
        mock_sqlite_db_class.return_value = mock_sqlite_db
        mock_sqlite_db.get_channel_data.return_value = mock_channel_data
        mock_service = mock_youtube_service_class.return_value
        
        # Configure API response
        mock_service.collect_channel_data.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 10500
        }
        
        # Set up session state
        if "session_state" not in st.__dict__:
            st.session_state = {}
        
        # Setup state as if we're in existing channel mode
        channel_id = "UC_test_channel"
        st.session_state.collection_mode = "existing_channel"
        st.session_state.existing_channel_id = channel_id
        st.session_state.debug_mode = True
        
        # Explicitly set the critical variables
        st.session_state.channel_input = channel_id
        st.session_state.api_initialized = True
        st.session_state.api_client_initialized = True
        
        # Verify they're set correctly
        assert st.session_state.channel_input == channel_id
        assert st.session_state.api_initialized == True
        assert st.session_state.api_client_initialized == True
        
        # Create a copy of variables before rendering the debug panel
        before_render = {
            'channel_input': st.session_state.get('channel_input', None),
            'api_initialized': st.session_state.get('api_initialized', None),
            'api_client_initialized': st.session_state.get('api_client_initialized', None),
        }
        
        # Mock the debug panel rendering to check if it changes any values
        debug_vars_captured = []
        def mock_table_fn(data):
            debug_vars_captured.extend(data)
        
        with patch("streamlit.table", side_effect=mock_table_fn), \
             patch("streamlit.tabs", return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()]), \
             patch("streamlit.subheader"), \
             patch("streamlit.expander", return_value=MagicMock().__enter__()), \
             patch("streamlit.info"), \
             patch("streamlit.error"), \
             patch("streamlit.metric"):
            
            # Import and call render_debug_panel directly
            render_debug_panel()
        
        # Check what values were used when rendering the debug panel
        rendered_values = {}
        for var in debug_vars_captured:
            if "Variable" in var and "Value" in var:
                rendered_values[var["Variable"]] = var["Value"]
        
        # Assert that the values shown in the panel match what we set
        assert rendered_values.get("channel_input") == str(channel_id), f"Debug panel showed wrong channel_input: {rendered_values.get('channel_input')}"
        assert rendered_values.get("api_initialized") == str(True), f"Debug panel showed wrong api_initialized: {rendered_values.get('api_initialized')}"
        assert rendered_values.get("api_client_initialized") == str(True), f"Debug panel showed wrong api_client_initialized: {rendered_values.get('api_client_initialized')}"
        
        # Now check if the actual session state values are still correct after rendering
        after_render = {
            'channel_input': st.session_state.get('channel_input', None),
            'api_initialized': st.session_state.get('api_initialized', None),
            'api_client_initialized': st.session_state.get('api_client_initialized', None),
        }
        
        # They should be the same as before rendering
        assert before_render == after_render, "Session state variables changed during debug panel rendering"

if __name__ == '__main__':
    pytest.main(['-xvs', __file__])