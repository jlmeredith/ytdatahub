"""
YouTube API base client implementation
"""
import json
import logging
import os
import time
import random
import googleapiclient.discovery
import googleapiclient.errors
from datetime import datetime
from typing import Dict, Any, Optional, Union

# Try to import streamlit but don't fail if it's not available
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    STREAMLIT_AVAILABLE = False
    # Create a dummy st module with cache_resource decorator for compatibility
    class DummySt:
        def cache_resource(self, func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
            
    st = DummySt()

from src.utils.debug_utils import debug_log
from src.services.youtube.error_handling_service import error_handling_service
from src.utils.validation import validate_api_key as validate_api_key_format

class YouTubeBaseClient:
    """Base class for YouTube API clients"""

    def __init__(self, api_key: str = None):
        """Initialize YouTube API client
        
        Args:
            api_key: YouTube API key
        """
        self.api_key = api_key
        self.youtube = None
        self._initialized = False
        self._cache = {}  # Local in-memory cache
        self._error_count = 0
        self.max_retries = 3
        
        # Initialize the client if API key is provided
        if api_key:
            self._initialize_api()

    def _initialize_api(self):
        """Initialize the YouTube API client"""
        debug_log("Initializing YouTube API client")
        
        if not self.api_key:
            debug_log("No API key provided. Cannot initialize.")
            return False
            
        # Validate API key format before trying to initialize
        if not validate_api_key_format(self.api_key):
            debug_log("API key format appears invalid.")
            return False
            
        try:
            # Build the YouTube API client
            self.youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=self.api_key, cache_discovery=False
            )
            self._initialized = True
            debug_log("YouTube API client initialized successfully")
            
            if hasattr(st, 'session_state'):
                st.session_state.api_client_initialized = True
                
            return True
            
        except Exception as e:
            self._initialized = False
            debug_log(f"Failed to initialize YouTube API client: {str(e)}")
            
            if hasattr(st, 'session_state'):
                st.session_state.api_client_initialized = False
                st.session_state.api_last_error = f"API initialization failed: {str(e)}"
                
            return False

    def is_initialized(self) -> bool:
        """Check if API client is initialized
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized and self.youtube is not None

    def check_api_key(self) -> tuple[bool, str]:
        """
        Validate YouTube API key by making a simple test call
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Use the centralized error handling service for API key validation
        return error_handling_service.check_api_key(self, self.api_key)

    def _handle_api_error(self, error: Exception, operation: str):
        """Handle API errors
        
        Args:
            error: The exception that was raised
            operation: The operation that failed
        """
        # Use the centralized error handling service
        return error_handling_service.handle_api_error(error, operation)

    def store_in_cache(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Store a value in the cache
        
        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl_seconds
        }
        
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self._cache:
            cache_item = self._cache[key]
            
            # Check if item has expired
            if time.time() <= cache_item['expires_at']:
                return cache_item['value']
            else:
                # Remove expired item
                del self._cache[key]
                
        return None
        
    def clear_cache(self):
        """Clear the entire cache"""
        self._cache = {}
        debug_log("API cache cleared")

    def ensure_api_cache(self):
        """Stub for API cache initialization (no-op for now)."""
        pass

@st.cache_resource
def get_youtube_api_client(api_key: str):
    return YouTubeBaseClient(api_key)