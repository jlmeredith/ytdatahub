"""
Tests for comment metrics delta calculations across sequential updates.
"""
import pytest
from unittest.mock import MagicMock, patch
import datetime

from .base_tests import TestSequentialDeltaBase


class TestCommentDeltaMetrics(TestSequentialDeltaBase):
    """Tests for sequential delta updates of comment metrics"""
    
    def test_comment_likes_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating comment like count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with comment like history
        like_history = [
            {"value": 5, "timestamp": self.create_timestamp(5)},   # 5 days ago
            {"value": 12, "timestamp": self.create_timestamp(3)},  # 3 days ago
            {"value": 18, "timestamp": self.create_timestamp(1)}   # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'likes', 'comment123', like_history)
        
        # Setup current comment data
        current_comment_data = {
            "comment_id": "comment123",
            "video_id": "video456",
            "text": "This is a test comment",
            "likes": 25,  # Current like count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_comment_deltas(current_comment_data)
        
        # Verify deltas were calculated correctly
        assert result["likes_total_delta"] == 20  # Total gain from first record
        assert result["likes_recent_delta"] == 7  # Gain since yesterday
        assert result["likes_average_delta"] == 4  # 20/5 days
        
    def test_reply_count_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating reply count deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with reply count history
        reply_history = [
            {"value": 0, "timestamp": self.create_timestamp(7)},   # 7 days ago
            {"value": 3, "timestamp": self.create_timestamp(4)},   # 4 days ago
            {"value": 5, "timestamp": self.create_timestamp(2)},   # 2 days ago
            {"value": 8, "timestamp": self.create_timestamp(1)}    # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'reply_count', 'comment123', reply_history)
        
        # Setup current comment data
        current_comment_data = {
            "comment_id": "comment123",
            "video_id": "video456",
            "text": "This is a test comment",
            "reply_count": 12,  # Current reply count
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_comment_deltas(current_comment_data)
        
        # Verify deltas were calculated correctly
        assert result["reply_count_total_delta"] == 12  # Total gain from first record
        assert result["reply_count_recent_delta"] == 4  # Gain since yesterday
        assert result["reply_count_average_delta"] == pytest.approx(1.71, 0.01)  # ~12/7 days
        
    def test_sentiment_score_delta(self, setup_youtube_service, setup_mock_db):
        """Test calculating sentiment score deltas across multiple updates"""
        service, mock_api = setup_youtube_service
        mock_db = setup_mock_db
        
        # Replace service's db with our mock
        service.db = mock_db
        
        # Configure mock database with sentiment score history (assuming -1 to 1 scale)
        sentiment_history = [
            {"value": 0.2, "timestamp": self.create_timestamp(10)},   # 10 days ago
            {"value": 0.3, "timestamp": self.create_timestamp(7)},    # 7 days ago
            {"value": 0.1, "timestamp": self.create_timestamp(4)},    # 4 days ago
            {"value": -0.1, "timestamp": self.create_timestamp(1)}    # Yesterday
        ]
        self.configure_sequential_snapshots(mock_db, 'sentiment_score', 'comment123', sentiment_history)
        
        # Setup current comment data
        current_comment_data = {
            "comment_id": "comment123",
            "video_id": "video456",
            "text": "This is a test comment",
            "sentiment_score": -0.2,  # Current sentiment score
            "timestamp": datetime.datetime.now().isoformat() + 'Z'
        }
        
        # Calculate delta metrics
        result = service.calculate_comment_sentiment_trend(current_comment_data)
        
        # Verify deltas were calculated correctly
        assert result["sentiment_total_delta"] == -0.4  # Change from first record to now
        assert result["sentiment_recent_delta"] == -0.1  # Change since yesterday
        assert result["sentiment_trend"] == "decreasing"  # Trend is decreasing
