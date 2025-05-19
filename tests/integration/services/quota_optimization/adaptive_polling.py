"""
Tests for adaptive polling quota optimization strategies.
"""
import pytest
from unittest.mock import MagicMock, patch
import time

from .base_strategy import BaseQuotaOptimizationTest


class TestAdaptivePollingStrategy(BaseQuotaOptimizationTest):
    """Tests for adaptive polling optimization strategies"""
    
    def test_dynamic_polling_interval(self, setup_service_with_mocks_and_quota_tracking):
        """Test adjusting polling interval based on data change frequency"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Setup channel history data showing frequent changes
        frequent_change_history = [
            {"snapshot_time": time.time() - 86400, "subscribers": "900"},  # 24 hours ago
            {"snapshot_time": time.time() - 43200, "subscribers": "950"},  # 12 hours ago
            {"snapshot_time": time.time() - 21600, "subscribers": "975"},  # 6 hours ago
            {"snapshot_time": time.time() - 3600, "subscribers": "1000"},  # 1 hour ago
        ]
        
        # Setup channel with infrequent changes
        infrequent_change_history = [
            {"snapshot_time": time.time() - 86400 * 7, "subscribers": "900"},  # 7 days ago
            {"snapshot_time": time.time() - 86400 * 5, "subscribers": "910"},  # 5 days ago
            {"snapshot_time": time.time() - 86400 * 2, "subscribers": "920"},  # 2 days ago
            {"snapshot_time": time.time() - 86400, "subscribers": "925"},      # 1 day ago
        ]
        
        # Configure mock DB to return different histories
        def get_channel_history(channel_id):
            if channel_id == "UC_frequent_change":
                return frequent_change_history
            else:
                return infrequent_change_history
                
        mock_db.get_channel_history.side_effect = get_channel_history
        
        # Test calculating polling interval
        frequent_interval = service.calculate_adaptive_polling_interval("UC_frequent_change")
        infrequent_interval = service.calculate_adaptive_polling_interval("UC_infrequent_change")
        
        # Verify polling is more frequent for rapidly changing channel
        assert frequent_interval < infrequent_interval
        
        # Now test actual polling behavior
        with patch('time.time') as mock_time:
            mock_time.return_value = time.time()
            
            # Configure next poll times
            service.next_poll_time = {
                "UC_frequent_change": time.time() - 100,  # Due for polling
                "UC_infrequent_change": time.time() + 3600  # Not due yet
            }
            
            # Test polling strategy
            service.reset_quota_usage()
            frequent_result = service.check_and_poll_if_needed("UC_frequent_change")
            infrequent_result = service.check_and_poll_if_needed("UC_infrequent_change")
            
            # Verify the frequent-change channel was polled but not the infrequent one
            assert frequent_result is not None
            assert infrequent_result is None
            assert mock_api.get_channel_info.call_count == 1
    
    def test_backoff_on_unchanged_data(self, setup_service_with_mocks_and_quota_tracking):
        """Test backing off polling when data hasn't changed"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Configure mock to return unchanged data
        mock_api.get_channel_info.return_value = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "subscribers": "1000"
        }
        
        # Configure mock DB to show no changes over multiple polls
        def get_unchanged_history(channel_id, limit=None):
            # Return identical snapshots
            return [
                {"snapshot_time": time.time() - 86400 * i, "subscribers": "1000"} 
                for i in range(1, 5)
            ]
            
        mock_db.get_channel_history.side_effect = get_unchanged_history
        
        # Test polling backoff
        service.initial_interval = 3600  # 1 hour
        service.max_backoff = 86400 * 7  # 7 days
        
        # First poll
        original_interval = service.get_polling_interval("UC_test_channel")
        service.update_polling_stats("UC_test_channel", has_changes=False)
        second_interval = service.get_polling_interval("UC_test_channel")
        
        # Second poll with no changes
        service.update_polling_stats("UC_test_channel", has_changes=False)
        third_interval = service.get_polling_interval("UC_test_channel")
        
        # Verify polling interval increases
        assert second_interval > original_interval
        assert third_interval > second_interval
        
        # Now simulate a change
        service.update_polling_stats("UC_test_channel", has_changes=True)
        reset_interval = service.get_polling_interval("UC_test_channel")
        
        # Verify interval is reset after change detected
        assert reset_interval <= original_interval
