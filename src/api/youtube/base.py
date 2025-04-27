"""
Base YouTube API client implementation.
"""
import streamlit as st
import googleapiclient.discovery
import googleapiclient.errors
from typing import Optional, Dict, Any

from src.config import API_SERVICE_NAME, API_VERSION
from src.utils.helpers import debug_log, validate_api_key

class YouTubeBaseClient:
    """Base YouTube Data API client with common functionality"""
    
    def __init__(self, api_key: str):
        """
        Initialize the YouTube API client
        
        Args:
            api_key: YouTube Data API v3 key
        """
        self.api_key = api_key
        self.youtube = None
        
        # Initialize the API client if a valid API key is provided
        if validate_api_key(api_key):
            try:
                self.youtube = googleapiclient.discovery.build(
                    API_SERVICE_NAME,
                    API_VERSION,
                    developerKey=api_key,
                    cache_discovery=False
                )
                debug_log("YouTube API client initialized successfully")
            except Exception as e:
                st.error(f"Error initializing YouTube API client: {str(e)}")
                debug_log(f"API client initialization failed: {str(e)}", e)
        else:
            st.error("Invalid API key format. Please provide a valid YouTube Data API key.")
    
    def is_initialized(self) -> bool:
        """Check if the API client is properly initialized"""
        return self.youtube is not None
        
    def _handle_api_error(self, error: Exception, method_name: str) -> None:
        """
        Handle API errors consistently
        
        Args:
            error: The caught exception
            method_name: Name of the method where the error occurred
        """
        if isinstance(error, googleapiclient.errors.HttpError):
            st.error(f"YouTube API error: {str(error)}")
            debug_log(f"API error in {method_name}: {str(error)}", error)
        else:
            st.error(f"Error in {method_name}: {str(error)}")
            debug_log(f"Exception in {method_name}: {str(error)}", error)
    
    def ensure_api_cache(self) -> None:
        """Ensure the API cache exists in the session state"""
        if 'api_cache' not in st.session_state:
            st.session_state.api_cache = {}
    
    def get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Get data from the cache if available
        
        Args:
            cache_key: The key to look for in the cache
            
        Returns:
            The cached data or None if not found
        """
        self.ensure_api_cache()
        return st.session_state.api_cache.get(cache_key)
    
    def store_in_cache(self, cache_key: str, data: Any) -> None:
        """
        Store data in the cache
        
        Args:
            cache_key: The key to use for storing in the cache
            data: The data to store
        """
        self.ensure_api_cache()
        st.session_state.api_cache[cache_key] = data