"""
Unit tests for utility helpers.
"""
import pytest
import time

from src.utils.debug_utils import debug_log
from src.utils.formatters import format_number, format_duration
from src.utils.duration_utils import duration_to_seconds
from src.utils.validation import validate_api_key, validate_channel_id

# Test formatting functions
def test_format_number():
    """Test format_number function for human-readable formatting"""
    assert format_number(1000) == "1K"
    assert format_number(1500) == "1.5K"
    assert format_number(1000000) == "1M"
    assert format_number(1500000) == "1.5M"
    assert format_number(1000000000) == "1B"
    assert format_number(1500000000) == "1.5B"
    assert format_number(123) == "123"
    assert format_number("50000") == "50K"
    assert format_number(None) == "0"

def test_format_duration():
    """Test format_duration function for YouTube duration strings"""
    assert format_duration("PT1H30M15S") == "1:30:15"
    assert format_duration("PT30M15S") == "30:15"
    assert format_duration("PT15S") == "0:15"
    assert format_duration("PT1H") == "1:00:00"
    assert format_duration("PT1H15S") == "1:00:15"
    assert format_duration(None) == "0:00"
    assert format_duration("") == "0:00"

def test_duration_to_seconds():
    """Test duration_to_seconds conversion function"""
    assert duration_to_seconds("PT1H30M15S") == 5415
    assert duration_to_seconds("PT30M15S") == 1815
    assert duration_to_seconds("PT15S") == 15
    assert duration_to_seconds("PT1H") == 3600
    assert duration_to_seconds(None) == 0
    assert duration_to_seconds("") == 0

def test_validate_api_key():
    """Test API key validation function"""
    # Valid keys (format only, not actual valid keys)
    assert validate_api_key("AIzaSyBqLLOlz9RCcJ_oC12345678901234567890") == True
    assert validate_api_key("AIzaSy-abcDefgHiJk_LMnoPqrstuvwXYZ123456") == True
    
    # Invalid keys
    assert validate_api_key("") == False
    assert validate_api_key("too_short") == False
    assert validate_api_key("invalid@characters$") == False
    assert validate_api_key("AI" + "a" * 50) == False  # Too long

def test_validate_channel_id():
    """Test channel ID validation and extraction"""
    # Direct channel ID
    assert validate_channel_id("UC_test1234567890123456789") == (True, "UC_test1234567890123456789")
    
    # URL with channel ID
    assert validate_channel_id("https://www.youtube.com/channel/UC_test1234567890123456789") == (True, "UC_test1234567890123456789")
    
    # Custom URL (needs resolution)
    result = validate_channel_id("https://www.youtube.com/c/TestChannel")
    assert result[0] == False
    assert "Custom URL" in result[1]
    
    # Handle (needs resolution)
    result = validate_channel_id("https://www.youtube.com/@TestChannel")
    assert result[0] == False
    assert "Handle" in result[1]
    
    # Invalid
    assert validate_channel_id("") == (False, "")
    assert validate_channel_id("invalid") == (False, "")


if __name__ == '__main__':
    pytest.main()