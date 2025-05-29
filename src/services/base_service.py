"""
Base service class that defines the common interface and functionality for all services.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseService(ABC):
    """
    Abstract base class for all service implementations.
    Defines common methods and utilities for services.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service with configuration.
        
        Args:
            config (dict, optional): Configuration dictionary for the service
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialize()
    
    def _initialize(self) -> None:
        """
        Initialize the service. Override in subclasses if needed.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the service is available and properly configured.
        
        Returns:
            bool: True if the service is available, False otherwise
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current service configuration.
        
        Returns:
            dict: The current configuration
        """
        return self.config
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update the service configuration.
        
        Args:
            new_config (dict): New configuration values to apply
        """
        self.config.update(new_config)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics and statistics.
        
        Returns:
            dict: Metrics and statistics for the service
        """
        return {
            'service_name': self.__class__.__name__,
            'is_available': self.is_available()
        }
    
    def validate_input(self, input_data: Any, required_keys: Optional[List[str]] = None) -> bool:
        """
        Validate input data for the service.
        
        Args:
            input_data: The input data to validate
            required_keys: List of required keys if input_data is a dictionary
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
        if input_data is None:
            return False
            
        if required_keys and isinstance(input_data, dict):
            return all(key in input_data for key in required_keys)
            
        return True
    
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
    
    def log_info(self, message: str) -> None:
        """
        Log an informational message.
        
        Args:
            message: The message to log
        """
        self.logger.info(message)
    
    def log_debug(self, message: str) -> None:
        """
        Log a debug message.
        
        Args:
            message: The message to log
        """
        self.logger.debug(message) 