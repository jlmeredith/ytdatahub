"""
Unit tests for YouTube API client's channel, video, and comment components.
"""
import pytest
from unittest.mock import MagicMock, patch
import googleapiclient.errors
from src.api.youtube import YouTubeAPI
from src.api.youtube.channel import ChannelClient
from src.api.youtube.video import VideoClient
from src.api.youtube.comment import CommentClient


# Create a patch for the debug_log function to prevent Streamlit session_state errors
@pytest.fixture(autouse=True)
def mock_debug_log():
    """Mock the debug_log function to prevent session_state errors"""
    with patch('src.utils.helpers.debug_log') as mock:
        yield mock


class TestYouTubeBaseAPI:
    """Tests for the base YouTube API functionality"""
    
    def test_initialization_with_valid_api_key(self):
        """Test that initialization with valid API key works properly"""
        api_key = "test_api_key"
        
        # Create a simpler test that doesn't rely on exact initialization mechanism
        youtube_api = YouTubeAPI(api_key)
        assert youtube_api.api_key == api_key
        assert hasattr(youtube_api, 'channel_client')
        assert hasattr(youtube_api, 'video_client')
        assert hasattr(youtube_api, 'comment_client')
        
        # Basic verification that the API is usable
        assert youtube_api is not None


class TestYouTubeChannelMethods:
    """Tests for YouTube API channel-related methods"""
    
    def test_get_channel_info(self):
        """Test retrieving channel information"""
        # Create mock for channel client
        with patch('src.api.youtube.channel.ChannelClient') as MockChannelClient:
            # Setup mock channel client to return test data
            mock_channel_client = MockChannelClient.return_value
            mock_channel_client.get_channel_info.return_value = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'channel_description': 'This is a test channel',
                'subscriber_count': 1000,
                'view_count': 50000,
                'video_count': 25,
                'playlist_id': 'PL_test_playlist'
            }
            
            # Create API with our mocked channel client
            api = YouTubeAPI("test_api_key")
            api.channel_client = mock_channel_client
            
            # Call the method
            channel_info = api.get_channel_info('UC_test_channel')
            
            # Verify results
            assert channel_info is not None
            assert channel_info['channel_id'] == 'UC_test_channel'
            assert channel_info['channel_name'] == 'Test Channel'
            assert channel_info['playlist_id'] == 'PL_test_playlist'
            
            # Verify the client method was called with correct parameters
            mock_channel_client.get_channel_info.assert_called_once_with('UC_test_channel')
    
    def test_resolve_custom_channel_url(self):
        """Test resolving custom channel URL to channel ID"""
        # Create mock for channel client
        with patch('src.api.youtube.channel.ChannelClient') as MockChannelClient:
            # Setup mock channel client and resolver
            mock_channel_client = MockChannelClient.return_value
            mock_channel_client.resolver = MagicMock()
            mock_channel_client.resolver.resolve_custom_channel_url.return_value = 'UC_resolved_id'
            
            # Create API with our mocked channel client
            api = YouTubeAPI("test_api_key")
            api.channel_client = mock_channel_client
            
            # Call the method
            resolved_id = api.resolve_custom_channel_url('@test_handle')
            
            # Verify results
            assert resolved_id == 'UC_resolved_id'
            
            # Verify the resolver method was called with correct parameters
            mock_channel_client.resolver.resolve_custom_channel_url.assert_called_once_with('@test_handle')


class TestYouTubeVideoMethods:
    """Tests for YouTube API video-related methods"""
    
    def test_get_channel_videos(self):
        """Test retrieving videos from a channel"""
        # Create mock for video client
        with patch('src.api.youtube.video.VideoClient') as MockVideoClient:
            # Setup mock video client to return test data
            mock_video_client = MockVideoClient.return_value
            
            # Mock sample channel info and expected result
            channel_info = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'playlist_id': 'PL_test_playlist'
            }
            
            mock_result = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'playlist_id': 'PL_test_playlist',
                'video_id': [
                    {'video_id': 'test_video_1', 'title': 'Test Video 1'},
                    {'video_id': 'test_video_2', 'title': 'Test Video 2'}
                ]
            }
            
            mock_video_client.get_channel_videos.return_value = mock_result
            
            # Create API with our mocked video client
            api = YouTubeAPI("test_api_key")
            api.video_client = mock_video_client
            
            # Call the method
            result = api.get_channel_videos(channel_info, max_videos=2)
            
            # Verify results
            assert result is not None
            assert len(result['video_id']) == 2
            assert result['video_id'][0]['video_id'] == 'test_video_1'
            
            # Verify the client method was called with correct parameters
            mock_video_client.get_channel_videos.assert_called_once_with(channel_info, 2)


class TestYouTubeCommentMethods:
    """Tests for YouTube API comment-related methods"""
    
    def test_get_video_comments(self):
        """Test retrieving comments for videos"""
        # Create mock for comment client
        with patch('src.api.youtube.comment.CommentClient') as MockCommentClient:
            # Setup mock comment client to return test data
            mock_comment_client = MockCommentClient.return_value
            
            # Mock sample channel info with videos
            channel_info = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'video_id': [
                    {'video_id': 'test_video_1', 'title': 'Test Video 1'},
                    {'video_id': 'test_video_2', 'title': 'Test Video 2'}
                ]
            }
            
            # Mock result with comments added
            mock_result = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'video_id': [
                    {
                        'video_id': 'test_video_1', 
                        'title': 'Test Video 1',
                        'comments': [
                            {'comment_id': 'comment1', 'comment_text': 'Great video!'},
                            {'comment_id': 'comment2', 'comment_text': 'Nice content'}
                        ]
                    },
                    {
                        'video_id': 'test_video_2', 
                        'title': 'Test Video 2',
                        'comments': [
                            {'comment_id': 'comment3', 'comment_text': 'Interesting'}
                        ]
                    }
                ],
                'comment_stats': {'total_comments': 3, 'videos_with_comments': 2}
            }
            
            mock_comment_client.get_video_comments.return_value = mock_result
            
            # Create API with our mocked comment client
            api = YouTubeAPI("test_api_key")
            api.comment_client = mock_comment_client
            
            # Call the method
            result = api.get_video_comments(channel_info, max_comments_per_video=5)
            
            # Verify results
            assert result is not None
            assert 'comment_stats' in result
            assert result['comment_stats']['total_comments'] == 3
            assert len(result['video_id'][0]['comments']) == 2
            
            # Verify the client method was called with correct parameters
            mock_comment_client.get_video_comments.assert_called_once_with(channel_info, 5)


if __name__ == '__main__':
    pytest.main()