"""
Tests for video metrics delta calculations across sequential updates.
"""
import pytest
from unittest.mock import MagicMock, patch
import datetime

from .base_tests import TestSequentialDeltaBase


class TestVideoDeltaMetrics(TestSequentialDeltaBase):
    """Tests for sequential delta updates of video metrics"""
    
    def test_video_views_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating video view count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with view history
        view_history = [
            {"value": 1000, "timestamp": self.create_timestamp(7)},   # 7 days ago
            {"value": 2500, "timestamp": self.create_timestamp(5)},   # 5 days ago
            {"value": 4000, "timestamp": self.create_timestamp(3)},   # 3 days ago 
            {"value": 5200, "timestamp": self.create_timestamp(1)}    # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'views', 'video123', view_history)
        
        # Setup current video data
        current_video_data = {
            "video_id": "video123",
            "title": "Test Video",
            "views": 6500,  # Current view count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_video_deltas(current_video_data)
        
        # Verify deltas were calculated correctly
        assert result["views_total_delta"] == 5500  # Total gain from first record
        assert result["views_recent_delta"] == 1300  # Gain since yesterday
        assert result["views_average_delta"] == pytest.approx(785.71, 0.01)  # ~5500/7 days
        assert "views_acceleration" in result
        
    def test_video_likes_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating video like count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with likes history
        likes_history = [
            {"value": 100, "timestamp": self.create_timestamp(10)},   # 10 days ago
            {"value": 150, "timestamp": self.create_timestamp(7)},    # 7 days ago
            {"value": 200, "timestamp": self.create_timestamp(4)},    # 4 days ago 
            {"value": 220, "timestamp": self.create_timestamp(2)},    # 2 days ago
            {"value": 250, "timestamp": self.create_timestamp(1)}     # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'likes', 'video123', likes_history)
        
        # Setup current video data
        current_video_data = {
            "video_id": "video123",
            "title": "Test Video",
            "likes": 300,  # Current like count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_video_deltas(current_video_data)
        
        # Verify deltas were calculated correctly
        assert result["likes_total_delta"] == 200  # Total gain from first record
        assert result["likes_recent_delta"] == 50  # Gain since yesterday
        assert result["likes_average_delta"] == 20  # 200/10 days
        
    def test_video_comment_count_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating video comment count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with comment count history
        comment_history = [
            {"value": 10, "timestamp": self.create_timestamp(14)},   # 14 days ago
            {"value": 25, "timestamp": self.create_timestamp(10)},   # 10 days ago
            {"value": 40, "timestamp": self.create_timestamp(6)},    # 6 days ago
            {"value": 52, "timestamp": self.create_timestamp(3)},    # 3 days ago
            {"value": 55, "timestamp": self.create_timestamp(1)}     # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'comment_count', 'video123', comment_history)
        
        # Setup current video data
        current_video_data = {
            "video_id": "video123",
            "title": "Test Video",
            "comment_count": 60,  # Current comment count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_video_deltas(current_video_data)
        
        # Verify deltas were calculated correctly
        assert result["comment_count_total_delta"] == 50  # Total gain from first record
        assert result["comment_count_recent_delta"] == 5  # Gain since yesterday
        assert result["comment_count_average_delta"] == pytest.approx(3.57, 0.01)  # ~50/14 days
        
    def test_engagement_ratio_calculation(self, setup_youtube_service, setup_mock_db):
        """Test calculating engagement ratio trends over time"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with view and like history
        view_history = [
            {"value": 1000, "timestamp": self.create_timestamp(5)},  # 5 days ago
            {"value": 2000, "timestamp": self.create_timestamp(3)},  # 3 days ago
            {"value": 3000, "timestamp": self.create_timestamp(1)}   # Yesterday
        ]
        
        likes_history = [
            {"value": 50, "timestamp": self.create_timestamp(5)},    # 5 days ago
            {"value": 120, "timestamp": self.create_timestamp(3)},   # 3 days ago
            {"value": 180, "timestamp": self.create_timestamp(1)}    # Yesterday
        ]
        
        self.configure_sequential_snapshots(mock_db, 'views', 'video123', view_history)
        # Override get_metric_history to handle multiple metric types
        mock_db.get_metric_history.side_effect = lambda t, id, *args, **kwargs: (
            view_history if t == 'views' and id == 'video123' else 
            likes_history if t == 'likes' and id == 'video123' else []
        )
        
        # Setup current video data
        current_video_data = {
            "video_id": "video123",
            "title": "Test Video",
            "views": 4000,
            "likes": 260,
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_video_engagement_trends(current_video_data)
        
        # Verify engagement ratio calculations
        # Initial: 50/1000 = 5%
        # Current: 260/4000 = 6.5%
        assert result["engagement_ratio_current"] == pytest.approx(0.065, 0.001)
        assert result["engagement_ratio_change"] == pytest.approx(0.015, 0.001)  # Difference in percentages
        assert result["engagement_ratio_percent_change"] == pytest.approx(30, 0.1)  # 30% increase
