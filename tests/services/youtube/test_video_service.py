import pytest
from unittest.mock import MagicMock, patch
from src.services.youtube.video_service import VideoService
from src.api.youtube_api import YouTubeAPIError

@pytest.fixture
def mock_api():
    return MagicMock()

@pytest.fixture
def video_service(mock_api):
    return VideoService(api_client=mock_api)

def test_collect_channel_videos_extracts_metrics(video_service, mock_api):
    """Test that video metrics are properly extracted from API response"""
    # Mock API response with video data
    mock_api.get_channel_videos.return_value = {
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
    channel_data = {'channel_id': 'test_channel', 'playlist_id': 'UU_test_playlist'}
    result = video_service.collect_channel_videos(channel_data)
    
    # Verify metrics were extracted
    assert result['video_id'], "'video_id' is empty in result; expected at least one video with metrics."
    video = result['video_id'][0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'

def test_collect_channel_videos_handles_missing_statistics(video_service, mock_api):
    """Test handling of videos with missing statistics"""
    # Mock API response with video missing statistics
    mock_api.get_channel_videos.return_value = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video'
        }]
    }
    
    # Call the method
    channel_data = {'channel_id': 'test_channel'}
    result = video_service.collect_channel_videos(channel_data)
    
    # Verify default values were set
    video = result['video_id'][0]
    assert video['views'] == '0'
    assert video['likes'] == '0'
    assert video['comment_count'] == '0'

def test_collect_channel_videos_handles_empty_statistics(video_service, mock_api):
    """Test handling of videos with empty statistics object"""
    # Mock API response with empty statistics
    mock_api.get_channel_videos.return_value = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'statistics': {}
        }]
    }
    
    # Call the method
    channel_data = {'channel_id': 'test_channel'}
    result = video_service.collect_channel_videos(channel_data)
    
    # Verify default values were set
    video = result['video_id'][0]
    assert video['views'] == '0'
    assert video['likes'] == '0'
    assert video['comment_count'] == '0'

def test_collect_channel_videos_handles_string_statistics(video_service, mock_api):
    """Test handling of videos with statistics as string"""
    # Mock API response with statistics as string
    mock_api.get_channel_videos.return_value = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'statistics': '{"viewCount": "1000", "likeCount": "100", "commentCount": "50"}'
        }]
    }
    
    # Call the method
    channel_data = {'channel_id': 'test_channel'}
    result = video_service.collect_channel_videos(channel_data)
    
    # Verify metrics were extracted
    video = result['video_id'][0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'

def test_collect_channel_videos_handles_nested_statistics(video_service, mock_api):
    """Test handling of videos with nested statistics"""
    # Mock API response with nested statistics
    mock_api.get_channel_videos.return_value = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'contentDetails': {
                'statistics': {
                    'viewCount': '1000',
                    'likeCount': '100',
                    'commentCount': '50'
                }
            }
        }]
    }
    
    # Call the method
    channel_data = {'channel_id': 'test_channel'}
    result = video_service.collect_channel_videos(channel_data)
    
    # Verify metrics were extracted
    video = result['video_id'][0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'

def test_collect_channel_videos_handles_quota_exceeded(video_service, mock_api):
    """Test handling of quota exceeded error"""
    # Mock API to raise quota exceeded error
    mock_api.get_channel_videos.side_effect = YouTubeAPIError(
        status_code=403,
        error_type='quotaExceeded',
        message='Quota exceeded'
    )
    
    # Call the method
    channel_data = {'channel_id': 'test_channel'}
    result = video_service.collect_channel_videos(channel_data)
    
    # Verify error was handled gracefully
    assert 'error_videos' in result
    assert 'Quota exceeded' in result['error_videos']

def test_refresh_video_details_updates_metrics(video_service, mock_api):
    """Test that refresh_video_details properly updates metrics"""
    # Mock initial channel data
    channel_data = {
        'video_id': [{
            'video_id': 'test123',
            'title': 'Test Video',
            'views': '1000',
            'likes': '100',
            'comment_count': '50'
        }]
    }
    
    # Mock API response for refresh
    mock_api.get_video_details_batch.return_value = {
        'items': [{
            'id': 'test123',
            'statistics': {
                'viewCount': '2000',
                'likeCount': '200',
                'commentCount': '100'
            }
        }]
    }
    
    # Call the method
    result = video_service.refresh_video_details(channel_data)
    
    # Verify metrics were updated
    video = result['video_id'][0]
    assert video['views'] == '2000'
    assert video['likes'] == '200'
    assert video['comment_count'] == '100' 