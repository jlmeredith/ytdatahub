"""
YouTube API base client implementation
"""
import json
import logging
import os
import time
import googleapiclient.discovery
import googleapiclient.errors
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, Union

from src.utils.helpers import debug_log

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
        debug_log("Checking API key validity")
        
        if not self.api_key:
            return False, "No API key provided"
            
        # If not yet initialized, try to initialize
        if not self.is_initialized():
            success = self._initialize_api()
            if not success:
                return False, "Failed to initialize API client"
        
        try:
            # Make a simple call to the API to check if key is valid
            request = self.youtube.channels().list(
                part="snippet",
                id="UC_x5XG1OV2P6uZZ5FSM9Ttw"  # This is Google's YouTube channel ID
            )
            response = request.execute()
            
            # For debugging purposes, store the raw response
            if hasattr(st, 'session_state'):
                st.session_state.api_last_response = response
                
            debug_log("API key validation successful")
            return True, "API key is valid"
            
        except googleapiclient.errors.HttpError as e:
            error_details = json.loads(e.content.decode())
            error_reason = error_details.get('error', {}).get('errors', [{}])[0].get('reason', 'unknown')
            
            debug_log(f"API key validation failed: {error_reason}")
            
            if error_reason == 'keyInvalid':
                return False, "Invalid API key"
            elif error_reason == 'quotaExceeded':
                return False, "Quota exceeded for this API key"
            else:
                return False, f"API Error: {error_reason}"
                
        except Exception as e:
            debug_log(f"API key validation failed with unexpected error: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    def _handle_api_error(self, error: Exception, operation: str):
        """Handle API errors
        
        Args:
            error: The exception that was raised
            operation: The operation that failed
        """
        error_msg = str(error)
        error_details = ""
        
        try:
            if hasattr(error, 'content'):
                error_content = json.loads(error.content.decode())
                error_reason = error_content.get('error', {}).get('errors', [{}])[0].get('reason', 'unknown')
                error_message = error_content.get('error', {}).get('message', 'Unknown error')
                error_details = f"Reason: {error_reason}, Message: {error_message}"
        except:
            error_details = "Could not parse error details"
            
        log_msg = f"YouTube API error in {operation}: {error_msg} - {error_details}"
        debug_log(log_msg)
        logging.error(log_msg)
        
        # Update session state for debug panel
        if hasattr(st, 'session_state'):
            st.session_state.api_last_error = log_msg
            st.session_state.api_call_status = f"Error in {operation}"
        
        # Increment error count
        self._error_count += 1
        
        # If too many errors, reset client
        if self._error_count > 5:
            debug_log("Too many API errors. Resetting client.")
            self._initialized = False
            self._error_count = 0

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