"""
Tests for quota budgeting optimization strategies.
"""
import pytest
from unittest.mock import MagicMock, patch
import time

from .base_strategy import BaseQuotaOptimizationTest


class TestQuotaBudgetingStrategy(BaseQuotaOptimizationTest):
    """Tests for quota budgeting optimization strategies"""
    
    def test_daily_quota_allocation(self, setup_service_with_mocks_and_quota_tracking):
        """Test allocating quota throughout the day to prevent early exhaustion"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Set up daily quota and time periods
        total_daily_quota = 10000
        hours_in_day = 24
        quota_per_hour = total_daily_quota / hours_in_day
        
        # Configure service with quota budget
        service.total_daily_quota = total_daily_quota
        
        # Test different times of day with mocked time
        def check_quota_at_hour(hour):
            # Mock the time to be specific hour of the day
            with patch('time.localtime') as mock_time:
                mock_struct = MagicMock()
                mock_struct.tm_hour = hour
                mock_time.return_value = mock_struct
                
                # Get available quota based on time of day
                return service.get_remaining_hourly_budget()
                
        # Morning quota (should have most of day's quota available)
        morning_quota = check_quota_at_hour(2)  # 2 AM
        
        # Noon quota (should have about half of day's quota available)
        noon_quota = check_quota_at_hour(12)  # 12 PM
        
        # Evening quota (should have small portion of day's quota available)
        evening_quota = check_quota_at_hour(20)  # 8 PM
        
        # Verify quota decreases as day progresses
        assert morning_quota > noon_quota
        assert noon_quota > evening_quota
        
        # Verify distribution is somewhat proportional
        assert morning_quota >= quota_per_hour * 20  # Most of day left
        assert noon_quota >= quota_per_hour * 10  # About half day left
        assert evening_quota >= quota_per_hour * 2  # Small portion of day left
    
    def test_operation_type_quota_limits(self, setup_service_with_mocks_and_quota_tracking):
        """Test limiting quota by operation type"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Configure quota limits by operation type
        service.operation_quotas = {
            'channel_info': 2000,  # 20% of total
            'videos': 5000,        # 50% of total
            'comments': 3000,      # 30% of total
        }
        
        # Configure tracking for operations
        service.quota_used_by_operation = {
            'channel_info': 0,
            'videos': 0,
            'comments': 0
        }
        
        # Test quota-managed operations
        
        # First, try operations within limits
        service.reset_quota_usage()
        service.quota_used_by_operation = {
            'channel_info': 1500,  # Under limit
            'videos': 4500,        # Under limit
            'comments': 2500       # Under limit
        }
        
        assert service.check_operation_quota('channel_info') is True
        assert service.check_operation_quota('videos') is True
        assert service.check_operation_quota('comments') is True
        
        # Now try operations exceeding their quota
        service.quota_used_by_operation = {
            'channel_info': 2100,  # Over limit
            'videos': 5100,        # Over limit
            'comments': 3100       # Over limit
        }
        
        assert service.check_operation_quota('channel_info') is False
        assert service.check_operation_quota('videos') is False
        assert service.check_operation_quota('comments') is False
    
    def test_adaptive_quota_borrowing(self, setup_service_with_mocks_and_quota_tracking):
        """Test borrowing quota between operation types when needed"""
        service, mock_api, mock_db = setup_service_with_mocks_and_quota_tracking
        
        # Configure initial quota limits by operation type
        service.operation_quotas = {
            'channel_info': 2000,
            'videos': 5000,
            'comments': 3000,
        }
        
        # Configure current usage - channel and comments under, videos over
        service.quota_used_by_operation = {
            'channel_info': 1000,  # 50% used (1000 remaining)
            'videos': 4800,        # 96% used (200 remaining)
            'comments': 1500,      # 50% used (1500 remaining)
        }
        
        # Test the borrowing mechanism
        original_video_limit = service.operation_quotas['videos']
        
        # Attempt to borrow quota for videos from other operations
        service.balance_quota('videos', extra_needed=800)
        
        # Verify quota was borrowed from other categories
        assert service.operation_quotas['videos'] > original_video_limit
        assert service.operation_quotas['channel_info'] < 2000
        assert service.operation_quotas['comments'] < 3000
        
        # Verify total quota remains the same
        total_quota = sum(service.operation_quotas.values())
        assert total_quota == 10000  # original total
