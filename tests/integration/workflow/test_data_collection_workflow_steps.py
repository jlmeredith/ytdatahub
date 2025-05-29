"""
Integration tests for the data collection workflow.
Tests the step-by-step collection process from API to database.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.utils.debug_utils import debug_log
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestDataCollectionWorkflow(BaseYouTubeTestCase):
    """Integration tests for the data collection workflow"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
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
    
    @pytest.fixture
    def sample_channel_data(self):
        """Sample channel data for testing"""
        return self.create_sample_channel_data()
    
    @pytest.fixture
    def sample_channel_with_videos(self):
        """Sample channel with videos"""
        return self.create_sample_videos_data()
    
    @pytest.fixture
    def sample_channel_with_comments(self):
        """Sample channel with comments"""
        return self.create_sample_comments_data()
    
    @pytest.fixture
    def sample_updated_channel_data(self):
        """Sample updated channel data for delta testing"""
        return self.create_updated_channel_data()
    
    def test_step_by_step_data_collection_workflow(self, setup_service_with_mocks):
        """Test the step-by-step data collection workflow as it appears in the UI"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API responses
        self.configure_mock_api_for_step_workflow(mock_api)
        
        # STEP 1: Load Channel Data Only
        step1_options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        channel_only_data = service.collect_channel_data('UC_test_channel', step1_options)
        
        # STEP 2: Load Videos with slider
        step2_options = {
            'fetch_channel_data': False,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 30
        }
        
        channel_with_videos = service.collect_channel_data('UC_test_channel', step2_options, existing_data=channel_only_data)
        
        # STEP 3: Load Comments
        step3_options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': 15
        }
        
        channel_with_comments = service.collect_channel_data('UC_test_channel', step3_options, existing_data=channel_with_videos)
        
        # Verify each step's results
        self.verify_step_results(channel_only_data, channel_with_videos, channel_with_comments, mock_api)
        
        # FINAL STEP: Save to database
        self.verify_storage_call(service, channel_with_comments, mock_db)


if __name__ == '__main__':
    pytest.main()
