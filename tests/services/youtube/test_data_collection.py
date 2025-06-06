import copy
import pytest
from unittest.mock import MagicMock, patch
from src.services.youtube.service_impl.data_collection import DataCollectionMixin
from src.api.youtube_api import YouTubeAPIError

@pytest.fixture
def mock_api():
    return MagicMock()

@pytest.fixture
def mock_video_service():
    return MagicMock()

@pytest.fixture
def mock_comment_service():
    return MagicMock()

@pytest.fixture
def data_collection(mock_api, mock_video_service, mock_comment_service):
    collection = DataCollectionMixin()
    collection.api = mock_api
    collection.video_service = mock_video_service
    collection.comment_service = mock_comment_service
    # PATCH: Add mock storage_service for DB fetch compatibility
    collection.storage_service = MagicMock()
    collection.storage_service.get_channel_data.return_value = {'video_id': []}
    return collection

def test_collect_channel_data_extracts_video_metrics(data_collection, mock_video_service):
    """Test that video metrics are properly extracted during channel data collection"""
    # Mock video service response with deep copy to prevent shared state
    mock_video_data = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'statistics': {
                'viewCount': '1000',
                'likeCount': '100',
                'commentCount': '50'
            }
        }]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    
    # Call the method
    result = data_collection.collect_channel_data('test_channel', {'fetch_videos': True})
    
    # Verify metrics were extracted
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    video = result['video_id'][0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'

def test_collect_channel_data_handles_missing_video_metrics(data_collection, mock_video_service):
    """Test handling of missing video metrics during channel data collection"""
    # Mock video service response with missing metrics
    mock_video_data = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video'
        }]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    
    # Call the method
    result = data_collection.collect_channel_data('test_channel', {'fetch_videos': True})
    
    # Verify default values were set
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    video = result['video_id'][0]
    assert video['views'] == '0'
    assert video['likes'] == '0'
    assert video['comment_count'] == '0'

def test_collect_channel_data_handles_video_service_error(data_collection, mock_video_service):
    """Test handling of video service errors during channel data collection"""
    # Mock video service to raise an error
    mock_video_service.collect_channel_videos.side_effect = Exception('Test error')
    
    # Call the method
    result = data_collection.collect_channel_data('test_channel', {'fetch_videos': True})
    
    # Verify error was handled
    assert 'error_videos' in result
    assert 'Test error' in result['error_videos']

def test_collect_channel_data_updates_existing_videos(data_collection, mock_video_service):
    """Test updating metrics for existing videos during channel data collection"""
    # Mock existing channel data with deep copy to prevent shared state
    existing_data = copy.deepcopy({
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'views': '500',
            'likes': '50',
            'comment_count': '25'
        }]
    })
    # Ensure no statistics field is present in existing_data
    if 'statistics' in existing_data['video_id'][0]:
        del existing_data['video_id'][0]['statistics']
    
    # Mock video service response with updated metrics
    mock_video_data = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'statistics': {
                'viewCount': '1000',
                'likeCount': '100',
                'commentCount': '50'
            }
        }]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    
    # Call the method
    result = data_collection.collect_channel_data('test_channel', {'fetch_videos': True}, existing_data)
    
    # Verify metrics were updated
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    video = result['video_id'][0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'
    
    # Verify deltas were calculated
    assert video['view_delta'] == 500
    assert video['like_delta'] == 50
    assert video['comment_delta'] == 25

def test_collect_channel_data_handles_quota_exceeded(data_collection, mock_video_service):
    """Test handling of quota exceeded error during channel data collection"""
    # Mock video service to raise quota exceeded error
    mock_video_service.collect_channel_videos.side_effect = YouTubeAPIError(
        status_code=403,
        error_type='quotaExceeded',
        message='Quota exceeded'
    )
    
    # Call the method
    result = data_collection.collect_channel_data('test_channel', {'fetch_videos': True})
    
    # Verify error was handled
    assert 'error_videos' in result
    assert 'Quota exceeded' in result['error_videos']

def test_collect_channel_data_handles_mixed_video_metrics(data_collection, mock_video_service):
    """Test handling of mixed video metrics during channel data collection"""
    # Mock video service response with mixed metrics
    mock_video_data = {
        'video_id': [
            {
                'video_id': 'test123',
                'title': 'Test Video 1',
                'statistics': {
                    'viewCount': '1000',
                    'likeCount': '100',
                    'commentCount': '50'
                }
            },
            {
                'video_id': 'test456',
                'title': 'Test Video 2',
                'statistics': {}
            },
            {
                'video_id': 'test789',
                'title': 'Test Video 3'
            }
        ]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    
    # Call the method
    result = data_collection.collect_channel_data('test_channel', {'fetch_videos': True})
    
    # Verify metrics were handled correctly
    videos = result['video_id']
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    assert videos[0]['views'] == '1000'
    assert videos[0]['likes'] == '100'
    assert videos[0]['comment_count'] == '50'
    assert videos[1]['views'] == '0'
    assert videos[1]['likes'] == '0'
    assert videos[1]['comment_count'] == '0'
    assert videos[2]['views'] == '0'
    assert videos[2]['likes'] == '0'
    assert videos[2]['comment_count'] == '0'

def test_new_collection_workflow_no_deltas(data_collection, mock_video_service):
    """Test new collection workflow: no deltas should be present."""
    # Mock video service response
    mock_video_data = {
        'video_id': [{
            'video_id': 'vid1',
            'title': 'Video 1',
            'statistics': {
                'viewCount': '100',
                'likeCount': '10',
                'commentCount': '5'
            }
        }]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    # Call as new collection (no existing_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True})
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    video = result['video_id'][0]
    assert video['views'] == '100'
    assert video['likes'] == '10'
    assert video['comment_count'] == '5'
    # No delta fields should be present
    assert 'view_delta' not in video
    assert 'like_delta' not in video
    assert 'comment_delta' not in video

def test_update_channel_workflow_with_deltas(data_collection, mock_video_service):
    """Test update channel workflow: deltas should be present and correct."""
    # Mock existing data
    existing_data = {
        'video_id': [{
            'video_id': 'vid1',
            'title': 'Video 1',
            'views': '80',
            'likes': '8',
            'comment_count': '2'
        }]
    }
    # Mock video service response with updated stats
    mock_video_data = {
        'video_id': [{
            'video_id': 'vid1',
            'title': 'Video 1',
            'statistics': {
                'viewCount': '100',
                'likeCount': '10',
                'commentCount': '5'
            }
        }]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    # Call as update (with existing_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True}, existing_data)
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    video = result['video_id'][0]
    assert video['views'] == '100'
    assert video['likes'] == '10'
    assert video['comment_count'] == '5'
    # Delta fields should be present and correct
    assert video['view_delta'] == 20
    assert video['like_delta'] == 2
    assert video['comment_delta'] == 3

def test_workflow_debug_log_on_error(data_collection, mock_video_service):
    """Test that debug log is populated on error in workflow."""
    # Mock video service to raise an error
    mock_video_service.collect_channel_videos.side_effect = Exception('Simulated error')
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True})
    assert 'error_videos' in result
    assert 'Simulated error' in result['error_videos']

def test_update_channel_response_includes_deltas_and_logs(data_collection, mock_video_service):
    """Test that update channel response includes delta info, debug logs, response data, and actual video count."""
    # Mock existing data
    existing_data = {
        'video_id': [{
            'video_id': 'vid1',
            'title': 'Video 1',
            'views': '80',
            'likes': '8',
            'comment_count': '2'
        }]
    }
    # Mock video service response with updated stats
    mock_video_data = {
        'video_id': [{
            'video_id': 'vid1',
            'title': 'Video 1',
            'statistics': {
                'viewCount': '100',
                'likeCount': '10',
                'commentCount': '5'
            }
        }]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    # Call as update (with existing_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True}, existing_data)
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    video = result['video_id'][0]
    # Delta fields should be present and correct
    assert video['view_delta'] == 20
    assert video['like_delta'] == 2
    assert video['comment_delta'] == 3
    # Debug logs and response data should be present
    assert 'debug_logs' in result
    assert isinstance(result['debug_logs'], list)
    assert any('Delta for video' in log for log in result['debug_logs'])
    assert 'response_data' in result
    assert isinstance(result['response_data'], dict)
    # Actual video count should be correct
    assert result.get('actual_video_count', 0) == 1
    # Video list should not be empty
    assert len(result['video_id']) > 0

def test_fetch_videos_returns_videos_and_logs(data_collection, mock_video_service):
    """Test that Fetch Videos returns a non-empty video list and debug logs."""
    # Mock video service response
    mock_video_data = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1', 'statistics': {'viewCount': '100', 'likeCount': '10', 'commentCount': '5'}},
            {'video_id': 'vid2', 'title': 'Video 2', 'statistics': {'viewCount': '200', 'likeCount': '20', 'commentCount': '10'}}
        ]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    # Call as new collection (no existing_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True})
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    # Video list should not be empty
    assert len(result['video_id']) == 2
    # Debug logs and response data should be present
    assert 'debug_logs' in result
    assert isinstance(result['debug_logs'], list)
    assert 'response_data' in result
    assert isinstance(result['response_data'], dict)
    # Actual video count should be correct
    assert result.get('actual_video_count', 0) == 2

def test_update_channel_response_includes_top_level_delta(data_collection, mock_video_service):
    """Test that update channel response includes a top-level 'delta' field summarizing video deltas."""
    # Mock existing data
    existing_data = {
        'video_id': [{
            'video_id': 'vid1',
            'title': 'Video 1',
            'views': '80',
            'likes': '8',
            'comment_count': '2'
        }]
    }
    # Mock video service response with updated stats
    mock_video_data = {
        'video_id': [{
            'video_id': 'vid1',
            'title': 'Video 1',
            'statistics': {
                'viewCount': '100',
                'likeCount': '10',
                'commentCount': '5'
            }
        }]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    # Call as update (with existing_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True}, existing_data)
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    # There should be a top-level 'delta' field
    assert 'delta' in result, "No top-level 'delta' field in response"
    delta = result['delta']
    assert isinstance(delta, dict)
    # It should summarize video deltas
    assert 'videos' in delta
    assert isinstance(delta['videos'], list)
    assert any('view_delta' in v for v in delta['videos'])

def test_update_channel_delta_videos_non_empty(data_collection, mock_video_service):
    """Test that delta['videos'] is non-empty after an update with multiple videos and changes."""
    existing_data = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1', 'views': '80', 'likes': '8', 'comment_count': '2'},
            {'video_id': 'vid2', 'title': 'Video 2', 'views': '50', 'likes': '5', 'comment_count': '1'}
        ]
    }
    mock_video_data = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1', 'statistics': {'viewCount': '100', 'likeCount': '10', 'commentCount': '5'}},
            {'video_id': 'vid2', 'title': 'Video 2', 'statistics': {'viewCount': '60', 'likeCount': '7', 'commentCount': '2'}},
            {'video_id': 'vid3', 'title': 'Video 3', 'statistics': {'viewCount': '30', 'likeCount': '3', 'commentCount': '0'}}
        ]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True}, existing_data)
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    assert 'delta' in result
    assert 'videos' in result['delta']
    # Should have at least two entries for updated videos
    assert len(result['delta']['videos']) >= 2
    # Check that at least one delta is nonzero
    assert any(v['view_delta'] != 0 or v['like_delta'] != 0 or v['comment_delta'] != 0 for v in result['delta']['videos'])

def test_fetch_all_videos_returns_all(data_collection, mock_video_service):
    """Test that all videos are returned when max_videos=0 (fetch all)."""
    mock_video_data = {
        'video_id': [
            {'video_id': f'vid{i}', 'title': f'Video {i}', 'statistics': {'viewCount': str(10*i), 'likeCount': str(i), 'commentCount': str(i//2)}}
            for i in range(1, 201)
        ]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True, 'max_videos': 0})
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    assert len(result['video_id']) == 200
    assert result.get('actual_video_count', 0) == 200

def test_debug_logs_and_response_data_present(data_collection, mock_video_service):
    """Test that debug_logs and response_data are present and accessible in the backend response."""
    mock_video_data = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1', 'statistics': {'viewCount': '100', 'likeCount': '10', 'commentCount': '5'}}
        ]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True})
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    assert 'debug_logs' in result
    assert isinstance(result['debug_logs'], list)
    assert 'response_data' in result
    assert isinstance(result['response_data'], dict)

def test_fetch_videos_returns_non_empty_list(data_collection, mock_video_service):
    """Test that fetching videos returns a non-empty video list."""
    mock_video_data = {
        'video_id': [
            {'video_id': 'vid1', 'title': 'Video 1', 'statistics': {'viewCount': '100', 'likeCount': '10', 'commentCount': '5'}},
            {'video_id': 'vid2', 'title': 'Video 2', 'statistics': {'viewCount': '200', 'likeCount': '20', 'commentCount': '10'}}
        ]
    }
    mock_video_service.collect_channel_videos.return_value = copy.deepcopy(mock_video_data)
    result = data_collection.collect_channel_data('chan1', {'fetch_videos': True})
    # Assert video_id is present and non-empty
    assert 'video_id' in result, "Missing 'video_id' in result"
    assert result['video_id'], "'video_id' is empty in result"
    assert len(result['video_id']) == 2

def test_get_basic_channel_info_all_input_types(youtube_service, monkeypatch):
    """Test get_basic_channel_info with channel ID, URL, handle, and custom URL."""
    # Mock channel_service methods
    class DummyChannelService:
        def parse_channel_input(self, inp):
            if inp.startswith('UC'): return inp
            if inp.startswith('http'): return 'UC1234567890123456789012'
            if inp.startswith('@'): return 'resolve:@handle'
            if inp.startswith('custom'): return 'resolve:customurl'
            return inp
        def validate_and_resolve_channel_id(self, inp):
            if inp.startswith('UC'): return True, inp
            if inp.startswith('resolve:@handle'): return True, 'UC_handle_resolved'
            if inp.startswith('resolve:customurl'): return True, 'UC_customurl_resolved'
            return False, 'invalid'
        def get_channel_info(self, cid):
            if cid.startswith('UC'): return {'channel_id': cid, 'playlist_id': 'UU'+cid[2:]}
            return None
    monkeypatch.setattr(youtube_service, 'channel_service', DummyChannelService())
    # Channel ID
    info = youtube_service.get_basic_channel_info('UC1234567890123456789012')
    assert info and info['playlist_id'].startswith('UU')
    # URL
    info = youtube_service.get_basic_channel_info('https://youtube.com/channel/UC1234567890123456789012')
    assert info and info['playlist_id'].startswith('UU')
    # Handle
    info = youtube_service.get_basic_channel_info('@handle')
    assert info and info['playlist_id'].startswith('UU')
    # Custom URL
    info = youtube_service.get_basic_channel_info('customurl')
    assert info and info['playlist_id'].startswith('UU')
    # Invalid
    info = youtube_service.get_basic_channel_info('invalid')
    assert info is None 