"""
Tests for the channel refresh UI in data collection.
"""
import pytest
import streamlit as st
import pandas as pd
from unittest.mock import patch, MagicMock
from src.ui.data_collection.channel_refresh_ui import channel_refresh_section, refresh_channel_data
from src.database.sqlite import SQLiteDatabase

@pytest.fixture
def mock_setup():
    """Prepare mocks for testing."""
    with patch("src.ui.data_collection.channel_refresh_ui.st") as mock_st, \
         patch("src.ui.data_collection.channel_refresh_ui.debug_log") as mock_debug_log, \
         patch("src.database.sqlite.SQLiteDatabase") as mock_db_class:
        
        # Mock YouTube service
        mock_youtube_service = MagicMock()
        
        # Set up a clean session state
        mock_st.session_state = {}
        
        # Mock columns to return two column objects for display_comparison_results
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]
        
        # Set up data
        test_data = {
            'db_data': {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'subscribers': 10000,
                'views': 5000000,
                'total_videos': 50,
            },
            'api_data': {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'subscribers': 10500, 
                'views': 5200000,
                'total_videos': 52,
            }
        }
        
        mock_youtube_service.update_channel_data.return_value = test_data
        mock_youtube_service.get_channels_list.return_value = [
            {'channel_id': 'UC_test_channel', 'channel_name': 'Test Channel'}
        ]
        
        yield mock_st, mock_youtube_service, mock_debug_log

class TestChannelRefreshUI:
    """Tests for the channel refresh UI."""
    
    def test_refresh_workflow_session_state_initialization(self, mock_setup):
        """Test that the session state is properly initialized in the refresh workflow."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # First call to initialize workflow step
        channel_refresh_section(mock_youtube_service)
        
        # Verify refresh_workflow_step was initialized correctly
        assert 'refresh_workflow_step' in mock_st.session_state
        assert mock_st.session_state.get('refresh_workflow_step') in [1, 2]  # Accept either 1 or 2
    
    def test_compare_with_api_button_click(self, mock_setup):
        """Test clicking the 'Compare with YouTube API' button."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # Set up session state for step 1 
        mock_st.session_state = {'refresh_workflow_step': 1}
        
        # Mock button click
        mock_st.button.return_value = True
        
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_spinner.__enter__ = MagicMock()
        mock_spinner.__exit__ = MagicMock()
        mock_st.spinner.return_value = mock_spinner
        
        # Run the function with button click simulation
        channel_refresh_section(mock_youtube_service)
        
        # Verify update_channel_data was called
        mock_youtube_service.update_channel_data.assert_called_once()
        
        # Check that session state was updated correctly
        assert mock_st.session_state.get('db_data') is not None
        assert mock_st.session_state.get('api_data') is not None
        assert mock_st.session_state.get('refresh_workflow_step') == 2
        assert mock_st.session_state.get('comparison_attempted') is True
    
    def test_missing_data_causes_warning(self, mock_setup):
        """Test that missing data causes a warning."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # Set up session state to simulate after clicking Compare button
        # but with missing data (this is the problematic state we're fixing)
        mock_st.session_state = {
            'refresh_workflow_step': 2,
            'comparison_attempted': True,
            'db_data': None,  # Missing data
            'api_data': {},    # Empty data
            'existing_channel_id': 'UC_test_channel'
        }
        
        # Run the function
        channel_refresh_section(mock_youtube_service)
        
        # Verify warning was displayed
        mock_st.warning.assert_called_once_with("Missing data for comparison. Please try the comparison again.")

    def test_empty_data_causes_warning(self, mock_setup):
        """Test that empty data dictionaries cause a warning."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # Set up session state with empty data dictionaries
        mock_st.session_state = {
            'refresh_workflow_step': 2,
            'comparison_attempted': True,
            'db_data': {},  # Empty data
            'api_data': {},  # Empty data
            'existing_channel_id': 'UC_test_channel'
        }
        
        # Run the function
        channel_refresh_section(mock_youtube_service)
        
        # Verify warning was displayed
        mock_st.warning.assert_called_once_with("Missing data for comparison. Please try the comparison again.")

    def test_critical_session_state_variables_set(self, mock_setup):
        """Test that critical session state variables are set when processing valid data."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # Set up session state for step 2 with valid data
        mock_st.session_state = {
            'refresh_workflow_step': 2,
            'comparison_attempted': True,
            'db_data': {'channel_id': 'UC_test_channel', 'subscribers': 10000},
            'api_data': {'channel_id': 'UC_test_channel', 'subscribers': 10500},
            'existing_channel_id': 'UC_test_channel'
        }
        
        # Run the function
        channel_refresh_section(mock_youtube_service)
        
        # Verify the critical session state variables are set
        assert mock_st.session_state.get('channel_input') == 'UC_test_channel'
        assert mock_st.session_state.get('api_initialized') is True
        assert mock_st.session_state.get('api_client_initialized') is True
        
    def test_reproduces_ui_issue(self, mock_setup):
        """Test that reproduces the exact scenario we're seeing in the UI screenshot."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # Set up session state to match what we see in the screenshot:
        # - api_initialized and api_client_initialized are True
        # - channel_input is not set
        # - Warning is displayed because db_data and api_data are empty/missing
        mock_st.session_state = {
            'refresh_workflow_step': 2,
            'comparison_attempted': True,
            'db_data': {},  # Empty data
            'api_data': {},  # Empty data
            'existing_channel_id': 'UC_FuzzyPotato_1980',
            'api_initialized': True,
            'api_client_initialized': True,
            # Deliberately NOT setting channel_input to reproduce the issue
        }
        
        # Run the function
        channel_refresh_section(mock_youtube_service)
        
        # Verify warning was displayed
        mock_st.warning.assert_called_once_with("Missing data for comparison. Please try the comparison again.")
        
        # After our fix, channel_input SHOULD be set (fixing the issue)
        assert 'channel_input' in mock_st.session_state
        assert mock_st.session_state['channel_input'] == 'UC_FuzzyPotato_1980'

    def test_critical_variables_set_even_with_warning(self, mock_setup):
        """Test that critical session state variables are set even when showing a warning for empty data."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # Set up session state to match what we see in the screenshot:
        # - Warning is displayed because db_data and api_data are empty
        # - But critical variables should still be set
        mock_st.session_state = {
            'refresh_workflow_step': 2,
            'comparison_attempted': True,
            'db_data': {},  # Empty data
            'api_data': {},  # Empty data
            'existing_channel_id': 'UC_FuzzyPotato_1980',
            # Deliberately NOT setting channel_input to reproduce the scenario
        }
        
        # Run the function
        channel_refresh_section(mock_youtube_service)
        
        # Verify warning was displayed
        mock_st.warning.assert_called_once_with("Missing data for comparison. Please try the comparison again.")
        
        # After our fix, channel_input should be set EVEN THOUGH we show a warning
        assert mock_st.session_state.get('channel_input') == 'UC_FuzzyPotato_1980'
        assert mock_st.session_state.get('api_initialized') is True
        assert mock_st.session_state.get('api_client_initialized') is True

    @patch('src.ui.data_collection.channel_refresh_ui.SQLiteDatabase')
    @patch('streamlit.session_state', {})
    def test_refresh_channel_data_parameter_order(self, mock_sqlite):
        # Arrange
        mock_db_instance = mock_sqlite.return_value
        mock_db_instance.get_channel_data.return_value = {'data_source': 'database', 'video_id': []}
        
        # Mock youtube service
        mock_youtube_service = MagicMock()
        mock_youtube_service.update_channel_data.return_value = {'updated': 'data'}
        
        # Set up test parameters
        channel_id = 'UC_test_channel'
        options = {'include_playlists': True}
        
        # Act
        with patch('streamlit.session_state', {}):
            result = refresh_channel_data(channel_id, mock_youtube_service, options)
        
        # Assert
        # Verify the update_channel_data was called with parameters in correct order
        mock_youtube_service.update_channel_data.assert_called_once()
        call_args = mock_youtube_service.update_channel_data.call_args
        
        # Check the first two positional arguments
        assert call_args[0][0] == channel_id, "First parameter should be channel_id"
        assert call_args[0][1] == options, "Second parameter should be options"
        
        # Check that the result is as expected
        assert result == {'updated': 'data'}

    def test_comparison_options_include_videos(self, mock_setup):
        """Test that the comparison options include videos when comparing with API."""
        mock_st, mock_youtube_service, _ = mock_setup
        
        # Set up session state for step 1 
        mock_st.session_state = {'refresh_workflow_step': 1}
        
        # Mock selectbox to return a selected channel
        mock_st.selectbox.return_value = 'Test Channel (UC_test_channel)'
        
        # Mock button click
        mock_st.button.return_value = True
        
        # Mock spinner context manager
        mock_spinner = MagicMock()
        mock_spinner.__enter__ = MagicMock()
        mock_spinner.__exit__ = MagicMock()
        mock_st.spinner.return_value = mock_spinner
        
        # Run the function with button click simulation
        channel_refresh_section(mock_youtube_service)
        
        # Get the options passed to update_channel_data
        call_args = mock_youtube_service.update_channel_data.call_args
        options = call_args[0][1]  # Second positional argument is options
        
        # Verify videos are included in the options
        assert options['fetch_videos'] is True, "fetch_videos should be set to True to include videos in comparison"
        assert options['max_videos'] > 0, "max_videos should be greater than 0 to fetch some videos"
        assert options['fetch_channel_data'] is True, "fetch_channel_data should be set to True"