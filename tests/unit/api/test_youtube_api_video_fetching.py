"""
Test cases for YouTube API video fetching.
"""
import pytest
from unittest.mock import MagicMock, patch
import json

from src.api.youtube_api import YouTubeAPI

@pytest.fixture
def mock_youtube_client():
    """Mock YouTube API client"""
    mock_client = MagicMock()
    return mock_client

@pytest.fixture
def api_with_mock_client(mock_youtube_client):
    """Create YouTube API instance with mock client"""
    api = YouTubeAPI('dummy_key')
    api.youtube = mock_youtube_client
    return api

def test_get_channel_videos_returns_correct_structure(api_with_mock_client, mock_youtube_client):
    """Test that get_channel_videos returns video data with the correct structure"""
    # Mock the channels.list response to return a uploads playlist ID
    channels_response = {
        "items": [
            {
                "contentDetails": {
                    "relatedPlaylists": {
                        "uploads": "UU_test_upload_playlist"
                    }
                }
            }
        ]
    }
    
    # Mock the playlistItems.list response to return some videos
    playlist_response = {
        "items": [
            {
                "snippet": {
                    "title": "Test Video 1",
                    "publishedAt": "2025-01-01T00:00:00Z"
                },
                "contentDetails": {
                    "videoId": "video1"
                }
            },
            {
                "snippet": {
                    "title": "Test Video 2",
                    "publishedAt": "2025-01-02T00:00:00Z"
                },
                "contentDetails": {
                    "videoId": "video2"
                }
            }
        ]
    }
    
    # Set up mock responses
    channels_mock = MagicMock()
    channels_mock.execute.return_value = channels_response
    
    playlist_mock = MagicMock()
    playlist_mock.execute.return_value = playlist_response
    
    # Configure mock methods
    mock_youtube_client.channels.return_value.list.return_value = channels_mock
    mock_youtube_client.playlistItems.return_value.list.return_value = playlist_mock
    
    # Call the get_channel_videos method
    result = api_with_mock_client.get_channel_videos("UC_test_channel")
    
    # Check that the response has the expected structure
    assert result is not None
    assert "channel_id" in result
    assert "video_id" in result
    assert isinstance(result["video_id"], list)
    assert len(result["video_id"]) == 2
    
    # Check that the videos have the expected fields
    video1 = result["video_id"][0]
    assert "video_id" in video1
    assert "title" in video1
    assert "published_at" in video1
    
    assert video1["video_id"] == "video1"
    assert video1["title"] == "Test Video 1"
    
    # Also verify the second video
    assert result["video_id"][1]["video_id"] == "video2"
    assert result["video_id"][1]["title"] == "Test Video 2"
