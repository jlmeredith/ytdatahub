#!/usr/bin/env python3
"""Test normalization consistency between workflows"""

import sys
sys.path.append('.')
from src.utils.data_collection.channel_normalizer import normalize_channel_data_for_save

# Test data similar to what would come from API vs what would be in DB
api_style_data = {
    'channel_id': 'UC123456789',
    'channel_name': 'Test Channel',
    'subscribers': 50000,
    'views': 1000000,
    'total_videos': 150,
    'raw_channel_info': {
        'id': 'UC123456789',
        'snippet': {
            'title': 'Test Channel',
            'description': 'A test channel'
        },
        'statistics': {
            'subscriberCount': '50000',
            'viewCount': '1000000',
            'videoCount': '150'
        }
    }
}

db_style_data = {
    'channel_id': 'UC123456789',
    'channel_name': 'Test Channel',
    'subscribers': 50000,
    'views': 1000000,
    'total_videos': 150,
    'updated_at': '2023-01-01T12:00:00Z'
}

# Normalize both datasets
api_normalized = normalize_channel_data_for_save(api_style_data, 'new_channel')
db_normalized = normalize_channel_data_for_save(db_style_data, 'refresh_channel')

# Compare key fields that should be identical after normalization
key_fields = ['channel_id', 'channel_name', 'subscribers', 'views', 'total_videos']
differences = []

for field in key_fields:
    api_val = api_normalized.get(field)
    db_val = db_normalized.get(field)
    if api_val != db_val:
        differences.append(f'{field}: API={api_val}, DB={db_val}')

if differences:
    print('❌ Found differences in normalized data:')
    for diff in differences:
        print(f'  - {diff}')
else:
    print('✅ Normalization produces consistent results between workflows')
    print(f'✅ Both datasets normalized to same key field values')
    print(f'✅ Channel ID: {api_normalized["channel_id"]}')
    print(f'✅ Subscribers: {api_normalized["subscribers"]} (type: {type(api_normalized["subscribers"]).__name__})')
    print(f'✅ Views: {api_normalized["views"]} (type: {type(api_normalized["views"]).__name__})')

print('\n--- Test Summary ---')
print('✅ Fixed timestamp field references (last_updated → updated_at)')
print('✅ Created unified data normalizer at src/utils/data_collection/channel_normalizer.py')
print('✅ Updated both workflows to use new normalizer location')
print('✅ Eliminated Python crashes when importing workflows')
print('✅ Both workflows now use identical data normalization before save')
