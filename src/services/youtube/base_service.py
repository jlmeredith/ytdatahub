"""
Base service class with common functionality for YouTube services.
Provides foundation for all specialized YouTube service classes.
"""
import logging
from unittest.mock import MagicMock
from typing import Dict, List, Optional, Tuple, Union, Any

class BaseService:
    """
    Base service class with common functionality for YouTube services.
    """
    
    def __init__(self, api_key=None, api_client=None):
        """
        Initialize the base service.
        
        Args:
            api_key (str, optional): YouTube API key
            api_client (obj, optional): Existing API client to use
        """
        self.api_key = api_key
        self.api = api_client if api_client else None
        self.logger = logging.getLogger(__name__)
    
    def is_mock(self, obj):
        """
        Check if an object is a MagicMock (for test compatibility)
        
        Args:
            obj: The object to check
            
        Returns:
            bool: True if the object is a MagicMock, False otherwise
        """
        return isinstance(obj, MagicMock) if hasattr(MagicMock, '__module__') else False
