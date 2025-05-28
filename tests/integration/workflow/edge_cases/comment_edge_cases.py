"""
Tests for handling edge cases with comment data.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


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

    def test_comment_cap_enforced(self, setup_service_with_mocks):
        """Test that max_comments_per_video is enforced as a hard cap."""
        service, mock_api, mock_db = setup_service_with_mocks
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
                    'title': 'Capped Comments Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '1000',
                    'likes': '100',
                    'comment_count': '10'
                }
            ]
        }
        # Simulate API returning 2 top-level, each with 2 replies
        mock_api.get_video_comments.return_value = {
            'video_id': [
                {
                    'video_id': 'video1',
                    'comments': [
                        {'comment_id': 'c1', 'comment_text': 'T1', 'comment_author': 'A', 'comment_published_at': '2025-04-02T10:00:00Z', 'like_count': '1'},
                        {'comment_id': 'r1', 'comment_text': '[REPLY] R1', 'comment_author': 'B', 'comment_published_at': '2025-04-02T11:00:00Z', 'like_count': '0', 'parent_id': 'c1'},
                        {'comment_id': 'r2', 'comment_text': '[REPLY] R2', 'comment_author': 'C', 'comment_published_at': '2025-04-02T12:00:00Z', 'like_count': '0', 'parent_id': 'c1'},
                        {'comment_id': 'c2', 'comment_text': 'T2', 'comment_author': 'D', 'comment_published_at': '2025-04-03T10:00:00Z', 'like_count': '2'},
                        {'comment_id': 'r3', 'comment_text': '[REPLY] R3', 'comment_author': 'E', 'comment_published_at': '2025-04-03T11:00:00Z', 'like_count': '0', 'parent_id': 'c2'},
                        {'comment_id': 'r4', 'comment_text': '[REPLY] R4', 'comment_author': 'F', 'comment_published_at': '2025-04-03T12:00:00Z', 'like_count': '0', 'parent_id': 'c2'}
                    ]
                }
            ],
            'comment_stats': {
                'total_comments': 6,
                'videos_with_comments': 1,
                'videos_with_disabled_comments': 0,
                'videos_with_errors': 0
            }
        }
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_top_level_comments': 2,
            'max_replies_per_comment': 2,
            'max_comments_per_video': 3
        }
        result = service.collect_channel_data('UC_test_channel', options, existing_data=channel_with_videos)
        video = result['video_id'][0]
        # Should only have 3 comments due to cap
        assert 'comments' in video
        assert len(video['comments']) == 3
