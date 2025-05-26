"""
Test that the new channel workflow correctly processes and displays videos.
"""
import streamlit as st
import pytest
import queue
from unittest.mock import patch, MagicMock

# Create a better mock for session_state that supports attribute setting
class SessionStateMock(dict):
    def __setattr__(self, name, value):
        self[name] = value
    
    def __getattr__(self, name):
        if name in self:
            return self[name]
        return None

# Create a session state mock with all the necessary attributes
session_state_mock = SessionStateMock({
    'performance_timers': {},
    'performance_metrics': {},
    'background_task_queue': queue.Queue(),
    'background_tasks_running': False,
    'background_task_results': {},
    'collection_step': 1,
    'channel_input': '',
    'api_initialized': True
})

# Sample video data that simulates the YouTube API response
SAMPLE_API_VIDEO_RESPONSE = [
    {
        'video_id': 'test1',
        'title': 'Test Video 1',
        'statistics': {
            'viewCount': '5000',
            'likeCount': '200',
            'commentCount': '50'
        },
        'snippet': {
            'publishedAt': '2023-01-01T00:00:00Z'
        }
    },
    {
        'video_id': 'test2',
        'title': 'Test Video 2',
        'statistics': {
            'viewCount': '7500',
            'likeCount': '300',
            'commentCount': '75'
        },
        'snippet': {
            'publishedAt': '2023-02-01T00:00:00Z'
        }
    }
]

@pytest.fixture
def mock_youtube_service():
    service = MagicMock()
    
    # Mock the collect_channel_data method to return sample data
    def mock_collect_data(channel_id, options, existing_data=None):
        return {
            'channel_id': channel_id,
            'video_id': SAMPLE_API_VIDEO_RESPONSE,
            'last_api_call': '2023-01-01T00:00:00Z'
        }
    
    service.collect_channel_data.side_effect = mock_collect_data
    return service

# Mock all streamlit.session_state references with our SessionStateMock
@patch('streamlit.session_state', session_state_mock)
@patch('src.utils.background_tasks.st.session_state', session_state_mock)
@patch('src.utils.performance_tracking.st.session_state', session_state_mock)
@patch('streamlit.subheader')
@patch('streamlit.write')
@patch('streamlit.slider')
@patch('streamlit.button')
@patch('streamlit.spinner')
@patch('streamlit.success')
@patch('streamlit.error')
@patch('streamlit.rerun')
@patch('streamlit.container')
@patch('streamlit.columns')
def test_new_channel_workflow_processes_videos(
    mock_columns, mock_container, mock_rerun, mock_error, 
    mock_success, mock_spinner, mock_button, mock_slider, 
    mock_write, mock_subheader, mock_youtube_service
):
    """Test that videos are processed correctly in the new channel workflow."""
    from src.ui.data_collection.new_channel_workflow import NewChannelWorkflow
    
    # Setup session state
    st.session_state['channel_info_temp'] = {
        'channel_id': 'UC12345',
        'channel_name': 'Test Channel',
        'total_videos': 100
    }
    st.session_state['debug_logs'] = []
    st.session_state['api_initialized'] = True

    # Setup mocks
    mock_cols = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    mock_columns.return_value = mock_cols
    mock_container.return_value.__enter__.return_value = MagicMock()
    mock_button.return_value = True  # Simulate button click
    mock_slider.return_value = 50
    
    # Instantiate workflow and run video collection
    workflow = NewChannelWorkflow(mock_youtube_service)
    
    # Mock that video_processing functions are called
    with patch('src.utils.video_processor.process_video_data') as mock_process_video_data, \
         patch('src.utils.video_formatter.fix_missing_views') as mock_fix_missing_views:
        
        # Configure mocks to return values
        mock_process_video_data.return_value = SAMPLE_API_VIDEO_RESPONSE
        mock_fix_missing_views.return_value = SAMPLE_API_VIDEO_RESPONSE
        
        # Run the step that fetches and processes videos
        workflow.render_step_2_video_collection()
        
        # Assert that video processing functions were called
        mock_process_video_data.assert_called_once()
        mock_fix_missing_views.assert_called_once()
        
        # Check that session state was updated correctly
        assert 'videos_fetched' in st.session_state
        assert st.session_state['videos_fetched'] == True
        
        # Check that channel_info_temp was updated with the processed videos
        assert 'video_id' in st.session_state['channel_info_temp']
        assert st.session_state['channel_info_temp']['video_id'] == SAMPLE_API_VIDEO_RESPONSE
        
        # Check that UI was updated
        mock_success.assert_called_once()
        mock_rerun.assert_called_once()
