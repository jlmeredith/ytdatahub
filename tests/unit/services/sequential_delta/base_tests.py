"""
Base test class for sequential delta update tests.
"""
import pytest
from unittest.mock import MagicMock, patch
import json
import datetime
from src.services.youtube_service import YouTubeService


class TestSequentialDeltaBase:
    """
    Base class for sequential delta update tests, providing common fixtures and utilities.
    """
    
    @pytest.fixture
    def setup_youtube_service(self):
        """Setup a YouTube service with mocked API for testing"""
        # Create mock API
        mock_api = MagicMock()
        
        # Setup service with mock API
        service = YouTubeService("test_api_key")
        service.api = mock_api
        
        # Patch the validate_and_resolve_channel_id method to always succeed
        service.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
        
        return service, mock_api
    
    @pytest.fixture
    def setup_mock_db(self):
        """Setup a mock database for delta tracking"""
        mock_db = MagicMock()
        
        # Configure mock to return empty history by default
        mock_db.get_metric_history.return_value = []
        
        return mock_db
    
    def create_timestamp(self, days_ago):
        """Create an ISO timestamp for a specified number of days in the past"""
        date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return date.isoformat() + 'Z'
    
    def configure_sequential_snapshots(self, mock_db, metric_type, entity_id, snapshots):
        """
        Configure mock database to return sequential snapshots for delta testing
        
        Args:
            mock_db: The mock database object
            metric_type: Type of metric ('views', 'likes', 'subscribers', etc)
            entity_id: Channel ID, video ID, etc.
            snapshots: List of dicts with value and timestamp keys
        """
        mock_db.get_metric_history.side_effect = lambda t, id, *args, **kwargs: (
            snapshots if t == metric_type and id == entity_id else []
        )
