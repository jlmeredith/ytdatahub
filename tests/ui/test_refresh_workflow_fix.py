"""
Test the fixes applied to the refresh channel workflow.
"""
import pytest
from unittest.mock import MagicMock, patch
import streamlit as st
import pandas as pd

# Mock session_state
@pytest.fixture
def mock_session_state():
    with patch("streamlit.session_state", {}) as mock_state:
        yield mock_state

# Create API response sample
@pytest.fixture
def api_response():
    return {
        "channel_id": "UC12345",
        "video_id": [
            {
                "video_id": "vid123",
                "title": "Test Video",
                "statistics": {
                    "viewCount": "5000",
                    "likeCount": "100",
                    "commentCount": "50"
                }
            },
            {
                "video_id": "vid456",
                "title": "Another Video",
                "statistics": {
                    "viewCount": "3000",
                    "likeCount": "75",
                    "commentCount": "25"
                }
            }
        ]
    }

def test_processing_videos_in_refresh_workflow():
    """Test that videos are properly processed in the refresh workflow."""
    from src.utils.video_processor import process_video_data
    from src.utils.video_formatter import fix_missing_views
    
    # Start with some video data similar to what the API would return
    videos = [
        {
            "video_id": "video123",
            "title": "Test Video", 
            "statistics": {"viewCount": "1000", "commentCount": "50"}
        },
        {
            "video_id": "video456",
            "title": "Another Video",
            "statistics": {"viewCount": "2000", "commentCount": "75"}
        }
    ]
    
    # Process videos using the utility functions
    processed_videos = process_video_data(videos)
    
    # Verify processing was done correctly
    assert processed_videos[0].get('views') == "1000"
    assert processed_videos[0].get('comment_count') == "50"
    assert processed_videos[1].get('views') == "2000"
    assert processed_videos[1].get('comment_count') == "75"
    
    # Now apply fix_missing_views which should not change anything
    # since values are already set
    fixed_videos = fix_missing_views(processed_videos)
    
    # Verify fix_missing_views doesn't break anything
    assert fixed_videos[0].get('views') == "1000"
    assert fixed_videos[0].get('comment_count') == "50"
    assert fixed_videos[1].get('views') == "2000"
    assert fixed_videos[1].get('comment_count') == "75"

def test_dataframe_creation_with_strings():
    """Test that creating a dataframe with string values works correctly."""
    # Create a list of dictionaries with string values
    data = [
        {"Video ID": str("video123"), "Title": str("Test Video"), "Views": str("1000")},
        {"Video ID": str("video456"), "Title": str("Another Video"), "Views": str("2000")}
    ]
    
    # Create a dataframe
    df = pd.DataFrame(data)
    
    # Verify dataframe was created correctly
    assert len(df) == 2
    assert df["Video ID"][0] == "video123"
    assert df["Views"][1] == "2000"

def test_button_keys_uniqueness():
    """
    Test that all buttons in the refresh workflow have unique keys.
    This is a static analysis test that doesn't need to run the workflow.
    """
    import os
    import re
    
    # Path to the refresh workflow file
    workflow_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                "src", "ui", "data_collection", "refresh_channel_workflow.py")
    
    # Path to the video section file
    video_section_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "src", "ui", "data_collection", "channel_refresh", "video_section.py")
    
    # Regular expression to find button keys
    button_key_pattern = r'st\.button\([^)]*key="([^"]+)"'
    
    # Read the files
    keys = []
    
    with open(workflow_file, 'r') as f:
        workflow_content = f.read()
        for match in re.finditer(button_key_pattern, workflow_content):
            keys.append(match.group(1))
    
    with open(video_section_file, 'r') as f:
        section_content = f.read()
        for match in re.finditer(button_key_pattern, section_content):
            keys.append(match.group(1))
    
    # Verify keys are unique
    assert len(keys) == len(set(keys)), "Button keys are not unique"
