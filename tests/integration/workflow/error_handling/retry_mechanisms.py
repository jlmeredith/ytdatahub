"""
Tests focusing on retry mechanisms during data collection.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging
from googleapiclient.errors import HttpError
import time

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.integration.workflow.test_data_collection_workflow import BaseYouTubeTestCase


class TestRetryMechanisms(BaseYouTubeTestCase):
    """Tests focusing on retry mechanisms during data collection"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def create_http_error(self, status_code, message):
        """Create a GoogleAPI HttpError with specified status code and message"""
        resp = MagicMock()
        resp.status = status_code
        content = f'{{"error": {{"message": "{message}", "code": {status_code}}}}}'.encode()
        return HttpError(resp=resp, content=content)
    
    def test_exponential_backoff(self, setup_service_with_mocks):
        """Test exponential backoff retry mechanism"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Mock the time.sleep function to avoid waiting during tests
        with patch('time.sleep') as mock_sleep:
            # Configure mock API to fail with 500 errors then succeed
            error_500 = self.create_http_error(500, "Backend Error")
            mock_api.get_channel_info.side_effect = [
                error_500, error_500, error_500,
                {"channel_id": "UC_test_channel", "title": "Test Channel"}
            ]
            
            # Set start time
            start = time.time()
            
            # Test retrieval with exponential backoff
            result = service.fetch_channel_data_with_backoff("UC_test_channel")
            
            # Verify result was successful after retries
            assert result is not None
            assert result["channel_id"] == "UC_test_channel"
            
            # Verify backoff was exponential
            assert mock_sleep.call_count == 3
            assert mock_sleep.call_args_list[0][0][0] < mock_sleep.call_args_list[1][0][0]
            assert mock_sleep.call_args_list[1][0][0] < mock_sleep.call_args_list[2][0][0]
    
    def test_retry_with_jitter(self, setup_service_with_mocks):
        """Test retry mechanism with jitter to avoid thundering herd"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Mock the time.sleep function
        with patch('time.sleep') as mock_sleep:
            # Configure mock API to fail with 503 errors then succeed
            error_503 = self.create_http_error(503, "Service Unavailable")
            mock_api.get_channel_info.side_effect = [
                error_503, error_503, 
                {"channel_id": "UC_test_channel", "title": "Test Channel"}
            ]
            
            # Test retrieval with jitter
            result = service.fetch_channel_data_with_jitter("UC_test_channel")
            
            # Verify result was successful after retries
            assert result is not None
            assert result["channel_id"] == "UC_test_channel"
            assert mock_sleep.call_count == 2
    
    def test_maximum_retry_limit(self, setup_service_with_mocks):
        """Test respecting maximum retry limits"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock to always fail
        mock_api.get_channel_info.side_effect = self.create_http_error(500, "Backend Error")
        
        # Test fetching with limited retries
        result = service.fetch_channel_data("UC_test_channel", max_retries=5)
        
        # Verify max retries was respected and operation eventually failed
        assert result is None
        assert mock_api.get_channel_info.call_count == 6  # Initial + 5 retries
