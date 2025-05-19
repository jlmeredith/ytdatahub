"""
Test API data display in the UI.
Ensures that API response data is properly displayed in the UI and compared with database data.
"""
import pytest
from unittest.mock import MagicMock, patch

# Mock response data
API_CHANNEL_DATA = {
    'channel_id': 'UC123456789',
    'channel_name': 'Test Channel',
    'subscribers': 10000,
    'views': 500000,
    'total_videos': 120,
    'channel_description': 'Test channel description from API',
    'data_source': 'api',
    'video_id': [
        {
            'video_id': 'video1',
            'title': 'Video 1',
            'views': 15000,
            'likes': 800,
            'comment_count': 100
        },
        {
            'video_id': 'video2',
            'title': 'Video 2',
            'views': 25000,
            'likes': 1500,
            'comment_count': 250
        }
    ]
}

DB_CHANNEL_DATA = {
    'channel_id': 'UC123456789',
    'channel_name': 'Test Channel',
    'subscribers': 9500,  # Different from API to show change
    'views': 480000,      # Different from API to show change
    'total_videos': 119,  # Different from API to show change
    'channel_description': 'Test channel description from database',
    'data_source': 'database',
    'video_id': [
        {
            'video_id': 'video1',
            'title': 'Video 1',
            'views': 14000,  # Different from API to show change
            'likes': 750,    # Different from API to show change
            'comment_count': 90  # Different from API to show change
        }
        # Missing video2 to show new video in API data
    ]
}


@pytest.fixture
def mock_st():
    """Create a mock for Streamlit with properly configured column support."""
    mock = MagicMock()
    
    # Configure session state as a dictionary
    mock.session_state = {}
    
    # Configure columns to return multiple column objects
    def mock_columns(n):
        if isinstance(n, int):
            return [MagicMock() for _ in range(n)]
        else:
            # Handle list input like [1, 2, 3]
            return [MagicMock() for _ in range(len(n))]
            
    mock.columns.side_effect = mock_columns
    
    # Configure expander to return a context manager mock
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=MagicMock())
    mock_cm.__exit__ = MagicMock(return_value=None)
    mock.expander.return_value = mock_cm
    
    return mock


def test_api_data_display(mock_st):
    """Test that API data is properly displayed in the UI comparison view."""
    from src.ui.data_collection import render_api_db_comparison
    
    # Setup session state with both API and DB data
    mock_st.session_state = {
        'api_data': API_CHANNEL_DATA,
        'db_data': DB_CHANNEL_DATA,
        'existing_channel_id': 'UC123456789',
        'api_call_status': 'Success: Data fetched from API',
        'compare_data_view': True
    }
    
    # Call the function that renders the comparison view
    render_api_db_comparison(mock_st)
    
    # Verify that metrics were displayed for both DB and API data
    assert mock_st.metric.call_count >= 6, "Should display at least 6 metrics (3 for DB, 3 for API)"
    
    # Verify that data from both sources was used
    metric_values = [call.args[1] for call in mock_st.metric.call_args_list]
    
    # Check for formatted subscriber values
    assert "10K" in str(metric_values), "API subscriber count (10K) should be displayed"
    assert "9.5K" in str(metric_values) or "9500" in str(metric_values), "DB subscriber count (9.5K) should be displayed"
    
    # Verify that API response logs were shown
    mock_st.expander.assert_called_with("API Response Logs")
    
    # Verify that JSON data was displayed
    mock_st.json.assert_called()
    
    # Extract the JSON data that was displayed
    json_data = mock_st.json.call_args[0][0]
    assert json_data['source'] == 'YouTube API', "API source should be displayed"
    assert json_data['channel_id'] == 'UC123456789', "Channel ID should be displayed"
    assert 'subscribers' in json_data['metrics'], "Subscriber count should be in metrics"
    assert 'views' in json_data['metrics'], "View count should be in metrics"
    assert 'videos' in json_data['metrics'], "Video count should be in metrics"


def test_api_db_comparison_with_new_videos(mock_st):
    """Test that new videos in API data are properly highlighted in the comparison view."""
    from src.ui.data_collection import render_api_db_comparison
    
    # Setup session state with both API and DB data
    mock_st.session_state = {
        'api_data': API_CHANNEL_DATA,
        'db_data': DB_CHANNEL_DATA,
        'existing_channel_id': 'UC123456789'
    }
    
    # Call the function that renders the comparison view
    render_api_db_comparison(mock_st)
    
    # Verify that the function detected new videos
    success_calls = [call for call in mock_st.success.call_args_list if "new videos" in str(call)]
    assert success_calls, "Should display success message about new videos"
    
    # Check that the video title was displayed
    write_calls = [call for call in mock_st.write.call_args_list if "Video 2" in str(call)]
    assert write_calls, "New video title should be displayed"


def test_api_db_comparison_with_updated_metrics(mock_st):
    """Test that changes in video metrics are properly displayed in the comparison view."""
    from src.ui.data_collection import render_api_db_comparison
    
    # Setup session state with both API and DB data
    mock_st.session_state = {
        'api_data': API_CHANNEL_DATA,
        'db_data': DB_CHANNEL_DATA,
        'existing_channel_id': 'UC123456789'
    }
    
    # Call the function that renders the comparison view
    render_api_db_comparison(mock_st)
    
    # Check for delta indicators in the metrics
    deltas = [call for call in mock_st.metric.call_args_list if len(call[0]) > 2 and call[0][2] is not None]
    assert deltas, "Should display delta indicators for changed metrics"
    
    # Verify that view count difference was displayed
    view_delta_calls = [call for call in deltas if "500000" in str(call) or "500K" in str(call)]
    assert view_delta_calls, "View count delta should be displayed"


def test_missing_comparison_data(mock_st):
    """Test the behavior when comparison data is missing."""
    from src.ui.data_collection import render_api_db_comparison
    
    # Setup session state with missing data
    mock_st.session_state = {
        'api_data': None,
        'db_data': None,
        'existing_channel_id': 'UC123456789'
    }
    
    # Call the function that renders the comparison view
    render_api_db_comparison(mock_st)
    
    # Should display an error about missing data
    mock_st.error.assert_called_with("Missing comparison data. Please try refreshing the channel data again.")