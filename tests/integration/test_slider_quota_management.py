"""
Integration tests for slider functionality and quota management.
Tests how the application handles different video count limits and quota-efficient options.
"""
import pytest
from unittest.mock import MagicMock, patch
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestSliderAndQuotaManagement(BaseYouTubeTestCase):
    """Tests focusing on slider functionality and quota management"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_dynamic_slider_for_video_selection(self, setup_service_with_mocks):
        """Test the dynamic slider functionality for selecting video counts"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API with a channel that has 100 videos
        mock_channel_info = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '100',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Setup a function to create mock videos based on the max_videos parameter
        def create_mock_videos(max_videos=None):
            count = min(max_videos if max_videos is not None else 100, 100)
            videos = []
            for i in range(count):
                videos.append({
                    'video_id': f'video{i+1}',
                    'title': f'Test Video {i+1}',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '10000',
                    'likes': '1000',
                    'comment_count': '200'
                })
            return {
                'channel_id': 'UC_test_channel',
                'video_id': videos,
                'total_videos': '100'
            }
        
        # Configure mock API responses
        mock_api.get_channel_info.return_value = mock_channel_info
        mock_api.get_channel_videos = MagicMock(side_effect=lambda channel_info, max_videos=None, page_token=None, optimize_quota=False: create_mock_videos(max_videos))
        
        # Get initial channel data
        channel_options = {'fetch_channel_data': True, 'fetch_videos': False, 'fetch_comments': False}
        channel_data = service.collect_channel_data('UC_test_channel', channel_options)
        
        # Test slider at different settings
        slider_settings = [10, 50, 100]  # Min, middle, max settings
        
        for video_count in slider_settings:
            # Reset mock call counts between tests
            mock_api.get_channel_videos.reset_mock()
            
            # Set options with current slider value
            options = {
                'fetch_channel_data': False,
                'fetch_videos': True,
                'fetch_comments': False,
                'max_videos': video_count
            }
            
            # Collect data with current slider setting
            result = service.collect_channel_data('UC_test_channel', options, existing_data=channel_data)
            
            # Verify correct number of videos returned
            assert result is not None
            assert 'video_id' in result
            assert len(result['video_id']) == video_count
            
            # Verify API was called with correct parameters
            mock_api.get_channel_videos.assert_called_once()
            _, kwargs = mock_api.get_channel_videos.call_args
            assert kwargs['max_videos'] == video_count
    
    def test_quota_efficient_data_collection(self, setup_service_with_mocks):
        """Test collection with quota-efficient settings"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API
        mock_channel_videos = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'video_description': 'Test description',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',
                    'likes': '1200'
                },
                {
                    'video_id': 'video456',
                    'title': 'Test Video 2',
                    'video_description': 'Another description',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '8000',
                    'likes': '700'
                }
            ]
        }
        
        channel_info = {'channel_id': 'UC_test_channel', 'channel_name': 'Test Channel'}
        mock_api.get_channel_info.return_value = channel_info
        
        # Mock the video fetching with max_videos parameter
        mock_api.get_channel_videos = MagicMock(side_effect=lambda channel_info_obj, max_videos=None, page_token=None, optimize_quota=False: mock_channel_videos)
        
        # Use quota-efficient options
        efficient_options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 10,
            'max_comments_per_video': 0
        }
        
        # Collect and verify data
        channel_data = service.collect_channel_data('UC_test_channel', efficient_options)
        
        assert channel_data is not None
        assert 'video_id' in channel_data
        
        # Verify API calls
        mock_api.get_channel_videos.assert_called_once()
        args, kwargs = mock_api.get_channel_videos.call_args
        assert kwargs.get('max_videos') == 10
        mock_api.get_video_comments.assert_not_called()
        
        # Test incremental comment fetching
        def mock_get_comments(videos, max_comments_per_video=None, page_token=None, optimize_quota=False):
            # Handle the case where videos is a list (from our implementation)
            # instead of a dict (as expected by the original mock)
            if isinstance(videos, list):
                return {
                    'video_id': videos,
                    'comment_stats': {
                        'total_comments': 5,
                        'videos_with_comments': len(videos),
                        'videos_with_disabled_comments': 0,
                        'videos_with_errors': 0
                    }
                }
                
            # Original mock implementation for backward compatibility
            return {
                'video_id': videos['video_id'],
                'comment_stats': {
                    'total_comments': 5,
                    'videos_with_comments': 2,
                    'videos_with_disabled_comments': 0,
                    'videos_with_errors': 0
                }
            }
            
        mock_api.get_video_comments = MagicMock(side_effect=mock_get_comments)
        
        # Update with just comments
        comment_options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': 5
        }
        
        updated_data = service.collect_channel_data('UC_test_channel', comment_options, existing_data=channel_data)
        
        # Verify comment collection call
        mock_api.get_video_comments.assert_called_once()
        args, kwargs = mock_api.get_video_comments.call_args
        assert kwargs.get('max_comments_per_video') == 5


if __name__ == '__main__':
    pytest.main()
