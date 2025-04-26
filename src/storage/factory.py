"""
Factory module for creating storage provider instances.
"""
import os
from pathlib import Path

class StorageFactory:
    """
    Factory class for creating storage provider instances.
    This centralizes the creation of different storage backends.
    """
    
    @staticmethod
    def get_storage_provider(storage_type, config=None):
        """
        Returns a storage provider instance based on the requested type.
        
        Args:
            storage_type (str): The type of storage provider to create.
                                Options: "SQLite Database", "Local Storage (JSON)",
                                "MongoDB", "PostgreSQL"
            config (Settings, optional): Application configuration
        
        Returns:
            object: An instance of the requested storage provider
        """
        if storage_type == "SQLite Database":
            from src.database.sqlite import SQLiteDatabase
            sqlite_path = config.sqlite_db_path if config else Path("./data/youtube_data.db")
            return SQLiteDatabase(sqlite_path)
            
        elif storage_type == "Local Storage (JSON)":
            from src.storage.local_storage import LocalStorage
            data_dir = config.data_dir if config else Path("./data")
            return LocalStorage(data_dir)
            
        elif storage_type == "MongoDB":
            from src.database.mongodb import MongoDB
            mongo_uri = os.getenv('MONGO_URI')
            if not mongo_uri:
                raise ValueError("MongoDB URI not found in environment variables")
            return MongoDB(mongo_uri)
            
        elif storage_type == "PostgreSQL":
            from src.database.postgres import PostgreSQL
            return PostgreSQL(
                host=os.getenv('PG_HOST'),
                user=os.getenv('PG_USER'),
                password=os.getenv('PG_PASSWORD'),
                database=os.getenv('PG_DATABASE'),
                port=os.getenv('PG_PORT', '5432')
            )
        
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")