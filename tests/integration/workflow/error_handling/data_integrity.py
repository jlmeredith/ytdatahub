"""
Tests focusing on data integrity error handling during data collection.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging
import json

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.integration.workflow.test_data_collection_workflow import BaseYouTubeTestCase


class TestDataIntegrityErrorHandling(BaseYouTubeTestCase):
    """Tests focusing on data integrity error handling during data collection"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_malformed_api_response(self, setup_service_with_mocks):
        """Test handling of malformed API responses"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to return malformed data
        mock_api.get_channel_info.return_value = {
            # Missing required fields
            "channel_id": "UC_test_channel"
        }
        
        # Test processing with malformed data
        result = service.process_channel_data("UC_test_channel")
        
        # Verify validation error is detected and logged
        assert not result
        mock_db.save_error_log.assert_called_once()
    
    def test_incomplete_video_data(self, setup_service_with_mocks):
        """Test handling of incomplete video data"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to return incomplete video data
        mock_api.get_video_details.return_value = {
            "video_id": "test_video",
            # Missing statistics and other required fields
        }
        
        # Test processing with incomplete data
        result = service.process_video_data("test_video")
        
        # Verify validation error is detected and logged
        assert not result
        mock_db.save_partial_data.assert_called_once()
    
    def test_corrupted_database_record(self, setup_service_with_mocks):
        """Test handling of corrupted database records"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock DB to raise an integrity error
        mock_db.save_channel.side_effect = Exception("Database integrity error")
        
        # Configure mock API to return valid data
        mock_api.get_channel_info.return_value = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "subscribers": "1000"
        }
        
        # Test processing channel data
        result = service.process_channel_data("UC_test_channel")
        
        # Verify database error is handled and logged
        assert not result
        mock_db.save_error_log.assert_called_once()
        
    def test_inconsistent_related_data(self, setup_service_with_mocks):
        """Test handling of inconsistent related data"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to return inconsistent related data
        mock_api.get_channel_info.return_value = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "subscribers": "1000",
            "video_count": "10"
        }
        
        # But video list returns more videos than the reported count
        mock_api.get_channel_videos.return_value = [
            {"video_id": f"video_{i}"} for i in range(15)
        ]
        
        # Test processing channel and its videos
        result = service.process_channel_and_videos("UC_test_channel")
        
        # Verify inconsistency is detected and logged
        assert result
        mock_db.save_data_inconsistency.assert_called_once()
