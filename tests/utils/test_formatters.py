import pytest
from datetime import timedelta
from src.utils.formatters import (
    format_number,
    format_duration,
    duration_to_seconds,
    format_timedelta,
    get_thumbnail_url,
    get_location_display
)

def test_format_number():
    """Test number formatting"""
    # Test billions
    assert format_number(1_500_000_000) == "1.5B"
    assert format_number(2_000_000_000) == "2B"
    
    # Test millions
    assert format_number(1_500_000) == "1.5M"
    assert format_number(2_000_000) == "2M"
    
    # Test thousands
    assert format_number(1_500) == "1.5K"
    assert format_number(2_000) == "2K"
    
    # Test small numbers
    assert format_number(500) == "500"
    assert format_number(0) == "0"
    
    # Test string inputs
    assert format_number("1500") == "1.5K"
    assert format_number("2000000") == "2M"
    
    # Test edge cases
    assert format_number(None) == "0"
    assert format_number("invalid") == "invalid"

def test_format_duration():
    """Test duration formatting"""
    # Test hours, minutes, seconds
    assert format_duration("PT1H2M3S") == "1:02:03"
    assert format_duration("PT2H30M15S") == "2:30:15"
    
    # Test minutes and seconds only
    assert format_duration("PT5M30S") == "5:30"
    assert format_duration("PT1M5S") == "1:05"
    
    # Test seconds only
    assert format_duration("PT30S") == "0:30"
    
    # Test edge cases
    assert format_duration("") == "0:00"
    assert format_duration(None) == "0:00"
    assert format_duration("invalid") == "0:00"

def test_duration_to_seconds():
    """Test duration to seconds conversion"""
    # Test hours, minutes, seconds
    assert duration_to_seconds("PT1H2M3S") == 3723  # 1 hour, 2 minutes, 3 seconds
    assert duration_to_seconds("PT2H30M15S") == 9015  # 2 hours, 30 minutes, 15 seconds
    
    # Test minutes and seconds only
    assert duration_to_seconds("PT5M30S") == 330  # 5 minutes, 30 seconds
    assert duration_to_seconds("PT1M5S") == 65  # 1 minute, 5 seconds
    
    # Test seconds only
    assert duration_to_seconds("PT30S") == 30
    
    # Test edge cases
    assert duration_to_seconds("") == 0
    assert duration_to_seconds(None) == 0
    assert duration_to_seconds("invalid") == 0

def test_format_timedelta():
    """Test timedelta formatting"""
    # Test seconds
    assert format_timedelta(timedelta(seconds=30)) == "30 seconds ago"
    assert format_timedelta(timedelta(seconds=1)) == "1 second ago"
    
    # Test minutes
    assert format_timedelta(timedelta(minutes=30)) == "30 minutes ago"
    assert format_timedelta(timedelta(minutes=1)) == "1 minute ago"
    
    # Test hours
    assert format_timedelta(timedelta(hours=5)) == "5 hours ago"
    assert format_timedelta(timedelta(hours=1)) == "1 hour ago"
    
    # Test days
    assert format_timedelta(timedelta(days=2)) == "2 days ago"
    assert format_timedelta(timedelta(days=1)) == "1 day ago"

def test_get_thumbnail_url():
    """Test thumbnail URL extraction"""
    # Test with full thumbnail data
    video_data = {
        'snippet': {
            'thumbnails': {
                'maxres': {'url': 'https://example.com/maxres.jpg'},
                'standard': {'url': 'https://example.com/standard.jpg'},
                'high': {'url': 'https://example.com/high.jpg'},
                'medium': {'url': 'https://example.com/medium.jpg'},
                'default': {'url': 'https://example.com/default.jpg'}
            }
        }
    }
    assert get_thumbnail_url(video_data) == 'https://example.com/maxres.jpg'
    
    # Test with direct thumbnail URL
    video_data = {'thumbnail_url': 'https://example.com/thumb.jpg'}
    assert get_thumbnail_url(video_data) == 'https://example.com/thumb.jpg'
    
    # Test with missing thumbnails
    video_data = {'snippet': {}}
    assert get_thumbnail_url(video_data) == 'https://i.ytimg.com/vi/default/hqdefault.jpg'
    
    # Test with invalid data
    assert get_thumbnail_url({}) == 'https://i.ytimg.com/vi/default/hqdefault.jpg'
    assert get_thumbnail_url(None) == 'https://i.ytimg.com/vi/default/hqdefault.jpg'

def test_get_location_display():
    """Test location display formatting"""
    # Test with recording details
    video_data = {
        'recordingDetails': {
            'location': {
                'latitude': 51.5074,
                'longitude': -0.1278
            },
            'locationDescription': 'London, UK'
        }
    }
    assert get_location_display(video_data) == '📍 51.51, -0.13 (London, UK)'
    
    # Test with coordinates only
    video_data = {
        'recordingDetails': {
            'location': {
                'latitude': 51.5074,
                'longitude': -0.1278
            }
        }
    }
    assert get_location_display(video_data) == '📍 51.51, -0.13'
    
    # Test with description only
    video_data = {
        'recordingDetails': {
            'locationDescription': 'London, UK'
        }
    }
    assert get_location_display(video_data) == '📍 London, UK'
    
    # Test with alternative location format
    video_data = {
        'location': {
            'latitude': 51.5074,
            'longitude': -0.1278
        }
    }
    assert get_location_display(video_data) == '📍 51.51, -0.13'
    
    # Test with no location data
    assert get_location_display({}) == ''
    assert get_location_display(None) == '' 