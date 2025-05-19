"""
Tests for batch request quota optimization strategies.
"""
import pytest
from unittest.mock import MagicMock, patch, call

from .base_strategy import BaseQuotaOptimizationTest


class TestBatchRequestStrategy(BaseQuotaOptimizationTest):
    """Tests for batch request optimization strategies"""
    
    def test_batch_video_requests(self, setup_service_with_mocks_and_quota_tracking):
        """Test that batch video requests use less quota than individual requests"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Configure mock API for batch requests
        video_ids = [f"video_{i}" for i in range(10)]
        mock_api.get_videos_batch.return_value = {
            vid: {"video_id": vid, "title": f"Video {i}"} 
            for i, vid in enumerate(video_ids)
        }
        
        # Cost for individual requests would be 10 videos * 2 units = 20 units
        
        # Configure quota cost for batch request (should be less)
        original_get_videos_batch = mock_api.get_videos_batch
        
        def track_batch_quota(*args, **kwargs):
            # Batch requests are more efficient
            self.quota_used += 5  # Less than individual requests
            return original_get_videos_batch(*args, **kwargs)
            
        mock_api.get_videos_batch.side_effect = track_batch_quota
        
        # Test batch fetching
        service.reset_quota_usage()
        batch_result = service.fetch_videos_batch(video_ids)
        batch_quota_used = service.get_quota_usage()
        
        # Test individual fetching
        service.reset_quota_usage()
        individual_results = []
        for vid in video_ids:
            # Configure mock for individual requests
            mock_api.get_video_details.return_value = {"video_id": vid, "title": f"Video {vid}"}
            result = service.fetch_video_data(vid)
            individual_results.append(result)
        individual_quota_used = service.get_quota_usage()
        
        # Verify batch uses less quota
        assert batch_quota_used < individual_quota_used
        assert len(batch_result) == 10
        assert len(individual_results) == 10
    
    def test_batch_channel_details(self, setup_service_with_mocks_and_quota_tracking):
        """Test batch channel detail fetching vs individual requests"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Channel IDs to fetch
        channel_ids = [f"UC_channel_{i}" for i in range(5)]
        
        # Configure mock for batch requests
        mock_api.get_channels_batch.return_value = {
            cid: {"channel_id": cid, "title": f"Channel {i}"} 
            for i, cid in enumerate(channel_ids)
        }
        
        # Configure quota tracking for batch
        original_get_channels_batch = mock_api.get_channels_batch
        
        def track_batch_channels_quota(*args, **kwargs):
            self.quota_used += 3  # More efficient than individual requests
            return original_get_channels_batch(*args, **kwargs)
            
        mock_api.get_channels_batch.side_effect = track_batch_channels_quota
        
        # Test batch fetching
        service.reset_quota_usage()
        batch_result = service.fetch_channels_batch(channel_ids)
        batch_quota_used = service.get_quota_usage()
        
        # Test individual fetching
        service.reset_quota_usage()
        individual_results = []
        for cid in channel_ids:
            mock_api.get_channel_info.return_value = {"channel_id": cid, "title": f"Channel {cid}"}
            result = service.fetch_channel_data(cid)
            individual_results.append(result)
        individual_quota_used = service.get_quota_usage()
        
        # Verify batch is more efficient
        assert batch_quota_used < individual_quota_used
        assert len(batch_result) == 5
        assert len(individual_results) == 5
    
    def test_comment_batch_requests(self, setup_service_with_mocks_and_quota_tracking):
        """Test batching comment requests for multiple videos"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Video IDs to fetch comments for
        video_ids = [f"video_{i}" for i in range(3)]
        
        # Configure mock for batch comment requests
        mock_api.get_comments_batch.return_value = {
            vid: [{"comment_id": f"c_{vid}_{j}", "text": f"Comment {j}"} for j in range(5)]
            for vid in video_ids
        }
        
        # Configure quota tracking for batch
        original_get_comments_batch = mock_api.get_comments_batch
        
        def track_batch_comments_quota(*args, **kwargs):
            self.quota_used += 7  # More efficient than individual requests
            return original_get_comments_batch(*args, **kwargs)
            
        mock_api.get_comments_batch.side_effect = track_batch_comments_quota
        
        # Test batch fetching
        service.reset_quota_usage()
        batch_result = service.fetch_comments_batch(video_ids)
        batch_quota_used = service.get_quota_usage()
        
        # Test individual fetching
        service.reset_quota_usage()
        individual_results = {}
        for vid in video_ids:
            mock_api.get_video_comments.return_value = [
                {"comment_id": f"c_{vid}_{j}", "text": f"Comment {j}"} for j in range(5)
            ]
            result = service.fetch_video_comments(vid)
            individual_results[vid] = result
        individual_quota_used = service.get_quota_usage()
        
        # Verify batch is more efficient
        assert batch_quota_used < individual_quota_used
        assert len(batch_result) == 3
        assert all(len(comments) == 5 for comments in batch_result.values())
