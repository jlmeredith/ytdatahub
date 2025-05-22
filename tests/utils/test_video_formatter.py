import pytest
from src.utils.video_formatter import (
    ensure_views_data,
    extract_video_views,
    fix_missing_views
)

def test_ensure_views_data():
    """Test ensuring views data is properly set"""
    # Test empty input
    assert ensure_views_data([]) == []
    assert ensure_views_data(None) is None
    
    # Test video with direct views
    video_data = [{
        'video_id': 'test1',
        'views': '1000'
    }]
    result = ensure_views_data(video_data)
    assert result[0]['views'] == '1000'
    
    # Test video with statistics
    video_data = [{
        'video_id': 'test2',
        'statistics': {
            'viewCount': '2000',
            'commentCount': '50'
        }
    }]
    result = ensure_views_data(video_data)
    assert result[0]['views'] == '2000'
    assert result[0]['comment_count'] == '50'
    
    # Test video with placeholder views
    video_data = [{
        'video_id': 'test3',
        'views': '0',
        'statistics': {
            'viewCount': '3000'
        }
    }]
    result = ensure_views_data(video_data)
    assert result[0]['views'] == '3000'
    
    # Test video with no views data
    video_data = [{
        'video_id': 'test4'
    }]
    result = ensure_views_data(video_data)
    assert result[0]['views'] == '0'

def test_extract_video_views():
    """Test extracting views from video data"""
    # Test direct views field
    video = {
        'video_id': 'test1',
        'views': '1000'
    }
    assert extract_video_views(video) == '1000'
    
    # Test statistics.viewCount
    video = {
        'video_id': 'test2',
        'statistics': {
            'viewCount': '2000'
        }
    }
    assert extract_video_views(video) == '2000'
    
    # Test contentDetails.statistics.viewCount
    video = {
        'video_id': 'test3',
        'contentDetails': {
            'statistics': {
                'viewCount': '3000'
            }
        }
    }
    assert extract_video_views(video) == '3000'
    
    # Test snippet.statistics.viewCount
    video = {
        'video_id': 'test4',
        'snippet': {
            'statistics': {
                'viewCount': '4000'
            }
        }
    }
    assert extract_video_views(video) == '4000'
    
    # Test with formatting function
    def format_views(views):
        return f"{int(views):,}"
    
    video = {
        'video_id': 'test5',
        'views': '5000'
    }
    assert extract_video_views(video, format_views) == '5,000'
    
    # Test invalid inputs
    assert extract_video_views(None) == '0'
    assert extract_video_views({}) == '0'
    assert extract_video_views({'views': '0'}) == '0'

def test_fix_missing_views():
    """Test fixing missing views data"""
    # Test empty input
    assert fix_missing_views([]) == []
    assert fix_missing_views(None) is None
    
    # Test video with valid views
    video_data = [{
        'video_id': 'test1',
        'views': '1000',
        'statistics': {
            'commentCount': '50'
        }
    }]
    result = fix_missing_views(video_data)
    assert result[0]['views'] == '1000'
    assert result[0]['comment_count'] == '50'
    
    # Test video with missing views but statistics
    video_data = [{
        'video_id': 'test2',
        'statistics': {
            'viewCount': '2000',
            'commentCount': '100'
        }
    }]
    result = fix_missing_views(video_data)
    assert result[0]['views'] == '2000'
    assert result[0]['comment_count'] == '100'
    
    # Test video with empty statistics
    video_data = [{
        'video_id': 'test3',
        'statistics': {}
    }]
    result = fix_missing_views(video_data)
    assert result[0]['views'] == '0'
    
    # Test video with no views or statistics
    video_data = [{
        'video_id': 'test4'
    }]
    result = fix_missing_views(video_data)
    assert result[0]['views'] == '0'
    
    # Test multiple videos
    video_data = [
        {
            'video_id': 'test5',
            'views': '5000'
        },
        {
            'video_id': 'test6',
            'statistics': {
                'viewCount': '6000'
            }
        },
        {
            'video_id': 'test7'
        }
    ]
    result = fix_missing_views(video_data)
    assert result[0]['views'] == '5000'
    assert result[1]['views'] == '6000'
    assert result[2]['views'] == '0'

def test_fix_missing_views_with_valid_statistics():
    """Test fixing views when statistics are present"""
    videos = [{
        'video_id': 'test123',
        'title': 'Test Video',
        'statistics': {
            'viewCount': '1000',
            'likeCount': '100',
            'commentCount': '50'
        }
    }]
    
    result = fix_missing_views(videos)
    video = result[0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'

def test_fix_missing_views_with_missing_statistics():
    """Test fixing views when statistics are missing"""
    videos = [{
        'video_id': 'test123',
        'title': 'Test Video'
    }]
    
    result = fix_missing_views(videos)
    video = result[0]
    assert video['views'] == '0'
    assert video['likes'] == '0'
    assert video['comment_count'] == '0'

def test_fix_missing_views_with_empty_statistics():
    """Test fixing views when statistics object is empty"""
    videos = [{
        'video_id': 'test123',
        'title': 'Test Video',
        'statistics': {}
    }]
    
    result = fix_missing_views(videos)
    video = result[0]
    assert video['views'] == '0'
    assert video['likes'] == '0'
    assert video['comment_count'] == '0'

def test_fix_missing_views_with_string_statistics():
    """Test fixing views when statistics is a string"""
    videos = [{
        'video_id': 'test123',
        'title': 'Test Video',
        'statistics': '{"viewCount": "1000", "likeCount": "100", "commentCount": "50"}'
    }]
    
    result = fix_missing_views(videos)
    video = result[0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'

def test_fix_missing_views_with_nested_statistics():
    """Test fixing views when statistics is nested"""
    videos = [{
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
    
    result = fix_missing_views(videos)
    video = result[0]
    assert video['views'] == '1000'
    assert video['likes'] == '100'
    assert video['comment_count'] == '50'

def test_fix_missing_views_with_multiple_videos():
    """Test fixing views for multiple videos"""
    videos = [
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
        }
    ]
    
    result = fix_missing_views(videos)
    assert result[0]['views'] == '1000'
    assert result[0]['likes'] == '100'
    assert result[0]['comment_count'] == '50'
    assert result[1]['views'] == '0'
    assert result[1]['likes'] == '0'
    assert result[1]['comment_count'] == '0'

def test_extract_video_views_with_valid_statistics():
    """Test extracting views when statistics are present"""
    video = {
        'video_id': 'test123',
        'statistics': {
            'viewCount': '1000'
        }
    }
    
    result = extract_video_views(video)
    assert result == '1000'

def test_extract_video_views_with_missing_statistics():
    """Test extracting views when statistics are missing"""
    video = {
        'video_id': 'test123'
    }
    
    result = extract_video_views(video)
    assert result == '0'

def test_extract_video_views_with_empty_statistics():
    """Test extracting views when statistics object is empty"""
    video = {
        'video_id': 'test123',
        'statistics': {}
    }
    
    result = extract_video_views(video)
    assert result == '0'

def test_extract_video_views_with_string_statistics():
    """Test extracting views when statistics is a string"""
    video = {
        'video_id': 'test123',
        'statistics': '{"viewCount": "1000"}'
    }
    
    result = extract_video_views(video)
    assert result == '1000'

def test_extract_video_views_with_nested_statistics():
    """Test extracting views when statistics is nested"""
    video = {
        'video_id': 'test123',
        'contentDetails': {
            'statistics': {
                'viewCount': '1000'
            }
        }
    }
    
    result = extract_video_views(video)
    assert result == '1000'

def test_extract_video_views_with_formatting():
    """Test extracting views with formatting function"""
    video = {
        'video_id': 'test123',
        'statistics': {
            'viewCount': '1000'
        }
    }
    
    def format_views(views):
        return f"{int(views):,}"
    
    result = extract_video_views(video, format_views)
    assert result == '1,000' 