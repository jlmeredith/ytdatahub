import pytest
from unittest.mock import MagicMock, patch
import streamlit as st
from src.ui.data_collection.new_channel_workflow import NewChannelWorkflow

@pytest.fixture
def mock_youtube_service():
    service = MagicMock()
    return service

@pytest.fixture
def session_state():
    state = {}
    with patch('streamlit.session_state', state):
        yield state

@patch('streamlit.error')
@patch('streamlit.spinner')
def test_channel_fetch_failure(mock_spinner, mock_error, mock_youtube_service, session_state):
    # Simulate API returning None (invalid channel)
    mock_youtube_service.get_basic_channel_info.return_value = None
    workflow = NewChannelWorkflow(mock_youtube_service)
    workflow.initialize_workflow('bad_channel')
    assert session_state['channel_fetch_failed'] is True
    mock_error.assert_called_with("Failed to fetch channel data. Please check the channel ID or URL and try again.")

@patch('streamlit.error')
@patch('streamlit.spinner')
def test_channel_fetch_api_exception(mock_spinner, mock_error, mock_youtube_service, session_state):
    # Simulate API raising exception
    mock_youtube_service.get_basic_channel_info.side_effect = Exception('API error')
    workflow = NewChannelWorkflow(mock_youtube_service)
    workflow.initialize_workflow('bad_channel')
    assert session_state['channel_fetch_failed'] is True
    mock_error.assert_called_with("Error: API error")

@patch('streamlit.error')
def test_channel_fetch_retry_after_failure(mock_error, mock_youtube_service, session_state):
    session_state['channel_info_temp'] = None  # Ensure no valid info present
    session_state['channel_fetch_failed'] = True
    workflow = NewChannelWorkflow(mock_youtube_service)
    workflow.initialize_workflow('any_channel')
    print('MOCK ERROR CALLS:', mock_error.mock_calls)
    mock_error.assert_called_with("Channel fetch previously failed. Please clear the form or enter a new channel.")

@patch('streamlit.success')
@patch('streamlit.spinner')
def test_channel_fetch_success(mock_spinner, mock_success, mock_youtube_service, session_state):
    # Simulate valid channel info with playlist_id
    mock_youtube_service.get_basic_channel_info.return_value = {'channel_id': 'UC123', 'playlist_id': 'UU123'}
    workflow = NewChannelWorkflow(mock_youtube_service)
    workflow.initialize_workflow('UC123')
    assert session_state['channel_info_temp']['channel_id'] == 'UC123'
    assert session_state['channel_info_temp']['playlist_id'] == 'UU123'
    assert session_state['channel_data_fetched'] is True

@patch('streamlit.error')
@patch('streamlit.spinner')
def test_video_fetch_failure(mock_spinner, mock_error, mock_youtube_service, session_state):
    # Setup channel info
    session_state['channel_info_temp'] = {'channel_id': 'UC123', 'playlist_id': 'UU123', 'total_videos': 10}
    session_state['debug_logs'] = []
    # Simulate collect_channel_data returning None
    mock_youtube_service.collect_channel_data.return_value = None
    workflow = NewChannelWorkflow(mock_youtube_service)
    with patch('streamlit.slider', return_value=5), patch('streamlit.button', side_effect=[True, False]):
        workflow.render_step_2_video_collection()
    mock_error.assert_called_with("Failed to fetch videos. Please try again.")

@patch('streamlit.error')
@patch('streamlit.spinner')
def test_save_failure(mock_spinner, mock_error, mock_youtube_service, session_state):
    # Setup channel info
    session_state['channel_info_temp'] = {'channel_id': 'UC123', 'playlist_id': 'UU123'}
    # Simulate save_channel_data returning False
    mock_youtube_service.save_channel_data.return_value = False
    workflow = NewChannelWorkflow(mock_youtube_service)
    with patch('streamlit.button', return_value=True):
        workflow.render_step_1_channel_data()
    mock_error.assert_any_call("Failed to save data.")

@patch('streamlit.error')
def test_channel_info_temp_invalid_triggers_refetch(mock_error, mock_youtube_service, session_state):
    # Simulate channel_info_temp present but missing playlist_id
    session_state['channel_info_temp'] = {'channel_id': 'UC123'}
    mock_youtube_service.get_basic_channel_info.return_value = {'channel_id': 'UC123', 'playlist_id': 'UU123'}
    workflow = NewChannelWorkflow(mock_youtube_service)
    workflow.initialize_workflow('UC123')
    # Should refetch and set playlist_id
    assert session_state['channel_info_temp']['playlist_id'] == 'UU123'
    assert session_state['channel_data_fetched'] is True

@patch('streamlit.error')
def test_session_state_cleared_on_new_workflow(mock_error, mock_youtube_service, session_state):
    # Set all relevant session state keys
    session_state['channel_info_temp'] = {'channel_id': 'UC123', 'playlist_id': 'UU123'}
    session_state['channel_data_fetched'] = True
    session_state['channel_fetch_failed'] = True
    session_state['collection_step'] = 2
    session_state['videos_fetched'] = True
    session_state['comments_fetched'] = True
    # Simulate starting a new workflow
    workflow = NewChannelWorkflow(mock_youtube_service)
    workflow.reset_workflow_state()
    # All keys should be reset
    assert 'channel_info_temp' not in session_state
    assert session_state.get('channel_data_fetched') is False
    assert session_state.get('channel_fetch_failed') is False
    assert session_state.get('collection_step') == 1
    assert session_state.get('videos_fetched') is False
    assert session_state.get('comments_fetched') is False

@patch('src.database.channel_repository.ChannelRepository')
def test_full_api_response_persisted_on_save(mock_channel_repo, mock_youtube_service, session_state):
    # Setup channel info with raw_channel_info
    raw_api = {'id': 'UC123', 'title': 'Test Channel', 'views': 1000}
    session_state['channel_info_temp'] = {'channel_id': 'UC123', 'raw_channel_info': raw_api}
    # Simulate successful save
    mock_channel_repo.return_value.get_channel_data.return_value = {'raw_channel_info': raw_api, 'channel_id': 'UC123', 'playlist_id': 'UU123'}
    mock_youtube_service.db_path = 'test.db'
    workflow = NewChannelWorkflow(mock_youtube_service)
    with patch('streamlit.button', return_value=True), patch('streamlit.spinner'), patch('streamlit.markdown'), patch('streamlit.subheader'), patch('streamlit.info'), patch('streamlit.success'), patch('streamlit.error'):
        workflow.render_step_1_channel_data()
    # Check that the DB was called with the correct raw_channel_info
    args, kwargs = mock_channel_repo.return_value.get_channel_data.call_args
    assert args[0] == 'UC123'
    db_record = mock_channel_repo.return_value.get_channel_data.return_value
    assert db_record['raw_channel_info'] == raw_api 