"""
Tests for resource prioritization quota optimization strategies.
"""
import pytest
from unittest.mock import MagicMock, patch

from .base_strategy import BaseQuotaOptimizationTest


class TestResourcePrioritization(BaseQuotaOptimizationTest):
    """Tests for resource prioritization optimization strategies"""
    
    def test_channel_importance_prioritization(self, setup_service_with_mocks_and_quota_tracking):
        """Test prioritizing channels based on importance score"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Set up channel data with importance scores
        channels = [
            {"channel_id": "UC_channel_1", "subscribers": "1000000", "importance_score": 95},
            {"channel_id": "UC_channel_2", "subscribers": "500000", "importance_score": 80},
            {"channel_id": "UC_channel_3", "subscribers": "100000", "importance_score": 60},
            {"channel_id": "UC_channel_4", "subscribers": "10000", "importance_score": 40},
            {"channel_id": "UC_channel_5", "subscribers": "1000", "importance_score": 20},
        ]
        
        # Configure mock DB to return the channels when requested
        mock_db.get_channels_with_importance.return_value = channels
        
        # Setup a mock quota limit
        with patch.object(service, 'get_remaining_quota', return_value=10):
            # Request processing with limited quota
            processed_channels = service.process_channels_by_importance(quota_limit=10)
            
            # Verify high importance channels were processed first
            processed_ids = [c["channel_id"] for c in processed_channels]
            assert "UC_channel_1" in processed_ids
            assert "UC_channel_2" in processed_ids
            assert "UC_channel_5" not in processed_ids  # Lowest importance shouldn't be processed
    
    def test_video_view_count_prioritization(self, setup_service_with_mocks_and_quota_tracking):
        """Test prioritizing videos based on view count"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Set up video data with view counts
        videos = [
            {"video_id": "video_1", "view_count": "1000000", "channel_id": "UC_channel_1"},
            {"video_id": "video_2", "view_count": "500000", "channel_id": "UC_channel_1"},
            {"video_id": "video_3", "view_count": "100000", "channel_id": "UC_channel_2"},
            {"video_id": "video_4", "view_count": "10000", "channel_id": "UC_channel_2"},
            {"video_id": "video_5", "view_count": "1000", "channel_id": "UC_channel_3"},
        ]
        
        # Configure mock DB to return the videos when requested
        mock_db.get_videos_by_view_count.return_value = videos
        
        # Setup a mock quota limit
        with patch.object(service, 'get_remaining_quota', return_value=6):
            # Request processing with limited quota (enough for 3 videos)
            processed_videos = service.process_videos_by_popularity(quota_limit=6)
            
            # Verify high view count videos were processed first
            processed_ids = [v["video_id"] for v in processed_videos]
            assert "video_1" in processed_ids
            assert "video_2" in processed_ids
            assert "video_3" in processed_ids
            assert "video_5" not in processed_ids  # Lowest views shouldn't be processed
    
    def test_recency_prioritization(self, setup_service_with_mocks_and_quota_tracking):
        """Test prioritizing videos based on recency"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Set up video data with publication dates
        videos = [
            {"video_id": "video_1", "published_at": "2023-05-01T00:00:00Z", "channel_id": "UC_channel_1"},
            {"video_id": "video_2", "published_at": "2023-04-15T00:00:00Z", "channel_id": "UC_channel_1"},
            {"video_id": "video_3", "published_at": "2023-03-20T00:00:00Z", "channel_id": "UC_channel_2"},
            {"video_id": "video_4", "published_at": "2023-02-10T00:00:00Z", "channel_id": "UC_channel_2"},
            {"video_id": "video_5", "published_at": "2023-01-05T00:00:00Z", "channel_id": "UC_channel_3"},
        ]
        
        # Configure mock DB to return the videos when requested
        mock_db.get_videos_by_recency.return_value = videos
        
        # Setup a mock quota limit
        with patch.object(service, 'get_remaining_quota', return_value=6):
            # Request processing with limited quota (enough for 3 videos)
            processed_videos = service.process_recent_videos(quota_limit=6)
            
            # Verify recent videos were processed first
            processed_ids = [v["video_id"] for v in processed_videos]
            assert "video_1" in processed_ids
            assert "video_2" in processed_ids
            assert "video_3" in processed_ids
            assert "video_5" not in processed_ids  # Oldest video shouldn't be processed
