"""
Tests focusing on connection error handling during data collection.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging
from googleapiclient.errors import HttpError
import socket
import requests

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.integration.workflow.test_data_collection_workflow import BaseYouTubeTestCase


class TestConnectionErrorHandling(BaseYouTubeTestCase):
    """Tests focusing on connection error handling during data collection"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
        
    def test_network_connection_error(self, setup_service_with_mocks):
        """Test handling of network connection errors"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to raise a connection error
        mock_api.get_channel_info.side_effect = socket.error("Network connection error")
        
        # Test fetching a channel when connection error occurs
        result = service.fetch_channel_data("UC_test_channel")
        
        # Verify error is handled and logged
        assert result is None
        mock_db.save_error_log.assert_called_once()
    
    def test_http_timeout_error(self, setup_service_with_mocks):
        """Test handling of HTTP timeout errors"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to raise a timeout error
        mock_api.get_channel_info.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Test fetching a channel when timeout occurs
        result = service.fetch_channel_data("UC_test_channel")
        
        # Verify error is handled and logged
        assert result is None
        mock_db.save_error_log.assert_called_once()
        
    def test_retry_on_connection_error(self, setup_service_with_mocks):
        """Test retry mechanism for connection errors"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock to raise error twice then succeed
        mock_api.get_channel_info.side_effect = [
            ConnectionError("Network error"),
            ConnectionError("Network error"),
            {"channel_id": "UC_test_channel", "title": "Test Channel"}
        ]
        
        # Test fetching with retries
        result = service.fetch_channel_data("UC_test_channel", max_retries=3)
        
        # Verify data was eventually retrieved after retries
        assert result is not None
        assert result["channel_id"] == "UC_test_channel"
        assert mock_api.get_channel_info.call_count == 3
