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
    # Video list should not be empty
    assert 'video_id' in result
    assert len(result['video_id']) == 2
    # Debug logs and response data should be present
    assert 'debug_logs' in result
    assert isinstance(result['debug_logs'], list)
    assert 'response_data' in result
    assert isinstance(result['response_data'], dict)
    # Actual video count should be correct
    assert result.get('actual_video_count', 0) == 2 