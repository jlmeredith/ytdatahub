"""
Tests for the YouTube channel service module.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.services.youtube.channel_service import ChannelService
from src.services.youtube_service import YouTubeService

class TestChannelService(unittest.TestCase):
    """Test YouTube channel service functionality."""

    def setUp(self):
        """Set up test environment."""
        self.api_key = 'test_api_key'
        self.channel_service = ChannelService(api_key=self.api_key)
        
        # Mock API client
        self.mock_api = MagicMock()
        self.channel_service.api = self.mock_api
        
    def test_parse_channel_input_direct_id(self):
        """Test parsing a direct channel ID."""
        channel_id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
        result = self.channel_service.parse_channel_input(channel_id)
        self.assertEqual(result, channel_id)
        
    def test_parse_channel_input_url(self):
        """Test parsing a channel URL."""
        channel_url = 'https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw'
        expected_id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
        result = self.channel_service.parse_channel_input(channel_url)
        self.assertEqual(result, expected_id)
        
    def test_parse_channel_input_handle(self):
        """Test parsing a channel handle."""
        channel_handle = '@googledevelopers'
        expected_result = 'resolve:@googledevelopers'
        result = self.channel_service.parse_channel_input(channel_handle)
        self.assertEqual(result, expected_result)
        
    def test_parse_channel_input_invalid(self):
        """Test parsing an invalid input."""
        # Special characters that aren't allowed in channel names
        invalid_input = 'not_a_channel$%^'
        result = self.channel_service.parse_channel_input(invalid_input)
        self.assertIsNone(result)

    def test_parse_channel_input_name(self):
        """Test parsing a simple channel name."""
        channel_name = 'channelname'
        result = self.channel_service.parse_channel_input(channel_name)
        self.assertEqual(result, 'resolve:channelname')

class TestYouTubeServiceChannelIntegration(unittest.TestCase):
    """Test YouTube service integration with channel service."""
    
    def setUp(self):
        """Set up test environment."""
        self.api_key = 'test_api_key'
        self.service = YouTubeService(api_key=self.api_key)
        
        # Mock API clients
        self.service.api = MagicMock()
        self.service.channel_service = MagicMock()
        
    def test_get_basic_channel_info_direct_id(self):
        """Test getting channel info with a direct channel ID."""
        channel_id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
        expected_info = {'channel_id': channel_id, 'playlist_id': 'UU_x5XG1OV2P6uZZ5FSM9Ttw'}
        
        # Configure mocks
        self.service.channel_service.parse_channel_input.return_value = channel_id
        self.service.channel_service.get_channel_info.return_value = expected_info
        
        # Call method
        result = self.service.get_basic_channel_info(channel_id)
        
        # Verify
        self.assertEqual(result, expected_info)
        self.service.channel_service.parse_channel_input.assert_called_once_with(channel_id)
        self.service.channel_service.get_channel_info.assert_called_once_with(channel_id)
        
    def test_get_basic_channel_info_handle(self):
        """Test getting channel info with a channel handle that needs resolution."""
        channel_handle = '@googledevelopers'
        resolved_id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
        expected_info = {'channel_id': resolved_id, 'playlist_id': 'UU_x5XG1OV2P6uZZ5FSM9Ttw'}
        
        # Configure mocks
        self.service.channel_service.parse_channel_input.return_value = 'resolve:@googledevelopers'
        self.service.channel_service.validate_and_resolve_channel_id.return_value = (True, resolved_id)
        self.service.channel_service.get_channel_info.return_value = expected_info
        
        # Call method
        result = self.service.get_basic_channel_info(channel_handle)
        
        # Verify
        self.assertEqual(result, expected_info)
        self.service.channel_service.parse_channel_input.assert_called_once_with(channel_handle)
        self.service.channel_service.validate_and_resolve_channel_id.assert_called_once_with('resolve:@googledevelopers')
        self.service.channel_service.get_channel_info.assert_called_once_with(resolved_id)
        
    def test_get_basic_channel_info_invalid(self):
        """Test getting channel info with invalid input."""
        invalid_input = 'not_a_channel'
        
        # Configure mocks
        self.service.channel_service.parse_channel_input.return_value = None
        
        # Call method
        result = self.service.get_basic_channel_info(invalid_input)
        
        # Verify
        self.assertIsNone(result)
        self.service.channel_service.parse_channel_input.assert_called_once_with(invalid_input)
        self.service.channel_service.get_channel_info.assert_not_called() 