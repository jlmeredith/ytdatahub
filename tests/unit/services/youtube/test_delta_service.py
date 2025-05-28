import pytest
from unittest.mock import patch, MagicMock
from src.services.youtube.delta_service import DeltaService

def test_calculate_deltas_basic_metrics():
    """Test basic delta calculation for simple metrics."""
    # Setup
    delta_service = DeltaService()
    channel_data = {
        'channel_id': 'UC123',
        'subscribers': 1000,
        'views': 50000,
        'total_videos': 30
    }
    original_data = {
        'channel_id': 'UC123',
        'subscribers': 900,
        'views': 45000,
        'total_videos': 25
    }
    
    # Execute
    result = delta_service.calculate_deltas(channel_data, original_data)
    
    # Verify
    assert result['delta']['subscribers'] == {'old': 900, 'new': 1000, 'diff': 100}
    assert result['delta']['views'] == {'old': 45000, 'new': 50000, 'diff': 5000}
    assert result['delta']['total_videos'] == {'old': 25, 'new': 30, 'diff': 5}

def test_calculate_deltas_comprehensive_level():
    """Test comprehensive delta calculation with more fields."""
    # Setup
    delta_service = DeltaService()
    channel_data = {
        'channel_id': 'UC123',
        'subscribers': 1000,
        'views': 50000,
        'total_videos': 30,
        'channel_name': 'New Channel Name',
        'channel_description': 'Updated description'
    }
    original_data = {
        'channel_id': 'UC123',
        'subscribers': 900,
        'views': 45000,
        'total_videos': 25,
        'channel_name': 'Old Channel Name',
        'channel_description': 'Original description'
    }
    
    # Execute with comprehensive level
    options = {'comparison_level': 'comprehensive'}
    result = delta_service.calculate_deltas(channel_data, original_data, options)
    
    # Verify
    assert result['delta']['subscribers'] == {'old': 900, 'new': 1000, 'diff': 100}
    assert result['delta']['channel_name'] == {'old': 'Old Channel Name', 'new': 'New Channel Name'}
    assert result['delta']['channel_description'] == {'old': 'Original description', 'new': 'Updated description'}

def test_compare_all_fields_option():
    """Test that compare_all_fields option compares all available fields."""
    # Setup
    delta_service = DeltaService()
    channel_data = {
        'channel_id': 'UC123',
        'subscribers': 1000,
        'views': 50000,
        'total_videos': 30,
        'custom_field1': 'new value',
        'custom_field2': 100,
        'raw_channel_info': {
            'id': 'UC123',
            'snippet': {
                'title': 'New Channel Name',
                'customUrl': 'newchannel',
                'description': 'Updated description'
            }
        }
    }
    original_data = {
        'channel_id': 'UC123',
        'subscribers': 900,
        'views': 45000,
        'total_videos': 25,
        'custom_field1': 'old value',
        'custom_field3': 'only in original',
        'raw_channel_info': {
            'id': 'UC123',
            'snippet': {
                'title': 'Old Channel Name',
                'customUrl': 'oldchannel',
                'description': 'Original description'
            }
        }
    }
    
    # Execute with compare_all_fields=True
    options = {
        'comparison_level': 'standard',
        'compare_all_fields': True
    }
    result = delta_service.calculate_deltas(channel_data, original_data, options)
    
    # Verify standard fields are compared
    assert result['delta']['subscribers'] == {'old': 900, 'new': 1000, 'diff': 100}
    assert result['delta']['views'] == {'old': 45000, 'new': 50000, 'diff': 5000}
    assert result['delta']['total_videos'] == {'old': 25, 'new': 30, 'diff': 5}
    
    # Verify custom fields are also compared when compare_all_fields is true
    assert 'custom_field1' in result['delta']
    assert result['delta']['custom_field1'] == {'old': 'old value', 'new': 'new value'}
    
    # Verify fields only in original are tracked
    assert 'custom_field3' in result['delta']
    assert result['delta']['custom_field3'] == {'old': 'only in original', 'new': None}
    
    # Verify fields only in new data are tracked
    assert 'custom_field2' in result['delta']
    assert result['delta']['custom_field2'] == {'old': None, 'new': 100}

def test_video_deltas_with_compare_all_fields():
    """Test that video deltas are calculated properly with compare_all_fields option."""
    # Setup
    delta_service = DeltaService()
    
    channel_data = {
        'channel_id': 'UC123',
        'video_id': [
            {
                'video_id': 'vid1',
                'title': 'Updated Video',
                'views': 1500,
                'likes': 100,
                'comment_count': 30,
                'custom_video_field': 'new value',
                'another_custom_field': 50
            }
        ]
    }
    
    original_data = {
        'channel_id': 'UC123',
        'video_id': [
            {
                'video_id': 'vid1',
                'title': 'Original Video',
                'views': 1000,
                'likes': 80,
                'comment_count': 20,
                'custom_video_field': 'old value',
                'only_in_original': 'some value'
            }
        ]
    }
    
    # Execute with compare_all_fields=True
    options = {
        'comparison_level': 'basic',  # Even with basic, all fields should be compared
        'compare_all_fields': True
    }
    result = delta_service.calculate_deltas(channel_data, original_data, options)
    
    # Verify basic video metrics are compared
    assert 'video_delta' in result
    assert len(result['video_delta']['updated_videos']) == 1
    updated_video = result['video_delta']['updated_videos'][0]
    assert updated_video['video_id'] == 'vid1'
    assert updated_video['views_delta'] == 500
    assert updated_video['likes_delta'] == 20
    assert updated_video['comment_delta'] == 10
    
    # Verify custom fields are also compared due to compare_all_fields
    assert 'custom_video_field' in updated_video
    assert updated_video['custom_video_field'] == {'old': 'old value', 'new': 'new value'}
    
    # Fields only in new data
    assert 'another_custom_field' in updated_video
    assert updated_video['another_custom_field'] == {'old': None, 'new': 50}
    
    # Fields only in original data
    assert 'only_in_original' in updated_video
    assert updated_video['only_in_original'] == {'old': 'some value', 'new': None} 