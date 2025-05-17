"""
Base repository interface for the repository pattern implementation.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class BaseRepository(ABC):
    """Base abstract class for all repository implementations."""
    
    @abstractmethod
    def __init__(self, db_path: str):
        """
        Initialize the repository with the database path.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an entity by its database ID.
        
        Args:
            id: The database ID of the entity
            
        Returns:
            Optional[Dict[str, Any]]: The entity data as a dictionary, or None if not found
        """
        pass
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the results as a list of dictionaries.
        
        Args:
            query: The SQL query to execute
            params: The parameters to substitute into the query
            
        Returns:
            List[Dict[str, Any]]: The query results as a list of dictionaries
        """
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use Row to access by column name
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return results
        except Exception as e:
            from src.utils.helpers import debug_log
            debug_log(f"Error executing query: {str(e)}", e)
            return []
    
    def execute_transaction(self, queries_and_params: List[tuple]) -> bool:
        """
        Execute multiple SQL queries as a single transaction.
        
        Args:
            queries_and_params: List of (query, params) tuples to execute
            
        Returns:
            bool: True if successful, False otherwise
        """
        import sqlite3
        from src.utils.helpers import debug_log
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for query, params in queries_and_params:
                cursor.execute(query, params)
                
            conn.commit()
            return True
        except Exception as e:
            debug_log(f"Transaction error: {str(e)}", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
