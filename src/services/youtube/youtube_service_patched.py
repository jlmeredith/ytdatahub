# This file will be updated to use the new implementation
from src.services.youtube.youtube_service_impl import YouTubeServiceImpl
 
class YouTubeService(YouTubeServiceImpl):
    """
    Service class that handles business logic for YouTube data operations.
    This class is maintained for backward compatibility and delegates to specialized service classes.
    """
    
    def __init__(self, api_key):
        """
        Initialize the YouTube service with an API key.
        
        Args:
            api_key (str): The YouTube Data API key
        """
        super().__init__(api_key)
        # The initialization is handled by YouTubeServiceImpl

    @property
    def api(self):
        """Get the API client"""
        return self._api
    
    @api.setter
    def api(self, new_api):
        """
        Set the API client and propagate to specialized services.
        This is crucial for testing where the API is replaced with a mock.
        """
        self._api = new_api
        
        # Propagate the API change to all specialized services
        if hasattr(self, 'channel_service'):
            self.channel_service.api = new_api
            
        if hasattr(self, 'video_service'):
            self.video_service.api = new_api
            
        if hasattr(self, 'comment_service'):
            self.comment_service.api = new_api
            
        if hasattr(self, 'quota_service'):
            self.quota_service.api = new_api
