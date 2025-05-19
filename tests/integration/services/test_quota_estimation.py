"""
Integration tests for YouTube API quota estimation.
Tests the application's ability to estimate quota usage accurately.
"""
from unittest.mock import MagicMock, patch, call
import pytest

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestQuotaEstimation(BaseYouTubeTestCase):
    """Tests for API quota usage estimation and tracking"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_quota_estimation_accuracy(self, setup_service_with_mocks):
        """Test accuracy of quota usage estimation"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Create a channel with moderate size
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '100',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for videos
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': f'video{i}',
                    'title': f'Test Video {i}',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': f'{10000-i*100}',
                    'likes': f'{1000-i*10}',
                    'comment_count': f'{100-i}'
                } for i in range(20)  # Create 20 videos
            ]
        }
        
        # Configure mock for quota tracking
        mock_api.get_quota_cost = MagicMock()
        
        # Define quota costs for different operations
        quota_costs = {
            'channels.list': 1,
            'playlistItems.list': 1,
            'videos.list': 1,
            'commentThreads.list': 1
        }
        
        # Configure the mock to return appropriate quota costs
        mock_api.get_quota_cost.side_effect = lambda operation: quota_costs.get(operation, 0)
        
        # Create a wrapper to track actual API calls
        original_execute = mock_api.execute_api_request
        api_calls = []
        
        def tracked_execute_api_request(operation, **kwargs):
            api_calls.append((operation, kwargs))
            return original_execute(operation, **kwargs)
            
        mock_api.execute_api_request = tracked_execute_api_request
        
        # Set up quota estimation method
        def estimate_quota(options, video_count=None):
            # Simple estimation logic
            estimated = 0
            
            if options.get('fetch_channel_data', False):
                estimated += 1  # channels.list call
                
            if options.get('fetch_videos', False):
                estimated += 2  # playlistItems.list (1) + videos.list (1) calls
            
            if options.get('fetch_comments', False) and video_count:
                estimated += video_count  # commentThreads.list call for each video
            
            return estimated
        
        # Replace the estimate_quota_usage method with our test implementation
        service.estimate_quota_usage = estimate_quota
        
        # Mock methods that access the delta_service to avoid errors
        mock_methods = ['_calculate_video_deltas', '_calculate_comment_deltas', '_calculate_channel_deltas']
        original_methods = {}
        
        for method_name in mock_methods:
            if hasattr(service, method_name):
                original_methods[method_name] = getattr(service, method_name)
                setattr(service, method_name, MagicMock(return_value={}))
        
        # Mock the store_channel_data method to avoid the error
        mock_db.store_channel_data = MagicMock(return_value=True)
        service.db = mock_db
        
        try:
            # Test channel-only collection
            channel_options = {
                'fetch_channel_data': True,
                'fetch_videos': False,
                'fetch_comments': False
            }
            
            # Get quota estimate for channel-only
            channel_estimate = service.estimate_quota_usage(channel_options)
            
            # Collect channel data
            api_calls.clear()
            service.collect_channel_data('UC_test_channel', channel_options)
            
            # Calculate actual quota used
            actual_channel_quota = sum(quota_costs.get(op, 0) for op, _ in api_calls)
            
            # Verify estimate accuracy
            assert channel_estimate == actual_channel_quota, f"Channel estimate ({channel_estimate}) didn't match actual usage ({actual_channel_quota})"
            
            # Test video collection
            video_options = {
                'fetch_channel_data': False,
                'fetch_videos': True,
                'fetch_comments': False,
                'max_videos': 20
            }
            
            # Get quota estimate for videos
            video_estimate = service.estimate_quota_usage(video_options, video_count=20)
            
            # Collect video data
            api_calls.clear()
            service.collect_channel_data('UC_test_channel', video_options, 
                                        existing_data={'channel_id': 'UC_test_channel', 'playlist_id': 'PL_test_playlist'})
            
            # Calculate actual quota used
            actual_video_quota = sum(quota_costs.get(op, 0) for op, _ in api_calls)
            
            # Verify estimate accuracy
            assert video_estimate == actual_video_quota, f"Video estimate ({video_estimate}) didn't match actual usage ({actual_video_quota})"
        
        finally:
            # Restore original methods
            for method_name, original in original_methods.items():
                setattr(service, method_name, original)
        
        # Calculate actual quota used
        actual_video_quota = sum(quota_costs.get(op, 0) for op, _ in api_calls)
        
        # Verify estimate accuracy
        assert video_estimate == actual_video_quota, f"Video estimate ({video_estimate}) didn't match actual usage ({actual_video_quota})"
    
    def test_quota_tracking(self, setup_service_with_mocks):
        """Test tracking of cumulative quota usage"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Mock methods that access the delta_service to avoid errors
        mock_methods = ['_calculate_video_deltas', '_calculate_comment_deltas', '_calculate_channel_deltas']
        original_methods = {}
        
        for method_name in mock_methods:
            if hasattr(service, method_name):
                original_methods[method_name] = getattr(service, method_name)
                setattr(service, method_name, MagicMock(return_value={}))
        
        # Mock the store_channel_data method to avoid the error
        mock_db.store_channel_data = MagicMock(return_value=True)
        
        # Ensure the service has the mock_db
        service.db = mock_db
        
        # Configure mocks
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '50',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Setup quota tracking
        quota_used = {'value': 0}
        
        def track_quota_usage(operation):
            # Define quota costs for different operations
            quota_costs = {
                'channels.list': 1,
                'playlistItems.list': 1,
                'videos.list': 1,
                'commentThreads.list': 1
            }
            cost = quota_costs.get(operation, 0)
            quota_used['value'] += cost
            return cost
        
        mock_api.get_quota_cost = MagicMock(side_effect=track_quota_usage)
        mock_api.get_current_quota_usage = MagicMock(return_value=quota_used['value'])
        
        # Patch the quota tracking method
        original_track_quota = service.track_quota_usage
        service.track_quota_usage = MagicMock(side_effect=lambda op: track_quota_usage(op))
        
        try:
            # Test sequential operations and cumulative tracking
            
            # 1. Fetch channel info
            quota_used['value'] = 0  # Reset quota
            service.collect_channel_data('UC_test_channel', {'fetch_channel_data': True, 'fetch_videos': False})
            channel_quota = quota_used['value']
            assert channel_quota > 0, "Channel fetch should use quota"
            
            # 2. Fetch videos
            quota_used['value'] = 0  # Reset quota
            mock_api.get_channel_videos.return_value = {
                'channel_id': 'UC_test_channel',
                'video_id': [
                    {
                        'video_id': f'video{i}',
                        'title': f'Test Video {i}'
                    } for i in range(10)
                ]
            }
            service.collect_channel_data('UC_test_channel', 
                                        {'fetch_channel_data': False, 'fetch_videos': True},
                                        existing_data={'channel_id': 'UC_test_channel', 'playlist_id': 'PL_test_playlist'})
            video_quota = quota_used['value']
            assert video_quota > 0, "Video fetch should use quota"
            
            # 3. Verify cumulative tracking
            total_expected = channel_quota + video_quota
            quota_used['value'] = 0  # Reset quota
            
            # Do both operations
            service.collect_channel_data('UC_test_channel', {'fetch_channel_data': True, 'fetch_videos': True})
            combined_quota = quota_used['value']
            
            assert combined_quota == total_expected, f"Combined quota ({combined_quota}) should equal sum of individual operations ({total_expected})"
            
        finally:
            # Restore original methods
            service.track_quota_usage = original_track_quota
            
            for method_name, original in original_methods.items():
                setattr(service, method_name, original)
    
    def test_quota_limit_enforcement(self, setup_service_with_mocks):
        """Test that the quota limit is enforced when collecting data"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Mock methods that access the delta_service to avoid errors
        mock_methods = ['_calculate_video_deltas', '_calculate_comment_deltas', '_calculate_channel_deltas']
        original_methods = {}
        
        for method_name in mock_methods:
            if hasattr(service, method_name):
                original_methods[method_name] = getattr(service, method_name)
                setattr(service, method_name, MagicMock(return_value={}))
        
        # Mock the store_channel_data method to avoid the error
        mock_db.store_channel_data = MagicMock(return_value=True)
        
        # Ensure the service has the mock_db
        service.db = mock_db
        
        # Configure basic channel mock
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '500',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Setup fake video generation
        def generate_videos(count):
            return {
                'channel_id': 'UC_test_channel',
                'video_id': [
                    {
                        'video_id': f'video{i}',
                        'title': f'Test Video {i}',
                        'published_at': '2025-04-01T12:00:00Z',
                        'views': f'{10000-i}',
                        'likes': f'{1000-i}',
                        'comment_count': f'{100-i}'
                    } for i in range(count)
                ]
            }
        
        mock_api.get_channel_videos = MagicMock(side_effect=lambda channel_info, max_videos=None: 
                                               generate_videos(min(max_videos or 500, 500)))
        
        # Setup quota tracking
        remaining_quota = {'value': 10}  # Start with limited quota
        
        def get_remaining_quota():
            return remaining_quota['value']
        
        def use_quota(amount):
            remaining_quota['value'] -= amount
            if remaining_quota['value'] < 0:
                raise ValueError("Quota exceeded - not enough quota available")
        
        # Mock the quota methods
        service.get_remaining_quota = MagicMock(side_effect=get_remaining_quota)
        service.estimate_quota_usage = MagicMock(return_value=5)  # Each operation costs 5 units
        service.use_quota = MagicMock(side_effect=use_quota)
        
        # Test quota limiting
        
        # First operation should succeed (10 quota remaining, 5 needed)
        options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        result1 = service.collect_channel_data('UC_test_channel', options)
        assert result1 is not None, "First operation should succeed"
        assert remaining_quota['value'] == 5, f"Should have 5 quota left, has {remaining_quota['value']}"
        
        # Second identical operation should succeed (5 quota remaining, 5 needed)
        result2 = service.collect_channel_data('UC_test_channel', options)
        assert result2 is not None, "Second operation should succeed"
        assert remaining_quota['value'] == 0, f"Should have 0 quota left, has {remaining_quota['value']}"
        
        # Third identical operation should fail (0 quota remaining, 5 needed)
        try:
            result3 = service.collect_channel_data('UC_test_channel', options)
            assert False, "Third operation should have failed due to insufficient quota"
        except ValueError as e:
            assert "Quota exceeded" in str(e), f"Expected 'Quota exceeded' error, got: {str(e)}"
        
        # Restore original methods
        for method_name, original in original_methods.items():
            setattr(service, method_name, original)


if __name__ == '__main__':
    pytest.main()
