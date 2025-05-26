"""
Integration tests for video views display in the YouTube channel refresh UI
"""
import pytest
import streamlit as st
import pandas as pd
from unittest.mock import MagicMock, patch
from src.ui.data_collection.channel_refresh_ui import channel_refresh_section
from src.utils.video_formatter import extract_video_views, fix_missing_views
from src.utils.video_processor import process_video_data

# Sample video data with different view count structures
SAMPLE_VIDEOS = [
    {
        "video_id": "video1",
        "title": "Video with direct views",
        "published_at": "2025-05-01T12:00:00Z",
        "views": "5000"
    },
    {
        "video_id": "video2",
        "title": "Video with statistics.viewCount",
        "published_at": "2025-05-02T12:00:00Z",
        "statistics": {
            "viewCount": "7500",
            "likeCount": "500"
        }
    },
    {
        "video_id": "video3",
        "title": "Video with nested viewCount",
        "published_at": "2025-05-03T12:00:00Z",
        "contentDetails": {
            "statistics": {
                "viewCount": "10000"
            }
        }
    },
    {
        "video_id": "video4",
        "title": "Video with placeholder views",
        "published_at": "2025-05-04T12:00:00Z",
        "views": "0"
    },
    {
        "video_id": "video5",
        "title": "Video with no view data",
        "published_at": "2025-05-05T12:00:00Z"
    }
]

# Test specifically for the issue where videos don't display in the new channel workflow
def test_new_channel_workflow_video_processing():
    """Test that the video processing functions work correctly for the new channel workflow"""
    # Create sample raw API response videos
    raw_videos = [
        {
            "video_id": "testvid1",
            "title": "Test Video 1",
            "statistics": {
                "viewCount": "5000",
                "likeCount": "200",
                "commentCount": "50"
            }
        },
        {
            "video_id": "testvid2",
            "title": "Test Video 2",
            "statistics": {}  # Missing view count
        }
    ]
    
    # Process the videos as done in the new channel workflow
    processed_videos = process_video_data(raw_videos)
    fixed_videos = fix_missing_views(processed_videos)
    
    # Check that the first video has views correctly extracted
    assert processed_videos[0]["views"] == "5000"
    assert processed_videos[0]["comment_count"] == "50"
    
    # Check that the second video has default values for missing data
    assert processed_videos[1]["views"] == "0"
    
    # Verify fix_missing_views doesn't change existing valid values
    assert fixed_videos[0]["views"] == "5000"
    assert fixed_videos[0]["comment_count"] == "50"

@pytest.fixture
def mock_youtube_service():
    """Create a mock YouTube service for testing"""
    mock_service = MagicMock()
    
    # Mock channel list method
    mock_service.get_channels_list.return_value = [
        {"channel_id": "UC12345", "channel_name": "Test Channel"}
    ]
    
    # Mock update_channel_data method to return our sample videos
    mock_service.update_channel_data.return_value = {
        "api_data": {
            "video_id": SAMPLE_VIDEOS
        }
    }
    
    # Mock save_channel_data to always succeed
    mock_service.save_channel_data.return_value = True
    
    return mock_service

@pytest.mark.parametrize("video_idx,expected_views", [
    (0, "5000"),  # Direct views
    (1, "7500"),  # statistics.viewCount
    (2, "10000"),  # nested viewCount
    (3, "0"),     # placeholder zero
    (4, "0")      # no view data
])
def test_video_views_extraction(video_idx, expected_views):
    """Test that view extraction works for various video structures"""
    video = SAMPLE_VIDEOS[video_idx]
    views = extract_video_views(video)
    assert views == expected_views

def test_fix_missing_views_processing():
    """Test that fix_missing_views properly processes all view data structures"""
    fixed_videos = fix_missing_views(SAMPLE_VIDEOS)
    
    # Check each video has views set correctly
    assert fixed_videos[0]["views"] == "5000"
    assert fixed_videos[1]["views"] == "7500"
    assert fixed_videos[2]["views"] == "10000"
    assert fixed_videos[3]["views"] == "0"
    assert fixed_videos[4]["views"] == "0"
    
    # Check that videos with zero views have '0' value (no special display placeholder)
    assert fixed_videos[3]['views'] == '0'
    assert fixed_videos[4]['views'] == '0'
    assert 'views_display' not in fixed_videos[3], "Should not have views_display field"
    assert 'views_display' not in fixed_videos[4], "Should not have views_display field"

@patch('streamlit.title')
@patch('streamlit.subheader')
@patch('streamlit.write')
@patch('streamlit.selectbox')
@patch('streamlit.button')
@patch('streamlit.spinner')
@patch('streamlit.success')
@patch('streamlit.dataframe')
def test_ui_displays_views_in_video_table(mock_dataframe, mock_success, mock_spinner, 
                                          mock_button, mock_selectbox, mock_write, 
                                          mock_subheader, mock_title, mock_youtube_service):
    """Test that the UI correctly displays video views in video table"""
    # Configure session state
    st.session_state['existing_channel_id'] = "UC12345"
    st.session_state['videos_data'] = SAMPLE_VIDEOS
    st.session_state['videos_fetched'] = True
    
    # Mock the format_number function to return plain numbers as strings
    with patch('src.ui.data_collection.channel_refresh.video_section.format_number',
                   side_effect=lambda x: str(x)):
        
        # Test the video section directly instead of going through the workflow
        from src.ui.data_collection.channel_refresh.video_section import render_video_section
        render_video_section(SAMPLE_VIDEOS, mock_youtube_service, "UC12345")
        
        # Check that dataframe was called
        mock_dataframe.assert_called()
        
        # Get the args passed to dataframe
        df = None
        for call in mock_dataframe.call_args_list:
            args, kwargs = call
            if args and isinstance(args[0], pd.DataFrame):
                df = args[0]
                break
        
        assert df is not None, "DataFrame was not passed to st.dataframe()"
        
        # Check that views are present in the dataframe
        assert "Views" in df.columns
        
        # Verify views are populated (note: the fix_missing_views function 
        # should have processed the views before display)
        views = df["Views"].tolist()
        assert any(v != "0" for v in views), "No non-zero views found in the dataframe"
        
        # The first video should show 5000 views
        assert "5000" in views
        
        # Videos with zero views should display "0"
        assert "0" in views, "Missing '0' for videos with no view data"
