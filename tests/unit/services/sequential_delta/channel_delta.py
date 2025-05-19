"""
Tests for channel metrics delta calculations across sequential updates.
"""
import pytest
from unittest.mock import MagicMock, patch
import datetime

from .base_tests import TestSequentialDeltaBase


class TestChannelDeltaMetrics(TestSequentialDeltaBase):
    """Tests for sequential delta updates of channel metrics"""
    
    def test_channel_subscribers_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating subscriber count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with subscriber history
        subscriber_history = [
            {"value": 1000, "timestamp": self.create_timestamp(7)},  # 1 week ago
            {"value": 1200, "timestamp": self.create_timestamp(5)},  # 5 days ago
            {"value": 1350, "timestamp": self.create_timestamp(3)},  # 3 days ago 
            {"value": 1500, "timestamp": self.create_timestamp(1)}   # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'subscribers', 'UC_test_channel', subscriber_history)
        
        # Setup current channel data
        current_channel_data = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "subscribers": 1800,  # Current subscriber count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_channel_deltas(current_channel_data)
        
        # Verify deltas were calculated correctly
        assert result["subscribers_total_delta"] == 800  # Total gain from first record
        assert result["subscribers_recent_delta"] == 300  # Gain since yesterday
        assert result["subscribers_average_delta"] == pytest.approx(114.28, 0.01)  # ~800/7 days
        assert result["subscribers_acceleration"] > 0  # Acceleration is positive
        
    def test_channel_view_count_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating view count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with view history
        view_history = [
            {"value": 10000, "timestamp": self.create_timestamp(10)},  # 10 days ago
            {"value": 12000, "timestamp": self.create_timestamp(7)},   # 7 days ago
            {"value": 15000, "timestamp": self.create_timestamp(4)},   # 4 days ago 
            {"value": 16000, "timestamp": self.create_timestamp(2)},   # 2 days ago
            {"value": 18000, "timestamp": self.create_timestamp(1)}    # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'views', 'UC_test_channel', view_history)
        
        # Setup current channel data
        current_channel_data = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "views": 22000,  # Current view count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_channel_deltas(current_channel_data)
        
        # Verify deltas were calculated correctly
        assert result["views_total_delta"] == 12000  # Total gain from first record
        assert result["views_recent_delta"] == 4000  # Gain since yesterday
        assert result["views_average_delta"] == pytest.approx(1200, 0.01)  # 12000/10 days
        
    def test_channel_video_count_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating video count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with video count history
        video_count_history = [
            {"value": 10, "timestamp": self.create_timestamp(30)},  # 30 days ago
            {"value": 12, "timestamp": self.create_timestamp(20)},  # 20 days ago
            {"value": 15, "timestamp": self.create_timestamp(10)},  # 10 days ago
            {"value": 17, "timestamp": self.create_timestamp(5)}    # 5 days ago
        ]
        self.configure_sequential_snapshots(mock_db, 'video_count', 'UC_test_channel', video_count_history)
        
        # Setup current channel data
        current_channel_data = {
            "channel_id": "UC_test_channel",
            "title": "Test Channel",
            "video_count": 20,  # Current video count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_channel_deltas(current_channel_data)
        
        # Verify deltas were calculated correctly
        assert result["video_count_total_delta"] == 10  # Total gain from first record
        assert result["video_count_recent_delta"] == 3  # Gain since 5 days ago
        assert result["video_count_average_delta"] == pytest.approx(0.333, 0.01)  # ~10/30 days
