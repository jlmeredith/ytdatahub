"""
This test validates that our YouTube service refactoring works correctly.
After removing the patched and refactored files, we need to make sure the 
core functionality still works.
"""
import pytest
from src.services.youtube_service import YouTubeService
import os
from src.services.youtube.storage_service import StorageService
import sqlite3
import tempfile

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

def test_storage_service_db_path_default():
    svc = StorageService()
    assert svc.db_path == 'data/youtube_data.db'

def test_storage_service_db_path_custom():
    svc = StorageService(db_path='custom/path/to.db')
    assert svc.db_path == 'custom/path/to.db'

def test_save_channel_data_logs_playlist_id_mapping(mocker):
    from src.services.youtube.storage_service import StorageService
    svc = StorageService()
    mock_debug = mocker.patch('src.utils.debug_utils.debug_log')
    channel_data = {'channel_id': 'UC123', 'playlist_id': 'UU123'}
    svc.save_channel_data(channel_data, storage_type='sqlite')
    # Check that debug_log was called with the mapping message
    assert any('[WORKFLOW] Mapped playlist_id to uploads_playlist_id' in str(call.args[0]) for call in mock_debug.call_args_list)

def test_new_channel_workflow_playlist_id_logging(mocker):
    from src.services.youtube.service_impl.data_collection import DataCollectionMixin
    mock_api = mocker.Mock()
    mock_api.get_channel_info.return_value = {'channel_id': 'UC123', 'channel_name': 'Test', 'subscribers': '100', 'views': '1000', 'total_videos': '10'}
    mock_api.get_playlist_id_for_channel.return_value = 'UU123'
    mock_video_service = mocker.Mock()
    mock_storage_service = mocker.Mock()
    mixin = DataCollectionMixin()
    mixin.api = mock_api
    mixin.video_service = mock_video_service
    mixin.storage_service = mock_storage_service
    mock_debug = mocker.patch('src.utils.debug_utils.debug_log')
    options = {'fetch_videos': False}
    result = mixin.collect_channel_data('UC123', options)
    # Should fetch playlist_id, store it, and log actions
    assert result['playlist_id'] == 'UU123'
    assert any('Successfully fetched playlist_id' in str(call.args[0]) for call in mock_debug.call_args_list)
    assert any('playlist_id already present' in str(call.args[0]) or 'Successfully fetched playlist_id' in str(call.args[0]) for call in mock_debug.call_args_list)

def test_update_channel_workflow_playlist_id_logging(mocker):
    from src.services.youtube.service_impl.data_collection import DataCollectionMixin
    mock_api = mocker.Mock()
    mock_api.get_channel_info.return_value = {'channel_id': 'UC456', 'channel_name': 'Test2', 'subscribers': '200', 'views': '2000', 'total_videos': '20'}
    mock_api.get_playlist_id_for_channel.return_value = 'UU456'
    mock_video_service = mocker.Mock()
    mock_storage_service = mocker.Mock()
    mixin = DataCollectionMixin()
    mixin.api = mock_api
    mixin.video_service = mock_video_service
    mixin.storage_service = mock_storage_service
    mock_debug = mocker.patch('src.utils.debug_utils.debug_log')
    options = {'fetch_videos': False}
    existing_data = {'channel_id': 'UC456'}
    result = mixin.collect_channel_data('UC456', options, existing_data)
    # Should fetch playlist_id, store it, and log actions
    assert result['playlist_id'] == 'UU456'
    assert any('Successfully fetched playlist_id' in str(call.args[0]) for call in mock_debug.call_args_list)
    assert any('playlist_id already present' in str(call.args[0]) or 'Successfully fetched playlist_id' in str(call.args[0]) for call in mock_debug.call_args_list)

def test_get_playlist_id_for_channel_never_returns_channel_id(mocker):
    from src.services.youtube_service import YouTubeService
    svc = YouTubeService('dummy')
    # Patch the API client
    mock_api = mocker.Mock()
    svc.api = mock_api
    # Case 1: API returns valid playlist ID
    mock_api.youtube.channels().list().execute.return_value = {
        'items': [{
            'contentDetails': {'relatedPlaylists': {'uploads': 'UU123'}}
        }]
    }
    result = svc.get_playlist_id_for_channel('UC123')
    assert result == 'UU123'
    # Case 2: API returns channel ID as playlist ID (invalid)
    mock_api.youtube.channels().list().execute.return_value = {
        'items': [{
            'contentDetails': {'relatedPlaylists': {'uploads': 'UC123'}}
        }]
    }
    result = svc.get_playlist_id_for_channel('UC123')
    assert result == ''
    # Case 3: API returns empty string
    mock_api.youtube.channels().list().execute.return_value = {
        'items': [{
            'contentDetails': {'relatedPlaylists': {'uploads': ''}}
        }]
    }
    result = svc.get_playlist_id_for_channel('UC123')
    assert result == ''
    # Case 4: API returns playlist ID not starting with UU
    mock_api.youtube.channels().list().execute.return_value = {
        'items': [{
            'contentDetails': {'relatedPlaylists': {'uploads': 'PL123'}}
        }]
    }
    result = svc.get_playlist_id_for_channel('UC123')
    assert result == ''
