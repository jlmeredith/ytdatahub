"""
Fixtures for delta reporting functionality tests.
Extends the base fixture with delta reporting specific test methods.
"""
import pytest
from unittest.mock import patch
from tests.fixtures.base_fixture import BaseYouTubeTestFixture


class DeltaReportingFixture(BaseYouTubeTestFixture):
    """Specialized fixtures for delta reporting tests"""
    
    @pytest.fixture
    def setup_delta_test(self, setup_service_with_mocks):
        """Configure everything needed for delta tests"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure initial data
        initial_data = self._create_sample_channel_data()
        
        # Configure updated data with subscriber and view count changes
        updated_data = self._create_updated_channel_data()
        
        # Setup mock API responses for sequential calls
        mock_api.get_channel_info.side_effect = [initial_data, updated_data]
        
        return {
            'service': service,
            'mock_api': mock_api,
            'mock_db': mock_db,
            'initial_data': initial_data,
            'updated_data': updated_data
        }
    
    @pytest.fixture
    def sample_channel_delta(self):
        """Generate sample channel delta data"""
        return {
            'subscribers': 2000,
            'views': 500000, 
            'total_videos': 5
        }
    
    @pytest.fixture
    def sample_video_delta(self):
        """Generate sample video delta data"""
        return {
            'new_videos': [
                {
                    'video_id': 'videoDelta1',
                    'title': 'New Test Video 1',
                    'published_at': '2025-04-28T12:00:00Z',
                    'views': '2500',
                    'likes': '320',
                    'comment_count': '75'
                },
                {
                    'video_id': 'videoDelta2',
                    'title': 'New Test Video 2',
                    'published_at': '2025-04-29T10:00:00Z',
                    'views': '1200',
                    'likes': '95',
                    'comment_count': '30'
                }
            ],
            'updated_videos': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'views_delta': 5000,
                    'likes_delta': 300,
                    'comment_count_delta': 50
                }
            ]
        }
    
    @pytest.fixture
    def sample_comment_delta(self):
        """Generate sample comment delta data"""
        return {
            'new_comments': 50,
            'videos_with_new_comments': 3,
            'average_new_comments_per_video': 16.67
        }
    
    def verify_sequential_delta(self, first_run, second_run):
        """Verify sequential delta processing"""
        # First run should be a complete dataset
        assert first_run is not None
        assert 'channel_id' in first_run
        assert first_run.get('subscribers') == '10000'
        
        # Second run should include delta reporting
        assert second_run is not None
        assert 'delta' in second_run
        assert second_run['delta']['subscribers'] == 2000
        assert second_run['delta']['views'] == 500000
        assert second_run['delta']['total_videos'] == 5
        
        # Compare timestamps if available
        if 'collection_date' in first_run and 'collection_date' in second_run:
            assert second_run['collection_date'] > first_run['collection_date']