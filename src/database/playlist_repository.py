"""
Playlist repository module for interacting with YouTube playlist data in the SQLite database.
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json
import os

from src.utils.debug_utils import debug_log
from src.database.base_repository import BaseRepository

def handle_missing_api_field(field_name: str, column_type: str = 'TEXT') -> Any:
    """
    Handle missing API fields by returning appropriate default values for playlists table.
    This helps distinguish between fields that are truly missing from the API response
    vs. fields that are not being mapped correctly.
    
    Args:
        field_name: The database column name
        column_type: The SQLite column type (TEXT, INTEGER, BOOLEAN, etc.)
    
    Returns:
        Appropriate default value based on the field semantics
    """
    # Fields that should explicitly indicate "not provided by API"
    api_provided_fields = {
        'snippet_defaultLanguage', 'snippet_channelTitle', 'snippet_localized_title', 
        'snippet_localized_description', 'snippet_tags', 'status_privacyStatus', 
        'status_made_for_kids', 'player_embedHtml'
    }
    
    # Complex fields that should be empty objects/arrays when missing
    complex_fields = {
        'localizations': '{}',  # Empty JSON object
        'snippet_tags': '[]',  # Empty JSON array
        'snippet_thumbnails': '{}'  # Empty JSON object
    }
    
    if field_name in api_provided_fields:
        return "NOT_PROVIDED_BY_API"
    elif field_name in complex_fields:
        return complex_fields[field_name]
    elif column_type == 'INTEGER':
        return None
    elif column_type == 'BOOLEAN':
        return False
    else:
        return None

# Define a canonical mapping of database columns to API fields
CANONICAL_FIELD_MAP = {
    # Basic info - map DB columns to flattened API field names
    'playlist_id': 'id',
    
    # IMPORTANT: We're standardizing on the prefixed field names (snippet_title, etc.)
    # The non-prefixed fields (title, description, etc.) are deprecated
    # but kept for backward compatibility
    'channel_id': 'snippet_channelId',  # Use snippet_channelId instead
    'title': 'snippet_title',  # Use snippet_title instead
    'description': 'snippet_description',  # Use snippet_description instead
    
    # Direct mappings to flattened API field names
    'kind': 'kind',
    'etag': 'etag',
    
    # Snippet fields - these are the preferred fields to use
    'snippet_publishedAt': 'snippet_publishedAt',
    'snippet_channelId': 'snippet_channelId',
    'snippet_title': 'snippet_title',
    'snippet_description': 'snippet_description',
    'snippet_thumbnails': 'snippet_thumbnails',
    'snippet_channelTitle': 'snippet_channelTitle',
    'snippet_defaultLanguage': 'snippet_defaultLanguage',
    'snippet_localized_title': 'snippet_localized_title',
    'snippet_localized_description': 'snippet_localized_description',
    
    # Status fields
    'status_privacyStatus': 'status_privacyStatus',
    'status_made_for_kids': 'status_madeForKids',
    
    # Content details
    'contentDetails_itemCount': 'contentDetails_itemCount',
    
    # Player info
    'player_embedHtml': 'player_embedHtml',
    
    # Localizations
    'localizations': 'localizations',
    
    # Type field (for uploads playlists)
    'type': 'type'
}

class PlaylistRepository(BaseRepository):
    """Repository for managing YouTube playlist data in the SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the repository with the database path."""
        self.db_path = db_path
        
    def get_by_id(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a playlist by its ID.
        
        Args:
            playlist_id: The YouTube playlist ID
            
        Returns:
            Optional[Dict[str, Any]]: The playlist data as a dictionary, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use Row to access by column name
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM playlists WHERE playlist_id = ?", (playlist_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            debug_log(f"Error retrieving playlist by ID {playlist_id}: {str(e)}", e)
            return None
    
    def flatten_dict(self, d, parent_key='', sep='.'):
        """Recursively flattens a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def store_playlist_data(self, playlist: dict) -> bool:
        """
        Save playlist data to SQLite database and insert full API response into playlists_history.
        
        Args:
            playlist: Dictionary containing playlist data (must include playlist_id and channel_id)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # --- Flatten the full raw API response ---
                raw_api = playlist.get('raw_playlist_info', playlist)
                
                # Flatten the raw API response using dot notation
                flat_api = self.flatten_dict(raw_api)
                
                # Convert dot notation to underscore for direct mapping
                flat_api_underscore = {k.replace('.', '_'): v for k, v in flat_api.items()}
                
                # --- Get all columns in the playlists table ---
                cursor.execute("PRAGMA table_info(playlists)")
                table_info = cursor.fetchall()
                existing_cols = set(row[1] for row in table_info)
                column_types = {row[1]: row[2] for row in table_info}
                
                db_row = {}
                
                # --- Map each database column to the correct flattened API field ---
                for col in existing_cols:
                    if col in ['created_at', 'updated_at']:
                        continue
                    
                    # Get the corresponding flattened API field from canonical mapping
                    api_field = CANONICAL_FIELD_MAP.get(col)
                    value = None
                    
                    if api_field and api_field in flat_api_underscore:
                        # Found the field in API response
                        value = flat_api_underscore[api_field]
                        debug_log(f"[DB MAPPING] {col} -> {api_field} = {str(value)[:100]}")
                    else:
                        # Field not found in API response
                        value = handle_missing_api_field(col, column_types.get(col, 'TEXT'))
                        if value == "NOT_PROVIDED_BY_API":
                            debug_log(f"[DB MISSING] {col} not provided by API")
                        else:
                            debug_log(f"[DB DEFAULT] {col} using default: {value}")
                    
                    # Handle JSON serialization for complex fields
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    
                    db_row[col] = value
                
                # Handle duplicate fields - ensure consistency
                # For fields that exist in both forms (title/snippet_title, etc.)
                duplicate_mappings = {
                    ('title', 'snippet_title'): 'snippet_title',
                    ('description', 'snippet_description'): 'snippet_description', 
                    ('channel_id', 'snippet_channelId'): 'snippet_channelId'
                }
                
                # Sync duplicate fields to ensure consistency
                for field_group, api_source in duplicate_mappings.items():
                    if api_source in flat_api_underscore:
                        api_value = flat_api_underscore[api_source]
                        for field in field_group:
                            if field in existing_cols:
                                db_row[field] = api_value
                                debug_log(f"[DB SYNC] Set {field} = {str(api_value)[:50]}")
                
                # Prepare columns and values for SQL insert
                columns = [col for col in existing_cols if col not in ['created_at', 'updated_at']]
                values = [db_row.get(col) for col in columns]
                
                debug_log(f"[DB INSERT] Final playlist insert columns: {columns}")
                debug_log(f"[DB INSERT] Final playlist insert values: {values}")
                
                if not columns:
                    debug_log("[DB WARNING] No columns to insert for playlist.")
                    return False
                
                placeholders = ','.join(['?'] * len(columns))
                update_clause = ','.join([f'{col}=excluded.{col}' for col in columns])
                
                cursor.execute(f'''
                    INSERT INTO playlists ({','.join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT(playlist_id) DO UPDATE SET {update_clause}, updated_at=CURRENT_TIMESTAMP
                ''', values)
                
                # --- Insert full JSON into playlists_history only ---
                now = datetime.utcnow().isoformat()
                raw_playlist_info = json.dumps(raw_api)
                
                cursor.execute('''
                    INSERT INTO playlists_history (playlist_id, fetched_at, raw_playlist_info)
                    VALUES (?, ?, ?)
                ''', (db_row.get('playlist_id'), now, raw_playlist_info))
                
                conn.commit()
                
                debug_log(f"Inserted/updated playlist: {db_row.get('playlist_id')} and saved to playlists_history.")
                return True
                
        except Exception as e:
            debug_log(f"Exception in store_playlist_data: {str(e)}")
            return False
    
    def get_uploads_playlist_id(self, channel_id: str) -> str:
        """
        Fetch the uploads playlist ID for a channel from the playlists table.
        
        Args:
            channel_id: The YouTube channel ID
            
        Returns:
            str: The uploads playlist ID, or empty string if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT playlist_id FROM playlists WHERE channel_id = ? AND type = 'uploads'", (channel_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                debug_log(f"Found uploads playlist_id for channel_id={channel_id}: {row[0]}")
                return row[0]
                
            debug_log(f"No uploads playlist_id found for channel_id={channel_id}")
            return ''
            
        except Exception as e:
            debug_log(f"Exception in get_uploads_playlist_id: {str(e)}")
            return ''
    
    def get_by_channel_id(self, channel_id: str) -> List[Dict[str, Any]]:
        """
        Get all playlists for a specific channel.
        
        Args:
            channel_id: The YouTube channel ID
            
        Returns:
            list: A list of playlist data dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM playlists WHERE channel_id = ?", (channel_id,))
            rows = cursor.fetchall()
            
            playlists = [dict(row) for row in rows]
            
            conn.close()
            
            return playlists
            
        except Exception as e:
            debug_log(f"Exception in get_by_channel_id: {str(e)}")
            return []
