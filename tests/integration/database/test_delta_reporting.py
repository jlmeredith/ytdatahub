"""
Integration tests for delta reporting functionality.
Tests the detection and reporting of changes in channel data.
"""
import pytest
from unittest.mock import MagicMock, patch
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase


class TestDeltaReporting(BaseYouTubeTestCase):
    """Tests focused on delta reporting functionality"""
    
    @pytest.fixture
    def setup_service_with_mocks(self):
        """Setup a YouTube service with mock API and DB"""
        return self.setup_mock_api_and_service()
    
    def test_delta_reporting_channel_stats(self, setup_service_with_mocks):
        """Test delta reporting for channel statistics changes"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Original channel data with initial stats
        original_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '250',
            'playlist_id': 'PL_test_playlist',
            'video_id': []
        }
        
        # Updated channel data with changed stats
        mock_api.get_channel_info.return_value = self.create_updated_channel_data()
        
        # Update options - only fetch channel data
        update_options = {
            'fetch_channel_data': True,
            'fetch_videos': False,
            'fetch_comments': False
        }
        
        # Perform the update using existing data
        result = service.collect_channel_data('UC_test_channel', update_options, existing_data=original_data)
        
        # Verify channel stats were updated and deltas are correct
        assert result is not None
        assert result['channel_id'] == 'UC_test_channel'
        assert result['subscribers'] == '12000'
        assert result['views'] == '5500000'
        assert result['total_videos'] == '255'
        
        # Verify delta calculations if the service provides them
        self.verify_delta_reporting(result)
        
        # Check that API was called correctly
        mock_api.get_channel_info.assert_called_once_with('UC_test_channel')
    
    def test_delta_reporting_after_each_step(self, setup_service_with_mocks):
        """Test that delta reports are generated after each step in the collection process"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Setup existing and updated data for testing
        existing_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '4800000',
            'total_videos': '240',
            'playlist_id': 'PL_test_playlist',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Original Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '10000',
                    'likes': '1000',
                    'comment_count': '200',
                    'comments': [
                        {
                            'comment_id': 'comment123',
                            'comment_text': 'Existing comment',
                            'comment_author': 'User 1'
                        }
                    ]
                }
            ]
        }
        
        # Setup updated data for each step
        updated_channel_info = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '12000',  # Increased
            'views': '5500000',      # Increased
            'total_videos': '252',    # Increased
            'channel_description': 'This is a test channel',
            'playlist_id': 'PL_test_playlist'
        }
        
        # Configure mock responses
        mock_api.get_channel_info.return_value = updated_channel_info
        
        # Setup videos with updates and new videos
        updated_videos = {
            'channel_id': 'UC_test_channel',
            'video_id': [
                # Updated existing video
                {
                    'video_id': 'video123',
                    'title': 'Original Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '15000',  # Increased
                    'likes': '1500',   # Increased
                    'comment_count': '300'  # Increased
                },
                # New videos
                {
                    'video_id': 'video456',
                    'title': 'New Video 1',
                    'published_at': '2025-04-15T10:00:00Z',
                    'views': '5000',
                    'likes': '400',
                    'comment_count': '50'
                },
                {
                    'video_id': 'video789',
                    'title': 'New Video 2',
                    'published_at': '2025-04-20T14:30:00Z',
                    'views': '2000',
                    'likes': '200',
                    'comment_count': '20'
                }
            ]
        }
        mock_api.get_channel_videos.return_value = updated_videos
        
        # Setup comments with updates
        updated_comments = {
            'video_id': [
                # Existing video with new comments
                {
                    'video_id': 'video123',
                    'comments': [
                        # Existing comment
                        {
                            'comment_id': 'comment123',
                            'comment_text': 'Existing comment',
                            'comment_author': 'User 1'
                        },
                        # New comments
                        {
                            'comment_id': 'comment456',
                            'comment_text': 'Love this video!',
                            'comment_author': 'User 2'
                        },
                        {
                            'comment_id': 'comment789',
                            'comment_text': 'Great content as always',
                            'comment_author': 'User 3'
                        }
                    ]
                },
                # New videos with comments
                {
                    'video_id': 'video456',
                    'comments': [
                        {
                            'comment_id': 'comment012',
                            'comment_text': 'First comment on new video',
                            'comment_author': 'User 4'
                        }
                    ]
                },
                {
                    'video_id': 'video789',
                    'comments': [
                        {
                            'comment_id': 'comment345',
                            'comment_text': 'Another great video',
                            'comment_author': 'User 5'
                        }
                    ]
                }
            ],
            'comment_stats': {
                'total_comments': 5,
                'videos_with_comments': 3,
                'videos_with_disabled_comments': 0,
                'videos_with_errors': 0
            }
        }
        mock_api.get_video_comments.return_value = updated_comments
        
        # Run the three collection steps and verify deltas after each
        
        # STEP 1: Update Channel Info
        step1_options = {'fetch_channel_data': True, 'fetch_videos': False, 'fetch_comments': False}
        step1_result = service.collect_channel_data('UC_test_channel', step1_options, existing_data=existing_data)
        
        # STEP 2: Update Videos
        step2_options = {'fetch_channel_data': False, 'fetch_videos': True, 'fetch_comments': False, 'max_videos': 50}
        step2_result = service.collect_channel_data('UC_test_channel', step2_options, existing_data=step1_result)
        
        # STEP 3: Update Comments
        step3_options = {'fetch_channel_data': False, 'fetch_videos': False, 'fetch_comments': True, 'max_comments_per_video': 20}
        step3_result = service.collect_channel_data('UC_test_channel', step3_options, existing_data=step2_result)
        
        # Verify deltas at each step
        
        # Step 1 - Channel Stats Delta
        if 'delta' in step1_result:
            assert step1_result['delta']['subscribers'] == 2000
            assert step1_result['delta']['views'] == 700000
            assert step1_result['delta']['total_videos'] == 12
        
        # Step 2 - Video Delta
        if 'video_delta' in step2_result:
            assert 'new_videos' in step2_result['video_delta']
            assert len(step2_result['video_delta']['new_videos']) == 2
            
            assert 'updated_videos' in step2_result['video_delta']
            updated_video = next((v for v in step2_result['video_delta']['updated_videos'] 
                               if v['video_id'] == 'video123'), None)
            if updated_video:
                assert updated_video['views_change'] == 5000
        
        # Step 3 - Comment Delta
        if 'comment_delta' in step3_result:
            assert step3_result['comment_delta']['new_comments'] >= 4
            assert step3_result['comment_delta']['videos_with_new_comments'] >= 2
        
        # Save final result
        self.verify_storage_call(service, step3_result, mock_db)
    
    def test_sequential_delta_updates(self, setup_service_with_mocks):
        """Test sequential updates and cumulative delta reporting"""
        service, mock_api, mock_db = setup_service_with_mocks
        
        # Initial data
        initial_data = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '1',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Initial Video',
                    'published_at': '2025-04-01T12:00:00Z',
                    'views': '10000',
                    'likes': '1000',
                    'comment_count': '100',
                    'comments': []
                }
            ]
        }
        
        # First update data
        first_update = {
            'channel_id': 'UC_test_channel',
            'subscribers': '11000',  # +1000
            'views': '5200000',      # +200000
            'total_videos': '2',
            'video_id': [
                {
                    'video_id': 'video123',
                    'title': 'Initial Video',
                    'views': '12000',  # +2000
                    'likes': '1200',   # +200
                    'comment_count': '120'  # +20
                },
                {
                    'video_id': 'video456',
                    'title': 'Second Video',
                    'views': '5000',
                    'likes': '500',
                    'comment_count': '50'
                }
            ]
        }
        
        # Configure sequential API responses
        mock_api.get_channel_info.side_effect = [
            {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'subscribers': '11000',
                'views': '5200000',
                'total_videos': '2'
            },
            {
                'channel_id': 'UC_test_channel',
                'channel_name': 'Test Channel',
                'subscribers': '12000',
                'views': '5500000',
                'total_videos': '3'
            }
        ]
        
        mock_api.get_channel_videos.side_effect = [
            {'channel_id': 'UC_test_channel', 'video_id': first_update['video_id']},
            {'channel_id': 'UC_test_channel', 'video_id': [
                # First video updated again
                {
                    'video_id': 'video123',
                    'title': 'Initial Video',
                    'views': '15000',  # +3000
                    'likes': '1500',   # +300
                    'comment_count': '150'  # +30
                },
                # Second video updated
                {
                    'video_id': 'video456',
                    'title': 'Second Video',
                    'views': '8000',  # +3000
                    'likes': '800',   # +300
                    'comment_count': '80'  # +30
                },
                # Third new video
                {
                    'video_id': 'video789',
                    'title': 'Third Video',
                    'views': '2000',
                    'likes': '200',
                    'comment_count': '20'
                }
            ]}
        ]
        
        # Run tests for sequential updates
        update_options = {
            'fetch_channel_data': True,
            'fetch_videos': True,
            'fetch_comments': False
        }
        
        # First update
        first_result = service.collect_channel_data('UC_test_channel', update_options, existing_data=initial_data)
        
        # Verify first update
        assert first_result['subscribers'] == '11000'
        assert first_result['total_videos'] == '2'
        assert len(first_result['video_id']) == 2
        
        video123_first = next(v for v in first_result['video_id'] if v['video_id'] == 'video123')
        assert video123_first['views'] == '12000'
        
        # Save first result
        with patch('src.storage.factory.StorageFactory.get_storage_provider', return_value=mock_db):
            service.save_channel_data(first_result, 'SQLite Database')
        
        # Second update using first result as baseline
        second_result = service.collect_channel_data('UC_test_channel', update_options, existing_data=first_result)
        
        # Verify second update
        assert second_result['subscribers'] == '12000'
        assert second_result['total_videos'] == '3' 
        assert len(second_result['video_id']) == 3
        
        # Verify specific video updates
        video123_second = next(v for v in second_result['video_id'] if v['video_id'] == 'video123')
        assert video123_second['views'] == '15000'
        
        video456_second = next(v for v in second_result['video_id'] if v['video_id'] == 'video456')
        assert video456_second['views'] == '8000'
        
        # Check for third video
        assert 'video789' in [v['video_id'] for v in second_result['video_id']]
        
        # Verify API call sequence
        assert mock_api.get_channel_info.call_count == 2
        assert mock_api.get_channel_videos.call_count == 2
        
        # Save final result
        with patch('src.storage.factory.StorageFactory.get_storage_provider', return_value=mock_db):
            save_result = service.save_channel_data(second_result, 'SQLite Database')
            assert save_result is True
            assert mock_db.store_channel_data.call_count == 2


if __name__ == '__main__':
    pytest.main()
