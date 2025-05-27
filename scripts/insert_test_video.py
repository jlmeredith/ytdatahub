import os
import json
from src.database.video_repository import VideoRepository

def full_video_api_response():
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

def main():
    db_path = os.path.join('data', 'youtube_data.db')
    repo = VideoRepository(db_path)
    video_json = full_video_api_response()
    result = repo.store_video_data(video_json)
    print('Insert result:', result)

if __name__ == '__main__':
    main() 