import pytest
from unittest.mock import MagicMock, patch
from src.api.youtube.channel_client import YouTubeChannelClient

@pytest.fixture
def mock_youtube():
    return MagicMock()

@pytest.fixture
def channel_client(mock_youtube):
    client = YouTubeChannelClient()
    client.youtube = mock_youtube
    client.is_initialized = MagicMock(return_value=True)
    return client

def test_get_channel_info_success(channel_client, mock_youtube):
    with patch('src.api.youtube.channel_client.clean_channel_id', return_value='UC123'):
        # Mock API response
        mock_response = {
            'items': [{
                'id': 'UC123',
                'snippet': {'title': 'Test Channel', 'description': 'Test Description'},
                'statistics': {'subscriberCount': '1000', 'viewCount': '5000', 'videoCount': '10'},
                'contentDetails': {'relatedPlaylists': {'uploads': 'UU123'}}
            }]
        }
        mock_youtube.channels().list().execute.return_value = mock_response

        # Call the method
        result = channel_client.get_channel_info('UC123')

        # Assertions
        assert result is not None
        assert result['channel_id'] == 'UC123'
        assert result['channel_name'] == 'Test Channel'
        assert result['subscribers'] == '1000'
        assert result['playlist_id'] == 'UU123'

def test_get_channel_info_not_found(channel_client, mock_youtube):
    with patch('src.api.youtube.channel_client.clean_channel_id', return_value='UC123'):
        # Mock empty response
        mock_youtube.channels().list().execute.return_value = {'items': []}

        # Call the method
        result = channel_client.get_channel_info('UC123')

        # Assertions
        assert result is None

def test_get_channel_by_username_success(channel_client, mock_youtube):
    # Mock API response
    mock_response = {
        'items': [{
            'id': 'UC123',
            'snippet': {'title': 'Test Channel', 'description': 'Test Description'},
            'statistics': {'subscriberCount': '1000', 'viewCount': '5000', 'videoCount': '10'},
            'contentDetails': {'relatedPlaylists': {'uploads': 'UU123'}}
        }]
    }
    mock_youtube.channels().list().execute.return_value = mock_response

    # Call the method
    result = channel_client.get_channel_by_username('testchannel')

    # Assertions
    assert result is not None
    assert result['channel_id'] == 'UC123'
    assert result['channel_name'] == 'Test Channel'

def test_get_channel_by_username_not_found(channel_client, mock_youtube):
    # Mock empty response
    mock_youtube.channels().list().execute.return_value = {'items': []}

    # Call the method
    result = channel_client.get_channel_by_username('testchannel')

    # Assertions
    assert result is None

def test_search_channel_success(channel_client, mock_youtube):
    with patch('src.api.youtube.channel_client.clean_channel_id', return_value='UC123'):
        # Mock API response
        mock_response = {
            'items': [
                {
                    'id': {'channelId': 'UC123'},
                    'snippet': {'title': 'Test Channel', 'description': 'Test Description'}
                }
            ]
        }
        mock_youtube.search().list().execute.return_value = mock_response
        mock_youtube.channels().list().execute.return_value = {
            'items': [{
                'id': 'UC123',
                'snippet': {'title': 'Test Channel', 'description': 'Test Description'},
                'statistics': {'subscriberCount': '1000', 'viewCount': '5000', 'videoCount': '10'},
                'contentDetails': {'relatedPlaylists': {'uploads': 'UU123'}}
            }]
        }

        # Call the method
        result = channel_client.search_channel('test')

        # Assertions
        assert len(result) == 1
        assert result[0]['channel_id'] == 'UC123'
        assert result[0]['channel_name'] == 'Test Channel'

def test_search_channel_no_results(channel_client, mock_youtube):
    with patch('src.api.youtube.channel_client.clean_channel_id', return_value='UC123'):
        # Mock empty response
        mock_youtube.search().list().execute.return_value = {'items': []}

        # Call the method
        result = channel_client.search_channel('test')

        # Assertions
        assert len(result) == 0 