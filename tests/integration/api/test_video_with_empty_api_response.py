"""
Integration test for handling videos with no view count data in API response
"""
import pytest
import streamlit as st
import pandas as pd
from unittest.mock import MagicMock, patch
from src.utils.video_formatter import extract_video_views, fix_missing_views
from src.ui.data_collection.utils.data_conversion import format_number

def test_video_with_empty_api_response():
    """Test handling of a video with an API response that does not contain view count data"""
    # This represents a video like the one in the screenshot with no viewCount
    video_with_no_viewcount = {
        "video_id": "kcumCHQZAdQ",
        "title": "New song named elbow to the face.",
        "published_at": "2024-10-10T09:58:50Z",
        "snippet": {
            "publishedAt": "2024-10-10T09:58:50Z",
            "title": "New song named elbow to the face."
        },
        "contentDetails": {
            "duration": "PT3M32S"
        },
        "statistics": {}  # Empty statistics, matches what was shown in the screenshot
    }
    
    # Test that extract_video_views returns '0'
    raw_views = extract_video_views(video_with_no_viewcount)
    assert raw_views == '0', "Should return '0' for videos with no view data"
    
    # Test with formatting function
    formatted_views = extract_video_views(video_with_no_viewcount, format_number)
    assert formatted_views != 'Not Available', "Should not return 'Not Available'"
    assert formatted_views == format_number('0'), "Should return formatted '0'"
    
    # Test fix_missing_views function
    fixed_videos = fix_missing_views([video_with_no_viewcount])
    assert fixed_videos[0]['views'] == '0', "Should set views to '0'"
    assert 'views_display' not in fixed_videos[0], "Should not add views_display field"
    
    # Test the full UI display logic as it happens in channel_refresh_ui.py
    # format_number is already imported at the top of the file
    
    # Simulate what happens in channel_refresh_ui.py
    views = extract_video_views(fixed_videos[0], format_number)
    if views == '0':
        views = format_number('0') if format_number else '0'
    
    # Verify the final display value
    assert views == format_number('0'), "Final display value should be formatted '0'"
    assert views != 'Not Available', "Final display value should not be 'Not Available'"
    assert fixed_videos[0]['views'] == '0', "Should set views to '0'"
    assert 'views_display' not in fixed_videos[0], "Should not add views_display field"

    # Simulate what happens in channel_refresh_ui.py
    views = extract_video_views(fixed_videos[0], format_number)
    if views == '0':
        views = format_number('0') if format_number else '0'
    
    # Verify the final display value
    assert views == format_number('0'), "Final display value should be formatted '0'"
    assert views != 'Not Available', "Final display value should not be 'Not Available'"
