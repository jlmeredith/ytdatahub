import pytest
from unittest.mock import MagicMock
from src.api.youtube.comment import CommentClient

@pytest.fixture
def mock_youtube():
    return MagicMock()

@pytest.fixture
def comment_client(mock_youtube):
    client = CommentClient()
    client.youtube = mock_youtube
    client.is_initialized = MagicMock(return_value=True)
    return client

def test_get_video_comments_success(comment_client, mock_youtube):
    # Mock video details response
    mock_video_details = {
        'items': [{
            'statistics': {'commentCount': '10'}
        }]
    }
    mock_youtube.videos().list().execute.return_value = mock_video_details

    # Mock comments response
    mock_comments = {
        'items': [
            {
                'id': 'comment1',
                'snippet': {
                    'topLevelComment': {
                        'snippet': {
                            'textDisplay': 'Test comment',
                            'authorDisplayName': 'Test User',
                            'publishedAt': '2021-01-01T00:00:00Z',
                            'likeCount': 5
                        }
                    },
                    'publishedAt': '2021-01-01T00:00:00Z'
                }
            }
        ]
    }
    mock_youtube.commentThreads().list().execute.return_value = mock_comments

    # Setup channel info with a video
    channel_info = {
        'video_id': [{'video_id': 'VIDEO123', 'title': 'Test Video'}]
    }

    # Call the method
    result = comment_client.get_video_comments(channel_info, max_comments_per_video=10)

    # Assertions
    assert result is not None
    assert 'comments' in result['video_id'][0]
    assert len(result['video_id'][0]['comments']) > 0
    assert result['video_id'][0]['comments'][0]['comment_text'] == 'Test comment'

def test_get_video_comments_disabled(comment_client, mock_youtube):
    # Mock video details response with comments disabled
    mock_video_details = {
        'items': [{
            'statistics': {}  # No commentCount indicates comments are disabled
        }]
    }
    mock_youtube.videos().list().execute.return_value = mock_video_details

    # Setup channel info with a video
    channel_info = {
        'video_id': [{'video_id': 'VIDEO123', 'title': 'Test Video'}]
    }

    # Call the method
    result = comment_client.get_video_comments(channel_info, max_comments_per_video=10)

    # Assertions
    assert result is not None
    assert result['video_id'][0].get('comments_disabled', False) is True 