import pytest
from src.utils.validation import (
    validate_api_key,
    validate_channel_id,
    validate_channel_id_old,
    estimate_quota_usage
)

def test_validate_api_key():
    """Test API key validation"""
    # Test valid API key
    valid_key = "AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8"
    assert validate_api_key(valid_key) is True
    
    # Test invalid lengths
    assert validate_api_key("short") is False
    assert validate_api_key("x" * 60) is False
    
    # Test invalid characters
    assert validate_api_key("AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8!") is False
    assert validate_api_key("AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q7R8 ") is False
    
    # Test edge cases
    assert validate_api_key("") is False
    assert validate_api_key(None) is False

def test_validate_channel_id():
    """Test channel ID validation and extraction"""
    # Test direct channel ID
    channel_id = "UC1234567890123456789012"
    is_valid, extracted = validate_channel_id(channel_id)
    assert is_valid is True
    assert extracted == channel_id
    
    # Test YouTube channel URL
    url = "https://www.youtube.com/channel/UC1234567890123456789012"
    is_valid, extracted = validate_channel_id(url)
    assert is_valid is True
    assert extracted == "UC1234567890123456789012"
    
    # Test custom URL
    custom_url = "https://www.youtube.com/c/ChannelName"
    is_valid, extracted = validate_channel_id(custom_url)
    assert is_valid is False
    assert extracted == "Custom URL: ChannelName (needs resolution)"
    
    # Test handle URL
    handle_url = "https://www.youtube.com/@ChannelHandle"
    is_valid, extracted = validate_channel_id(handle_url)
    assert is_valid is False
    assert extracted == "Handle: @ChannelHandle (needs resolution)"
    
    # Test invalid formats
    assert validate_channel_id("invalid") == (False, "")
    assert validate_channel_id("") == (False, "")
    assert validate_channel_id(None) == (False, "")

def test_validate_channel_id_old():
    """Test legacy channel ID validation"""
    # Test valid channel ID
    assert validate_channel_id_old("UC1234567890123456789012") is True
    
    # Test invalid formats
    assert validate_channel_id_old("invalid") is False
    assert validate_channel_id_old("UC123") is False
    assert validate_channel_id_old("") is False
    assert validate_channel_id_old(None) is False

def test_estimate_quota_usage():
    """Test quota usage estimation"""
    # Test channel only
    assert estimate_quota_usage(fetch_channel=True) == 1
    
    # Test channel and videos
    assert estimate_quota_usage(fetch_channel=True, fetch_videos=True, video_count=25) == 3  # 1 for channel + 1 for video list + 1 for video details
    assert estimate_quota_usage(fetch_channel=True, fetch_videos=True, video_count=75) == 5  # 1 for channel + 2 for video list + 2 for video details
    
    # Test channel, videos, and comments
    assert estimate_quota_usage(
        fetch_channel=True,
        fetch_videos=True,
        fetch_comments=True,
        video_count=25,
        comments_count=10
    ) == 4  # 1 for channel + 1 for video list + 1 for video details + 1 for comments
    
    # Test videos and comments only
    assert estimate_quota_usage(
        fetch_channel=False,
        fetch_videos=True,
        fetch_comments=True,
        video_count=25,
        comments_count=10
    ) == 3  # 1 for video list + 1 for video details + 1 for comments
    
    # Test edge cases
    assert estimate_quota_usage(fetch_channel=False) == 0
    assert estimate_quota_usage(fetch_channel=True, fetch_videos=True, video_count=0) == 1
    assert estimate_quota_usage(fetch_channel=True, fetch_videos=True, fetch_comments=True, video_count=0) == 1 