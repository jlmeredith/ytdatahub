import pytest
import pandas as pd
from src.analysis.comment_analyzer import CommentAnalyzer

@pytest.fixture
def analyzer():
    return CommentAnalyzer()

def test_no_comments_returns_empty(analyzer):
    channel_data = {}
    result = analyzer.get_comment_analysis(channel_data)
    assert result['total_comments'] == 0
    assert result['df'] is None

def test_top_level_comments(analyzer):
    channel_data = {
        'comments': {
            'video1': [
                {
                    'comment_id': 'c1',
                    'comment_author': 'Alice',
                    'comment_text': 'Great video!',
                    'comment_published_at': '2023-01-01T12:00:00Z',
                    'like_count': 5
                }
            ]
        }
    }
    result = analyzer.get_comment_analysis(channel_data)
    assert result['total_comments'] == 1
    assert isinstance(result['df'], pd.DataFrame)
    assert result['df'].iloc[0]['Author'] == 'Alice'
    assert result['df'].iloc[0]['Text'] == 'Great video!'
    assert result['df'].iloc[0]['Likes'] == 5
    assert not result['df'].iloc[0]['Is Reply']

def test_video_embedded_comments(analyzer):
    channel_data = {
        'videos': [
            {
                'id': 'video2',
                'snippet': {'title': 'Test Video', 'publishedAt': '2023-01-02T12:00:00Z'},
                'comments': [
                    {
                        'comment_id': 'c2',
                        'comment_author': 'Bob',
                        'comment_text': 'Nice!',
                        'comment_published_at': '2023-01-02T13:00:00Z',
                        'like_count': 2
                    }
                ]
            }
        ]
    }
    result = analyzer.get_comment_analysis(channel_data)
    assert result['total_comments'] == 1
    assert result['df'].iloc[0]['Author'] == 'Bob'
    assert result['df'].iloc[0]['Video'] == 'Test Video'

def test_comment_with_reply(analyzer):
    channel_data = {
        'comments': {
            'video3': [
                {
                    'comment_id': 'c3',
                    'comment_author': 'Carol',
                    'comment_text': 'First!',
                    'comment_published_at': '2023-01-03T12:00:00Z',
                    'like_count': 1,
                    'snippet': {
                        'topLevelComment': {
                            'snippet': {
                                'authorDisplayName': 'Carol',
                                'textDisplay': 'First!',
                                'publishedAt': '2023-01-03T12:00:00Z',
                                'likeCount': 1
                            }
                        }
                    }
                },
                {
                    'comment_id': 'c3.1',
                    'comment_author': 'Dave',
                    'comment_text': '[REPLY] Thanks!',
                    'comment_published_at': '2023-01-03T12:05:00Z',
                    'like_count': 0,
                    'parent_id': 'c3',
                    'snippet': {
                        'topLevelComment': {
                            'snippet': {
                                'authorDisplayName': 'Dave',
                                'textDisplay': '[REPLY] Thanks!',
                                'publishedAt': '2023-01-03T12:05:00Z',
                                'likeCount': 0
                            }
                        }
                    }
                }
            ]
        }
    }
    result = analyzer.get_comment_analysis(channel_data)
    assert result['total_comments'] == 2
    df = result['df']
    if df.empty:
        print('DF is empty:', df)
    parent_rows = df[df['Comment ID'] == 'c3']
    reply_rows = df[df['Comment ID'] == 'c3.1']
    if parent_rows.empty or reply_rows.empty:
        print('Parent rows:', parent_rows)
        print('Reply rows:', reply_rows)
    parent = parent_rows.iloc[0] if not parent_rows.empty else None
    reply = reply_rows.iloc[0] if not reply_rows.empty else None
    assert parent is not None
    assert reply is not None
    assert not parent['Is Reply']
    assert reply['Is Reply']
    assert reply['Parent ID'] == 'c3'
    assert reply['Text'] == 'Thanks!'

def test_edge_case_missing_fields(analyzer):
    channel_data = {
        'comments': {
            'video4': [
                {
                    # Missing author, text, published, likes
                    'comment_id': 'c4'
                }
            ]
        }
    }
    result = analyzer.get_comment_analysis(channel_data)
    assert result['total_comments'] == 1
    row = result['df'].iloc[0]
    assert row['Author'] == 'Unknown'
    assert row['Text'] == 'Unknown'
    assert row['Likes'] == 0
    assert row['Text Length'] == len('Unknown')

def test_temporal_analysis(analyzer):
    channel_data = {
        'comments': {
            'video5': [
                {
                    'comment_id': 'c5',
                    'comment_author': 'Eve',
                    'comment_text': 'Temporal!',
                    'comment_published_at': '2023-01-05T15:00:00Z',
                    'like_count': 3,
                    'snippet': {
                        'topLevelComment': {
                            'snippet': {
                                'authorDisplayName': 'Eve',
                                'textDisplay': 'Temporal!',
                                'publishedAt': '2023-01-05T15:00:00Z',
                                'likeCount': 3
                            }
                        }
                    }
                }
            ]
        }
    }
    result = analyzer.get_comment_analysis(channel_data)
    temporal = result['temporal_data']
    assert temporal is not None
    # Check for expected keys
    assert 'daily' in temporal
    assert 'monthly' in temporal
    assert 'hourly' in temporal
    assert 'day_of_week' in temporal
    # Check DataFrame columns
    assert set(temporal['daily'].columns) == {'Date', 'Count'}
    assert set(temporal['monthly'].columns) >= {'Year', 'Month', 'Month_Name', 'Count', 'YearMonth'}
    assert set(temporal['hourly'].columns) == {'Hour', 'Count'}
    assert set(temporal['day_of_week'].columns) >= {'Day', 'Count'} 