import os
import tempfile
import sqlite3
import json
import pytest
from src.database.video_repository import VideoRepository

def full_video_api_response():
    """Return a full YouTube API video response with all fields populated."""
    return {
        'id': 'abc123xyz',
        'kind': 'youtube#video',
        'etag': 'etag123',
        'snippet': {
            'publishedAt': '2024-06-01T12:00:00Z',
            'channelId': 'chan_001',
            'title': 'Test Video',
            'description': 'A test video.',
            'channelTitle': 'Test Channel',
            'tags': ['tag1', 'tag2'],
            'categoryId': '22',
            'liveBroadcastContent': 'none',
            'defaultLanguage': 'en',
            'localized': {
                'title': 'Test Video (EN)',
                'description': 'A test video (localized).'
            },
            'defaultAudioLanguage': 'en',
            'thumbnails': {
                'default': {'url': 'url1', 'width': 120, 'height': 90},
                'medium': {'url': 'url2', 'width': 320, 'height': 180},
                'high': {'url': 'url3', 'width': 480, 'height': 360},
                'standard': {'url': 'url4', 'width': 640, 'height': 480},
                'maxres': {'url': 'url5', 'width': 1280, 'height': 720}
            }
        },
        'contentDetails': {
            'duration': 'PT10M',
            'dimension': '2d',
            'definition': 'hd',
            'caption': 'true',
            'licensedContent': True,
            'regionRestriction': {
                'allowed': ['US', 'CA'],
                'blocked': ['DE']
            },
            'contentRating': {'ytRating': 'ytAgeRestricted'},
            'projection': 'rectangular',
            'hasCustomThumbnail': True
        },
        'status': {
            'uploadStatus': 'processed',
            'failureReason': None,
            'rejectionReason': None,
            'privacyStatus': 'public',
            'publishAt': '2024-06-01T12:00:00Z',
            'license': 'youtube',
            'embeddable': True,
            'publicStatsViewable': True,
            'madeForKids': False
        },
        'statistics': {
            'viewCount': 12345,
            'likeCount': 678,
            'dislikeCount': 0,
            'favoriteCount': 0,
            'commentCount': 12
        },
        'player': {
            'embedHtml': '<iframe></iframe>',
            'embedHeight': 360,
            'embedWidth': 640
        },
        'topicDetails': {
            'topicIds': ['/m/01k8wb'],
            'relevantTopicIds': ['/m/02mjmr'],
            'topicCategories': ['https://en.wikipedia.org/wiki/Technology']
        },
        'liveStreamingDetails': {
            'actualStartTime': '2024-06-01T12:00:00Z',
            'actualEndTime': '2024-06-01T13:00:00Z',
            'scheduledStartTime': '2024-06-01T12:00:00Z',
            'scheduledEndTime': '2024-06-01T13:00:00Z',
            'concurrentViewers': 100,
            'activeLiveChatId': 'chat_001'
        },
        'localizations': {
            'en': {'title': 'Test Video', 'description': 'A test video.'},
            'es': {'title': 'Video de Prueba', 'description': 'Un video de prueba.'}
        }
    }

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        repo = VideoRepository(path)
        # Manually create the videos table with the full schema
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE videos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          youtube_id TEXT UNIQUE NOT NULL,
          kind TEXT,
          etag TEXT,
          channel_id TEXT,
          title TEXT,
          description TEXT,
          published_at TEXT,
          snippet_channel_id TEXT,
          snippet_channel_title TEXT,
          snippet_tags TEXT,
          snippet_category_id TEXT,
          snippet_live_broadcast_content TEXT,
          snippet_default_language TEXT,
          snippet_localized_title TEXT,
          snippet_localized_description TEXT,
          snippet_default_audio_language TEXT,
          snippet_thumbnails_default TEXT,
          snippet_thumbnails_medium TEXT,
          snippet_thumbnails_high TEXT,
          snippet_thumbnails_standard TEXT,
          snippet_thumbnails_maxres TEXT,
          content_details_duration TEXT,
          content_details_dimension TEXT,
          content_details_definition TEXT,
          content_details_caption TEXT,
          content_details_licensed_content BOOLEAN,
          content_details_region_restriction_allowed TEXT,
          content_details_region_restriction_blocked TEXT,
          content_details_content_rating TEXT,
          content_details_projection TEXT,
          content_details_has_custom_thumbnail BOOLEAN,
          status_upload_status TEXT,
          status_failure_reason TEXT,
          status_rejection_reason TEXT,
          status_privacy_status TEXT,
          status_publish_at TEXT,
          status_license TEXT,
          status_embeddable BOOLEAN,
          status_public_stats_viewable BOOLEAN,
          status_made_for_kids BOOLEAN,
          statistics_view_count INTEGER,
          statistics_like_count INTEGER,
          statistics_dislike_count INTEGER,
          statistics_favorite_count INTEGER,
          statistics_comment_count INTEGER,
          player_embed_html TEXT,
          player_embed_height INTEGER,
          player_embed_width INTEGER,
          topic_details_topic_ids TEXT,
          topic_details_relevant_topic_ids TEXT,
          topic_details_topic_categories TEXT,
          live_streaming_details_actual_start_time TEXT,
          live_streaming_details_actual_end_time TEXT,
          live_streaming_details_scheduled_start_time TEXT,
          live_streaming_details_scheduled_end_time TEXT,
          live_streaming_details_concurrent_viewers INTEGER,
          live_streaming_details_active_live_chat_id TEXT,
          localizations TEXT,
          fetched_at TEXT,
          updated_at TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE videos_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          video_id TEXT NOT NULL,
          fetched_at TEXT NOT NULL,
          raw_video_info TEXT NOT NULL
        )
        ''')
        conn.commit()
        conn.close()
        yield repo
    finally:
        os.remove(path)

def test_store_full_video_json(temp_db):
    repo = temp_db
    video_json = full_video_api_response()
    # Insert the video
    assert repo.store_video_data(video_json) is True
    # Fetch the row
    conn = sqlite3.connect(repo.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM videos WHERE youtube_id = ?', (video_json['id'],))
    row = cursor.fetchone()
    assert row is not None, 'Video row not found in DB'
    col_names = [desc[0] for desc in cursor.description]
    row_dict = dict(zip(col_names, row))
    # Check all fields are present and correctly stored (including JSON arrays/objects)
    assert row_dict['youtube_id'] == video_json['id']
    assert row_dict['kind'] == video_json['kind']
    assert row_dict['etag'] == video_json['etag']
    assert row_dict['channel_id'] == video_json['snippet']['channelId']
    assert row_dict['title'] == video_json['snippet']['title']
    assert row_dict['description'] == video_json['snippet']['description']
    assert row_dict['published_at'] == video_json['snippet']['publishedAt']
    assert row_dict['snippet_channel_id'] == video_json['snippet']['channelId']
    assert row_dict['snippet_channel_title'] == video_json['snippet']['channelTitle']
    assert json.loads(row_dict['snippet_tags']) == video_json['snippet']['tags']
    assert row_dict['snippet_category_id'] == video_json['snippet']['categoryId']
    assert row_dict['snippet_live_broadcast_content'] == video_json['snippet']['liveBroadcastContent']
    assert row_dict['snippet_default_language'] == video_json['snippet']['defaultLanguage']
    assert row_dict['snippet_localized_title'] == video_json['snippet']['localized']['title']
    assert row_dict['snippet_localized_description'] == video_json['snippet']['localized']['description']
    assert row_dict['snippet_default_audio_language'] == video_json['snippet']['defaultAudioLanguage']
    assert json.loads(row_dict['snippet_thumbnails_default']) == video_json['snippet']['thumbnails']['default']
    assert json.loads(row_dict['snippet_thumbnails_medium']) == video_json['snippet']['thumbnails']['medium']
    assert json.loads(row_dict['snippet_thumbnails_high']) == video_json['snippet']['thumbnails']['high']
    assert json.loads(row_dict['snippet_thumbnails_standard']) == video_json['snippet']['thumbnails']['standard']
    assert json.loads(row_dict['snippet_thumbnails_maxres']) == video_json['snippet']['thumbnails']['maxres']
    assert row_dict['content_details_duration'] == video_json['contentDetails']['duration']
    assert row_dict['content_details_dimension'] == video_json['contentDetails']['dimension']
    assert row_dict['content_details_definition'] == video_json['contentDetails']['definition']
    assert row_dict['content_details_caption'] == video_json['contentDetails']['caption']
    assert row_dict['content_details_licensed_content'] == int(video_json['contentDetails']['licensedContent'])
    assert json.loads(row_dict['content_details_region_restriction_allowed']) == video_json['contentDetails']['regionRestriction']['allowed']
    assert json.loads(row_dict['content_details_region_restriction_blocked']) == video_json['contentDetails']['regionRestriction']['blocked']
    assert json.loads(row_dict['content_details_content_rating']) == video_json['contentDetails']['contentRating']
    assert row_dict['content_details_projection'] == video_json['contentDetails']['projection']
    assert row_dict['content_details_has_custom_thumbnail'] == int(video_json['contentDetails']['hasCustomThumbnail'])
    assert row_dict['status_upload_status'] == video_json['status']['uploadStatus']
    assert row_dict['status_failure_reason'] == video_json['status']['failureReason']
    assert row_dict['status_rejection_reason'] == video_json['status']['rejectionReason']
    assert row_dict['status_privacy_status'] == video_json['status']['privacyStatus']
    assert row_dict['status_publish_at'] == video_json['status']['publishAt']
    assert row_dict['status_license'] == video_json['status']['license']
    assert row_dict['status_embeddable'] == int(video_json['status']['embeddable'])
    assert row_dict['status_public_stats_viewable'] == int(video_json['status']['publicStatsViewable'])
    assert row_dict['status_made_for_kids'] == int(video_json['status']['madeForKids'])
    assert row_dict['statistics_view_count'] == video_json['statistics']['viewCount']
    assert row_dict['statistics_like_count'] == video_json['statistics']['likeCount']
    assert row_dict['statistics_dislike_count'] == video_json['statistics']['dislikeCount']
    assert row_dict['statistics_favorite_count'] == video_json['statistics']['favoriteCount']
    assert row_dict['statistics_comment_count'] == video_json['statistics']['commentCount']
    assert row_dict['player_embed_html'] == video_json['player']['embedHtml']
    assert row_dict['player_embed_height'] == video_json['player']['embedHeight']
    assert row_dict['player_embed_width'] == video_json['player']['embedWidth']
    assert json.loads(row_dict['topic_details_topic_ids']) == video_json['topicDetails']['topicIds']
    assert json.loads(row_dict['topic_details_relevant_topic_ids']) == video_json['topicDetails']['relevantTopicIds']
    assert json.loads(row_dict['topic_details_topic_categories']) == video_json['topicDetails']['topicCategories']
    assert row_dict['live_streaming_details_actual_start_time'] == video_json['liveStreamingDetails']['actualStartTime']
    assert row_dict['live_streaming_details_actual_end_time'] == video_json['liveStreamingDetails']['actualEndTime']
    assert row_dict['live_streaming_details_scheduled_start_time'] == video_json['liveStreamingDetails']['scheduledStartTime']
    assert row_dict['live_streaming_details_scheduled_end_time'] == video_json['liveStreamingDetails']['scheduledEndTime']
    assert row_dict['live_streaming_details_concurrent_viewers'] == video_json['liveStreamingDetails']['concurrentViewers']
    assert row_dict['live_streaming_details_active_live_chat_id'] == video_json['liveStreamingDetails']['activeLiveChatId']
    assert json.loads(row_dict['localizations']) == video_json['localizations']
    # Check that fetched_at and updated_at are not null
    assert row_dict['fetched_at'] is not None, 'fetched_at should not be null after insert'
    assert row_dict['updated_at'] is not None, 'updated_at should not be null after insert' 