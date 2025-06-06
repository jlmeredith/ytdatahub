print("[TEST DEBUG] base_fixture.py loaded")
"""
Base fixtures for YouTube data hub tests.
Contains common test fixtures and helper methods used across test suites.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase


class BaseYouTubeTestFixture:
    """Base class with common fixtures and helper methods for YouTube data tests"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        # Create the mocks
        mock_api = MagicMock(spec=YouTubeAPI)
        mock_db = MagicMock(spec=SQLiteDatabase)
        
        # Configure mock API to behave correctly
        mock_api.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
        mock_db.store_channel_data = MagicMock(return_value=True)
        
        # Mock channel data response
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '50'
        }
        
        # Setup service with our mocks
        service = YouTubeService("test_api_key")
        
        # Ensure we're using our mock API
        service.api = mock_api
        
        # Replace the validate_and_resolve_channel_id method
        service.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
        
        return service, mock_api, mock_db
    
    @pytest.fixture
    def sample_collection_options(self):
        """Standard options for full collection"""
        return {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': True,
            'max_videos': 50,
            'max_comments_per_video': 20
        }
    
    # Test data fixtures
    
    @pytest.fixture
    def sample_channel_data(self):
        """Sample channel data for testing"""
        return self._create_sample_channel_data()
    
    @pytest.fixture
    def sample_channel_with_videos(self):
        """Sample channel with videos"""
        return self._create_sample_videos_data()
    
    @pytest.fixture
    def sample_channel_with_comments(self):
        """Sample channel with comments"""
        return self._create_sample_comments_data()
    
    @pytest.fixture
    def sample_updated_channel_data(self):
        """Sample updated channel data for delta testing"""
        return self._create_updated_channel_data()
    
    # Helper methods for creating test data
    
    def _create_sample_channel_data(self):
        """Create standard sample channel data"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '250',
            'channel_description': 'This is a test channel',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'video_description': 'Test video description',
                    'published_at': '2025-04-01T12:00:00Z',
                    'published_date': '2025-04-01',
                    'views': '15000',
                    'likes': '1200',
                    'comment_count': '300',
                    'duration': 'PT10M30S',
                    'thumbnails': 'https://example.com/thumb1.jpg',
                    'comments': [
                        {
                            'comment_id': 'comment123',
                            'comment_text': 'Great video!',
                            'comment_author': 'Test User 1',
                            'comment_published_at': '2025-04-02T10:00:00Z',
                            'like_count': '50'
                        }
                    ]
                }
            ]
        }
    
    def _create_sample_videos_data(self):
        """Create sample data with multiple videos"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '250',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',
                    'likes': '1200',
                    'comment_count': '300'
                },
                {
                    'video_id': 'video456',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '8000',
                    'likes': '700',
                    'comment_count': '150'
                }
            ]
        }
    
    def _create_sample_comments_data(self):
        """Create sample data with comments"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '250',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',
                    'likes': '1200',
                    'comment_count': '300',
                    'comments': [
                        {
                            'comment_id': 'comment123',
                            'comment_text': 'Great video!',
                            'comment_author': 'Test User 1',
                            'comment_published_at': '2025-04-02T10:00:00Z',
                            'like_count': '50'
                        }
                    ]
                },
                {
                    'video_id': 'video456',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '8000',
                    'likes': '700',
                    'comment_count': '150',
                    'comments': [
                        {
                            'comment_id': 'comment456',
                            'comment_text': 'Very informative',
                            'comment_author': 'Test User 2',
                            'comment_published_at': '2025-04-06T14:20:00Z',
                            'like_count': '30'
                        }
                    ]
                }
            ],
            'comment_stats': {
                'total_comments': 2,
                'videos_with_comments': 2,
                'videos_with_disabled_comments': 0,
                'videos_with_errors': 0
            }
        }
    
    def _create_updated_channel_data(self):
        """Create updated channel data for delta testing"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '12000',
            'views': '5500000',
            'total_videos': '255',
            'playlist_id': 'PL_test_playlist',
            'video_id': []
        }
    
    # Helper methods for test workflows
    
    def _configure_mock_api_for_step_workflow(self, mock_api):
        """Configure mock API responses for step-by-step workflow"""
        mock_channel_info = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '250',
            'channel_description': 'This is a test channel',
            'playlist_id': 'PL_test_playlist'
        }
        
        mock_channel_with_videos = self._create_sample_videos_data()
        mock_channel_with_comments = self._create_sample_comments_data()
        
        # Setup API method responses
        mock_api.get_channel_info.return_value = mock_channel_info
        mock_api.get_channel_videos.return_value = mock_channel_with_videos
        mock_api.get_video_comments.return_value = mock_channel_with_comments
        
        return mock_channel_info, mock_channel_with_videos, mock_channel_with_comments
    
    def _verify_step_results(self, channel_only_data, channel_with_videos, channel_with_comments, mock_api):
        """Verify results from the step-by-step workflow test"""
        # Verify step 1
        assert channel_only_data is not None
        assert channel_only_data['channel_id'] == 'UC_test_channel'
        assert 'video_id' not in channel_only_data
        
        # Verify step 2
        assert channel_with_videos is not None
        assert 'video_id' in channel_with_videos
        assert len(channel_with_videos['video_id']) == 2
        
        # Verify API call parameters
        _, kwargs = mock_api.get_channel_videos.call_args
        assert kwargs['max_videos'] == 30
        
        # Verify step 3
        assert channel_with_comments is not None
        assert 'comments' in channel_with_comments['video_id'][0]
        assert 'comment_stats' in channel_with_comments
        
        # Verify API parameters
        _, kwargs = mock_api.get_video_comments.call_args
        assert kwargs['max_comments_per_video'] == 15
    
    def _verify_delta_reporting(self, result):
        """Verify delta reporting results"""
        if 'delta' in result:
            assert result['delta']['subscribers'] == 2000
            assert result['delta']['views'] == 500000
            assert result['delta']['total_videos'] == 5
            
        if 'video_delta' in result and 'new_videos' in result['video_delta']:
            assert len(result['video_delta']['new_videos']) > 0
            
        if 'comment_delta' in result:
            assert result['comment_delta']['new_comments'] >= 0