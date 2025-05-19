"""
Integration tests for pagination and batch processing.
Tests the system's ability to handle large collections requiring pagination.
"""
import pytest
from unittest.mock import MagicMock, patch, call
import copy
from src.services.youtube_service import YouTubeService

# Import the base test case
from tests.integration.test_data_collection_workflow import BaseYouTubeTestCase


class TestPaginationBehavior(BaseYouTubeTestCase):
    """Tests for paginated data collection handling"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_video_pagination(self, setup_service_with_mocks):
        """Test pagination when collecting videos for a large channel"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Configure mock channel response
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Large Test Channel',
            'subscribers': '1000000',  # 1M subscribers
            'views': '100000000',      # 100M views
            'total_videos': '500',     # 500 videos (requiring pagination)
            'playlist_id': 'PL_test_playlist'
        }
        
        # Create paginated video responses (simulating YouTube API pagination)
        page1_videos = self._create_video_batch(1, 50)  # Videos 1-50
        page2_videos = self._create_video_batch(51, 100)  # Videos 51-100
        page3_videos = self._create_video_batch(101, 150)  # Videos 101-150
        
        # Configure mock to return different pages on subsequent calls
        # Note: The implementation may vary depending on how your service processes pages
        mock_api.get_channel_videos = MagicMock()
        mock_api.get_channel_videos.side_effect = [
            # First call - returns page 1 with a nextPageToken
            {
                'channel_id': 'UC_test_channel',
                'video_id': page1_videos,
                'nextPageToken': 'page2_token'
            },
            # Second call - returns page 2 with a nextPageToken
            {
                'channel_id': 'UC_test_channel',
                'video_id': page2_videos,
                'nextPageToken': 'page3_token'
            },
            # Third call - returns page 3 with no nextPageToken (end of results)
            {
                'channel_id': 'UC_test_channel',
                'video_id': page3_videos,
                'nextPageToken': None
            }
        ]
        
        # Collect channel data with all videos (using max_videos=0)
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 150  # Fetch exactly 150 videos
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify API calls
        assert mock_api.get_channel_info.call_count == 1
        assert mock_api.get_channel_videos.call_count >= 1
        
        # Verify all pages of videos were collected and merged
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 150
        
        # Check for specific videos from different pages
        video_ids = [v['video_id'] for v in result['video_id']]
        assert 'video1' in video_ids  # From page 1
        assert 'video51' in video_ids  # From page 2
        assert 'video150' in video_ids  # From page 3
    
    def test_comment_pagination(self, setup_service_with_mocks):
        """Test pagination when collecting comments for videos with many comments"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Setup channel data with a single video that has many comments
        channel_with_video = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'video_id': [
                {
                    'video_id': 'video_with_many_comments',
                    'title': 'Popular Video',
                    'comment_count': '500'  # 500 comments requires pagination
                }
            ]
        }
        
        # Create comment batches for testing
        page1_comments = self._create_comment_batch('video_with_many_comments', 1, 100)
        page2_comments = self._create_comment_batch('video_with_many_comments', 101, 200)
        page3_comments = self._create_comment_batch('video_with_many_comments', 201, 300)
        
        # Create a properly behaving mock for pagination
        # Use a counter to track the number of calls and avoid infinite recursion
        call_count = [0]
        
        def mock_comments_api(channel_info, max_comments_per_video=None, page_token=None):
            """Mock implementation that properly handles pagination with call tracking"""
            call_count[0] += 1
            print(f"[DEBUG TEST] mock_comments_api call #{call_count[0]} with page_token={page_token}")
            
            # If we've made too many calls, break the potential infinite loop
            if call_count[0] > 5:
                print("[DEBUG TEST] Too many calls to mock_comments_api, breaking potential infinite loop")
                return {
                    'video_id': [],
                    'nextPageToken': None,
                    'comment_stats': {'total_comments': 0, 'videos_with_comments': 0}
                }
            
            # First call (no page token) returns first page
            if page_token is None:
                return {
                    'video_id': [
                        {
                            'video_id': 'video_with_many_comments',
                            'comments': page1_comments,
                            'nextPageToken': 'page2_token'
                        }
                    ],
                    'nextPageToken': 'page2_token',
                    'comment_stats': {'total_comments': 100, 'videos_with_comments': 1, 'has_more_comments': True}
                }
            # Second page
            elif page_token == 'page2_token':
                return {
                    'video_id': [
                        {
                            'video_id': 'video_with_many_comments',
                            'comments': page2_comments,
                            'nextPageToken': 'page3_token'
                        }
                    ],
                    'nextPageToken': 'page3_token',
                    'comment_stats': {'total_comments': 100, 'videos_with_comments': 1, 'has_more_comments': True}
                }
            # Final page
            elif page_token == 'page3_token':
                return {
                    'video_id': [
                        {
                            'video_id': 'video_with_many_comments',
                            'comments': page3_comments,
                            'nextPageToken': None
                        }
                    ],
                    'nextPageToken': None,
                    'comment_stats': {'total_comments': 100, 'videos_with_comments': 1, 'has_more_comments': False}
                }
            # Any other token (safety fallback)
            else:
                return {
                    'video_id': [],
                    'nextPageToken': None,
                    'comment_stats': {'total_comments': 0, 'videos_with_comments': 0}
                }
                
        # Use our simplified mock
        mock_api.get_video_comments = MagicMock(side_effect=mock_comments_api)
        
        # Collect comments with pagination
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': 300  # Fetch all 300 comments
        }
        
        print("[DEBUG TEST] Running test_comment_pagination with simplified mock")
        
        # Execute the collection
        result = service.collect_channel_data('UC_test_channel', options, existing_data=channel_with_video)
        
        # Verify the results
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 1
        
        video = result['video_id'][0]
        assert 'comments' in video
        
        # Verify we got all comments from all "pages"
        comments = video['comments']
        assert len(comments) == 300  # 300 total comments (100 per page × 3 pages)
        
        # Verify comments from different pages are present
        comment_ids = [comment['comment_id'] for comment in comments]
        
        # Check for comments from each "page"
        assert "comment1" in comment_ids  # From page 1
        assert "comment101" in comment_ids  # From page 2
        assert "comment201" in comment_ids  # From page 3
        
        print("[DEBUG TEST] Comment pagination test completed successfully")
        
        # Check for specific comment IDs from different pages
        expected_ids = ['comment1', 'comment101', 'comment200', 'comment300'] 
        for expected_id in expected_ids:
            found = expected_id in [c['comment_id'] for c in video['comments']]
            print(f"[DEBUG TEST] Expected comment {expected_id}: {'FOUND' if found else 'MISSING'}")
        
        # Verify API calls
        assert mock_api.get_video_comments.call_count >= 1
    
    def test_fetch_all_videos_unlimited(self, setup_service_with_mocks):
        """Test fetching all videos without a limit (max_videos=0)"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Setup a channel with 250 videos to ensure pagination is required
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '50000',
            'views': '10000000',
            'total_videos': '250',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Create paginated video responses
        page1_videos = self._create_video_batch(1, 50)
        page2_videos = self._create_video_batch(51, 100)
        page3_videos = self._create_video_batch(101, 150)
        page4_videos = self._create_video_batch(151, 200)
        page5_videos = self._create_video_batch(201, 250)
        
        # Configure mock for pagination
        mock_api.get_channel_videos = MagicMock()
        mock_api.get_channel_videos.side_effect = [
            {'channel_id': 'UC_test_channel', 'video_id': page1_videos, 'nextPageToken': 'page2_token'},
            {'channel_id': 'UC_test_channel', 'video_id': page2_videos, 'nextPageToken': 'page3_token'},
            {'channel_id': 'UC_test_channel', 'video_id': page3_videos, 'nextPageToken': 'page4_token'},
            {'channel_id': 'UC_test_channel', 'video_id': page4_videos, 'nextPageToken': 'page5_token'},
            {'channel_id': 'UC_test_channel', 'video_id': page5_videos, 'nextPageToken': None}
        ]
        
        # Request all videos (max_videos=0)
        options = {
            'fetch_channel_data': False,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 0  # 0 means fetch all available videos
        }
        
        # Create a minimal channel_data to start with
        initial_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'playlist_id': 'PL_test_playlist'
        }
        
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_data)
        
        # Verify all videos were collected
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 250
        
        # Check for videos from each page
        video_ids = [v['video_id'] for v in result['video_id']]
        assert 'video1' in video_ids  # First page
        assert 'video100' in video_ids  # Middle page
        assert 'video250' in video_ids  # Last page
    
    def test_next_page_token_handling(self, setup_service_with_mocks):
        """Test proper handling of nextPageToken for paginated requests"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Mock channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'total_videos': '100',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Setup for checking page token handling
        page1_videos = self._create_video_batch(1, 30)
        page2_videos = self._create_video_batch(31, 60)
        
        # Track API calls to verify page tokens are passed correctly
        api_calls = []
        
        def mock_get_videos_with_token(channel_info, max_videos=None, page_token=None, optimize_quota=False):
            # Record the call parameters
            api_calls.append({
                'max_videos': max_videos,
                'page_token': page_token
            })
            
            # Return appropriate page based on token
            if page_token is None:
                return {
                    'channel_id': 'UC_test_channel',
                    'video_id': page1_videos,
                    'nextPageToken': 'next_page_token'
                }
            elif page_token == 'next_page_token':
                return {
                    'channel_id': 'UC_test_channel',
                    'video_id': page2_videos,
                    'nextPageToken': None  # No more pages
                }
        
        # Use a side effect to track calls and return appropriate responses
        mock_api.get_channel_videos.side_effect = mock_get_videos_with_token
        
        # Fetch videos with enough max_videos to require pagination
        options = {
            'fetch_channel_data': False,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 60  # Will require 2 pages
        }
        
        initial_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'playlist_id': 'PL_test_playlist'
        }
        
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_data)
        
        # Verify result contains videos from both pages
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 60
        
        # Verify page token was properly passed in the second call
        assert len(api_calls) == 2
        assert api_calls[0]['page_token'] is None  # First call has no page token
        assert api_calls[1]['page_token'] == 'next_page_token'  # Second call uses token from first response
    
    def test_multi_page_error_recovery(self, setup_service_with_mocks):
        """Test recovery from errors during multi-page data collection"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Mock channel info
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'total_videos': '150',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Create video batches for multiple pages
        page1_videos = self._create_video_batch(1, 50)
        page2_videos = self._create_video_batch(51, 100)
        page3_videos = self._create_video_batch(101, 150)
        
        # Create a connection error to simulate network issues
        connection_error = ConnectionError("Connection reset")
        
        # Mock API to fail on the second page, then succeed when retried
        mock_api.get_channel_videos.side_effect = [
            # First call - returns page 1 successfully
            {
                'channel_id': 'UC_test_channel',
                'video_id': page1_videos,
                'nextPageToken': 'page2_token'
            },
            # Second call - connection error
            connection_error,
            # Third call (retry for page 2) - succeeds
            {
                'channel_id': 'UC_test_channel',
                'video_id': page2_videos,
                'nextPageToken': 'page3_token'
            },
            # Fourth call - returns page 3 successfully
            {
                'channel_id': 'UC_test_channel',
                'video_id': page3_videos,
                'nextPageToken': None
            }
        ]
        
        # Patch sleep to avoid delays in tests
        with patch('time.sleep'):
            # Fetch all videos
            options = {
                'fetch_channel_data': False,
                'fetch_videos': True,
                'fetch_comments': False,
                'max_videos': 150,
                'retry_attempts': 1  # Add retry attempts to handle the connection error
            }
            
            initial_data = {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'playlist_id': 'PL_test_playlist'
            }
            
            result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_data)
        
        # Verify all pages were collected despite the error
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 150
        
        # Check for videos from all pages to ensure complete collection
        video_ids = [v['video_id'] for v in result['video_id']]
        assert 'video1' in video_ids    # From page 1
        assert 'video75' in video_ids   # From page 2
        assert 'video150' in video_ids  # From page 3
    
    def _create_video_batch(self, start_index, end_index):
        """Helper to create a batch of test videos"""
        videos = []
        for i in range(start_index, end_index + 1):
            videos.append({
                'video_id': f'video{i}',
                'title': f'Test Video {i}',
                'published_at': '2025-04-01T12:00:00Z',
                'views': str(10000 - i * 10),  # Decreasing views for newer videos
                'likes': str(1000 - i * 5),
                'comment_count': str(100 - i)
            })
        return videos
    
    def _create_comment_batch(self, video_id, start_index, end_index):
        """Helper to create a batch of test comments for a video"""
        comments = []
        for i in range(start_index, end_index + 1):
            comments.append({
                'comment_id': f'comment{i}',
                'comment_text': f'Test comment {i}',
                'comment_author': f'User {i}',
                'comment_published_at': '2025-04-02T10:00:00Z',
                'like_count': str(50 - i % 50)  # Some variation in likes
            })
        return comments


class TestBatchProcessing(BaseYouTubeTestCase):
    """Tests for batch processing of YouTube data"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
        
    def test_video_id_batching(self, setup_service_with_mocks):
        """Test batching of video ID requests for efficient API usage"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Mock channel info with existing videos
        channel_with_videos = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'video_id': [
                {'video_id': 'video1', 'title': 'Video 1'},
                {'video_id': 'video2', 'title': 'Video 2'},
                {'video_id': 'video3', 'title': 'Video 3'},
                {'video_id': 'video4', 'title': 'Video 4'},
                {'video_id': 'video5', 'title': 'Video 5'},
                {'video_id': 'video6', 'title': 'Video 6'},
                {'video_id': 'video7', 'title': 'Video 7'},
                {'video_id': 'video8', 'title': 'Video 8'},
                {'video_id': 'video9', 'title': 'Video 9'},
                {'video_id': 'video10', 'title': 'Video 10'},
                {'video_id': 'video11', 'title': 'Video 11'},
                # ... more videos ...
                {'video_id': 'video50', 'title': 'Video 50'},
            ]
        }
        
        # Add more videos to make 50+ for testing batch API calls
        for i in range(51, 60):
            channel_with_videos['video_id'].append({
                'video_id': f'video{i}', 
                'title': f'Video {i}'
            })
        
        # Track batch API calls
        batch_api_calls = []
        
        def mock_get_video_details(video_ids):
            """Mock video details API that records what IDs were requested together"""
            batch_api_calls.append(video_ids)
            
            # Generate response with details for all requested videos
            return {
                'items': [
                    {
                        'id': video_id,
                        'snippet': {'title': f'Video {video_id.replace("video", "")}'},
                        'statistics': {'viewCount': '1000', 'likeCount': '100', 'commentCount': '10'}
                    }
                    for video_id in video_ids
                ]
            }
        
        # Replace the relevant API method with our mock
        mock_api.get_video_details_batch = MagicMock(side_effect=mock_get_video_details)
        
        # Trigger a refresh of video details
        options = {
            'fetch_channel_data': False,
            'fetch_videos': True,
            'refresh_video_details': True,  # Special flag to trigger batch API for existing videos
            'fetch_comments': False
        }
        
        result = service.collect_channel_data('UC_test_channel', options, existing_data=channel_with_videos)
        
        # Verify batch API was called efficiently
        assert len(batch_api_calls) > 0
        
        # Verify each batch doesn't exceed max allowed IDs per request (typically 50)
        for batch in batch_api_calls:
            assert len(batch) <= 50
        
        # Verify all videos were processed
        assert result is not None
        assert len(result['video_id']) == len(channel_with_videos['video_id'])
    
    def test_comment_batching_across_videos(self, setup_service_with_mocks):
        """Test batching of comment requests for multiple videos"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Setup channel with multiple videos
        channel_with_videos = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'video_id': [
                {
                    'video_id': 'video1',
                    'title': 'Video 1',
                    'comment_count': '50'
                },
                {
                    'video_id': 'video2',
                    'title': 'Video 2',
                    'comment_count': '30'
                },
                {
                    'video_id': 'video3',
                    'title': 'Video 3',
                    'comment_count': '20'
                }
            ]
        }
        
        # Track comment API calls
        comment_api_calls = []
        
        def mock_get_comments(videos, max_comments_per_video=None):
            """Mock comment API recording which videos were requested together"""
            # Extract video IDs from the request
            if isinstance(videos, list):
                video_ids = [v['video_id'] for v in videos if 'video_id' in v]
            else:
                # Handle possible alternative formats depending on your implementation
                video_ids = [v['video_id'] for v in videos.get('video_id', [])]
                
            comment_api_calls.append({
                'video_ids': video_ids,
                'max_comments': max_comments_per_video
            })
            
            # Generate response with comments for all videos
            response_videos = []
            for video_id in video_ids:
                # Number of comments (different for each video)
                if video_id == 'video1':
                    num_comments = 50
                elif video_id == 'video2':
                    num_comments = 30
                else:  # video3
                    num_comments = 20
                
                # Generate comments
                comments = []
                for i in range(1, min(num_comments + 1, max_comments_per_video + 1) if max_comments_per_video else num_comments + 1):
                    comments.append({
                        'comment_id': f'{video_id}_comment{i}',
                        'comment_text': f'Comment {i} on {video_id}',
                        'comment_author': f'User {i}'
                    })
                
                # Add to response
                response_videos.append({
                    'video_id': video_id,
                    'comments': comments
                })
            
            return {
                'video_id': response_videos,
                'comment_stats': {
                    'total_comments': sum(len(v['comments']) for v in response_videos),
                    'videos_with_comments': len(response_videos),
                    'videos_with_disabled_comments': 0,
                    'videos_with_errors': 0
                }
            }
        
        # Replace the API method with our mock
        mock_api.get_video_comments = MagicMock(side_effect=mock_get_comments)
        
        # Collect comments for all videos
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': 25  # Fetch up to 25 comments per video
        }
        
        result = service.collect_channel_data('UC_test_channel', options, existing_data=channel_with_videos)
        
        # Verify comment API was called
        assert len(comment_api_calls) > 0
        
        # Verify result contains comments for all videos
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 3
        
        # Check video 1 (should have 25 comments due to limit)
        video1 = next(v for v in result['video_id'] if v['video_id'] == 'video1')
        assert 'comments' in video1
        assert len(video1['comments']) == 25
        
        # Check video 2 (should have all 30 comments as it's within limit)
        video2 = next(v for v in result['video_id'] if v['video_id'] == 'video2')
        assert 'comments' in video2
        # This test depends on your implementation - it would have all comments if your service
        # batches efficiently, or only 25 if it applies the limit per video
        expected_comment_count = 25  # Assuming the limit applies per video
        assert len(video2['comments']) == expected_comment_count
        
        # Verify each comment has the correct properties
        sample_comment = video1['comments'][0]
        assert 'comment_id' in sample_comment
        assert 'comment_text' in sample_comment
        assert 'comment_author' in sample_comment
    
    def test_quota_efficient_batch_processing(self, setup_service_with_mocks):
        """Test quota-efficient batch processing for large collections"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Setup mock channel with many videos
        channel_info = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Large Test Channel',
            'subscribers': '1000000',
            'views': '100000000',
            'total_videos': '500',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Create a large batch of videos
        all_videos = []
        for i in range(1, 101):  # 100 videos
            all_videos.append({
                'video_id': f'video{i}',
                'title': f'Test Video {i}',
                'published_at': '2025-04-01T12:00:00Z',
                'views': '10000',
                'likes': '1000',
                'comment_count': '100'
            })
        
        # Configure get_channel_videos to return all videos at once
        mock_api.get_channel_videos.return_value = {
            'channel_id': 'UC_test_channel',
            'video_id': all_videos
        }
        
        # Configure get_channel_info to return the channel info
        mock_api.get_channel_info.return_value = channel_info
        
        # Track quota consumption
        quota_usage = {'value': 0}
        
        # Create a mock for API quota tracking
        def mock_increment_quota(units):
            quota_usage['value'] += units
        
        # Replace the quota tracking method if your service has one
        if hasattr(mock_api, 'increment_quota_usage'):
            original_increment = mock_api.increment_quota_usage
            mock_api.increment_quota_usage = MagicMock(side_effect=mock_increment_quota)
        
        # Collect channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'optimize_quota': True  # Flag to enable quota optimization if your service supports it
        }
        
        result = service.collect_channel_data('UC_test_channel', options)
        
        # Verify result contains all videos
        assert result is not None
        assert 'video_id' in result
        assert len(result['video_id']) == 100
        
        # Restore original method if we patched it
        if hasattr(mock_api, 'increment_quota_usage'):
            mock_api.increment_quota_usage = original_increment
            
            # If your service tracks quota, verify it was optimized
            # The exact quota values depend on your implementation
            expected_max_quota = 110  # Typical max for batched operations
            assert quota_usage['value'] <= expected_max_quota, f"Expected quota usage <= {expected_max_quota}, got {quota_usage['value']}"


if __name__ == '__main__':
    pytest.main(['-xvs', 'test_pagination_batch.py'])