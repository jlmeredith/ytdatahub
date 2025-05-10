"""
Integration test for the YouTube Channel Refresh UI video extraction and display.

This test verifies that the UI correctly processes and displays video data
coming from the YouTube API in various formats.
"""

import pytest
import streamlit as st
import pandas as pd
from unittest.mock import MagicMock, patch

from src.ui.data_collection.channel_refresh_ui import channel_refresh_section
from src.utils.video_formatter import extract_video_views, fix_missing_views, ensure_views_data

# Sample API response with videos in different formats
API_RESPONSE = {
    'api_data': {
        'video_id': [
            {
                'video_id': 'video1',
                'title': 'Test Video 1',
                'published_at': '2023-01-01T00:00:00Z',
                'views': '1000',
                'comment_count': '50'  # Direct comment count
            },
            {
                'video_id': 'video2',
                'title': 'Test Video 2',
                'published_at': '2023-01-02T00:00:00Z',
                'statistics': {
                    'viewCount': '2000',
                    'likeCount': '100',
                    'commentCount': '75'  # Comment count in statistics
                }
            },
            {
                'video_id': 'video3',
                'title': 'Test Video 3',
                'published_at': '2023-01-03T00:00:00Z',
                # No views or comment data to test fallback
            }
        ]
    }
}

class TestChannelRefreshUI:
    """Tests for the YouTube channel refresh UI handling of video data"""
    
    @pytest.fixture
    def mock_youtube_service(self):
        """Mock YouTube service that returns our predefined API response"""
        mock_service = MagicMock()
        mock_service.update_channel_data.return_value = API_RESPONSE
        mock_service.get_channels_list.return_value = [
            {"channel_id": "UC12345", "channel_name": "Test Channel"}
        ]
        return mock_service
    
    def test_process_video_data(self):
        """Test that video data is correctly extracted from API response"""
        # Extract videos from API response as the UI would
        videos_data = API_RESPONSE.get('api_data', {}).get('video_id', [])
        
        # Verify video count
        assert len(videos_data) == 3
        
        # Test the first video with direct views field
        video1 = videos_data[0]
        assert video1['video_id'] == 'video1'
        assert video1['title'] == 'Test Video 1'
        assert video1['published_at'] == '2023-01-01T00:00:00Z'
        assert video1['views'] == '1000'
        assert video1['comment_count'] == '50'  # Check direct comment count
        
        # Test the second video with statistics.viewCount and statistics.commentCount
        video2 = videos_data[1]
        assert video2['video_id'] == 'video2'
        assert video2['title'] == 'Test Video 2'
        assert video2['statistics']['viewCount'] == '2000'
        assert video2['statistics']['commentCount'] == '75'  # Check comment count in statistics
        
        # Verify that extract_video_views gets the correct values
        assert extract_video_views(video1) == '1000'
        assert extract_video_views(video2) == '2000'
        assert extract_video_views(videos_data[2]) == '0'  # Default for missing views
    
    def test_fix_missing_views_function(self):
        """Test that fix_missing_views correctly updates views for all formats"""
        # Get the videos and fix them
        videos_data = API_RESPONSE.get('api_data', {}).get('video_id', [])
        fixed_videos = fix_missing_views(videos_data)
        
        # Check all videos now have a 'views' field
        for video in fixed_videos:
            assert 'views' in video
        
        # Verify correct values were extracted/preserved
        assert fixed_videos[0]['views'] == '1000'  # Direct field preserved
        assert fixed_videos[1]['views'] == '2000'  # Extracted from statistics
        assert fixed_videos[2]['views'] == '0'     # Default for missing data
        
        # Check that comment counts are also properly extracted
        assert fixed_videos[0]['comment_count'] == '50'  # Direct field preserved
        assert 'comment_count' in fixed_videos[1]  # Should be added from statistics
        assert fixed_videos[1]['comment_count'] == '75'  # Extracted from statistics
    
    def test_ensure_views_data_legacy_function(self):
        """Test that the original ensure_views_data function still works"""
        # Get the videos and fix them
        videos_data = API_RESPONSE.get('api_data', {}).get('video_id', [])
        fixed_videos = ensure_views_data(videos_data)
        
        # Check all videos now have a 'views' field
        for video in fixed_videos:
            assert 'views' in video
        
        # Check that the second video now has both the views field and statistics
        assert fixed_videos[1]['views'] == '2000'
        assert fixed_videos[1]['statistics']['viewCount'] == '2000'
    
    def test_view_and_comment_count_in_refresh_mode(self):
        """Test that both view and comment counts are correctly processed in refresh mode"""
        # Create a simple API response that simulates refreshing a channel
        refresh_response = {
            'api_data': {
                'channel_id': 'UC12345',
                'channel_name': 'Test Channel',
                'subscribers': '1000',
                'views': '50000',
                'video_id': [
                    {
                        'video_id': 'video1',
                        'title': 'Test Video 1',
                        'published_at': '2023-01-01T00:00:00Z',
                        'statistics': {
                            'viewCount': '3000',  # Updated view count
                            'likeCount': '150',
                            'commentCount': '80'  # Updated comment count
                        }
                    }
                ]
            },
            'db_data': {
                'channel_id': 'UC12345',
                'channel_name': 'Test Channel',
                'subscribers': '950',
                'views': '48000',
                'video_id': [
                    {
                        'video_id': 'video1',
                        'title': 'Test Video 1',
                        'published_at': '2023-01-01T00:00:00Z',
                        'views': '2500',          # Old view count
                        'comment_count': '65'     # Old comment count
                    }
                ]
            }
        }
        
        # Process the videos with our utility functions
        api_videos = refresh_response['api_data']['video_id']
        fixed_videos = fix_missing_views(api_videos)
        
        # Verify that both view count and comment count are correctly extracted
        assert fixed_videos[0]['views'] == '3000'  # Should extract from statistics
        assert 'comment_count' in fixed_videos[0]  # Should have comment_count field
        assert fixed_videos[0]['comment_count'] == '80'  # Should extract from statistics
        
        # Compare with db data to verify delta calculation would work
        db_video = refresh_response['db_data']['video_id'][0]
        api_video = fixed_videos[0]
        
        # Calculate deltas as the application would
        view_delta = int(api_video['views']) - int(db_video['views'])
        comment_delta = int(api_video['comment_count']) - int(db_video['comment_count'])
        
        # Verify deltas are calculated correctly
        assert view_delta == 500  # 3000 - 2500
        assert comment_delta == 15  # 80 - 65

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
