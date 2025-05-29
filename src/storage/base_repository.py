"""
Base repository class for data storage operations.
"""
from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional, List, Union

class BaseRepository(ABC):
    """
    Abstract base class for repository implementations.
    Defines the common interface for data storage operations.
    """
    
    def __init__(self, storage_provider: Any):
        """
        Initialize the repository with a storage provider.
        
        Args:
            storage_provider: The storage backend to use
        """
        self.storage = storage_provider
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: The ID of the entity to retrieve
            
        Returns:
            dict: The entity or None if not found
        """
        pass
    
    @abstractmethod
    def save(self, entity: Dict[str, Any]) -> bool:
        """
        Save an entity.
        
        Args:
            entity: The entity to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all entities.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            list: List of entities
        """
        pass
    
    @abstractmethod
    def find_by_field(self, field_name: str, field_value: Any) -> List[Dict[str, Any]]:
        """
        Find entities by field value.
        
        Args:
            field_name: The field to search
            field_value: The value to search for
            
        Returns:
            list: List of matching entities
        """
        pass
    
    def validate_entity(self, entity: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate an entity against required fields.
        
        Args:
            entity: The entity to validate
            required_fields: List of required field names
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not entity or not isinstance(entity, dict):
            return False
            
        return all(field in entity for field in required_fields)
    
    def log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        Log an error message.
        
        Args:
            message: The error message
            exception: The exception that caused the error, if any
        """
        if exception:
            self.logger.error(f"{message}: {str(exception)}")
        else:
            self.logger.error(message)
            
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage provider.
        
        Returns:
            dict: Information about the storage provider
        """
        if hasattr(self.storage, 'get_info'):
            return self.storage.get_info()
        else:
            return {
                'provider_type': self.storage.__class__.__name__,
                'status': 'active'
            } 