"""
Base class for quota optimization strategy tests.
"""
import pytest
from unittest.mock import MagicMock, patch
import time
import googleapiclient.errors

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class BaseQuotaOptimizationTest(BaseYouTubeTestCase):
    """Base class for quota optimization test cases"""
    
    @pytest.fixture
    def setup_service_with_mocks_and_quota_tracking(self):
        """Setup a YouTube service with mocks that track quota usage"""
        service, mock_api, mock_db = self.setup_mock_api_and_service()
        
        # Initialize quota tracking
        self.quota_used = 0
        
        # Configure mock API to track quota usage
        original_get_channel_info = mock_api.get_channel_info
        original_get_channel_videos = mock_api.get_channel_videos
        original_get_video_details = mock_api.get_video_details
        original_get_video_comments = mock_api.get_video_comments
        
        def track_channel_info_quota(*args, **kwargs):
            self.quota_used += 1  # Channel info costs 1 quota unit
            return original_get_channel_info(*args, **kwargs)
            
        def track_channel_videos_quota(*args, **kwargs):
            self.quota_used += 3  # Channel videos costs 3 quota units
            return original_get_channel_videos(*args, **kwargs)
            
        def track_video_details_quota(*args, **kwargs):
            self.quota_used += 2  # Video details costs 2 quota units
            return original_get_video_details(*args, **kwargs)
            
        def track_video_comments_quota(*args, **kwargs):
            self.quota_used += 5  # Comments costs 5 quota units
            return original_get_video_comments(*args, **kwargs)
        
        # Replace API methods with quota-tracking versions
        mock_api.get_channel_info.side_effect = track_channel_info_quota
        mock_api.get_channel_videos.side_effect = track_channel_videos_quota
        mock_api.get_video_details.side_effect = track_video_details_quota
        mock_api.get_video_comments.side_effect = track_video_comments_quota
        
        # Add quota tracking to service object
        service.get_quota_usage = lambda: self.quota_used
        service.reset_quota_usage = lambda: setattr(self, 'quota_used', 0)
        
        return service, mock_api, mock_db
        
    def reset_quota_counter(self):
        """Reset the quota usage counter for a new test"""
        self.quota_used = 0
