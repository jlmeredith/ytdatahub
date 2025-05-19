"""
Tests focusing on recovery strategies during data collection failures.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging
from googleapiclient.errors import HttpError
import json

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.integration.workflow.test_data_collection_workflow import BaseYouTubeTestCase


class TestRecoveryStrategies(BaseYouTubeTestCase):
    """Tests focusing on recovery strategies after failures"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_partial_data_storage(self, setup_service_with_mocks):
        """Test storing partial data when full collection fails"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to return channel data but fail on videos
        mock_api.get_channel_info.return_value = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "subscribers": "1000"
        }
        mock_api.get_channel_videos.side_effect = Exception("API error")
        
        # Test processing channel and its videos
        result = service.process_channel_and_videos_with_recovery("UC_test_channel")
        
        # Verify partial data was saved
        assert result is not None
        assert mock_db.save_channel.called
        assert mock_db.save_error_log.called
    
    def test_resume_from_checkpoint(self, setup_service_with_mocks):
        """Test resuming collection from last checkpoint"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock DB to return a checkpoint
        mock_db.get_collection_checkpoint.return_value = {
            "channel_id": "UC_test_channel",
            "completed_videos": ["video1", "video2"],
            "pending_videos": ["video3", "video4", "video5"]
        }
        
        # Configure API to return valid video data
        mock_api.get_video_details.return_value = {
            "video_id": "test_id",
            "title": "Test Video",
            "view_count": "1000"
        }
        
        # Test resuming collection
        result = service.resume_collection_from_checkpoint("UC_test_channel")
        
        # Verify only pending videos were processed
        assert result is not None
        assert mock_api.get_video_details.call_count == 3
        assert mock_db.save_video.call_count == 3
    
    def test_data_validation_and_repair(self, setup_service_with_mocks):
        """Test validating and repairing inconsistent data"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock DB to return inconsistent data
        mock_db.get_channel_stats.return_value = {
            "video_count": 10,
            "actual_videos": 8  # Missing videos
        }
        
        # Configure mock API for refresh
        mock_api.get_channel_videos.return_value = [
            {"video_id": f"video_{i}"} for i in range(10)
        ]
        mock_api.get_video_details.return_value = {
            "video_id": "test_id",
            "title": "Test Video"
        }
        
        # Test validation and repair
        result = service.validate_and_repair_channel_data("UC_test_channel")
        
        # Verify repair was attempted and data was fixed
        assert result
        assert mock_api.get_channel_videos.called
        assert mock_db.save_video.call_count == 2  # Only missing videos
    
    def test_fallback_to_cached_data(self, setup_service_with_mocks):
        """Test fallback to cached data when API is unavailable"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to fail
        mock_api.get_channel_info.side_effect = Exception("API unavailable")
        
        # Configure mock DB to have cached data
        mock_db.get_cached_channel_data.return_value = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "timestamp": "2023-01-01"
        }
        
        # Test retrieving channel with fallback
        result = service.get_channel_info_with_fallback("UC_test_channel")
        
        # Verify cached data was returned
        assert result is not None
        assert result["channel_id"] == "UC_test_channel"
        assert mock_db.get_cached_channel_data.called
