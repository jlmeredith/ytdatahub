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
    with patch('src.utils.debug_utils.debug_log') as mock:
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
            # Setup mock channel client to return test data with enhanced statistics
            mock_channel_client = MockChannelClient.return_value
            mock_channel_client.get_channel_info.return_value = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'channel_description': 'This is a test channel',
                'subscribers': '1000',
                'views': '50000',
                'total_videos': '25',
                'playlist_id': 'PL_test_playlist',
                'published_at': '2020-01-01T00:00:00Z',
                'country': 'US',
                'custom_url': '@test_channel',
                'thumbnail_default': 'http://example.com/default.jpg',
                'thumbnail_medium': 'http://example.com/medium.jpg',
                'thumbnail_high': 'http://example.com/high.jpg',
                'fetched_at': '2023-01-01T00:00:00Z',
                'video_id': []
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
            assert channel_info['subscribers'] == '1000'
            assert channel_info['views'] == '50000'
            assert channel_info['total_videos'] == '25'
            assert channel_info['published_at'] == '2020-01-01T00:00:00Z'
            assert channel_info['country'] == 'US'
            assert channel_info['custom_url'] == '@test_channel'
            assert channel_info['thumbnail_default'] == 'http://example.com/default.jpg'
            assert channel_info['thumbnail_medium'] == 'http://example.com/medium.jpg'
            assert channel_info['thumbnail_high'] == 'http://example.com/high.jpg'
            assert channel_info['fetched_at'] == '2023-01-01T00:00:00Z'
            
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
    
    def test_get_video_details_batch(self):
        """Test retrieving detailed information for a batch of videos"""
        # Create mock for video client
        with patch('src.api.youtube.video.VideoClient') as MockVideoClient:
            # Setup mock video client to return test data
            mock_video_client = MockVideoClient.return_value
            
            # Mock video IDs
            video_ids = ['test_video_1', 'test_video_2']
            
            # Mock detailed video results 
            mock_result = [
                {
                    'id': 'test_video_1',
                    'snippet': {
                        'title': 'Test Video 1',
                        'description': 'Test description 1',
                        'publishedAt': '2023-01-01T00:00:00Z',
                        'thumbnails': {
                            'default': {'url': 'http://example.com/thumb1_default.jpg'},
                            'medium': {'url': 'http://example.com/thumb1_medium.jpg'},
                            'high': {'url': 'http://example.com/thumb1_high.jpg'}
                        }
                    },
                    'contentDetails': {
                        'duration': 'PT5M30S',
                        'dimension': '2d',
                        'definition': 'hd'
                    },
                    'statistics': {
                        'viewCount': '1000',
                        'likeCount': '50',
                        'commentCount': '10'
                    }
                },
                {
                    'id': 'test_video_2',
                    'snippet': {
                        'title': 'Test Video 2',
                        'description': 'Test description 2',
                        'publishedAt': '2023-01-02T00:00:00Z',
                        'thumbnails': {
                            'default': {'url': 'http://example.com/thumb2_default.jpg'},
                            'medium': {'url': 'http://example.com/thumb2_medium.jpg'},
                            'high': {'url': 'http://example.com/thumb2_high.jpg'}
                        }
                    },
                    'contentDetails': {
                        'duration': 'PT3M15S',
                        'dimension': '2d',
                        'definition': 'hd'
                    },
                    'statistics': {
                        'viewCount': '2000',
                        'likeCount': '100',
                        'commentCount': '20'
                    }
                }
            ]
            
            mock_video_client.get_video_details_batch.return_value = mock_result
            
            # Create API with our mocked video client
            api = YouTubeAPI("test_api_key")
            api.video_client = mock_video_client
            
            # Call the method
            result = api.get_video_details_batch(video_ids)
            
            # Verify results
            assert result is not None
            assert len(result) == 2
            assert result[0]['id'] == 'test_video_1'
            assert result[0]['statistics']['viewCount'] == '1000'
            assert result[0]['statistics']['likeCount'] == '50'
            assert result[0]['statistics']['commentCount'] == '10'
            assert result[1]['id'] == 'test_video_2'
            assert result[1]['statistics']['viewCount'] == '2000'
            
            # Verify the client method was called with correct parameters
            mock_video_client.get_video_details_batch.assert_called_once_with(video_ids)
    
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
            
            # Enhanced mock result with complete statistics
            mock_result = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'playlist_id': 'PL_test_playlist',
                'video_id': [
                    {
                        'video_id': 'test_video_1', 
                        'title': 'Test Video 1',
                        'views': '1000',
                        'likes': '50',
                        'comment_count': '10',
                        'statistics': {
                            'viewCount': '1000',
                            'likeCount': '50',
                            'commentCount': '10'
                        }
                    },
                    {
                        'video_id': 'test_video_2', 
                        'title': 'Test Video 2',
                        'views': '2000',
                        'likes': '100',
                        'comment_count': '20',
                        'statistics': {
                            'viewCount': '2000',
                            'likeCount': '100',
                            'commentCount': '20'
                        }
                    }
                ],
                'comment_counts': {
                    'total_comment_count': 30,
                    'videos_with_comments': 2
                }
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
            
            # Verify statistics are present
            assert 'views' in result['video_id'][0]
            assert result['video_id'][0]['views'] == '1000'
            assert 'likes' in result['video_id'][0]
            assert result['video_id'][0]['likes'] == '50'
            assert 'comment_count' in result['video_id'][0]
            assert result['video_id'][0]['comment_count'] == '10'
            assert 'statistics' in result['video_id'][0]
            assert result['video_id'][0]['statistics']['viewCount'] == '1000'
            
            # Verify the comment counts aggregate is present
            assert 'comment_counts' in result
            assert result['comment_counts']['total_comment_count'] == 30
            
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
            
            # Mock sample channel info with videos including statistics
            channel_info = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'video_id': [
                    {
                        'video_id': 'test_video_1', 
                        'title': 'Test Video 1',
                        'comment_count': '10',
                        'statistics': {
                            'viewCount': '1000',
                            'likeCount': '50',
                            'commentCount': '10'
                        }
                    },
                    {
                        'video_id': 'test_video_2', 
                        'title': 'Test Video 2',
                        'comment_count': '5',
                        'statistics': {
                            'viewCount': '2000',
                            'likeCount': '100',
                            'commentCount': '5'
                        }
                    }
                ]
            }
            
            # Mock result with comments added and comprehensive statistics
            mock_result = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'video_id': [
                    {
                        'video_id': 'test_video_1', 
                        'title': 'Test Video 1',
                        'comment_count': '10',
                        'statistics': {
                            'viewCount': '1000',
                            'likeCount': '50',
                            'commentCount': '10'
                        },
                        'comments': [
                            {
                                'comment_id': 'comment1', 
                                'comment_text': 'Great video!',
                                'comment_author': 'User1',
                                'comment_published_at': '2023-01-01T00:00:00Z',
                                'like_count': 5
                            },
                            {
                                'comment_id': 'comment2', 
                                'comment_text': 'Nice content',
                                'comment_author': 'User2',
                                'comment_published_at': '2023-01-02T00:00:00Z',
                                'like_count': 2
                            }
                        ]
                    },
                    {
                        'video_id': 'test_video_2', 
                        'title': 'Test Video 2',
                        'comment_count': '5',
                        'statistics': {
                            'viewCount': '2000',
                            'likeCount': '100',
                            'commentCount': '5'
                        },
                        'comments': [
                            {
                                'comment_id': 'comment3', 
                                'comment_text': 'Interesting',
                                'comment_author': 'User3',
                                'comment_published_at': '2023-01-03T00:00:00Z',
                                'like_count': 3
                            }
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
            assert result['comment_stats']['videos_with_comments'] == 2
            
            # Verify video 1 comments
            assert len(result['video_id'][0]['comments']) == 2
            assert result['video_id'][0]['comments'][0]['comment_id'] == 'comment1'
            assert result['video_id'][0]['comments'][0]['comment_author'] == 'User1'
            assert 'like_count' in result['video_id'][0]['comments'][0]
            
            # Verify video 2 comments
            assert len(result['video_id'][1]['comments']) == 1
            assert result['video_id'][1]['comments'][0]['comment_id'] == 'comment3'
            
            # Verify statistics are maintained
            assert result['video_id'][0]['comment_count'] == '10'
            assert result['video_id'][0]['statistics']['commentCount'] == '10'
            
            # Verify the client method was called with correct parameters
            # Note: We need to check for page_token parameter which was added for pagination support
            mock_comment_client.get_video_comments.assert_called_once_with(channel_info, 5, page_token=None)


if __name__ == '__main__':
    pytest.main()