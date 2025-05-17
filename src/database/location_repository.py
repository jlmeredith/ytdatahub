"""
Location repository module for interacting with video location data in the SQLite database.
"""
import sqlite3
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

from src.utils.helpers import debug_log
from src.database.base_repository import BaseRepository

class LocationRepository(BaseRepository):
    """Repository for managing video location data in the SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the repository with the database path."""
        self.db_path = db_path
    
    def store_video_locations(self, locations: List[Dict[str, Any]], video_db_id: int) -> bool:
        """
        Save video location data to SQLite database.
        
        Args:
            locations: List of locations for a video
            video_db_id: The database ID of the video these locations belong to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not locations:
                return True
                
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for location in locations:
                location_type = location.get('location_type', '')
                location_name = location.get('location_name', '')
                confidence = float(location.get('confidence', 0.0))
                source = location.get('source', 'auto')
                created_at = location.get('created_at', '')
                
                # Use current timestamp if created_at is not provided
                if not created_at:
                    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Insert location data
                cursor.execute('''
                INSERT INTO video_locations (
                    video_id, location_type, location_name, confidence, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    video_db_id, location_type, location_name, confidence, source, created_at
                ))
            
            # Commit changes
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            debug_log(f"Error storing video location data: {str(e)}", e)
            return False
    
    def get_video_locations(self, video_db_id: int) -> List[Dict[str, Any]]:
        """
        Get all locations for a specific video.
        
        Args:
            video_db_id: The database ID of the video
            
        Returns:
            list: A list of location data dictionaries
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get locations for this video
            cursor.execute("""
                SELECT location_type, location_name, confidence, source, created_at
                FROM video_locations
                WHERE video_id = ?
            """, (video_db_id,))
            
            locations_rows = cursor.fetchall()
            
            locations = []
            for location_row in locations_rows:
                location_data = {
                    'location_type': location_row[0],
                    'location_name': location_row[1],
                    'confidence': location_row[2],
                    'source': location_row[3],
                    'created_at': location_row[4]
                }
                locations.append(location_data)
            
            conn.close()
            
            return locations
        except Exception as e:
            debug_log(f"Error getting video locations: {str(e)}", e)
            return []
            
    def get_locations_by_type(self, location_type: str) -> List[Dict[str, Any]]:
        """
        Get all locations of a specific type across all videos.
        
        Args:
            location_type: The type of location to filter by (e.g., 'country', 'city')
            
        Returns:
            list: A list of location data dictionaries with video information
        """
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all locations of the specified type with video info
            cursor.execute("""
                SELECT 
                    vl.location_name, 
                    vl.confidence, 
                    vl.source, 
                    v.youtube_id as video_id, 
                    v.title as video_title,
                    c.title as channel_name
                FROM 
                    video_locations vl
                JOIN 
                    videos v ON vl.video_id = v.id
                JOIN 
                    channels c ON v.channel_id = c.id
                WHERE 
                    vl.location_type = ?
                ORDER BY 
                    vl.location_name, vl.confidence DESC
            """, (location_type,))
            
            locations_rows = cursor.fetchall()
            
            locations = []
            for location_row in locations_rows:
                location_data = {
                    'name': location_row[0],
                    'confidence': location_row[1],
                    'source': location_row[2],
                    'video': {
                        'id': location_row[3],
                        'title': location_row[4]
                    },
                    'channel': location_row[5]
                }
                locations.append(location_data)
            
            conn.close()
            
            return locations
        except Exception as e:
            debug_log(f"Error getting locations by type: {str(e)}", e)
            return []

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a location by its database ID.
        
        Args:
            id: The database ID of the location
            
        Returns:
            Optional[Dict[str, Any]]: The location data as a dictionary, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use Row to access by column name
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM video_locations WHERE id = ?", (id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            debug_log(f"Error retrieving location by ID {id}: {str(e)}", e)
            return None
