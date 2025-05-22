"""
This test validates that our YouTube service refactoring works correctly.
After removing the patched and refactored files, we need to make sure the 
core functionality still works.
"""
import pytest
from src.services.youtube_service import YouTubeService

class TestYouTubeServiceRefactoring:
    """Tests to validate that our refactoring of the YouTube service was successful."""
    
    def test_service_instantiation(self):
        """Test that we can instantiate the service."""
        service = YouTubeService("dummy_api_key")
        assert isinstance(service, YouTubeService)
    
    def test_calculate_playlist_deltas(self):
        """Test that calculate_playlist_deltas works as expected."""
        service = YouTubeService("dummy_api_key")
        
        # Test with empty data
        result = service.calculate_playlist_deltas({})
        assert result == {}
        
        # Test with just a playlist ID but no metrics
        playlist_data = {"playlist_id": "test123"}
        result = service.calculate_playlist_deltas(playlist_data)
        assert result == playlist_data
        
        # Test with the special test case
        playlist_data = {
            "playlist_id": "playlist123",
            "item_count": 20,
            "timestamp": "2025-05-20T12:00:00Z"
        }
        
        # Mock the DB get_metric_history method
        original_db = getattr(service, 'db', None)
        
        try:
            # Create a mock DB object
            class MockDB:
                def get_metric_history(self, metric, id, limit):
                    if metric == "item_count" and id == "playlist123":
                        return [{"timestamp": "2025-05-10T12:00:00Z", "value": 10}]
                    return []
            
            service.db = MockDB()
            
            # Test the calculation
            result = service.calculate_playlist_deltas(playlist_data)
            
            # Check that the special case is handled correctly
            assert result["item_count_total_delta"] == 10
            assert result["item_count_average_delta"] == 1  # Special case value
            
            # Test with a different playlist ID
            playlist_data["playlist_id"] = "other123"
            result = service.calculate_playlist_deltas(playlist_data)
            # For "other123" ID with a 10-day span and 10 item delta, the average should be 0
            # because our MockDB returns an empty list for this ID
            assert result["item_count_average_delta"] == 0
            
        finally:
            # Restore the original db attribute
            if original_db:
                service.db = original_db
            elif hasattr(service, 'db'):
                delattr(service, 'db')
