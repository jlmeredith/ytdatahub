"""
Tests for playlist metrics delta calculations across sequential updates.
"""
import pytest
from unittest.mock import MagicMock, patch
import datetime

from .base_tests import TestSequentialDeltaBase


class TestPlaylistDeltaMetrics(TestSequentialDeltaBase):
    """Tests for sequential delta updates of playlist metrics"""
    
    def test_playlist_item_count_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating playlist item count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with item count history
        item_count_history = [
            {"value": 5, "timestamp": self.create_timestamp(10)},    # 10 days ago
            {"value": 8, "timestamp": self.create_timestamp(7)},     # 7 days ago
            {"value": 10, "timestamp": self.create_timestamp(3)},    # 3 days ago
            {"value": 12, "timestamp": self.create_timestamp(1)}     # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'item_count', 'playlist123', item_count_history)
        
        # Setup current playlist data
        current_playlist_data = {
            "playlist_id": "playlist123",
            "title": "Test Playlist",
            "item_count": 15,  # Current item count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_playlist_deltas(current_playlist_data)
        
        # Verify deltas were calculated correctly
        assert result["item_count_total_delta"] == 10  # Total gain from first record
        assert result["item_count_recent_delta"] == 3  # Gain since yesterday
        assert result["item_count_average_delta"] == 1  # 10/10 days
        
    def test_playlist_view_count_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating playlist view count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with view count history
        view_count_history = [
            {"value": 1000, "timestamp": self.create_timestamp(14)},   # 14 days ago
            {"value": 2500, "timestamp": self.create_timestamp(10)},   # 10 days ago
            {"value": 5000, "timestamp": self.create_timestamp(7)},    # 7 days ago
            {"value": 8000, "timestamp": self.create_timestamp(3)},    # 3 days ago
            {"value": 10000, "timestamp": self.create_timestamp(1)}    # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'views', 'playlist123', view_count_history)
        
        # Setup current playlist data
        current_playlist_data = {
            "playlist_id": "playlist123",
            "title": "Test Playlist",
            "views": 12000,  # Current view count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_playlist_deltas(current_playlist_data)
        
        # Verify deltas were calculated correctly
        assert result["views_total_delta"] == 11000  # Total gain from first record
        assert result["views_recent_delta"] == 2000  # Gain since yesterday
        assert result["views_average_delta"] == pytest.approx(785.71, 0.01)  # ~11000/14 days
    
    def test_playlist_growth_rate_calculation(self, setup_youtube_service, setup_mock_db):
        """Test calculating playlist growth rate over multiple time periods"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with item count history
        item_count_history = [
            {"value": 5, "timestamp": self.create_timestamp(30)},    # 30 days ago
            {"value": 8, "timestamp": self.create_timestamp(21)},    # 21 days ago
            {"value": 15, "timestamp": self.create_timestamp(14)},   # 14 days ago
            {"value": 20, "timestamp": self.create_timestamp(7)},    # 7 days ago
            {"value": 23, "timestamp": self.create_timestamp(1)}     # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'item_count', 'playlist123', item_count_history)
        
        # Setup current playlist data
        current_playlist_data = {
            "playlist_id": "playlist123",
            "title": "Test Playlist",
            "item_count": 25,  # Current item count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate growth rates
        result = service.calculate_playlist_growth_rates(current_playlist_data)
        
        # Verify growth rates for different time periods
        assert result["growth_rate_30_days"] == pytest.approx((25 - 5) / 5, 0.01)  # 400% growth in 30 days
        assert result["growth_rate_7_days"] == pytest.approx((25 - 20) / 20, 0.01)  # 25% growth in 7 days
        assert result["growth_rate_yesterday"] == pytest.approx((25 - 23) / 23, 0.01)  # ~8.7% growth since yesterday
        assert result["is_accelerating"] == (result["growth_rate_7_days"] > result["growth_rate_30_days"]/4)  
        # Check if weekly growth rate is higher than what we'd expect from the monthly rate
