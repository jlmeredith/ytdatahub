"""
Fixtures for data collection workflow tests.
Extends the base fixture with data collection specific test methods.
"""
import pytest
from unittest.mock import patch
from tests.fixtures.base_fixture import BaseYouTubeTestFixture


class DataCollectionFixture(BaseYouTubeTestFixture):
    """Specialized fixtures for data collection workflow tests"""
    
    @pytest.fixture
    def setup_workflow_test(self, setup_service_with_mocks):
        """Configure everything needed for workflow tests"""
        service, mock_api, mock_db = setup_service_with_mocks
        mock_channel_info, mock_channel_with_videos, mock_channel_with_comments = self._configure_mock_api_for_step_workflow(mock_api)
        
        return {
            'service': service,
            'mock_api': mock_api,
            'mock_db': mock_db,
            'channel_info': mock_channel_info,
            'channel_with_videos': mock_channel_with_videos,
            'channel_with_comments': mock_channel_with_comments
        }
    
    @pytest.fixture
    def workflow_step_options(self):
        """Return common workflow steps options as a dict"""
        return {
            'channel_only': {
                'fetch_channel_data': True,
                'fetch_videos': False,
                'fetch_comments': False
            },
            'videos': {
                'fetch_channel_data': False,
                'fetch_videos': True,
                'fetch_comments': False,
                'max_videos': 30
            },
            'comments': {
                'fetch_channel_data': False,
                'fetch_videos': False,
                'fetch_comments': True,
                'max_comments_per_video': 15
            },
            'full': {
                'fetch_channel_data': True,
                'fetch_videos': True,
                'fetch_comments': True,
                'max_videos': 50,
                'max_comments_per_video': 20
            }
        }
    
    def verify_full_collection_workflow(self, result, mock_api, mock_db):
        """Verify results from a full collection workflow test"""
        # Check overall structure
        assert result is not None
        assert 'channel_id' in result
        assert 'video_id' in result
        assert len(result['video_id']) > 0
        
        # Verify video collection parameters
        _, kwargs = mock_api.get_channel_videos.call_args
        assert kwargs['max_videos'] > 0
        
        # Verify comment collection parameters
        _, kwargs = mock_api.get_video_comments.call_args
        assert kwargs['max_comments_per_video'] > 0
        
        # Verify storage was called if applicable
        if hasattr(mock_db, 'store_channel_data') and mock_db.store_channel_data.called:
            mock_db.store_channel_data.assert_called_once()