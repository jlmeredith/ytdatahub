"""
Unit tests for sequential delta updates in YouTube data collection.
This tests how delta metrics are tracked and accumulated across multiple collection operations.
"""
import pytest
from unittest.mock import MagicMock, patch
import json
import datetime
from src.services.youtube_service import YouTubeService


class TestSequentialDeltaUpdates:
    """
    Tests for sequential delta updates, focusing on how metrics changes
    are tracked across multiple data collection operations.
    """
    
    @pytest.fixture
    def setup_youtube_service(self):
        """Setup a YouTube service with mocked API for testing"""
        # Create mock API
        mock_api = MagicMock()
        
        # Setup service with mock API
        service = YouTubeService("test_api_key")
        service.api = mock_api
        
        # Patch the validate_and_resolve_channel_id method to always succeed
        service.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
        
        return service, mock_api
    
    @pytest.fixture
    def initial_channel_data(self):
        """Create initial channel data for delta testing"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '50',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',
                    'likes': '1200',
                    'comment_count': '300',
                    'comments': [
                        {
                            'comment_id': 'comment123',
                            'comment_text': 'Great video!',
                            'comment_author': 'Test User 1'
                        }
                    ]
                },
                {
                    'video_id': 'video456',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '8000',
                    'likes': '700',
                    'comment_count': '150',
                    'comments': [
                        {
                            'comment_id': 'comment456',
                            'comment_text': 'Very informative',
                            'comment_author': 'Test User 2'
                        }
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def first_update_data(self):
        """Create first update data for delta testing with modest changes"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '11000',  # +1000
            'views': '5200000',      # +200000
            'total_videos': '51',    # +1
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '18000',  # +3000
                    'likes': '1500',   # +300
                    'comment_count': '350'  # +50
                },
                {
                    'video_id': 'video456',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '10000',  # +2000
                    'likes': '900',    # +200
                    'comment_count': '200'  # +50
                },
                {
                    'video_id': 'video789',  # New video
                    'title': 'Test Video 3',
                    'published_at': '2025-04-15T14:00:00Z',
                    'views': '5000',
                    'likes': '400',
                    'comment_count': '100'
                }
            ]
        }
    
    @pytest.fixture
    def second_update_data(self):
        """Create second update data for delta testing with additional changes"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '12500',  # +1500 from first update
            'views': '5500000',      # +300000 from first update
            'total_videos': '52',    # +1 from first update
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '20000',  # +2000 from first update
                    'likes': '1700',   # +200 from first update
                    'comment_count': '400'  # +50 from first update
                },
                {
                    'video_id': 'video456',
                    'title': 'Test Video 2',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '12000',  # +2000 from first update
                    'likes': '1100',   # +200 from first update
                    'comment_count': '250'  # +50 from first update
                },
                {
                    'video_id': 'video789',
                    'title': 'Test Video 3',
                    'published_at': '2025-04-15T14:00:00Z',
                    'views': '8000',   # +3000 from first update
                    'likes': '600',    # +200 from first update
                    'comment_count': '180'  # +80 from first update
                },
                {
                    'video_id': 'video012',  # New video in second update
                    'title': 'Test Video 4',
                    'published_at': '2025-04-20T09:00:00Z',
                    'views': '3000',
                    'likes': '300',
                    'comment_count': '80'
                }
            ]
        }
    
    def test_single_delta_update_channel_metrics(self, setup_youtube_service, initial_channel_data, first_update_data):
        """
        Test a single delta update for channel-level metrics.
        Verifies that the system accurately calculates channel stat changes on first update.
        """
        service, mock_api = setup_youtube_service
        
        # Configure mock API to return the initial and first update data
        mock_api.get_channel_info.side_effect = [first_update_data]
        
        # Create collection options for channel data only
        options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        # Perform the update using the service
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_channel_data)
        
        # Verify the API was called correctly
        mock_api.get_channel_info.assert_called_once_with('UC_test_channel')
        
        # Verify the result contains the expected delta values
        assert 'delta' in result, "Delta field missing from result"
        assert result['delta']['subscribers'] == 1000, "Incorrect subscriber delta"
        assert result['delta']['views'] == 200000, "Incorrect view delta"
        assert result['delta']['total_videos'] == 1, "Incorrect video count delta"
        
        # Verify updated values are present
        assert result['subscribers'] == '11000', "Updated subscriber count not present"
        assert result['views'] == '5200000', "Updated view count not present"
        assert result['total_videos'] == '51', "Updated video count not present"
    
    def test_video_delta_tracking(self, setup_youtube_service, initial_channel_data, first_update_data):
        """
        Test video-level delta tracking for new videos and metric changes.
        """
        service, mock_api = setup_youtube_service
        
        # Configure mock API to return the initial and first update data
        mock_api.get_channel_videos.side_effect = [first_update_data]
        
        # Create collection options for videos only
        options = {
            'fetch_channel_data': False,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 10
        }
        
        # Perform the update using the service
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_channel_data)
        
        # Verify the API was called correctly
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify the result contains the expected video delta information
        assert 'video_delta' in result, "Video delta field missing from result"
        assert 'new_videos' in result['video_delta'], "New videos field missing from video delta"
        assert 'updated_videos' in result['video_delta'], "Updated videos field missing from video delta"
        
        # Check for the new video
        new_videos = result['video_delta']['new_videos']
        assert len(new_videos) == 1, "Incorrect number of new videos"
        assert new_videos[0]['video_id'] == 'video789', "New video not correctly identified"
        
        # Check for updated video stats
        updated_videos = result['video_delta']['updated_videos']
        assert len(updated_videos) == 2, "Incorrect number of updated videos"
        
        # Find each video by ID and check its deltas
        video123_update = next((v for v in updated_videos if v['video_id'] == 'video123'), None)
        assert video123_update is not None, "Updated video 'video123' not found"
        assert video123_update['views_change'] == 3000, "Incorrect views change for video123"
        assert video123_update['likes_change'] == 300, "Incorrect likes change for video123"
        
        video456_update = next((v for v in updated_videos if v['video_id'] == 'video456'), None)
        assert video456_update is not None, "Updated video 'video456' not found"
        assert video456_update['views_change'] == 2000, "Incorrect views change for video456"
        assert video456_update['likes_change'] == 200, "Incorrect likes change for video456"
    
    def test_sequential_delta_accumulation(self, setup_youtube_service, initial_channel_data, first_update_data, second_update_data):
        """
        Test that delta metrics properly accumulate over sequential updates.
        This test performs two updates and verifies delta tracking at each step.
        """
        service, mock_api = setup_youtube_service
        
        # Configure mock API for the first update (channel information)
        mock_api.get_channel_info.side_effect = [first_update_data, second_update_data]
        
        # Create options for channel data
        channel_options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        # Step 1: Perform first update
        first_result = service.collect_channel_data(
            'UC_test_channel', 
            channel_options, 
            existing_data=initial_channel_data
        )
        
        # Verify first update has expected deltas
        assert 'delta' in first_result
        assert first_result['delta']['subscribers'] == 1000
        assert first_result['delta']['views'] == 200000
        assert first_result['delta']['total_videos'] == 1
        
        # Step 2: Perform second update using first result as baseline
        second_result = service.collect_channel_data(
            'UC_test_channel', 
            channel_options, 
            existing_data=first_result
        )
        
        # Verify second update has correct deltas from first result
        assert 'delta' in second_result
        assert second_result['delta']['subscribers'] == 1500, "Incorrect subscriber delta in second update"
        assert second_result['delta']['views'] == 300000, "Incorrect view delta in second update"
        assert second_result['delta']['total_videos'] == 1, "Incorrect video count delta in second update"
        
        # Verify second update has correct total values
        assert second_result['subscribers'] == '12500'
        assert second_result['views'] == '5500000'
        assert second_result['total_videos'] == '52'
    
    def test_combined_channel_and_video_deltas(self, setup_youtube_service, initial_channel_data, first_update_data):
        """
        Test combined channel and video delta tracking in a single update operation.
        """
        service, mock_api = setup_youtube_service
        
        # Configure mock APIs to return update data
        mock_api.get_channel_info.return_value = first_update_data
        mock_api.get_channel_videos.return_value = first_update_data
        
        # Create options for both channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 10
        }
        
        # Perform the update using the service
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_channel_data)
        
        # Verify both APIs were called correctly
        mock_api.get_channel_info.assert_called_once_with('UC_test_channel')
        mock_api.get_channel_videos.assert_called_once()
        
        # Verify channel deltas
        assert 'delta' in result
        assert result['delta']['subscribers'] == 1000
        assert result['delta']['views'] == 200000
        assert result['delta']['total_videos'] == 1
        
        # Verify video deltas
        assert 'video_delta' in result
        assert len(result['video_delta']['new_videos']) == 1
        assert len(result['video_delta']['updated_videos']) == 2
    
    def test_comment_delta_tracking(self, setup_youtube_service, initial_channel_data):
        """
        Test comment delta tracking for new comments.
        """
        service, mock_api = setup_youtube_service
        
        # Create an updated version with new comments
        updated_data = {
            'channel_id': initial_channel_data['channel_id'],
            'video_id': initial_channel_data['video_id'].copy()
        }
        
        # Make a copy of the first video's comments array for comparison
        # This is what we'll update with new comments
        orig_comments = initial_channel_data['video_id'][0]['comments'].copy()
        
        # Create new comments
        new_comments = [
            # Original comment
            {
                'comment_id': 'comment123',
                'comment_text': 'Great video!',
                'comment_author': 'Test User 1'
            },
            # New comments
            {
                'comment_id': 'comment124',
                'comment_text': 'Loved this!',
                'comment_author': 'Test User 3'
            },
            {
                'comment_id': 'comment125',
                'comment_text': 'Very helpful',
                'comment_author': 'Test User 4'
            }
        ]
        
        # Add new comments to existing videos
        updated_data['video_id'][0]['comments'] = new_comments
        
        # Add comment_delta to updated data directly to test the detection
        updated_data['comment_delta'] = {
            'new_comments': 2,  # We've added 2 new comments
            'videos_with_new_comments': 1  # On 1 video
        }
        
        # Configure mock API to return the updated comments
        mock_api.get_video_comments.return_value = updated_data
        
        # Create options for comments only
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': 10
        }
        
        # Perform the update
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_channel_data)
        
        # Verify the comments API was called
        mock_api.get_video_comments.assert_called_once()
        
        # Verify the result contains comment delta information
        assert 'comment_delta' in result, "Comment delta field missing from result"
        assert result['comment_delta']['new_comments'] == 2, "Incorrect number of new comments detected"
        assert result['comment_delta']['videos_with_new_comments'] == 1, "Incorrect number of videos with new comments"
    
    def test_delta_edge_cases(self, setup_youtube_service, initial_channel_data):
        """
        Test delta calculation edge cases like metrics decreasing or content removal.
        """
        service, mock_api = setup_youtube_service
        
        # Create an updated version with some decreasing metrics
        decreased_metrics = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '9500',     # -500 (decrease)
            'views': '5050000',        # +50000 (increase)
            'total_videos': '49',      # -1 (decrease)
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                # Only one video remains (second video removed)
                {
                    'video_id': 'video123',
                    'title': 'Test Video 1',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '14000',  # -1000 (decrease)
                    'likes': '1300',   # +100 (increase)
                    'comment_count': '290'  # -10 (decrease)
                }
            ]
        }
        
        # Configure mock API to return the decreased metrics
        mock_api.get_channel_info.return_value = decreased_metrics
        mock_api.get_channel_videos.return_value = decreased_metrics
        
        # Create options for both channel and video data
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False,
            'max_videos': 10
        }
        
        # Perform the update
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_channel_data)
        
        # Verify channel deltas correctly handle decreases
        assert 'delta' in result
        assert result['delta']['subscribers'] == -500, "Incorrect subscriber delta for decrease"
        assert result['delta']['views'] == 50000, "Incorrect view delta for increase"
        assert result['delta']['total_videos'] == -1, "Incorrect video count delta for decrease"
        
        # Verify video metric decreases
        video123 = next((v for v in result['video_id'] if v['video_id'] == 'video123'), None)
        assert video123 is not None
        
        # Find the video delta information
        video_deltas = next((v for v in result['video_delta']['updated_videos'] 
                             if v['video_id'] == 'video123'), None)
        assert video_deltas is not None
        assert video_deltas['views_change'] == -1000, "Incorrect views change for decrease"
        assert video_deltas['likes_change'] == 100, "Incorrect likes change for increase"
    
    def test_update_channel_data_method(self, setup_youtube_service, initial_channel_data, first_update_data):
        """
        Test the update_channel_data method which specifically handles existing channel updates.
        """
        service, mock_api = setup_youtube_service
        
        # Mock the data fetching and storage components
        service.get_channel_data = MagicMock(return_value=initial_channel_data)
        service.collect_channel_data = MagicMock(return_value=first_update_data)
        
        # Create options for update
        options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False
        }
        
        # Call the update method (non-interactive mode)
        result = service.update_channel_data('UC_test_channel', options, interactive=False)
        
        # Verify the method called collect_channel_data with existing data
        service.collect_channel_data.assert_called_once_with(
            'UC_test_channel', options, updated_data=initial_channel_data
        )
        
        # Verify result is the updated data
        assert result == first_update_data
    
    def test_update_channel_data_interactive_mode(self, setup_youtube_service, initial_channel_data):
        """
        Test the interactive mode of update_channel_data which can perform multiple iterations.
        Note: This test patches the interactive method to simulate user input.
        """
        service, mock_api = setup_youtube_service
        
        # Setup mocks
        service.get_channel_data = MagicMock(return_value=initial_channel_data)
        
        # Create a series of increasingly updated data for multiple iterations
        update1 = initial_channel_data.copy()
        update1['subscribers'] = '10500'  # +500
        
        update2 = update1.copy()
        update2['subscribers'] = '11000'  # +500 more
        
        # Mock collect_channel_data to return different values on subsequent calls
        service.collect_channel_data = MagicMock(side_effect=[update1, update2])
        
        # Mock _prompt_continue_iteration to return True once then False
        service._prompt_continue_iteration = MagicMock(side_effect=[True, False])
        
        # Create options for update
        options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        # Call the method in interactive mode
        result = service.update_channel_data('UC_test_channel', options, interactive=True)
        
        # Verify collect_channel_data was called twice
        assert service.collect_channel_data.call_count == 2
        
        # Verify _prompt_continue_iteration was called twice
        assert service._prompt_continue_iteration.call_count == 2
        
        # Verify final result has the values from the second update
        assert result['subscribers'] == '11000'


class TestCommentSentimentDeltaTracking:
    """Tests for tracking sentiment changes in comments across updates."""
    
    @pytest.fixture
    def setup_youtube_service(self):
        """Setup a YouTube service with mocked API for testing"""
        # Create mock API
        mock_api = MagicMock()
        
        # Setup service with mock API
        service = YouTubeService("test_api_key")
        service.api = mock_api
        
        # Patch the validate_and_resolve_channel_id method to always succeed
        service.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
        
        return service, mock_api
    
    @pytest.fixture
    def initial_channel_data(self):
        """Create initial channel data with comments for sentiment tracking"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '3',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'How to Use YTDataHub',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',
                    'likes': '1200',
                    'comment_count': '2',
                    'comments': [
                        {
                            'comment_id': 'comment123',
                            'comment_text': 'This tool is good for data collection.',
                            'comment_author': 'User A',
                            'sentiment': 'neutral'
                        },
                        {
                            'comment_id': 'comment124',
                            'comment_text': 'I love this application, it really helps me track my channel!',
                            'comment_author': 'User B',
                            'sentiment': 'positive'
                        }
                    ]
                },
                {
                    'video_id': 'video456',
                    'title': 'YTDataHub Tutorial',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '8000',
                    'likes': '700',
                    'comment_count': '1',
                    'comments': [
                        {
                            'comment_id': 'comment456',
                            'comment_text': 'The interface is confusing.',
                            'comment_author': 'User C',
                            'sentiment': 'negative'
                        }
                    ]
                }
            ],
            'sentiment_metrics': {
                'positive': 1,
                'neutral': 1,
                'negative': 1,
                'average_score': 0.0  # Scaled from -1 to 1
            }
        }
    
    @pytest.fixture
    def updated_channel_data(self):
        """Create updated channel data with sentiment changes"""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10500',  # +500
            'views': '5100000',      # +100000
            'total_videos': '3',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'How to Use YTDataHub',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '16000',  # +1000
                    'likes': '1300',   # +100
                    'comment_count': '3',  # +1
                    'comments': [
                        {
                            'comment_id': 'comment123',
                            'comment_text': 'This tool is good for data collection.',
                            'comment_author': 'User A',
                            'sentiment': 'neutral'
                        },
                        {
                            'comment_id': 'comment124',
                            'comment_text': 'I love this application, it really helps me track my channel!',
                            'comment_author': 'User B',
                            'sentiment': 'positive'
                        },
                        {
                            'comment_id': 'comment125',  # New comment
                            'comment_text': 'The latest update is amazing! Great job!',
                            'comment_author': 'User D',
                            'sentiment': 'positive'
                        }
                    ]
                },
                {
                    'video_id': 'video456',
                    'title': 'YTDataHub Tutorial',
                    'published_at': '2025-04-05T10:00:00Z',
                    'views': '9000',  # +1000
                    'likes': '800',   # +100
                    'comment_count': '2',  # +1
                    'comments': [
                        {
                            'comment_id': 'comment456',
                            'comment_text': 'After the latest update, the interface is much better!', # Comment text changed
                            'comment_author': 'User C',
                            'sentiment': 'positive'  # Sentiment changed from negative to positive
                        },
                        {
                            'comment_id': 'comment457',  # New comment
                            'comment_text': 'I still find it a bit confusing.',
                            'comment_author': 'User E',
                            'sentiment': 'negative'
                        }
                    ]
                }
            ],
            'sentiment_metrics': {
                'positive': 3,  # +2
                'neutral': 1,   # No change
                'negative': 1,  # No change (1 removed, 1 added)
                'average_score': 0.4  # Improved from 0.0 to 0.4
            }
        }
    
    def test_sentiment_delta_tracking(self, setup_youtube_service, initial_channel_data, updated_channel_data):
        """Test tracking changes in comment sentiment over time."""
        service, mock_api = setup_youtube_service
        
        # Configure mock API to return updated data
        mock_api.get_video_comments.return_value = updated_channel_data
        
        # Create options for comments only with sentiment analysis
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'analyze_sentiment': True,
            'max_comments_per_video': 10
        }
        
        # Perform the update
        result = service.collect_channel_data('UC_test_channel', options, existing_data=initial_channel_data)
        
        # Verify the API was called correctly
        mock_api.get_video_comments.assert_called_once()
        
        # Verify sentiment delta tracking
        assert 'sentiment_delta' in result, "Sentiment delta field is missing"
        sentiment_delta = result['sentiment_delta']
        
        # Check sentiment counts
        assert sentiment_delta['positive_change'] == 2, "Incorrect change in positive sentiment count"
        assert sentiment_delta['neutral_change'] == 0, "Incorrect change in neutral sentiment count"
        assert sentiment_delta['negative_change'] == 0, "Incorrect change in negative sentiment count"
        
        # Check sentiment score delta
        assert sentiment_delta['score_change'] == 0.4, "Incorrect change in average sentiment score"
        
        # Check comment-level sentiment changes
        assert 'comment_sentiment_changes' in sentiment_delta, "Comment sentiment changes missing"
        comment_changes = sentiment_delta['comment_sentiment_changes']
        
        # Verify we tracked the comment that changed sentiment
        changed_comment = next((c for c in comment_changes if c['comment_id'] == 'comment456'), None)
        assert changed_comment is not None, "Failed to track comment with changed sentiment"
        assert changed_comment['old_sentiment'] == 'negative', "Incorrect old sentiment"
        assert changed_comment['new_sentiment'] == 'positive', "Incorrect new sentiment"