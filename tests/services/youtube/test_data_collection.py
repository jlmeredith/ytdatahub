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
    # Mock video service response
    mock_video_service.collect_channel_videos.return_value = {
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
    mock_video_service.collect_channel_videos.return_value = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video'
        }]
    }
    
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
    # Mock existing channel data
    existing_data = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'views': '500',
            'likes': '50',
            'comment_count': '25'
        }]
    }
    
    # Mock video service response with updated metrics
    mock_video_service.collect_channel_videos.return_value = {
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
    mock_video_service.collect_channel_videos.return_value = {
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
    
    # Call the method
    result = data_collection.collect_channel_data('test_channel', {'fetch_videos': True})
    
    # Verify metrics were handled correctly
    assert result['video_id'][0]['views'] == '1000'
    assert result['video_id'][0]['likes'] == '100'
    assert result['video_id'][0]['comment_count'] == '50'
    
    assert result['video_id'][1]['views'] == '0'
    assert result['video_id'][1]['likes'] == '0'
    assert result['video_id'][1]['comment_count'] == '0'
    
    assert result['video_id'][2]['views'] == '0'
    assert result['video_id'][2]['likes'] == '0'
    assert result['video_id'][2]['comment_count'] == '0' 