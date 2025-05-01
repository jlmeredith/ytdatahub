"""
Abstraction layer for YouTube Data Collection testing.
This module provides a simplified interface for testing data collection workflows.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.services.youtube_service import YouTubeService
from src.storage.factory import StorageFactory
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from src.utils.queue_tracker import add_to_queue, remove_from_queue, set_test_mode
import datetime
import random


class YouTubeTestFactory:
    """
    Factory class that simplifies creation of YouTube test scenarios.
    Helps reduce boilerplate code in test files by providing reusable test components.
    """
    
    @staticmethod
    def create_mock_service():
        """Create a mock YouTube service with preset behavior"""
        mock_api = MagicMock(spec=YouTubeAPI)
        mock_db = MagicMock(spec=SQLiteDatabase)
        
        # Configure default behavior
        mock_api.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
        mock_db.store_channel_data = MagicMock(return_value=True)
        
        mock_api.get_channel_info.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '50'
        }
        
        # Create service
        service = YouTubeService("test_api_key")
        service.api = mock_api
        service.validate_and_resolve_channel_id = MagicMock(return_value=(True, 'UC_test_channel'))
        
        return service, mock_api, mock_db
    
    @staticmethod
    def collection_options(channel_data=True, videos=True, comments=True, max_videos=50, max_comments=20):
        """Generate collection options with specified settings"""
        return {
            'fetch_channel_data': channel_data,
            'fetch_videos': videos,
            'fetch_comments': comments,
            'max_videos': max_videos,
            'max_comments_per_video': max_comments
        }
    
    @staticmethod
    def create_channel_data(channel_id='UC_test_channel', subs='10000', views='5000000', 
                           videos='250', include_videos=False, video_count=1, include_comments=False):
        """Create channel data with optional videos and comments"""
        channel_data = {
            'channel_id': channel_id,
            'channel_name': 'Test Channel',
            'subscribers': subs,
            'views': views,
            'total_videos': videos,
            'channel_description': 'This is a test channel',
            'playlist_id': 'PL_test_playlist'
        }
        
        if include_videos:
            video_list = []
            for i in range(video_count):
                video = {
                    'video_id': f'video{i+1}',
                    'title': f'Test Video {i+1}',
                    'video_description': f'Test video description {i+1}',
                    'published_at': '2025-04-01T12:00:00Z',
                    'published_date': '2025-04-01',
                    'views': f'{15000 * (i+1)}',
                    'likes': f'{1200 * (i+1)}',
                    'comment_count': f'{300 * (i+1)}',
                    'duration': 'PT10M30S',
                    'thumbnails': f'https://example.com/thumb{i+1}.jpg'
                }
                
                if include_comments:
                    video['comments'] = [
                        {
                            'comment_id': f'comment{i+1}_{j+1}',
                            'comment_text': f'Comment {j+1} on video {i+1}',
                            'comment_author': f'Test User {j+1}',
                            'comment_published_at': '2025-04-02T10:00:00Z',
                            'like_count': f'{50 * (j+1)}'
                        } for j in range(3)  # 3 comments per video
                    ]
                
                video_list.append(video)
            
            channel_data['video_id'] = video_list
            
            if include_comments:
                channel_data['comment_stats'] = {
                    'total_comments': 3 * video_count,
                    'videos_with_comments': video_count,
                    'videos_with_disabled_comments': 0,
                    'videos_with_errors': 0
                }
        
        return channel_data
    
    @staticmethod
    def configure_mock_api_for_workflow(mock_api, channel_data=None, video_data=None, comment_data=None):
        """Configure a mock API to return specified responses"""
        if channel_data:
            mock_api.get_channel_info.return_value = channel_data
        
        if video_data:
            mock_api.get_channel_videos.return_value = video_data
            
        if comment_data:
            mock_api.get_video_comments.return_value = comment_data
            
        return mock_api
    
    @staticmethod
    def create_delta_scenario(initial_state, updated_state):
        """Create a scenario for testing delta updates"""
        # Compute deltas automatically
        deltas = {
            'subscribers': int(updated_state.get('subscribers', '0')) - int(initial_state.get('subscribers', '0')),
            'views': int(updated_state.get('views', '0')) - int(initial_state.get('views', '0')),
            'total_videos': int(updated_state.get('total_videos', '0')) - int(initial_state.get('total_videos', '0'))
        }
        
        # Add delta field to updated_state
        updated_state['delta'] = deltas
        
        return initial_state, updated_state
    
    @staticmethod
    def verify_service_calls(mock_api, channel_id='UC_test_channel', expect_videos=True, 
                            expect_comments=False, max_videos=None, max_comments=None):
        """Verify that the API was called with expected parameters"""
        # Check channel info call
        mock_api.get_channel_info.assert_called_with(channel_id)
        
        # Check video calls
        if expect_videos:
            mock_api.get_channel_videos.assert_called_once()
            if max_videos is not None:
                _, kwargs = mock_api.get_channel_videos.call_args
                assert kwargs.get('max_videos') == max_videos
        else:
            assert mock_api.get_channel_videos.call_count == 0
            
        # Check comment calls
        if expect_comments:
            mock_api.get_video_comments.assert_called_once()
            if max_comments is not None:
                _, kwargs = mock_api.get_video_comments.call_args
                assert kwargs.get('max_comments_per_video') == max_comments
        else:
            assert mock_api.get_video_comments.call_count == 0
    
    @staticmethod
    def mock_video_generator(count=10, base_views=10000, base_likes=1000):
        """Generate a specified number of mock videos"""
        videos = []
        for i in range(count):
            videos.append({
                'video_id': f'video{i+1}',
                'title': f'Test Video {i+1}',
                'published_at': '2025-04-01T12:00:00Z',
                'views': str(base_views * (i+1)),
                'likes': str(base_likes * (i+1)),
                'comment_count': str(int(base_likes * (i+1) / 10))
            })
            
        return {
            'channel_id': 'UC_test_channel',
            'video_id': videos,
            'total_videos': str(count)
        }
    
    @staticmethod
    def verify_step_sequence(steps_results, mock_api):
        """Verify results from a sequence of steps"""
        verification_results = {}
        
        # Verify all steps produced valid results
        for step, result in steps_results.items():
            assert result is not None
            assert result['channel_id'] == 'UC_test_channel'
            verification_results[step] = {'status': 'passed'}
            
            # Check step-specific results
            if step == 'channel_data':
                if 'video_id' not in result:
                    verification_results[step]['note'] = 'Channel data only, no videos'
            elif step == 'videos':
                assert 'video_id' in result
                verification_results[step]['video_count'] = len(result['video_id'])
            elif step == 'comments':
                assert 'video_id' in result
                has_comments = any('comments' in video for video in result['video_id'])
                assert has_comments
                verification_results[step]['has_comments'] = True
        
        # Verify API calls were made correctly
        if len(mock_api.get_channel_info.call_args_list) > 0:
            verification_results['api_calls'] = {'channel_info': 'called'}
            
        if len(mock_api.get_channel_videos.call_args_list) > 0:
            verification_results['api_calls']['videos'] = 'called'
            
        if len(mock_api.get_video_comments.call_args_list) > 0:
            verification_results['api_calls']['comments'] = 'called'
            
        return verification_results
    
    @staticmethod
    def verify_database_save(mock_db, expect_calls=1):
        """Verify that the database save method was called correctly"""
        assert mock_db.store_channel_data.call_count == expect_calls
        return {'database_saves': expect_calls}
    
    @staticmethod
    def create_test_steps_pipeline(service, mock_api, mock_db, steps_config=None):
        """
        Create a complete test pipeline with multiple steps
        
        Parameters:
        - steps_config: Dictionary with configuration for each step
          Example: {
              'channel': {'fetch': True},
              'videos': {'fetch': True, 'max': 30},
              'comments': {'fetch': True, 'max': 15},
              'save': True
          }
        """
        if steps_config is None:
            steps_config = {
                'channel': {'fetch': True},
                'videos': {'fetch': True, 'max': 30},
                'comments': {'fetch': True, 'max': 15},
                'save': True
            }
            
        results = {}
        current_data = None
        
        # Step 1: Channel data
        if steps_config.get('channel', {}).get('fetch', False):
            step1_options = {
                'fetch_channel_data': True,
                'fetch_videos': False,
                'fetch_comments': False
            }
            
            channel_data = service.collect_channel_data('UC_test_channel', step1_options)
            results['channel'] = channel_data
            current_data = channel_data
            
        # Step 2: Videos
        if steps_config.get('videos', {}).get('fetch', False):
            step2_options = {
                'fetch_channel_data': False,
                'fetch_videos': True,
                'fetch_comments': False,
                'max_videos': steps_config['videos'].get('max', 50)
            }
            
            video_data = service.collect_channel_data('UC_test_channel', step2_options, 
                                                     existing_data=current_data)
            results['videos'] = video_data
            current_data = video_data
            
        # Step 3: Comments
        if steps_config.get('comments', {}).get('fetch', False):
            step3_options = {
                'fetch_channel_data': False,
                'fetch_videos': False,
                'fetch_comments': True,
                'max_comments_per_video': steps_config['comments'].get('max', 20)
            }
            
            comment_data = service.collect_channel_data('UC_test_channel', step3_options, 
                                                      existing_data=current_data)
            results['comments'] = comment_data
            current_data = comment_data
            
        # Final step: Save
        if steps_config.get('save', False) and current_data:
            with patch('src.storage.factory.StorageFactory.get_storage_provider', return_value=mock_db):
                save_result = service.save_channel_data(current_data, 'SQLite Database')
                results['save'] = save_result
        
        return results, current_data

    @staticmethod
    def create_channel(
        channel_id=None, 
        subscribers=None, 
        videos=None, 
        views=None, 
        include_videos=False,
        video_count=1
    ):
        """
        Create a channel data dictionary with optional parameters
        
        Args:
            channel_id: Optional channel ID (default: random)
            subscribers: Optional subscriber count (default: random)
            videos: Optional video count (default: random)
            views: Optional view count (default: random)
            include_videos: Whether to include video objects (default: False)
            video_count: How many videos to include if include_videos is True
            
        Returns:
            Dict containing channel data
        """
        if channel_id is None:
            channel_id = f"UC{YouTubeTestFactory._random_id(22)}"
            
        if subscribers is None:
            subscribers = str(random.randint(100, 1000000))
            
        if videos is None:
            videos = str(random.randint(5, 500))
            
        if views is None:
            views = str(random.randint(1000, 50000000))
            
        channel = {
            'channel_id': channel_id,
            'channel_name': f"Test Channel {YouTubeTestFactory._random_id(4)}",
            'subscribers': subscribers,
            'views': views,
            'total_videos': videos,
            'channel_description': f"This is a test channel created at {datetime.datetime.now().isoformat()}",
            'playlist_id': f"PL{YouTubeTestFactory._random_id(24)}"
        }
        
        if include_videos:
            channel['video_id'] = [
                YouTubeTestFactory.create_video(include_comments=(i % 2 == 0))
                for i in range(video_count)
            ]
            
        return channel
        
    @staticmethod
    def create_video(
        video_id=None,
        title=None,
        views=None,
        likes=None,
        comments=None,
        include_comments=False,
        comment_count=3
    ):
        """
        Create a video data dictionary with optional parameters
        
        Args:
            video_id: Optional video ID (default: random)
            title: Optional video title (default: random)
            views: Optional view count (default: random)
            likes: Optional like count (default: random) 
            comments: Optional comment count (default: random)
            include_comments: Whether to include comment objects (default: False)
            comment_count: How many comments to include if include_comments is True
            
        Returns:
            Dict containing video data
        """
        if video_id is None:
            video_id = YouTubeTestFactory._random_id(11)
            
        if title is None:
            title = f"Test Video {YouTubeTestFactory._random_id(5)}"
            
        if views is None:
            views = str(random.randint(50, 1000000))
            
        if likes is None:
            likes = str(random.randint(5, int(int(views) * 0.1)))
            
        if comments is None:
            comments = str(random.randint(0, int(int(likes) * 0.5)))
            
        # Calculate a realistic publish date within last year
        days_ago = random.randint(0, 365)
        publish_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        published_at = publish_date.isoformat().split('.')[0] + 'Z'
        published_date = publish_date.strftime('%Y-%m-%d')
        
        video = {
            'video_id': video_id,
            'title': title,
            'video_description': f"Description for {title}",
            'published_at': published_at,
            'published_date': published_date,
            'views': views,
            'likes': likes,
            'comment_count': comments,
            'duration': f"PT{random.randint(1, 60)}M{random.randint(0, 59)}S",
            'thumbnails': f"https://example.com/thumb_{video_id}.jpg"
        }
        
        if include_comments:
            video['comments'] = [
                YouTubeTestFactory.create_comment(video_id=video_id)
                for _ in range(comment_count)
            ]
            
        return video
        
    @staticmethod
    def create_comment(
        comment_id=None,
        video_id=None,
        text=None,
        author=None,
        likes=None
    ):
        """
        Create a comment data dictionary with optional parameters
        
        Args:
            comment_id: Optional comment ID (default: random)
            video_id: Optional video ID this comment belongs to (default: random)
            text: Optional comment text (default: random)
            author: Optional author name (default: random)
            likes: Optional like count (default: random)
            
        Returns:
            Dict containing comment data
        """
        if comment_id is None:
            comment_id = YouTubeTestFactory._random_id(12)
            
        if video_id is None:
            video_id = YouTubeTestFactory._random_id(11)
            
        if text is None:
            comments = [
                "Great video!",
                "Thanks for sharing this.",
                "I learned a lot from this video.",
                "First!",
                "Could you make a follow-up on this topic?",
                "I disagree with your point at 5:23.",
                "The information was very helpful.",
                "Love the way you explained this!"
            ]
            text = random.choice(comments)
            
        if author is None:
            author = f"Test User {YouTubeTestFactory._random_id(4)}"
            
        if likes is None:
            likes = str(random.randint(0, 200))
            
        # Calculate a realistic publish date (after video)
        days_ago = random.randint(0, 30)
        publish_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        published_at = publish_date.isoformat().split('.')[0] + 'Z'
        
        return {
            'comment_id': comment_id,
            'comment_text': text,
            'comment_author': author,
            'comment_published_at': published_at,
            'like_count': likes
        }
        
    @staticmethod
    def create_delta_report(
        old_channel=None,
        new_channel=None,
        include_video_delta=True,
        include_comment_delta=True
    ):
        """
        Create a delta report between two channels
        
        Args:
            old_channel: Previous channel data (created if None)
            new_channel: Updated channel data (created if None)
            include_video_delta: Whether to include video delta
            include_comment_delta: Whether to include comment delta
            
        Returns:
            Dict containing delta report
        """
        if old_channel is None:
            old_channel = YouTubeTestFactory.create_channel(
                subscribers='10000',
                views='5000000',
                videos='200',
                include_videos=True,
                video_count=5
            )
            
        if new_channel is None:
            # Increase some metrics for the new channel
            new_channel = YouTubeTestFactory.create_channel(
                channel_id=old_channel['channel_id'],
                subscribers=str(int(old_channel['subscribers']) + 2000),
                views=str(int(old_channel['views']) + 500000),
                videos=str(int(old_channel['total_videos']) + 5),
                include_videos=True,
                video_count=7  # More videos than before
            )
        
        delta = {
            'collection_date': datetime.datetime.now().isoformat(),
            'channel_id': new_channel['channel_id'],
            'channel_name': new_channel['channel_name'],
            'subscribers': new_channel['subscribers'],
            'views': new_channel['views'],
            'total_videos': new_channel['total_videos'],
            'delta': {
                'subscribers': int(new_channel['subscribers']) - int(old_channel['subscribers']),
                'views': int(new_channel['views']) - int(old_channel['views']),
                'total_videos': int(new_channel['total_videos']) - int(old_channel['total_videos'])
            }
        }
        
        if include_video_delta and 'video_id' in old_channel and 'video_id' in new_channel:
            # Find new videos
            old_video_ids = {v['video_id'] for v in old_channel['video_id']}
            new_videos = [v for v in new_channel['video_id'] if v['video_id'] not in old_video_ids]
            
            # Find updated videos (videos in both old and new)
            updated_videos = []
            for new_video in new_channel['video_id']:
                for old_video in old_channel['video_id']:
                    if new_video['video_id'] == old_video['video_id']:
                        # This video exists in both datasets
                        delta_info = {
                            'video_id': new_video['video_id'],
                            'title': new_video['title'],
                            'views_delta': int(new_video['views']) - int(old_video['views']),
                            'likes_delta': int(new_video['likes']) - int(old_video['likes'])
                        }
                        
                        if 'comment_count' in new_video and 'comment_count' in old_video:
                            delta_info['comment_count_delta'] = int(new_video['comment_count']) - int(old_video['comment_count'])
                            
                        updated_videos.append(delta_info)
            
            delta['video_delta'] = {
                'new_videos': new_videos,
                'updated_videos': updated_videos,
                'total_new_videos': len(new_videos),
                'total_updated_videos': len(updated_videos)
            }
            
        if include_comment_delta:
            # Count comments in old and new datasets
            old_comment_count = 0
            new_comment_count = 0
            
            if 'video_id' in old_channel:
                for video in old_channel['video_id']:
                    if 'comments' in video:
                        old_comment_count += len(video['comments'])
                        
            if 'video_id' in new_channel:
                for video in new_channel['video_id']:
                    if 'comments' in video:
                        new_comment_count += len(video['comments'])
            
            delta['comment_delta'] = {
                'new_comments': new_comment_count - old_comment_count,
                'videos_with_new_comments': 0,  # Would require deeper analysis
                'old_comment_count': old_comment_count,
                'new_comment_count': new_comment_count
            }
        
        return delta
    
    @staticmethod
    def _random_id(length):
        """Generate a random ID of specified length"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        return ''.join(random.choice(chars) for _ in range(length))


# Example use:
"""
from tests.utils.youtube_test_factory import YouTubeTestFactory

def test_example_using_factory():
    # Create service with mocks
    service, mock_api, mock_db = YouTubeTestFactory.create_mock_service()
    
    # Configure test data
    channel_data = YouTubeTestFactory.create_channel_data(include_videos=True, video_count=3, include_comments=True)
    
    # Configure API
    YouTubeTestFactory.configure_mock_api_for_workflow(mock_api, channel_data=channel_data, video_data=channel_data)
    
    # Generate collection options
    options = YouTubeTestFactory.collection_options(max_videos=10)
    
    # Run collection
    result = service.collect_channel_data('UC_test_channel', options)
    
    # Verify API calls
    YouTubeTestFactory.verify_service_calls(mock_api, max_videos=10)
    
    # Save and verify
    with patch('src.storage.factory.StorageFactory.get_storage_provider', return_value=mock_db):
        save_result = service.save_channel_data(result, 'SQLite Database')
        YouTubeTestFactory.verify_database_save(mock_db)
"""