"""
Unit tests for the Enhanced Data Comparison Framework functionality.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure project root is on path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.services.youtube_service import YouTubeService
from src.services.youtube.delta_service import DeltaService

class TestEnhancedComparisonFramework:
    """Tests for the Enhanced Data Comparison Framework"""
    
    @pytest.fixture
    def mock_storage_service(self):
        """Create a mock storage service"""
        mock_storage = MagicMock()
        mock_storage.get_channel_data.return_value = None
        return mock_storage
    
    def test_comparison_options_defaults(self, mock_youtube_api):
        """Test that default comparison options are set properly"""
        # Create service with mocked components
        service = YouTubeService("test_api_key")
        service.api = mock_youtube_api
        service.storage_service = MagicMock()
        service.storage_service.get_channel_data.return_value = None
        
        # Mock the collect_channel_data method
        service.collect_channel_data = MagicMock(return_value={
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
        })
        
        # Call update_channel_data without specifying comparison_level
        result = service.update_channel_data('UC_test_channel', {
            'fetch_channel_data': True
        })
        
        # Check that comparison options are properly set with defaults
        assert 'comparison_options' in result
        assert result['comparison_options']['comparison_level'] == 'comprehensive'
        assert isinstance(result['comparison_options']['track_keywords'], list)
        assert result['comparison_options']['alert_on_significant_changes'] is True
        assert result['comparison_options']['persist_change_history'] is True
    
    def test_comparison_options_custom(self, mock_youtube_api):
        """Test that custom comparison options are respected"""
        # Create service with mocked components
        service = YouTubeService("test_api_key")
        service.api = mock_youtube_api
        service.storage_service = MagicMock()
        service.storage_service.get_channel_data.return_value = None
        
        # Mock the collect_channel_data method
        service.collect_channel_data = MagicMock(return_value={
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
        })
        
        # Call update_channel_data with custom comparison options
        custom_options = {
            'fetch_channel_data': True,
            'comparison_level': 'basic',
            'track_keywords': ['test', 'custom'],
            'alert_on_significant_changes': False,
            'persist_change_history': False
        }
        result = service.update_channel_data('UC_test_channel', custom_options)
        
        # Check that custom comparison options are preserved
        assert 'comparison_options' in result
        assert result['comparison_options']['comparison_level'] == 'basic'
        assert 'test' in result['comparison_options']['track_keywords']
        assert 'custom' in result['comparison_options']['track_keywords']
        assert result['comparison_options']['alert_on_significant_changes'] is False
        assert result['comparison_options']['persist_change_history'] is False
    
    def test_delta_calculation_with_comprehensive_mode(self):
        """Test comprehensive delta calculation"""
        # Create the DeltaService directly
        delta_service = DeltaService()
        
        # Create test data
        new_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel Updated',
            'subscribers': 1100,
            'views': 55000,
            'total_videos': 22,
            'channel_description': 'This is a new description with copyright notice',
            'country': 'US',
            'published_at': '2022-01-01T00:00:00Z'
        }
        
        old_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': 1000,
            'views': 50000,
            'total_videos': 20,
            'channel_description': 'This is a test channel description',
            'country': 'UK',
            'published_at': '2022-01-01T00:00:00Z'
        }
        
        # Calculate deltas with comprehensive mode
        options = {
            'comparison_level': 'comprehensive',
            'track_keywords': ['copyright', 'new owner'],
            'alert_on_significant_changes': True
        }
        
        result = delta_service.calculate_deltas(new_data, old_data, options)
        
        # Check that delta was properly calculated
        assert 'delta' in result
        delta = result['delta']
        
        # Check numeric fields
        assert 'subscribers' in delta
        assert delta['subscribers']['old'] == 1000
        assert delta['subscribers']['new'] == 1100
        
        # Check text fields
        assert 'channel_name_new' in delta
        assert delta['channel_name_new']['value'] == 'Test Channel Updated'
        
        # Check country change (indicator of ownership change)
        assert 'country_new' in delta
        assert delta['country_new']['value'] == 'US'
        
        # Check keyword tracking in description
        assert 'channel_description_new' in delta
        
        # Check significant_changes detection
        assert 'significant_changes' in delta
        
        # Check comparison level is recorded
        assert '_comparison_level' in delta
        assert delta['_comparison_level'] == 'comprehensive'

    def test_keyword_tracking_functionality(self):
        """Test keyword tracking functionality"""
        # Create the DeltaService directly
        delta_service = DeltaService()
        
        # Test the _check_text_for_keywords method directly
        old_text = "This is a normal description without any keywords"
        new_text = "This is a description with new ownership disclosure and copyright notice"
        keywords = ['ownership', 'copyright']
        
        result = delta_service._check_text_for_keywords(new_text, old_text, keywords)
        
        # Verify keywords were detected
        assert 'added' in result
        assert len(result['added']) > 0
        assert any('ownership' in kw.lower() for kw in result['added'])
        
        # Verify context was captured
        assert 'context' in result
