"""
Tests focusing on quota error handling during data collection.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging
from googleapiclient.errors import HttpError

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.integration.workflow.test_data_collection_workflow import BaseYouTubeTestCase


class TestQuotaErrorHandling(BaseYouTubeTestCase):
    """Tests focusing on API quota error handling during data collection"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def create_quota_error(self):
        """Create a GoogleAPI HttpError for quota exceeded"""
        resp = MagicMock()
        resp.status = 403
        content = '{"error": {"message": "Quota exceeded", "code": 403, "errors": [{"reason": "quotaExceeded"}]}}'.encode()
        return HttpError(resp=resp, content=content)
    
    def test_quota_exceeded_handling(self, setup_service_with_mocks):
        """Test handling of quota exceeded errors"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to raise a quota exceeded error
        quota_error = self.create_quota_error()
        mock_api.get_channel_info.side_effect = quota_error
        
        # Test fetching a channel when quota is exceeded
        result = service.fetch_channel_data("UC_test_channel")
        
        # Verify quota error is detected and logged
        assert result is None
        mock_db.save_quota_limit_reached.assert_called_once()
    
    def test_quota_deferral(self, setup_service_with_mocks):
        """Test deferral of operations when quota is low"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure service to have low quota
        with patch.object(service, 'get_remaining_quota', return_value=5):
            # Test fetching a high-cost operation
            result = service.fetch_channel_videos("UC_test_channel", video_limit=None)
            
            # Verify operation is deferred
            assert result is None
            mock_db.save_deferred_operation.assert_called_once()
    
    def test_quota_prioritization(self, setup_service_with_mocks):
        """Test prioritization of operations when quota is limited"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure service to have limited quota
        with patch.object(service, 'get_remaining_quota', return_value=20):
            # Attempt multiple operations
            service.process_multiple_data_requests([
                {"type": "channel", "id": "UC_channel1"},
                {"type": "video", "id": "video1"},
                {"type": "comments", "id": "video2"}
            ])
            
            # Verify high priority operations were executed
            assert mock_api.get_channel_info.called
            assert not mock_api.get_comment_threads.called
