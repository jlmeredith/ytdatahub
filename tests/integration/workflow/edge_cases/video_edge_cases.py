"""
Tests for handling edge cases with video data.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestVideoEdgeCases(BaseYouTubeTestCase):
    """Tests for handling edge cases with video data"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_video_with_no_likes_or_views(self, setup_service_with_mocks):
        """Test handling of videos with zero likes and views"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API for channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '100',
            'views': '100',
            'total_videos': '1',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for video with no engagement
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Zero Engagement Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '0',
                    'likes': '0',
                    'comment_count': '0'
                }
            ]
        }
        
        # Collect channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert len(result['video_id']) == 1
        
        # Verify zero values are preserved
        video = result['video_id'][0]
        assert video['views'] == '0'
        assert video['likes'] == '0'
        assert video['comment_count'] == '0'
    
    def test_video_with_missing_fields(self, setup_service_with_mocks):
        """Test handling of videos with missing metadata fields"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API for channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '1000',
            'views': '10000',
            'total_videos': '1',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for video with missing fields
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Incomplete Metadata Video',
                    # Missing: published_at
                    'views': '1000'
                    # Missing: likes, comment_count
                }
            ]
        }
        
        # Collect channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert len(result['video_id']) == 1
        
        # Verify available fields and graceful handling of missing fields
        video = result['video_id'][0]
        assert video['video_id'] == 'video1'
        assert video['title'] == 'Incomplete Metadata Video'
        assert video['views'] == '1000'
