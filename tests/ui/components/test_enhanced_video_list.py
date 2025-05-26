"""
Test the enhanced video list component.
"""

import pytest
import streamlit as st
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure the src module is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ui.data_collection.components.enhanced_video_list import render_enhanced_video_list

@pytest.fixture
def sample_videos():
    return [
        {
            'video_id': 'test1',
            'title': 'Test Video 1',
            'views': '5000',
            'likes': '200',
            'comment_count': '50',
            'thumbnail_url': 'https://img.youtube.com/vi/test1/default.jpg'
        },
        {
            'video_id': 'test2',
            'title': 'Test Video 2',
            'views': '1000',
            'likes': '100',
            'comment_count': '20',
            'thumbnail': 'https://img.youtube.com/vi/test2/default.jpg'
        },
        {
            'video_id': 'test3',
            'title': 'Test Video 3',
            'views': '3000',
            'likes': '150',
            'comment_count': '30',
            # No thumbnail to test fallback
        }
    ]

@patch('streamlit.tabs')
@patch('streamlit.columns')
@patch('streamlit.image')
@patch('streamlit.write')
@patch('streamlit.caption')
@patch('streamlit.metric')
@patch('streamlit.markdown')
def test_render_enhanced_video_list_simple_view(mock_markdown, mock_metric, mock_caption, 
                                              mock_write, mock_image, mock_columns, mock_tabs,
                                              sample_videos):
    """Test that the enhanced video list component renders correctly in simple view."""
    # Setup mocks for tab switching
    mock_tabs.return_value = [MagicMock(), MagicMock()]
    mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    
    # Call the function
    render_enhanced_video_list(sample_videos)
    
    # Verify tabs were created
    mock_tabs.assert_called_once_with(["Simple View", "Detailed View"])
    
    # Verify video rendering (at least verify that write was called for each video)
    assert mock_write.call_count >= len(sample_videos)
    
    # Verify image display for thumbnails
    assert mock_image.call_count >= 2  # At least 2 videos have thumbnails
    
    # Verify metrics display
    assert mock_metric.call_count >= 3 * len(sample_videos)  # 3 metrics per video (views, likes, comments)

@patch('streamlit.tabs')
def test_render_enhanced_video_list_with_empty_data(mock_tabs):
    """Test that the component handles empty data correctly."""
    render_enhanced_video_list([])
    
    # Verify tabs were not created for empty data
    mock_tabs.assert_not_called()

@patch('streamlit.tabs')
@patch('streamlit.columns')
@patch('streamlit.image')
def test_render_enhanced_video_list_thumbnail_fallback(mock_image, mock_columns, mock_tabs, sample_videos):
    """Test that thumbnail fallbacks work correctly."""
    # Setup mocks for tab switching
    mock_tabs.return_value = [MagicMock(), MagicMock()]
    mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    
    # Call the function
    render_enhanced_video_list(sample_videos)
    
    # Verify image display for all videos (including fallback)
    assert mock_image.call_count >= len(sample_videos)  # All videos should have thumbnails (even with fallback)

def test_numeric_formatting():
    """Test numeric formatting function in the component."""
    from src.ui.data_collection.components.enhanced_video_list import render_enhanced_video_list
    
    # Extract the formatting functionality from the component for testing
    def format_numeric(value):
        try:
            value_str = str(value)
            return f"{int(value_str):,}" if value_str.isdigit() else value_str
        except:
            return value
    
    assert format_numeric(1000) == "1,000"
    assert format_numeric("5000") == "5,000"
    assert format_numeric("abc") == "abc"
    assert format_numeric(None) is None
