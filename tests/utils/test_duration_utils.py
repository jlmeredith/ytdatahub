import pytest
from src.utils.duration_utils import (
    parse_duration_with_regex,
    duration_to_seconds,
    format_duration,
    format_duration_human_friendly
)

def test_parse_duration_with_regex():
    """Test parsing of ISO 8601 duration strings"""
    # Test empty string
    assert parse_duration_with_regex("") == 0
    
    # Test hours only
    assert parse_duration_with_regex("PT1H") == 3600
    assert parse_duration_with_regex("PT2H") == 7200
    
    # Test minutes only
    assert parse_duration_with_regex("PT1M") == 60
    assert parse_duration_with_regex("PT30M") == 1800
    
    # Test seconds only
    assert parse_duration_with_regex("PT1S") == 1
    assert parse_duration_with_regex("PT30S") == 30
    
    # Test combinations
    assert parse_duration_with_regex("PT1H2M3S") == 3723  # 1 hour, 2 minutes, 3 seconds
    assert parse_duration_with_regex("PT2H30M15S") == 9015  # 2 hours, 30 minutes, 15 seconds
    
    # Test invalid formats
    assert parse_duration_with_regex("invalid") == 0
    assert parse_duration_with_regex("PT") == 0

def test_duration_to_seconds():
    """Test conversion of duration strings to seconds"""
    # Test ISO 8601 format
    assert duration_to_seconds("PT1H2M3S") == 3723
    
    # Test empty string
    assert duration_to_seconds("") == 0
    
    # Test invalid format
    assert duration_to_seconds("invalid") == 0

def test_format_duration():
    """Test formatting of durations"""
    # Test with ISO 8601 strings
    assert format_duration("PT1H2M3S") == "1:02:03"
    assert format_duration("PT2H30M15S") == "2:30:15"
    assert format_duration("PT5M30S") == "5:30"
    assert format_duration("PT1M5S") == "1:05"
    
    # Test with seconds
    assert format_duration(3723) == "1:02:03"  # 1 hour, 2 minutes, 3 seconds
    assert format_duration(90) == "1:30"  # 1 minute, 30 seconds
    assert format_duration(45) == "0:45"  # 45 seconds
    
    # Test edge cases
    assert format_duration("") == "0:00"
    assert format_duration(None) == "0:00"
    assert format_duration(0) == "0:00"
    assert format_duration(-1) == "0:00"

def test_format_duration_human_friendly():
    """Test human-friendly duration formatting"""
    # Test hours
    assert format_duration_human_friendly(3600) == "1 hour"
    assert format_duration_human_friendly(7200) == "2 hours"
    
    # Test minutes
    assert format_duration_human_friendly(60) == "1 minute"
    assert format_duration_human_friendly(90) == "1 minute and 30 seconds"
    assert format_duration_human_friendly(120) == "2 minutes"
    
    # Test seconds
    assert format_duration_human_friendly(1) == "1 second"
    assert format_duration_human_friendly(30) == "30 seconds"
    
    # Test combinations
    assert format_duration_human_friendly(3723) == "1 hour, 2 minutes, and 3 seconds"
    assert format_duration_human_friendly(3661) == "1 hour and 1 second"
    assert format_duration_human_friendly(61) == "1 minute and 1 second"
    
    # Test edge cases
    assert format_duration_human_friendly(0) == "0 seconds"
    assert format_duration_human_friendly(None) == "0 seconds"
    assert format_duration_human_friendly(-1) == "0 seconds" 