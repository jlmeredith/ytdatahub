"""
Tests for caching quota optimization strategies.
"""
import pytest
from unittest.mock import MagicMock, patch
import time

from .base_strategy import BaseQuotaOptimizationTest


class TestCachingStrategy(BaseQuotaOptimizationTest):
    """Tests for caching optimization strategies"""
    
    def test_cache_first_strategy(self, setup_service_with_mocks_and_quota_tracking):
        """Test using cache first before making API calls"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Configure mock DB with cached data
        mock_db.get_cached_channel.return_value = {
            "channel_id": "UC_test_channel", 
            "title": "Test Channel",
            "cache_time": time.time() - 3600  # Cached 1 hour ago
        }
        
        # Configure the service's cache TTL setting
        service.cache_ttl = 7200  # 2 hours TTL
        
        # Test fetching data with cache_first strategy
        service.reset_quota_usage()
        result = service.get_channel_info_cache_first("UC_test_channel")
        
        # Verify the API was not called and cached data was used
        assert result["channel_id"] == "UC_test_channel"
        assert mock_api.get_channel_info.call_count == 0
        assert service.get_quota_usage() == 0  # No quota used
        
        # Now set cache to be expired
        mock_db.get_cached_channel.return_value = {
            "channel_id": "UC_test_channel", 
            "title": "Test Channel",
            "cache_time": time.time() - 8000  # Cached more than TTL ago
        }
        
        # Configure API to return fresh data
        mock_api.get_channel_info.return_value = {
            "channel_id": "UC_test_channel",
            "title": "Updated Test Channel",
            "fresh_data": True
        }
        
        # Test fetching with expired cache
        service.reset_quota_usage()
        result = service.get_channel_info_cache_first("UC_test_channel")
        
        # Verify API was called due to expired cache
        assert result["fresh_data"] == True
        assert mock_api.get_channel_info.call_count == 1
        assert service.get_quota_usage() > 0  # Quota was used
    
    def test_stale_cache_fallback(self, setup_service_with_mocks_and_quota_tracking):
        """Test falling back to stale cache when API fails"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Configure mock DB with stale cached data
        mock_db.get_cached_channel.return_value = {
            "channel_id": "UC_test_channel", 
            "title": "Test Channel",
            "cache_time": time.time() - 86400  # Cached 24 hours ago (stale)
        }
        
        # Configure the service's cache TTL setting
        service.cache_ttl = 7200  # 2 hours TTL
        
        # Configure API to fail
        mock_api.get_channel_info.side_effect = Exception("API Error")
        
        # Test fetching with API error fallback
        service.reset_quota_usage()
        result = service.get_channel_info_with_stale_fallback("UC_test_channel")
        
        # Verify stale cache was used despite being expired
        assert result["channel_id"] == "UC_test_channel"
        assert mock_api.get_channel_info.call_count == 1  # API call was attempted
        assert service.get_quota_usage() > 0  # Quota was used for failed attempt
        assert "stale" in result  # Should be marked as stale
    
    def test_conditional_refresh(self, setup_service_with_mocks_and_quota_tracking):
        """Test conditional refresh of cache based on update frequency"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Configure channel data with different update frequencies
        high_activity_channel = {
            "channel_id": "UC_active_channel",
            "title": "Active Channel",
            "update_frequency": "high",
            "cache_time": time.time() - 3600  # Cached 1 hour ago
        }
        
        low_activity_channel = {
            "channel_id": "UC_inactive_channel",
            "title": "Inactive Channel",
            "update_frequency": "low",
            "cache_time": time.time() - 3600  # Cached 1 hour ago
        }
        
        # Configure service cache TTL strategy based on activity
        service.high_activity_ttl = 3600  # 1 hour for high activity
        service.low_activity_ttl = 86400  # 24 hours for low activity
        
        # Test high activity channel
        mock_db.get_cached_channel.return_value = high_activity_channel
        service.reset_quota_usage()
        service.refresh_if_needed("UC_active_channel")
        
        # Should refresh due to high activity and TTL
        assert mock_api.get_channel_info.call_count == 1
        assert service.get_quota_usage() > 0
        
        # Reset and test low activity channel
        mock_api.get_channel_info.reset_mock()
        service.reset_quota_usage()
        mock_db.get_cached_channel.return_value = low_activity_channel
        service.refresh_if_needed("UC_inactive_channel")
        
        # Should NOT refresh due to low activity and longer TTL
        assert mock_api.get_channel_info.call_count == 0
        assert service.get_quota_usage() == 0
