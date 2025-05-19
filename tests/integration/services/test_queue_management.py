"""
Integration tests for queue management of uncommitted data.
Tests the tracking of uncommitted data in the application queue.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.utils.queue_tracker import add_to_queue, remove_from_queue, set_test_mode
from src.utils.queue_tracker import set_queue_hooks, clear_queue_hooks
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestQueueManagement(BaseYouTubeTestCase):
    """Tests for queue management of uncommitted data"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_queue_management_uncommitted_data(self, setup_service_with_mocks):
        """Test the queue management system for tracking uncommitted data"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Enable test mode in the queue tracker
        set_test_mode(True)
        
        # Configure mock API responses
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '50'
        }
        
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video',
                    'views': '15000'
                }
            ]
        }
        
        # Create mocks for the hook functions
        mock_add_hook = MagicMock()
        mock_remove_hook = MagicMock()
        
        # Set hooks to track queue operations
        set_queue_hooks(add_hook=mock_add_hook, remove_hook=mock_remove_hook)
        
        try:
            # Collect channel and video data
            options = {
                'fetch_channel_data': True,
                'fetch_videos': True,
                'fetch_comments': False
            }
            
            # 1. Start collection - this should add to the queue
            channel_data = service.collect_channel_data('UC_test_channel', options)
            
            # Verify data was added to the queue
            assert mock_add_hook.call_count == 1, f"Expected add_to_queue to be called once, was called {mock_add_hook.call_count} times"
            args = mock_add_hook.call_args[0]
            assert args[0] == 'channels'
            assert args[2] == 'UC_test_channel'
            
            mock_add_hook.reset_mock()
            
            # 2. Save the data (should remove from queue)
            with patch('src.storage.factory.StorageFactory.get_storage_provider', return_value=mock_db):
                save_result = service.save_channel_data(channel_data, 'SQLite Database')
                assert save_result is True
                
                # Verify save completed and removed item from queue
                assert mock_remove_hook.call_count == 1, f"Expected remove_from_queue to be called once, was called {mock_remove_hook.call_count} times"
                args = mock_remove_hook.call_args[0]
                assert args[0] == 'channels'
                assert args[1] == 'UC_test_channel'
        
        finally:
            # Always clean up hooks after test
            clear_queue_hooks()
            set_test_mode(False)


if __name__ == '__main__':
    pytest.main()
