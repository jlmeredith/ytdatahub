import pytest
from unittest.mock import MagicMock, patch
import streamlit as st
from src.ui.data_collection.refresh_channel_workflow import RefreshChannelWorkflow

@pytest.fixture
def mock_youtube_service():
    service = MagicMock()
    return service

@pytest.fixture
def mock_session_state():
    with patch('streamlit.session_state') as mock:
        mock.get = MagicMock(return_value=None)
        yield mock

def test_refresh_workflow_displays_delta(mock_youtube_service, mock_session_state):
    """Test that the refresh workflow displays delta information when present."""
    # Mock backend response with delta
    mock_response = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1', 'views': '100', 'likes': '10', 'comment_count': '5'}
        ],
        'delta': {
            'videos': [
                {'video_id': 'vid1', 'view_delta': 20, 'like_delta': 2, 'comment_delta': 3}
            ]
        },
        'debug_logs': ['Test log'],
        'response_data': {'test': 'data'}
    }
    
    mock_youtube_service.update_channel_data.return_value = mock_response
    
    # Create workflow instance
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    
    # Mock session state for existing channel
    mock_session_state.get.side_effect = lambda key, default=None: {
        'existing_channel_id': 'test_channel',
        'collection_mode': 'refresh_channel'
    }.get(key, default)
    
    # Call the video collection method
    workflow._handle_video_collection('test_channel', 0)  # 0 means fetch all
    
    # Verify delta was stored in session state
    mock_session_state.__setitem__.assert_any_call('delta', mock_response['delta'])
    mock_session_state.__setitem__.assert_any_call('debug_logs', mock_response['debug_logs'])
    mock_session_state.__setitem__.assert_any_call('response_data', mock_response['response_data'])

def test_refresh_workflow_fetches_all_videos(mock_youtube_service, mock_session_state):
    """Test that the refresh workflow fetches all videos when max_videos=0."""
    # Mock backend response with many videos
    mock_response = {
        'video_id': [
            {'video_id': f'vid{i}', 'title': f'Video {i}'} for i in range(1, 201)
        ],
        'actual_video_count': 200
    }
    
    mock_youtube_service.update_channel_data.return_value = mock_response
    
    # Create workflow instance
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    
    # Call the video collection method with max_videos=0
    workflow._handle_video_collection('test_channel', 0)
    
    # Verify the correct options were passed to the backend
    mock_youtube_service.update_channel_data.assert_called_once()
    call_args = mock_youtube_service.update_channel_data.call_args
    # call_args[0] is a tuple of positional args: (channel_id, options, ...)
    options = call_args[0][1]
    assert options['max_videos'] == 0
    
    # Verify all videos were stored in session state
    mock_session_state.__setitem__.assert_any_call('videos_data', mock_response['video_id'])

def test_refresh_workflow_handles_debug_data(mock_youtube_service, mock_session_state):
    """Test that the refresh workflow properly handles and stores debug data."""
    # Mock backend response with debug data
    mock_response = {
        'video_id': [{'video_id': 'vid1', 'title': 'Video 1'}],
        'debug_logs': ['Log 1', 'Log 2'],
        'response_data': {'test': 'data'},
        'actual_video_count': 1
    }
    
    mock_youtube_service.update_channel_data.return_value = mock_response
    
    # Create workflow instance
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    
    # Call the video collection method
    workflow._handle_video_collection('test_channel', 50)
    
    # Verify debug data was stored in session state
    mock_session_state.__setitem__.assert_any_call('debug_logs', mock_response['debug_logs'])
    mock_session_state.__setitem__.assert_any_call('response_data', mock_response['response_data'])

def test_refresh_workflow_displays_video_list(mock_youtube_service, mock_session_state):
    """Test that the refresh workflow properly displays the video list."""
    # Mock backend response with videos
    mock_response = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1', 'views': '100'},
            {'video_id': 'vid2', 'title': 'Video 2', 'views': '200'}
        ],
        'actual_video_count': 2
    }
    
    mock_youtube_service.update_channel_data.return_value = mock_response
    
    # Create workflow instance
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    
    # Call the video collection method
    workflow._handle_video_collection('test_channel', 50)
    
    # Verify videos were stored in session state
    mock_session_state.__setitem__.assert_any_call('videos_data', mock_response['video_id'])
    mock_session_state.__setitem__.assert_any_call('videos_fetched', True)

def test_detailed_change_report_displays_delta(mock_youtube_service, mock_session_state):
    """Test that the Detailed Change Report displays delta data if present."""
    mock_response = {
        'video_id': [{'video_id': 'vid1', 'title': 'Video 1'}],
        'delta': {'videos': [{'video_id': 'vid1', 'view_delta': 10}]},
        'debug_logs': ['Delta log'],
        'response_data': {'delta': 'data'},
        'actual_video_count': 1
    }
    mock_youtube_service.update_channel_data.return_value = mock_response
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    workflow._handle_video_collection('test_channel', 1)
    # Assert delta is stored and would be rendered
    mock_session_state.__setitem__.assert_any_call('delta', mock_response['delta'])


def test_debug_panel_displays_logs_and_response_data(mock_youtube_service, mock_session_state):
    """Test that the Debug panel displays logs and response data if present."""
    mock_response = {
        'video_id': [{'video_id': 'vid1', 'title': 'Video 1'}],
        'debug_logs': ['Log entry'],
        'response_data': {'foo': 'bar'},
        'actual_video_count': 1
    }
    mock_youtube_service.update_channel_data.return_value = mock_response
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    workflow._handle_video_collection('test_channel', 1)
    mock_session_state.__setitem__.assert_any_call('debug_logs', mock_response['debug_logs'])
    mock_session_state.__setitem__.assert_any_call('response_data', mock_response['response_data'])


def test_api_status_panel_updates_after_api_call(mock_youtube_service, mock_session_state):
    """Test that the API Status panel updates after an API call."""
    mock_response = {
        'video_id': [{'video_id': 'vid1', 'title': 'Video 1'}],
        'actual_video_count': 1
    }
    mock_youtube_service.update_channel_data.return_value = mock_response
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    workflow._handle_video_collection('test_channel', 1)
    # Check that last_api_call is set
    found = False
    for call in mock_session_state.__setitem__.call_args_list:
        if call[0][0] == 'last_api_call':
            found = True
    assert found, "last_api_call was not set in session state"


def test_video_list_displayed_after_fetch(mock_youtube_service, mock_session_state):
    """Test that the video list is displayed after fetching videos."""
    mock_response = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1'},
            {'video_id': 'vid2', 'title': 'Video 2'}
        ],
        'actual_video_count': 2
    }
    mock_youtube_service.update_channel_data.return_value = mock_response
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    workflow._handle_video_collection('test_channel', 2)
    mock_session_state.__setitem__.assert_any_call('videos_data', mock_response['video_id']) 

@patch('streamlit.error')
def test_channel_fetch_failure(mock_error, mock_youtube_service, mock_session_state):
    # Simulate comparison_data is None (API/db failure)
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    with patch('streamlit.selectbox', return_value='Test Channel (UC123)'), \
         patch('streamlit.button', return_value=True), \
         patch('streamlit.spinner'):
        st.session_state['refresh_workflow_step'] = 1
        st.session_state['db_data'] = {}
        st.session_state['api_data'] = {}
        workflow.render_step_1_select_channel()
    mock_error.assert_any_call("Failed to retrieve channel data for comparison. Please try again.")

@patch('streamlit.error')
def test_video_fetch_failure(mock_error, mock_youtube_service, mock_session_state):
    # Simulate update_channel_data returns None
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    st.session_state['refresh_workflow_step'] = 3
    st.session_state['channel_input'] = 'UC123'
    mock_youtube_service.update_channel_data.return_value = None
    with patch('streamlit.slider', return_value=5), patch('streamlit.button', side_effect=[True, False]):
        workflow.render_step_2_video_collection()
    mock_error.assert_any_call("Video fetch failed: No response from API.")

@patch('streamlit.error')
def test_save_failure(mock_error, mock_youtube_service, mock_session_state):
    # Simulate save_channel_data returns False
    workflow = RefreshChannelWorkflow(mock_youtube_service)
    st.session_state['api_data'] = {'channel_id': 'UC123'}
    st.session_state['videos_data'] = []
    st.session_state['refresh_workflow_step'] = 4
    with patch('src.ui.data_collection.refresh_channel_workflow.SaveOperationManager') as mock_save_mgr:
        mock_save_mgr.return_value.perform_save_operation.return_value = False
        workflow.save_data()
    mock_error.assert_any_call("Failed to save data.") 