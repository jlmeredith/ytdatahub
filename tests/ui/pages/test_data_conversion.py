"""
Tests for data conversion functionality in the data collection UI.
"""
import pytest
import pandas as pd
import logging
import os
import sys
from unittest.mock import MagicMock

# Ensure working directory is correct for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ui.data_collection import convert_db_to_api_format


class TestDataConversion:
    """Tests for data conversion functions in the data collection UI."""

    @pytest.fixture
    def mock_channel_data(self):
        """Create mock channel data from database."""
        return {
            "channel_info": {
                "id": "UC_test_channel",
                "title": "Test Channel",
                "description": "This is a test channel",
                "statistics": {
                    "subscriberCount": "10000",
                    "viewCount": "5000000",
                    "videoCount": "50"
                },
                "contentDetails": {
                    "relatedPlaylists": {
                        "uploads": "UU_test_channel_uploads"
                    }
                }
            },
            "videos": [
                {
                    "id": "video123",
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test video description", 
                        "publishedAt": "2025-04-01T12:00:00Z"
                    },
                    "statistics": {
                        "viewCount": "15000",
                        "likeCount": "1200",
                        "commentCount": "300"
                    },
                    "contentDetails": {
                        "duration": "PT10M30S"
                    }
                }
            ]
        }

    def test_convert_db_to_api_format(self, mock_channel_data):
        """Test the conversion from database format to API format."""
        # Enable debug logging to see what's happening
        logging.basicConfig(level=logging.DEBUG)
        
        # Convert the data
        api_data = convert_db_to_api_format(mock_channel_data)
        
        # Verify the conversion worked correctly
        assert api_data is not None, "API data should not be None"
        assert api_data["channel_id"] == "UC_test_channel"
        assert api_data["channel_name"] == "Test Channel"
        assert api_data["subscribers"] == 10000
        assert api_data["views"] == 5000000
        assert api_data["total_videos"] == 50
        assert api_data["playlist_id"] == "UU_test_channel_uploads"
        
        # Verify video conversion
        assert len(api_data["video_id"]) == 1
        assert api_data["video_id"][0]["video_id"] == "video123"
        assert api_data["video_id"][0]["title"] == "Test Video"

    def test_missing_channel_info(self):
        """Test handling of missing channel info in the conversion function."""
        # Test with empty data
        empty_data = {}
        api_data = convert_db_to_api_format(empty_data)
        assert api_data is not None, "Should handle empty data gracefully"
        
        # Test with partial data
        partial_data = {"channel_info": {"id": "UC_test_channel", "title": "Test Channel"}}
        api_data = convert_db_to_api_format(partial_data)
        assert api_data is not None, "Should handle partial data gracefully"
        assert api_data["channel_id"] == "UC_test_channel"
        assert api_data["channel_name"] == "Test Channel"
