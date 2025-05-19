"""
Unit tests for the YouTube Service, which coordinates data collection and storage.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.services.youtube_service import YouTubeService


class TestYouTubeService:
    """Tests for the YouTube Service"""
    
    def test_initialization(self, mock_youtube_api, mock_sqlite_db):
        """Test service initialization with API key and DB"""
        # Create and verify basic service initialization
        service = YouTubeService("test_api_key")
        
        # Check that the service has critical attributes 
        assert hasattr(service, 'api')
        assert service.api is not None
        
        # Manually replace the API with our mock for subsequent tests
        service.api = mock_youtube_api
        assert service.api == mock_youtube_api
    
    # For the remaining tests, we'll manually set the mock API
    def test_collect_channel_data_full(self, mock_youtube_api, sample_collection_options):
        """Test collecting full channel data (channel info, videos, comments)"""
        # Create service and manually set the mock
        service = YouTubeService("test_api_key")
        service.api = mock_youtube_api
        
        # Call the method being tested
        channel_data = service.collect_channel_data('UC_test_channel', sample_collection_options)
        
        # Verify the channel data was collected correctly
        assert channel_data is not None
        assert channel_data['channel_id'] == 'UC_test_channel'
        assert channel_data['channel_name'] == 'Test Channel'
        assert len(channel_data['video_id']) > 0
        
        # Verify the right API methods were called with the right params
        mock_youtube_api.get_channel_info.assert_called_once_with('UC_test_channel')
        mock_youtube_api.get_channel_videos.assert_called_once()
        mock_youtube_api.get_video_comments.assert_called_once()
    
    def test_collect_channel_data_channel_only(self, mock_youtube_api):
        """Test collecting only channel info (no videos/comments)"""
        # Create service and manually set the mock
        service = YouTubeService("test_api_key")
        service.api = mock_youtube_api
        
        # Options to fetch only channel data
        options = {
            'fetch_channel_data': True, 
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        # Call the method being tested
        channel_data = service.collect_channel_data('UC_test_channel', options)
        
        # Verify only channel info was collected
        assert channel_data is not None
        assert channel_data['channel_id'] == 'UC_test_channel'
        
        # Verify only the right API methods were called
        mock_youtube_api.get_channel_info.assert_called_once_with('UC_test_channel')
        mock_youtube_api.get_channel_videos.assert_not_called()
        mock_youtube_api.get_video_comments.assert_not_called()
    
    def test_collect_channel_data_with_existing_data(self, mock_youtube_api, sample_channel_data):
        """Test updating existing channel data"""
        # Create service and manually set the mock
        service = YouTubeService("test_api_key")
        service.api = mock_youtube_api
        
        # Options to fetch videos only
        options = {
            'fetch_channel_data': False,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 10
        }
        
        # Call the method with existing data
        updated_data = service.collect_channel_data(
            'UC_test_channel', 
            options, 
            existing_data=sample_channel_data
        )
        
        # Verify the data was updated correctly
        assert updated_data is not None
        assert updated_data['channel_id'] == sample_channel_data['channel_id']
        
        # Verify appropriate API methods were called
        mock_youtube_api.get_channel_info.assert_not_called()  # Should not call this
        mock_youtube_api.get_channel_videos.assert_called_once()
    
    def test_collect_channel_data_validate_resolve_channel_id(self, mock_youtube_api):
        """Test channel ID resolution for custom URLs"""
        # Create service and manually set the mock
        service = YouTubeService("test_api_key")
        service.api = mock_youtube_api
        
        # Mock the validate_and_resolve_channel_id method
        service.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_resolved_channel'))
        
        # Options for basic channel info
        options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        # Call the method with a custom URL
        service.collect_channel_data('@custom_handle', options)
        
        # Verify the resolve method was called and resolved ID was used
        service.validate_and_resolve_channel_id.assert_called_once_with('@custom_handle')
        mock_youtube_api.get_channel_info.assert_called_once_with('UC_resolved_channel')
    
    def test_save_channel_data(self, mock_youtube_api, mock_sqlite_db, sample_channel_data):
        """Test saving channel data to storage"""
        # Create service
        service = YouTubeService("test_api_key")
        
        # Specify the storage type - must match values in StorageFactory
        storage_type = "SQLite Database"
        
        # Configure the mock to return True for store_channel_data
        mock_sqlite_db.store_channel_data.return_value = True
        
        # Patch the storage factory to return our mock DB
        with patch('src.storage.factory.StorageFactory.get_storage_provider', return_value=mock_sqlite_db):
            # Call the method with the required storage_type parameter
            result = service.save_channel_data(sample_channel_data, storage_type)
            
            # Verify the database store_channel_data method was called (correct method name)
            mock_sqlite_db.store_channel_data.assert_called_once_with(sample_channel_data)
            assert result is True
    
    def test_save_channel_data_with_individual_methods(self, mock_youtube_api, mock_sqlite_db, sample_channel_data):
        """Test the individual save methods for channels, videos, and comments"""
        with patch('src.api.youtube_api.YouTubeAPI', return_value=mock_youtube_api), \
             patch('src.database.sqlite.SQLiteDatabase', return_value=mock_sqlite_db):
            
            service = YouTubeService("test_api_key")
            service.db = mock_sqlite_db
            
            # Test save_channel
            channel_result = service.save_channel(sample_channel_data)
            assert channel_result is True
            mock_sqlite_db.store_channel_data.assert_called_once_with(sample_channel_data)
            
            # Test save_video
            video_result = service.save_video(sample_channel_data['video_id'][0])
            assert video_result is True
            mock_sqlite_db.store_video_data.assert_called_once_with(sample_channel_data['video_id'][0])
            
            # Test save_comments
            comments = sample_channel_data['video_id'][0]['comments']
            video_id = sample_channel_data['video_id'][0]['video_id']
            comment_result = service.save_comments(comments, video_id)
            assert comment_result is True
            mock_sqlite_db.store_comments.assert_called_once_with(comments, video_id)
    
    def test_validate_and_resolve_channel_id(self, mock_youtube_api):
        """Test channel ID validation and resolution"""
        # Create service
        service = YouTubeService("test_api_key")
        
        # Mock channel_service directly since validate_and_resolve_channel_id delegates to it
        service.channel_service = MagicMock()
        
        # First test: Valid channel ID directly
        service.channel_service.validate_and_resolve_channel_id.return_value = (True, 'UC_test_channel')
        
        valid, channel_id = service.validate_and_resolve_channel_id('UC_test_channel')
        assert valid is True
        assert channel_id == 'UC_test_channel'
        
        # Second test: Custom URL that needs resolution
        service.channel_service.validate_and_resolve_channel_id.return_value = (True, 'UC_resolved_channel')
        
        valid, channel_id = service.validate_and_resolve_channel_id('@custom_handle')
        assert valid is True
        assert channel_id == 'UC_resolved_channel'
        
        # Verify the right methods were called
        service.channel_service.validate_and_resolve_channel_id.assert_called_with('@custom_handle')


if __name__ == '__main__':
    pytest.main()