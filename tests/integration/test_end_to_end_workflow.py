"""
Integration tests for the complete end-to-end workflow.
Tests the full data collection and storage pipeline.
"""
import pytest
from unittest.mock import MagicMock, patch
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestEndToEndWorkflow(BaseYouTubeTestCase):
    """Test the complete end-to-end workflow"""
    
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
    
    def test_full_channel_collection_and_storage(self, setup_service_with_mocks, sample_collection_options):
        """Test the complete workflow of collecting and storing channel data"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Get sample data
        sample_channel_data = self.create_sample_channel_data()
        
        # Configure mocks to return proper data for the service methods
        mock_api.get_channel_info.return_value = sample_channel_data
        mock_api.get_channel_videos.return_value = sample_channel_data
        mock_api.get_video_comments.return_value = sample_channel_data
        
        # Step 1: Collect channel data
        channel_data = service.collect_channel_data('UC_test_channel', sample_collection_options)
        
        # Verify collection step
        assert channel_data is not None
        assert channel_data['channel_id'] == 'UC_test_channel'
        assert 'video_id' in channel_data and len(channel_data['video_id']) > 0
        assert 'comments' in channel_data['video_id'][0]
        
        # Save the data with proper patching
        self.verify_storage_call(service, channel_data, mock_db)


if __name__ == '__main__':
    pytest.main()
