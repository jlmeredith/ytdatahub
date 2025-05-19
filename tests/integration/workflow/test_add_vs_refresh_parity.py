print("[TEST DEBUG] test_add_vs_refresh_parity.py module loaded")

"""
Test parity between adding a new channel and refreshing an existing channel for YouTube API data points.
Ensures that view counts and comment counts are always present and consistent in both flows.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from tests.utils.youtube_test_factory import YouTubeTestFactory

# @pytest.mark.integration
def test_add_vs_refresh_channel_data_parity():
    print("[TEST DEBUG] Entered test_add_vs_refresh_channel_data_parity")
    print("[TEST DEBUG] test_add_vs_refresh_channel_data_parity starting")
    # Setup mock service and API
    service, mock_api, mock_db = YouTubeTestFactory.create_mock_service()

    # Create channel data with videos and comments
    channel_data = YouTubeTestFactory.create_channel_data(include_videos=True, video_count=3, include_comments=True)
    YouTubeTestFactory.configure_mock_api_for_workflow(mock_api, channel_data=channel_data, video_data=channel_data, comment_data=channel_data)

    print("[TEST DEBUG] test_add_vs_refresh_channel_data_parity setup complete, running main test logic")

    # Simulate 'add new channel' flow (full collection)
    add_steps = {
        'channel': {'fetch': True},
        'videos': {'fetch': True, 'max': 3},
        'comments': {'fetch': True, 'max': 3},
        'save': False
    }
    print("[TEST DEBUG] About to call collect_channel_data")
    add_results, add_final = YouTubeTestFactory.create_test_steps_pipeline(service, mock_api, mock_db, steps_config=add_steps)
    print("[TEST DEBUG] collect_channel_data call returned")
    # Reset video pagination counter before refresh flow
    YouTubeTestFactory.reset_video_pagination_counter(mock_api)
    # Simulate 'refresh channel' flow (full refresh)
    refresh_steps = {
        'channel': {'fetch': True},
        'videos': {'fetch': True, 'max': 3},
        'comments': {'fetch': True, 'max': 3},
        'save': False
    }
    print("[TEST DEBUG] About to call collect_channel_data")
    refresh_results, refresh_final = YouTubeTestFactory.create_test_steps_pipeline(service, mock_api, mock_db, steps_config=refresh_steps)
    print("[TEST DEBUG] collect_channel_data call returned")

    # Compare video data for parity
    add_videos = add_results['videos']['video_id']
    refresh_videos = refresh_results['videos']['video_id']
    assert len(add_videos) == len(refresh_videos)
    for v_add, v_refresh in zip(add_videos, refresh_videos):
        assert v_add['video_id'] == v_refresh['video_id']
        assert v_add['views'] == v_refresh['views']
        assert v_add['comment_count'] == v_refresh['comment_count']
        # If statistics dict is present, check viewCount and commentCount
        if 'statistics' in v_add and 'statistics' in v_refresh:
            assert v_add['statistics'].get('viewCount', v_add['views']) == v_refresh['statistics'].get('viewCount', v_refresh['views'])
            assert v_add['statistics'].get('commentCount', v_add['comment_count']) == v_refresh['statistics'].get('commentCount', v_refresh['comment_count'])

    # Compare comments for parity
    for v_add, v_refresh in zip(add_videos, refresh_videos):
        if 'comments' in v_add and 'comments' in v_refresh:
            assert len(v_add['comments']) == len(v_refresh['comments'])
            for c_add, c_refresh in zip(v_add['comments'], v_refresh['comments']):
                assert c_add['comment_id'] == c_refresh['comment_id']
                assert c_add['comment_text'] == c_refresh['comment_text']
                assert c_add['comment_author'] == c_refresh['comment_author']

    # Ensure all videos have view and comment counts and check for edge cases
    for v in add_videos + refresh_videos:
        assert 'views' in v, f"Missing 'views' in video: {v}"
        assert 'comment_count' in v, f"Missing 'comment_count' in video: {v}"
        assert isinstance(v['views'], (int, float)), f"'views' is not numeric: {v['views']} in video: {v}"
        assert isinstance(v['comment_count'], (int, float)), f"'comment_count' is not numeric: {v['comment_count']} in video: {v}"
        assert v['views'] >= 0, f"'views' is negative: {v['views']} in video: {v}"
        assert v['comment_count'] >= 0, f"'comment_count' is negative: {v['comment_count']} in video: {v}"
        # If statistics dict is present, check types and values
        if 'statistics' in v:
            stats = v['statistics']
            if 'viewCount' in stats:
                assert isinstance(stats['viewCount'], (int, float, str)), f"'viewCount' is not numeric or string: {stats['viewCount']}"
                # Accept string numbers as valid (YouTube API sometimes returns strings)
                if isinstance(stats['viewCount'], str):
                    assert stats['viewCount'].isdigit(), f"'viewCount' string is not digit: {stats['viewCount']}"
            if 'commentCount' in stats:
                assert isinstance(stats['commentCount'], (int, float, str)), f"'commentCount' is not numeric or string: {stats['commentCount']}"
                if isinstance(stats['commentCount'], str):
                    assert stats['commentCount'].isdigit(), f"'commentCount' string is not digit: {stats['commentCount']}"

    # Edge case: Video with missing statistics
    edge_channel_data = YouTubeTestFactory.create_channel_data(include_videos=True, video_count=1, include_comments=False)
    # Remove statistics from the video
    for v in edge_channel_data['video_id']:
        if 'statistics' in v:
            del v['statistics']
    YouTubeTestFactory.configure_mock_api_for_workflow(mock_api, channel_data=edge_channel_data, video_data=edge_channel_data, comment_data=edge_channel_data)
    edge_steps = {
        'channel': {'fetch': True},
        'videos': {'fetch': True, 'max': 1},
        'comments': {'fetch': False},
        'save': False
    }
    edge_results, _ = YouTubeTestFactory.create_test_steps_pipeline(service, mock_api, mock_db, steps_config=edge_steps)
    edge_video = edge_results['videos']['video_id'][0]
    assert 'views' in edge_video, "Missing 'views' in video with missing statistics"
    assert 'comment_count' in edge_video, "Missing 'comment_count' in video with missing statistics"
    # Edge case: Video with malformed statistics
    malformed_channel_data = YouTubeTestFactory.create_channel_data(include_videos=True, video_count=1, include_comments=False)
    for v in malformed_channel_data['video_id']:
        v['statistics'] = {'viewCount': 'not_a_number', 'commentCount': None}
    YouTubeTestFactory.configure_mock_api_for_workflow(mock_api, channel_data=malformed_channel_data, video_data=malformed_channel_data, comment_data=malformed_channel_data)
    malformed_results, _ = YouTubeTestFactory.create_test_steps_pipeline(service, mock_api, mock_db, steps_config=edge_steps)
    malformed_video = malformed_results['videos']['video_id'][0]
    assert 'views' in malformed_video, "Missing 'views' in video with malformed statistics"
    assert 'comment_count' in malformed_video, "Missing 'comment_count' in video with malformed statistics"
    # Accept fallback to 0 or None for malformed data
    assert isinstance(malformed_video['views'], (int, float)), f"Malformed 'views' not handled: {malformed_video['views']}"
    assert isinstance(malformed_video['comment_count'], (int, float)), f"Malformed 'comment_count' not handled: {malformed_video['comment_count']}"

    print("[TEST DEBUG] test_add_vs_refresh_channel_data_parity finished")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
