import pytest
from src.utils.video_processor import process_video_data, process_videos

def test_process_video_data_empty():
    """Test processing empty video data"""
    assert process_video_data([]) == []
    assert process_video_data(None) is None

def test_process_video_data_basic():
    """Test basic video data processing"""
    video_data = [{
        'video_id': 'test1',
        'statistics': {
            'viewCount': '1000',
            'commentCount': '50'
        }
    }]
    result = process_video_data(video_data)
    assert result[0]['views'] == '1000'
    assert result[0]['comment_count'] == '50'

def test_process_video_data_content_details():
    """Test processing video data with contentDetails"""
    video_data = [{
        'video_id': 'test1',
        'contentDetails': {
            'statistics': {
                'viewCount': '2000',
                'commentCount': '100'
            }
        }
    }]
    result = process_video_data(video_data)
    assert result[0]['views'] == '2000'
    assert result[0]['comment_count'] == '100'

def test_process_video_data_existing_values():
    """Test processing video data with existing values"""
    video_data = [{
        'video_id': 'test1',
        'views': '3000',
        'comment_count': '150',
        'statistics': {
            'viewCount': '4000',
            'commentCount': '200'
        }
    }]
    result = process_video_data(video_data)
    # Should keep existing values if they're valid
    assert result[0]['views'] == '3000'
    # Should update comment_count from statistics
    assert result[0]['comment_count'] == '200'

def test_process_video_data_zero_values():
    """Test processing video data with zero values"""
    video_data = [{
        'video_id': 'test1',
        'views': '0',
        'statistics': {
            'viewCount': '1000',
            'commentCount': '50'
        }
    }]
    result = process_video_data(video_data)
    # Should update zero views with value from statistics
    assert result[0]['views'] == '1000'
    assert result[0]['comment_count'] == '50'

def test_process_video_data_missing_values():
    """Test processing video data with missing values"""
    video_data = [{
        'video_id': 'test1'
    }]
    result = process_video_data(video_data)
    assert result[0]['views'] == '0'
    assert 'comment_count' not in result[0]

def test_process_video_data_multiple_videos():
    """Test processing multiple videos"""
    video_data = [
        {
            'video_id': 'test1',
            'statistics': {
                'viewCount': '1000',
                'commentCount': '50'
            }
        },
        {
            'video_id': 'test2',
            'contentDetails': {
                'statistics': {
                    'viewCount': '2000',
                    'commentCount': '100'
                }
            }
        },
        {
            'video_id': 'test3',
            'views': '3000'
        }
    ]
    result = process_video_data(video_data)
    assert result[0]['views'] == '1000'
    assert result[0]['comment_count'] == '50'
    assert result[1]['views'] == '2000'
    assert result[1]['comment_count'] == '100'
    assert result[2]['views'] == '3000'
    assert 'comment_count' not in result[2]

def test_process_video_data_regex_extraction():
    """Test comment count extraction using regex"""
    video_data = [{
        'video_id': 'test1',
        'statistics': '"commentCount": "75"'
    }]
    result = process_video_data(video_data)
    assert result[0]['comment_count'] == '75'

def test_process_videos_alias():
    """Test that process_videos is an alias for process_video_data"""
    video_data = [{
        'video_id': 'test1',
        'statistics': {
            'viewCount': '1000',
            'commentCount': '50'
        }
    }]
    result1 = process_video_data(video_data)
    result2 = process_videos(video_data)
    assert result1 == result2 