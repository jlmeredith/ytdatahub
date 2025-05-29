"""
Factory module for creating service instances.
This ensures consistent creation and configuration of service objects.
"""
import os
import logging
from typing import Dict, Any, Optional, Union, Type

from src.services.youtube.youtube_service import YouTubeService
from src.services.youtube.channel_service import ChannelService
from src.services.youtube.video_service import VideoService
from src.services.youtube.comment_service import CommentService
from src.services.youtube.error_handling_service import ErrorHandlingService
from src.services.youtube.storage_service import StorageService
from src.services.youtube.delta_service import DeltaService

logger = logging.getLogger(__name__)

class ServiceFactory:
    """
    Factory class for creating service instances.
    This centralizes the creation of different service objects and ensures
    consistent configuration and dependency injection.
    """
    
    _instances = {}  # Cache for singleton service instances
    
    @staticmethod
    def get_service(service_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Returns a service instance based on the requested type.
        
        Args:
            service_type (str): The type of service to create.
                                Options: "youtube", "channel", "video", "comment",
                                "error", "storage", "delta"
            config (dict, optional): Configuration for the service
        
        Returns:
            object: An instance of the requested service
        """
        config = config or {}
        api_key = config.get('api_key') or os.getenv('YOUTUBE_API_KEY')
        
        # Normalize service type string
        service_type_lower = service_type.lower()
        
        # Check if we already have a cached instance
        if service_type_lower in ServiceFactory._instances:
            return ServiceFactory._instances[service_type_lower]
        
        # Create the requested service
        if service_type_lower in ['youtube', 'youtube_service']:
            service = YouTubeService(api_key=api_key)
            
        elif service_type_lower in ['channel', 'channel_service']:
            service = ChannelService(api_key=api_key)
            
        elif service_type_lower in ['video', 'video_service']:
            service = VideoService(api_key=api_key)
            
        elif service_type_lower in ['comment', 'comment_service']:
            service = CommentService(api_key=api_key)
            
        elif service_type_lower in ['error', 'error_service', 'error_handling']:
            service = ErrorHandlingService.get_instance()
            
        elif service_type_lower in ['storage', 'storage_service']:
            service = StorageService()
            
        elif service_type_lower in ['delta', 'delta_service']:
            service = DeltaService()
            
        else:
            raise ValueError(f"Unsupported service type: {service_type}")
            
        # Cache the instance for future use
        ServiceFactory._instances[service_type_lower] = service
        
        return service
    
    @staticmethod
    def reset_instance(service_type: str) -> None:
        """
        Reset a cached service instance.
        
        Args:
            service_type (str): The type of service to reset
        """
        service_type_lower = service_type.lower()
        if service_type_lower in ServiceFactory._instances:
            del ServiceFactory._instances[service_type_lower]
            logger.debug(f"Reset service instance: {service_type}")
    
    @staticmethod
    def reset_all() -> None:
        """Reset all cached service instances."""
        ServiceFactory._instances.clear()
        logger.debug("Reset all service instances") 