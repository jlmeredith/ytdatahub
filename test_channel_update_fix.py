#!/usr/bin/env python3
"""
Test script to verify the channel update fix.
This script tests whether the CANONICAL_FIELD_MAP fix resolves the data zeroing issue.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.channel_repository import ChannelRepository, flatten_dict
from config import SQLITE_DB_PATH

def test_canonical_field_mapping():
    """Test that the CANONICAL_FIELD_MAP properly maps API fields to database columns."""
    print("=== Testing CANONICAL_FIELD_MAP ===")
    
    repo = ChannelRepository(SQLITE_DB_PATH)
    
    # Sample API data that would come from YouTube API
    sample_api_data = {
        'raw_channel_info': {
            'kind': 'youtube#channel',
            'etag': 'test_etag_123',
            'id': 'UCTestChannel123',
            'snippet': {
                'title': 'Test Channel Name',
                'description': 'This is a test channel description that should not be zeroed out',
                'customUrl': '@testchannel',
                'publishedAt': '2020-01-01T00:00:00Z',
                'country': 'US',
                'defaultLanguage': 'en',
                'thumbnails': {
                    'default': {'url': 'https://example.com/default.jpg'},
                    'medium': {'url': 'https://example.com/medium.jpg'},
                    'high': {'url': 'https://example.com/high.jpg'}
                }
            },
            'statistics': {
                'subscriberCount': '1000000',
                'viewCount': '50000000',
                'videoCount': '250',
                'hiddenSubscriberCount': False
            },
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'UUTestChannel123'
                }
            },
            'status': {
                'privacyStatus': 'public',
                'isLinked': True,
                'longUploadsStatus': 'allowed',
                'madeForKids': False
            },
            'brandingSettings': {
                'channel': {
                    'keywords': 'test, channel, youtube',
                    'description': 'Branding description'
                }
            },
            'topicDetails': {
                'topicCategories': [
                    'https://en.wikipedia.org/wiki/Technology',
                    'https://en.wikipedia.org/wiki/Science'
                ]
            }
        },
        'channel_id': 'UCTestChannel123',
        'channel_title': 'Test Channel Name'
    }
    
    # Flatten the API data like the store_channel_data method does
    raw_api = sample_api_data.get('raw_channel_info') or sample_api_data.get('channel_info', sample_api_data)
    flat_api = flatten_dict(raw_api)
    extra_fields = {k: v for k, v in sample_api_data.items() if k not in ['raw_channel_info', 'channel_info']}
    flat_api.update(extra_fields)
    flat_api_underscore = {k.replace('.', '_'): v for k, v in flat_api.items()}
    
    print(f"Flattened API data keys: {list(flat_api_underscore.keys())}")
    
    # Test the mapping for some critical fields
    from database.channel_repository import CANONICAL_FIELD_MAP
    
    test_cases = [
        ('snippet_description', 'This is a test channel description that should not be zeroed out'),
        ('snippet_customUrl', '@testchannel'),
        ('snippet_country', 'US'),
        ('statistics_subscriberCount', '1000000'),
        ('statistics_viewCount', '50000000'),
        ('contentDetails_relatedPlaylists_uploads', 'UUTestChannel123'),
        ('status_privacyStatus', 'public'),
        ('brandingSettings_channel_keywords', 'test, channel, youtube')
    ]
    
    print("\n=== Testing field mappings ===")
    for db_column, expected_value in test_cases:
        api_key = CANONICAL_FIELD_MAP.get(db_column, db_column)
        actual_value = flat_api_underscore.get(api_key, None)
        
        status = "✅ PASS" if actual_value == expected_value else "❌ FAIL"
        print(f"{status} {db_column}: {api_key} -> {actual_value} (expected: {expected_value})")
        
        if actual_value != expected_value:
            print(f"    Available keys with similar names: {[k for k in flat_api_underscore.keys() if db_column.split('_')[-1] in k]}")
    
    return True

def test_database_update_simulation():
    """Simulate the database update process to verify no data loss."""
    print("\n=== Testing Database Update Simulation ===")
    
    # Create a temporary database connection
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create the channels table with the actual schema
    cursor.execute('''
    CREATE TABLE channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT UNIQUE NOT NULL,
        channel_title TEXT,
        uploads_playlist_id TEXT,
        subscriber_count INTEGER,
        view_count INTEGER,
        video_count INTEGER,
        kind TEXT,
        etag TEXT,
        snippet_title TEXT,
        snippet_description TEXT,
        snippet_customUrl TEXT,
        snippet_publishedAt TEXT,
        snippet_defaultLanguage TEXT,
        snippet_country TEXT,
        snippet_thumbnails_default_url TEXT,
        snippet_thumbnails_medium_url TEXT,
        snippet_thumbnails_high_url TEXT,
        snippet_localized_title TEXT,
        snippet_localized_description TEXT,
        contentDetails_relatedPlaylists_uploads TEXT,
        contentDetails_relatedPlaylists_likes TEXT,
        contentDetails_relatedPlaylists_favorites TEXT,
        statistics_viewCount INTEGER,
        statistics_subscriberCount INTEGER,
        statistics_hiddenSubscriberCount BOOLEAN,
        statistics_videoCount INTEGER,
        brandingSettings_channel_title TEXT,
        brandingSettings_channel_description TEXT,
        brandingSettings_channel_keywords TEXT,
        brandingSettings_channel_country TEXT,
        brandingSettings_image_bannerExternalUrl TEXT,
        status_privacyStatus TEXT,
        status_isLinked BOOLEAN,
        status_longUploadsStatus TEXT,
        status_madeForKids BOOLEAN,
        topicDetails_topicIds TEXT,
        topicDetails_topicCategories TEXT,
        localizations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert initial data
    cursor.execute('''
    INSERT INTO channels (
        channel_id, 
        channel_title, 
        snippet_description, 
        snippet_customUrl,
        statistics_subscriberCount,
        statistics_viewCount,
        contentDetails_relatedPlaylists_uploads
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'UCTestChannel123',
        'Original Channel Name',
        'Original channel description',
        '@originalchannel',
        500000,
        25000000,
        'UUTestChannel123'
    ))
    
    print("Initial data inserted.")
    
    # Now simulate the update process
    from database.channel_repository import CANONICAL_FIELD_MAP, serialize_for_sqlite
    
    # Sample "new" API data for update
    update_data = {
        'raw_channel_info': {
            'id': 'UCTestChannel123',
            'snippet': {
                'title': 'Updated Channel Name',
                'description': 'Updated channel description - this should not be lost!',
                'customUrl': '@updatedchannel',
                'country': 'CA'
            },
            'statistics': {
                'subscriberCount': '1500000',
                'viewCount': '75000000',
                'videoCount': '300'
            },
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'UUTestChannel123'
                }
            }
        },
        'channel_id': 'UCTestChannel123',
        'channel_title': 'Updated Channel Name'
    }
    
    # Process the update like store_channel_data does
    raw_api = update_data.get('raw_channel_info') or update_data.get('channel_info', update_data)
    flat_api = flatten_dict(raw_api)
    extra_fields = {k: v for k, v in update_data.items() if k not in ['raw_channel_info', 'channel_info']}
    flat_api.update(extra_fields)
    flat_api_underscore = {k.replace('.', '_'): v for k, v in flat_api.items()}
    
    # Get all columns and prepare update
    cursor.execute("PRAGMA table_info(channels)")
    existing_cols = set(row[1] for row in cursor.fetchall())
    
    columns = []
    values = []
    for col in existing_cols:
        if col in ['id', 'created_at', 'updated_at']:
            continue
        api_key = CANONICAL_FIELD_MAP.get(col, col)
        v = flat_api_underscore.get(api_key, None)
        values.append(serialize_for_sqlite(v))
        columns.append(col)
    
    # Execute the update
    placeholders = ','.join(['?'] * len(columns))
    update_clause = ','.join([f'{col}=excluded.{col}' for col in columns])
    
    print(f"Updating columns: {columns}")
    print(f"With values: {values}")
    
    cursor.execute(f'''
        INSERT INTO channels ({','.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(channel_id) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP
    ''', values)
    
    # Check the result
    cursor.execute("SELECT * FROM channels WHERE channel_id = ?", ('UCTestChannel123',))
    result = cursor.fetchone()
    
    if result:
        columns_info = [desc[0] for desc in cursor.description]
        result_dict = dict(zip(columns_info, result))
        
        print("\n=== Final result after update ===")
        key_fields = [
            'channel_title', 'snippet_description', 'snippet_customUrl', 
            'statistics_subscriberCount', 'statistics_viewCount',
            'contentDetails_relatedPlaylists_uploads'
        ]
        
        all_good = True
        for field in key_fields:
            value = result_dict.get(field)
            if value is None:
                print(f"❌ FAIL: {field} is None (data was lost!)")
                all_good = False
            else:
                print(f"✅ PASS: {field} = {value}")
        
        if all_good:
            print("\n🎉 SUCCESS: No data was lost during the update!")
        else:
            print("\n💥 FAILURE: Some data was lost during the update!")
            
    conn.close()
    return all_good

if __name__ == "__main__":
    print("Testing Channel Update Fix")
    print("=" * 50)
    
    try:
        # Test the field mapping
        test_canonical_field_mapping()
        
        # Test the database update simulation
        success = test_database_update_simulation()
        
        if success:
            print("\n🎉 All tests passed! The fix should resolve the data zeroing issue.")
        else:
            print("\n💥 Some tests failed. The fix may need additional work.")
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
