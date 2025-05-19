"""
Tests focusing on API error handling during data collection.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import logging
from googleapiclient.errors import HttpError

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.integration.workflow.test_data_collection_workflow import BaseYouTubeTestCase


class TestApiErrorHandling(BaseYouTubeTestCase):
    """Tests focusing on API error handling during data collection"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def create_http_error(self, status_code, message):
        """Create a GoogleAPI HttpError with specified status code and message"""
        # Mock the content returned from the HTTPError exception
        resp = MagicMock()
        resp.status = status_code
        content = f'{{"error": {{"message": "{message}", "code": {status_code}}}}}'.encode()
        
        from googleapiclient.errors import HttpError
        return HttpError(resp=resp, content=content, uri='')
    
    def test_api_error_during_channel_fetch(self, setup_service_with_mocks):
        """Test recovery when channel info fetch fails with API error"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock to raise an API error
        mock_api.get_channel_info.side_effect = self.create_http_error(
            403, "The request cannot be completed because you have exceeded your quota."
        )
        
        # Attempt to collect channel data
        with pytest.raises(HttpError) as excinfo:
            service.collect_channel_data('UC_test_channel', {
                'fetch_channel_data': True,
                'fetch_videos': False,
                'fetch_comments': False
            })
        
        # Verify error details
        error = excinfo.value
        assert error.status_code == 403
        assert "exceeded your quota" in str(error)

    def test_api_error_logging(self, setup_service_with_mocks, caplog):
        """Test that API errors are properly logged with details"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Enable logging capture
        caplog.set_level(logging.ERROR)
        
        # Configure mock to raise an API error
        mock_api.get_channel_info.side_effect = self.create_http_error(
            500, "Backend Error"
        )
        
        # Attempt to collect channel data
        with pytest.raises(HttpError):
            service.collect_channel_data('UC_test_channel', {
                'fetch_channel_data': True,
                'fetch_videos': False,
                'fetch_comments': False
            })
        
        # Verify error was logged with key details
        assert "API error" in caplog.text
        assert "500" in caplog.text
        assert "Backend Error" in caplog.text
    
    def test_error_code_handling(self):
        """Test handling of specific error codes and types"""
        service, mock_api, mock_db = self.setup_mock_api_and_service()
        
        # Test different error codes and types
        error_code_tests = [
            # (error_code, error_type, should_retry)
            (400, 'invalidRequest', False),  # Don't retry invalid requests
            (403, 'quotaExceeded', False),   # Don't retry quota issues
            (404, 'notFound', False),        # Don't retry not found
            (429, 'rateLimitExceeded', True), # Retry rate limits
            (500, 'serverError', True),      # Retry server errors
            (503, 'backendError', True)      # Retry backend errors
        ]
        
        for code, error_type, should_retry in error_code_tests:
            # Reset mocks
            mock_api.get_channel_info.reset_mock()
            mock_api.get_channel_info.side_effect = None
            
            # Configure error for this test case
            error = YouTubeAPIError(
                f"Test error {code}", status_code=code, error_type=error_type
            )
            
            if should_retry:
                # For retriable errors, fail then succeed
                mock_api.get_channel_info.side_effect = [
                    error,
                    {'channel_id': 'UC_test_channel', 'channel_name': 'Test Channel'}
                ]
            else:
                # For non-retriable errors, just fail
                mock_api.get_channel_info.side_effect = error
            
            # Spy on time.sleep
            with patch('time.sleep'):
                # Test with retry attempts
                options = {'retry_attempts': 3}
                result = service.collect_channel_data('UC_test_channel', options)
                
                if should_retry:
                    # Should have succeeded after retry
                    assert 'channel_id' in result
                    assert mock_api.get_channel_info.call_count == 2
                else:
                    # Should have failed with error
                    assert 'error' in result
                    assert mock_api.get_channel_info.call_count == 1
