"""
Factory module for creating repository instances.
"""
import logging
from typing import Dict, Any, Optional, Union, Type

from src.storage.base_repository import BaseRepository
from src.storage.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)

class RepositoryFactory:
    """
    Factory class for creating repository instances.
    This centralizes the creation of different repository objects.
    """
    
    _instances = {}  # Cache for repository instances
    
    @staticmethod
    def get_repository(repository_type: str, storage_type: str = "SQLite Database", 
                      config: Optional[Dict[str, Any]] = None) -> BaseRepository:
        """
        Returns a repository instance based on the requested type.
        
        Args:
            repository_type (str): The type of repository to create.
                                  Options: "channel", "video", "comment", "playlist"
            storage_type (str): The type of storage to use (default: SQLite Database)
            config (dict, optional): Configuration for the repository
        
        Returns:
            BaseRepository: An instance of the requested repository
        """
        config = config or {}
        
        # Normalize repository type string
        repository_type_lower = repository_type.lower()
        
        # Create cache key that includes both repository and storage type
        cache_key = f"{repository_type_lower}_{storage_type}"
        
        # Check if we already have a cached instance
        if cache_key in RepositoryFactory._instances:
            return RepositoryFactory._instances[cache_key]
        
        # Create the requested repository
        if repository_type_lower in ['channel', 'channel_repository']:
            repository = ChannelRepository(storage_type, config)
            
        # Add other repository types as they are implemented
        elif repository_type_lower in ['video', 'video_repository']:
            # This is a placeholder - implement VideoRepository
            raise NotImplementedError("VideoRepository not yet implemented")
            
        elif repository_type_lower in ['comment', 'comment_repository']:
            # This is a placeholder - implement CommentRepository
            raise NotImplementedError("CommentRepository not yet implemented")
            
        elif repository_type_lower in ['playlist', 'playlist_repository']:
            # This is a placeholder - implement PlaylistRepository
            raise NotImplementedError("PlaylistRepository not yet implemented")
            
        else:
            raise ValueError(f"Unsupported repository type: {repository_type}")
            
        # Cache the instance for future use
        RepositoryFactory._instances[cache_key] = repository
        
        return repository
    
    @staticmethod
    def reset_instance(repository_type: str, storage_type: str = "SQLite Database") -> None:
        """
        Reset a cached repository instance.
        
        Args:
            repository_type (str): The type of repository to reset
            storage_type (str): The type of storage used by the repository
        """
        repository_type_lower = repository_type.lower()
        cache_key = f"{repository_type_lower}_{storage_type}"
        
        if cache_key in RepositoryFactory._instances:
            del RepositoryFactory._instances[cache_key]
            logger.debug(f"Reset repository instance: {cache_key}")
    
    @staticmethod
    def reset_all() -> None:
        """Reset all cached repository instances."""
        RepositoryFactory._instances.clear()
        logger.debug("Reset all repository instances") 