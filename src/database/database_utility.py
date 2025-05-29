"""
Database utility module for SQLite database maintenance operations.
"""
import sqlite3
import shutil
from datetime import datetime
from typing import Optional, Union, Dict, List, Any

from src.utils.debug_utils import debug_log
from src.database.base_repository import BaseRepository

class DatabaseUtility(BaseRepository):
    """Utility class for SQLite database maintenance operations."""
    
    def __init__(self, db_path: str):
        """Initialize the utility with the database path."""
        self.db_path = db_path
    
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Not applicable for DatabaseUtility, but implemented for interface compatibility.
        
        Args:
            id: Entity ID (not used)
            
        Returns:
            None: This method always returns None for DatabaseUtility
        """
        debug_log("get_by_id is not applicable for DatabaseUtility")
        return None
    
    def clear_cache(self) -> bool:
        """
        Clear any database caches or temporary data
        
        This method:
        1. Releases any connection pools
        2. Runs VACUUM to optimize the database
        3. Clears any prepared statement caches
        
        Returns:
            bool: True if successful, False otherwise
        """
        debug_log("Clearing database caches")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Run PRAGMA statements to clear SQLite's internal caches
            cursor.execute("PRAGMA cache_size = 0")  # Clear page cache
            cursor.execute("PRAGMA cache_size = -2000")  # Reset to default
            
            # Run VACUUM to optimize the database and reclaim space
            cursor.execute("VACUUM")
            
            # Execute a checkpoint to ensure all changes are written to disk
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            debug_log("Database caches cleared successfully")
            return True
        except Exception as e:
            debug_log(f"Error clearing database caches: {str(e)}", e)
            return False

    def continue_iteration(self, channel_id: str, max_iterations: int = 3, time_threshold_days: int = 7) -> bool:
        """
        Determine if data collection should continue for a given channel.
        
        Args:
            channel_id (str): The YouTube channel ID to check
            max_iterations (int): Maximum number of iterations allowed for a channel
            time_threshold_days (int): Number of days to consider for recent iterations
            
        Returns:
            bool: True if iteration should continue, False otherwise
        """
        debug_log(f"Checking if data collection should continue for channel: {channel_id}")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if the iteration_history table exists
            cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='iteration_history'
            ''')
            
            if not cursor.fetchone():
                # Create the iteration_history table if it doesn't exist
                cursor.execute('''
                CREATE TABLE iteration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    iteration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    metrics_changed BOOLEAN DEFAULT FALSE
                )
                ''')
                conn.commit()
                debug_log("Created iteration_history table")
            
            # Get current timestamp in SQLite format
            import datetime
            current_time = datetime.datetime.now()
            time_threshold = current_time - datetime.timedelta(days=time_threshold_days)
            threshold_timestamp = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
            
            # Count recent iterations for this channel
            cursor.execute('''
            SELECT COUNT(*) FROM iteration_history
            WHERE channel_id = ? AND iteration_date > ?
            ''', (channel_id, threshold_timestamp))
            
            recent_iterations = cursor.fetchone()[0]
            
            # Record this iteration attempt
            cursor.execute('''
            INSERT INTO iteration_history (channel_id)
            VALUES (?)
            ''', (channel_id,))
            
            # Get the ID of the newly inserted record
            iteration_id = cursor.lastrowid
            
            # Commit the changes
            conn.commit()
            
            # Check if we should continue
            should_continue = recent_iterations < max_iterations
            
            # Update the status if we're not continuing
            if not should_continue:
                cursor.execute('''
                UPDATE iteration_history
                SET status = 'skipped - max iterations reached'
                WHERE id = ?
                ''', (iteration_id,))
                conn.commit()
                debug_log(f"Skipping iteration for channel {channel_id} - maximum iterations reached")
            
            # Close the connection
            conn.close()
            
            return should_continue
            
        except Exception as e:
            debug_log(f"Exception in continue_iteration: {str(e)}", e)
            # Default to continuing if there's an error
            return True

    def clear_all_data(self) -> bool:
        """
        Clear all data from the database by dropping and recreating all tables.
        
        This is a destructive operation and should be used with caution,
        primarily for testing purposes.
        
        Returns:
            bool: True if successful, False otherwise
        """
        debug_log("WARNING: Clearing all data from the database")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, back up the database
            import shutil
            from datetime import datetime
            
            # Create backup filename with timestamp
            backup_path = f"{self.db_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            
            # Close connection to allow backup
            conn.close()
            
            # Create backup
            shutil.copy2(self.db_path, backup_path)
            debug_log(f"Created database backup at: {backup_path}")
            
            # Reconnect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Drop all tables in the correct order to respect foreign keys
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # First drop tables with foreign key dependencies
            tables_to_drop = [
                "comments", 
                "video_locations", 
                "videos", 
                "channels",
                "iteration_history"
            ]
            
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    debug_log(f"Dropped table: {table}")
                except Exception as e:
                    debug_log(f"Error dropping table {table}: {str(e)}")
            
            # Commit changes
            conn.commit()
            
            # Re-initialize the database tables
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.close()
            
            # Return True to indicate success, actual table recreation will be handled by initialize_db
            return True
                
        except Exception as e:
            debug_log(f"Error clearing database: {str(e)}", e)
            return False

    def get_connection(self):
        """
        Get a direct SQLite database connection.
        This is useful for performing custom queries.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            debug_log(f"Error connecting to database: {str(e)}")
            return None
