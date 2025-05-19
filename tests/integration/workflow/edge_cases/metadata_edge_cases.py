"""
Tests for API parameter validation and metadata edge cases.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestMetadataEdgeCases(BaseYouTubeTestCase):
    """Tests for API parameter validation and metadata edge cases"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_channel_url_formats(self, setup_service_with_mocks):
        """Test handling of different channel URL formats"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Define various channel input formats to test
        channel_formats = [
            ('UC_test_channel', True, 'UC_test_channel'),                            # Raw Channel ID
            ('https://www.youtube.com/channel/UC_test_channel', True, 'UC_test_channel'),  # Channel URL
            ('https://www.youtube.com/c/TestChannel', True, 'UC_test_channel'),       # Custom URL
            ('https://youtube.com/user/TestUser', True, 'UC_test_channel'),           # Legacy user URL
            ('https://youtube.com/@TestHandle', True, 'UC_test_channel'),             # Handle URL
            ('invalid_input', False, None)                                            # Invalid input
        ]
        
        # Configure validation mock to return appropriate values
        def mock_validate_side_effect(channel_input):
            # Find the matching input format and return its validation result
            for fmt, valid, resolved in channel_formats:
                if fmt == channel_input:
                    return valid, resolved
            return False, None
        
        service.validate_and_resolve_channel_id = MagicMock(side_effect=mock_validate_side_effect)
        
        # Test each format
        for channel_input, should_be_valid, expected_id in channel_formats:
            # Reset mocks for each test
            mock_api.get_channel_info.reset_mock()
            
            if should_be_valid:
                # For valid formats, mock a successful API response
                mock_api.get_channel_info.return_value = {
                    'channel_id': expected_id,
                    'channel_name': 'Test Channel',
                    'subscribers': '1000',
                    'total_videos': '10'
                }
                
                # Attempt collection with this format
                options = {'fetch_channel_data': True, 'fetch_videos': False}
                result = service.collect_channel_data(channel_input, options)
                
                # Verify resolution and API calls
                assert result is not None
                assert result['channel_id'] == expected_id
                mock_api.get_channel_info.assert_called_once_with(expected_id)
            else:
                # For invalid formats, verify it returns None
                options = {'fetch_channel_data': True, 'fetch_videos': False}
                result = service.collect_channel_data(channel_input, options)
                
                assert result is None
                mock_api.get_channel_info.assert_not_called()
    
    def test_zero_max_videos_meaning(self, setup_service_with_mocks):
        """Test that max_videos=0 means 'fetch all videos', not 'fetch zero videos'"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '1000',
            'views': '10000',
            'total_videos': '3',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for 3 videos
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '1000',
                    'likes': '100'
                },
                {
                    'video_id': 'video2',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '500',
                    'likes': '50'
                },
                {
                    'video_id': 'video3',
                    'title': 'Test Video 3',
                    'published_at': '2025-04-10T14:30:00Z',
                    'views': '200',
                    'likes': '20'
                }
            ]
        }
        
        # Collect with max_videos=0 (should fetch all)
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 0  # Special value meaning 'all'
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify param was passed correctly
        _, kwargs = mock_api.get_channel_videos.call_args
        assert kwargs.get('max_videos') == 0
        
        # Verify all videos were fetched
        assert result is not None
        assert len(result['video_id']) == 3
