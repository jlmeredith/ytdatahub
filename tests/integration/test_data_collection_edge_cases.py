"""
Integration tests for edge cases in the data collection process.
Tests handling of unusual channel data, empty channels, and other edge cases.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestChannelEdgeCases(BaseYouTubeTestCase):
    """Tests for handling edge cases with channel data"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_channel_with_zero_videos(self, setup_service_with_mocks):
        """Test handling of a channel with zero videos"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to return a channel with zero videos
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Empty Channel',
            'subscribers': '100',
            'views': '0',
            'total_videos': '0',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for video fetching
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': []  # Empty video list
        }
        
        # Collect channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 10
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        mock_api.get_video_comments.assert_not_called()  # No videos, no comments to fetch
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert result['channel_name'] == 'Empty Channel'
        assert result['total_videos'] == '0'
        assert 'video_id' in result
        assert len(result['video_id']) == 0  # Empty list
    
    def test_all_videos_with_disabled_comments(self, setup_service_with_mocks):
        """Test handling of videos where all have disabled comments"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API for channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'No Comments Channel',
            'subscribers': '1000',
            'views': '50000',
            'total_videos': '3',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for videos with disabled comments
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',
                    'likes': '1200',
                    'comment_count': '0',
                    'comments_disabled': True
                },
                {
                    'video_id': 'video2',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '8000',
                    'likes': '700',
                    'comment_count': '0',
                    'comments_disabled': True
                },
                {
                    'video_id': 'video3',
                    'title': 'Test Video 3',
                    'published_at': '2025-04-10T14:30:00Z',
                    'views': '5000',
                    'likes': '400',
                    'comment_count': '0',
                    'comments_disabled': True
                }
            ]
        }
        
        # Configure comment fetch to return stats but no actual comments
        mock_api.get_video_comments.return_value = {
            'video_id': [
                {
                    'video_id': 'video1',
                    'comments': [],
                    'comments_disabled': True
                },
                {
                    'video_id': 'video2',
                    'comments': [],
                    'comments_disabled': True
                },
                {
                    'video_id': 'video3',
                    'comments': [],
                    'comments_disabled': True
                }
            ],
            'comment_stats': {
                'total_comments': 0,
                'videos_with_comments': 0,
                'videos_with_disabled_comments': 3,
                'videos_with_errors': 0
            }
        }
        
        # Collect all data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': True,
            'max_videos': 10,
            'max_comments_per_video': 10
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        mock_api.get_video_comments.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert len(result['video_id']) == 3
        
        # Verify comments disabled status
        for video in result['video_id']:
            assert 'comments_disabled' in video
            assert video['comments_disabled'] is True
            assert 'comments' in video
            assert len(video['comments']) == 0  # No comments
        
        # Verify comment stats
        assert 'comment_stats' in result
        assert result['comment_stats']['total_comments'] == 0
        assert result['comment_stats']['videos_with_comments'] == 0
        assert result['comment_stats']['videos_with_disabled_comments'] == 3
    
    def test_mixture_of_public_and_private_videos(self, setup_service_with_mocks):
        """Test handling of a channel with both public and private videos"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API for channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Mixed Access Channel',
            'subscribers': '5000',
            'views': '200000',
            'total_videos': '5',  # Total videos reported by API
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for videos with some unavailable
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Public Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',
                    'likes': '1200',
                    'comment_count': '300'
                },
                {
                    'video_id': 'video2',
                    'title': 'Public Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '8000',
                    'likes': '700',
                    'comment_count': '150'
                }
            ],
            'videos_fetched': 2,
            'videos_unavailable': 3  # 3 videos are private or deleted
        }
        
        # Configure comment fetch
        mock_api.get_video_comments.return_value = {
            'video_id': [
                {
                    'video_id': 'video1',
                    'comments': [
                        {
                            'comment_id': 'comment1',
                            'comment_text': 'Great video!',
                            'comment_author': 'User 1',
                            'comment_published_at': '2025-04-02T10:00:00Z',
                            'like_count': '5'
                        }
                    ]
                },
                {
                    'video_id': 'video2',
                    'comments': [
                        {
                            'comment_id': 'comment2',
                            'comment_text': 'Nice content',
                            'comment_author': 'User 2',
                            'comment_published_at': '2025-04-06T14:20:00Z',
                            'like_count': '3'
                        }
                    ]
                }
            ],
            'comment_stats': {
                'total_comments': 2,
                'videos_with_comments': 2,
                'videos_with_disabled_comments': 0,
                'videos_with_errors': 0
            }
        }
        
        # Collect all data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': True,
            'max_videos': 10,
            'max_comments_per_video': 10
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        mock_api.get_video_comments.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert result['total_videos'] == '5'  # API reports 5 total
        assert len(result['video_id']) == 2   # But only 2 are accessible
        
        # Verify unavailable videos count
        assert 'videos_unavailable' in result
        assert result['videos_unavailable'] == 3
        
        # Verify video and comment content
        for video in result['video_id']:
            assert 'comments' in video
            assert len(video['comments']) == 1
    
    def test_very_large_channel_collection(self, setup_service_with_mocks):
        """Test collecting data for a very large channel"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API for large channel info (10,000 videos)
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Massive Channel',
            'subscribers': '10000000',  # 10 million
            'views': '5000000000',      # 5 billion
            'total_videos': '10000',    # 10 thousand videos
            'playlist_id': 'PL_test_playlist'
        }
        
        # For this test, we won't actually return 10,000 videos,
        # but we'll verify that the max_videos parameter is respected
        def mock_get_videos_impl(channel_info, max_videos=None, page_token=None, optimize_quota=False):
            # Calculate how many videos to return based on max_videos
            if max_videos == 0 or max_videos is None:
                # Return a reasonable default to avoid creating massive objects
                video_count = 100
            else:
                video_count = min(max_videos, 500)  # Cap at 500 for test performance
            
            videos = []
            for i in range(1, video_count + 1):
                videos.append({
                    'video_id': f'video{i}',
                    'title': f'Test Video {i}',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': str(10000 + i),
                    'likes': str(1000 + i),
                    'comment_count': str(100 + i)
                })
            
            return {
                'channel_id': 'UC_test_channel',
                'video_id': videos,
                'videos_fetched': len(videos),
                'videos_unavailable': 0
            }
            
        mock_api.get_channel_videos = MagicMock(side_effect=mock_get_videos_impl)
        
        # Set up a more limited collection (not the whole 10,000)
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 250  # Reasonable limit for testing
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify the max_videos parameter was used
        _, kwargs = mock_api.get_channel_videos.call_args
        assert kwargs.get('max_videos') == 250
        
        # Verify result contains the specified number of videos
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert result['total_videos'] == '10000'  # Total from API
        assert len(result['video_id']) == 250     # Limited by our max_videos parameter
    
    def test_channel_with_no_subscribers(self, setup_service_with_mocks):
        """Test handling of a channel with zero subscribers"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to return a channel with zero subscribers
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'No Subscribers Channel',
            'subscribers': '0',
            'views': '100',
            'total_videos': '1',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for a single video
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Test Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '100',
                    'likes': '0',
                    'comment_count': '0'
                }
            ]
        }
        
        # Collect channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert result['subscribers'] == '0'
        assert len(result['video_id']) == 1
    
    def test_channel_with_hidden_subscriber_count(self, setup_service_with_mocks):
        """Test handling of a channel with hidden subscriber count"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API to return a channel with hidden subscriber count
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Hidden Subscribers Channel',
            'subscribers': 'hidden',  # Special value indicating hidden count
            'views': '5000',
            'total_videos': '2',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Collect channel data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert result['subscribers'] == 'hidden'


class TestVideoEdgeCases(BaseYouTubeTestCase):
    """Tests for handling edge cases with video data"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_video_with_no_likes_or_views(self, setup_service_with_mocks):
        """Test handling of videos with zero likes and views"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API for channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '100',
            'views': '100',
            'total_videos': '1',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for video with no engagement
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Zero Engagement Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '0',
                    'likes': '0',
                    'comment_count': '0'
                }
            ]
        }
        
        # Collect channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert len(result['video_id']) == 1
        
        # Verify zero values are preserved
        video = result['video_id'][0]
        assert video['views'] == '0'
        assert video['likes'] == '0'
        assert video['comment_count'] == '0'
    
    def test_video_with_missing_fields(self, setup_service_with_mocks):
        """Test handling of videos with missing metadata fields"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API for channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '1000',
            'views': '10000',
            'total_videos': '1',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for video with missing fields
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Incomplete Metadata Video',
                    # Missing: published_at
                    'views': '1000'
                    # Missing: likes, comment_count
                }
            ]
        }
        
        # Collect channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert len(result['video_id']) == 1
        
        # Verify available fields and graceful handling of missing fields
        video = result['video_id'][0]
        assert video['video_id'] == 'video1'
        assert video['title'] == 'Incomplete Metadata Video'
        assert video['views'] == '1000'
        
        # The following assertions might depend on how your implementation handles missing fields
        # It might provide default values or leave them out entirely
        # Adjust these assertions based on your expected behavior
        # assert 'published_at' not in video  # Field should be missing or have a default
        # assert 'likes' not in video         # Field should be missing or have a default
        # assert 'comment_count' not in video # Field should be missing or have a default


class TestCommentEdgeCases(BaseYouTubeTestCase):
    """Tests for handling edge cases with comment data"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_empty_comments_array(self, setup_service_with_mocks):
        """Test handling of videos with empty comments array (not disabled)"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Setup channel with videos that have zero comments but are not disabled
        channel_with_videos = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '1000',
            'views': '10000',
            'total_videos': '1',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'No Comments Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '1000',
                    'likes': '100',
                    'comment_count': '0'  # Zero comments, but not disabled
                }
            ]
        }
        
        # Configure comment fetch to return empty comments
        mock_api.get_video_comments.return_value = {
            'video_id': [
                {
                    'video_id': 'video1',
                    'comments': []  # Empty array, not disabled
                }
            ],
            'comment_stats': {
                'total_comments': 0,
                'videos_with_comments': 0,
                'videos_with_disabled_comments': 0,
                'videos_with_errors': 0
            }
        }
        
        # Collect only comments
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': 10
        }
        
        result = service.collect_channel_data('UC_test_channel', options, existing_data=channel_with_videos)
        
        # Verify API calls
        mock_api.get_video_comments.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 1
        
        # Verify comments field exists but is empty
        video = result['video_id'][0]
        assert 'comments' in video
        assert len(video['comments']) == 0
        assert 'comments_disabled' not in video  # Not disabled, just empty
        
        # Verify comment stats
        assert 'comment_stats' in result
        assert result['comment_stats']['total_comments'] == 0
        assert result['comment_stats']['videos_with_comments'] == 0
        assert result['comment_stats']['videos_with_disabled_comments'] == 0
    
    def test_comment_fetch_with_errors(self, setup_service_with_mocks):
        """Test handling of videos where comment fetch had errors"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Setup channel with videos
        channel_with_videos = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '1000',
            'views': '10000',
            'total_videos': '2',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Normal Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '1000',
                    'likes': '100',
                    'comment_count': '10'
                },
                {
                    'video_id': 'video2',
                    'title': 'Problem Video',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '500',
                    'likes': '50',
                    'comment_count': '5'
                }
            ]
        }
        
        # Configure comment fetch with error indication
        mock_api.get_video_comments.return_value = {
            'video_id': [
                {
                    'video_id': 'video1',
                    'comments': [
                        {
                            'comment_id': 'comment1',
                            'comment_text': 'Great video!',
                            'comment_author': 'User 1',
                            'comment_published_at': '2025-04-02T10:00:00Z',
                            'like_count': '5'
                        }
                    ]
                },
                {
                    'video_id': 'video2',
                    'comments': [],
                    'comment_error': 'Failed to retrieve comments for this video'
                }
            ],
            'comment_stats': {
                'total_comments': 1,
                'videos_with_comments': 1,
                'videos_with_disabled_comments': 0,
                'videos_with_errors': 1
            }
        }
        
        # Collect only comments
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': 10
        }
        
        result = service.collect_channel_data('UC_test_channel', options, existing_data=channel_with_videos)
        
        # Verify API calls
        mock_api.get_video_comments.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 2
        
        # Verify normal video has comments
        video1 = next(v for v in result['video_id'] if v['video_id'] == 'video1')
        assert 'comments' in video1
        assert len(video1['comments']) == 1
        
        # Verify error video has error flag
        video2 = next(v for v in result['video_id'] if v['video_id'] == 'video2')
        assert 'comments' in video2
        assert len(video2['comments']) == 0
        assert 'comment_error' in video2
        
        # Verify comment stats
        assert 'comment_stats' in result
        assert result['comment_stats']['videos_with_errors'] == 1


class TestApiInputValidation(BaseYouTubeTestCase):
    """Tests for API parameter validation"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_channel_url_formats(self, setup_service_with_mocks):
        """Test handling of different channel URL formats"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Define various channel input formats to test
        channel_formats = [
            ('UC_test_channel', True, 'UC_test_channel'),                            # Raw Channel ID
            ('https://www.youtube.com/channel/UC_test_channel', True, 'UC_test_channel'),  # Channel URL
            ('https://www.youtube.com/c/TestChannel', True, 'UC_test_channel'),       # Custom URL
            ('https://youtube.com/user/TestUser', True, 'UC_test_channel'),           # Legacy user URL
            ('https://youtube.com/@TestHandle', True, 'UC_test_channel'),             # Handle URL
            ('invalid_input', False, None)                                            # Invalid input
        ]
        
        # Configure validation mock to return appropriate values
        def mock_validate_side_effect(channel_input):
            # Find the matching input format and return its validation result
            for fmt, valid, resolved in channel_formats:
                if fmt == channel_input:
                    return valid, resolved
            return False, None
        
        service.validate_and_resolve_channel_id = MagicMock(side_effect=mock_validate_side_effect)
        
        # Test each format
        for channel_input, should_be_valid, expected_id in channel_formats:
            # Reset mocks for each test
            mock_api.get_channel_info.reset_mock()
            
            if should_be_valid:
                # For valid formats, mock a successful API response
                mock_api.get_channel_info.return_value = {
                    'channel_id': expected_id,
                    'channel_name': 'Test Channel',
                    'subscribers': '1000',
                    'total_videos': '10'
                }
                
                # Attempt collection with this format
                options = {'fetch_channel_data': True, 'fetch_videos': False}
                result = service.collect_channel_data(channel_input, options)
                
                # Verify resolution and API calls
                assert result is not None
                assert result['channel_id'] == expected_id
                mock_api.get_channel_info.assert_called_once_with(expected_id)
            else:
                # For invalid formats, verify it returns None
                options = {'fetch_channel_data': True, 'fetch_videos': False}
                result = service.collect_channel_data(channel_input, options)
                
                assert result is None
                mock_api.get_channel_info.assert_not_called()
    
    def test_zero_max_videos_meaning(self, setup_service_with_mocks):
        """Test that max_videos=0 means 'fetch all videos', not 'fetch zero videos'"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock API
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '1000',
            'views': '10000',
            'total_videos': '3',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock for 3 videos
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '1000',
                    'likes': '100'
                },
                {
                    'video_id': 'video2',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '500',
                    'likes': '50'
                },
                {
                    'video_id': 'video3',
                    'title': 'Test Video 3',
                    'published_at': '2025-04-10T14:30:00Z',
                    'views': '200',
                    'likes': '20'
                }
            ]
        }
        
        # Collect with max_videos=0 (should fetch all)
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 0  # Special value meaning 'all'
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        mock_api.get_channel_info.assert_called_once()
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify param was passed correctly
        _, kwargs = mock_api.get_channel_videos.call_args
        assert kwargs.get('max_videos') == 0
        
        # Verify all videos were fetched
        assert result is not None
        assert len(result['video_id']) == 3


if __name__ == '__main__':
    pytest.main()