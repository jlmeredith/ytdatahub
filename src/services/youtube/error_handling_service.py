"""
Centralized error handling service for YouTube API operations.
Consolidates error handling from service mixins, API base classes, and utility modules.
"""
import logging
import json
import time
import random
import traceback
from typing import Dict, Any, Optional, Union, Tuple

# Try to import streamlit but don't fail if it's not available
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    STREAMLIT_AVAILABLE = False

import googleapiclient.errors
from src.utils.debug_utils import debug_log

class YouTubeErrorHandlingService:
    """
    Centralized service for handling errors in YouTube API operations.
    Combines error handling from service mixins, API base classes, and utility modules.
    """
    
    def __init__(self):
        """Initialize the error handling service."""
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self._error_count = 0
    
    def handle_retriable_error(self, error: Exception, current_attempt: int, max_attempts: int) -> bool:
        """
        Handle errors that can be retried.
        
        Args:
            error: The exception that was raised
            current_attempt: Current retry attempt number
            max_attempts: Maximum number of retry attempts
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        # Determine if we can retry based on the attempt count
        if current_attempt < max_attempts:
            self.logger.warning(f"Error on attempt {current_attempt + 1}/{max_attempts + 1}: {str(error)}. Retrying...")
            return True
            
        # We've exhausted our retry attempts
        self.logger.error(f"Max retry attempts ({max_attempts}) exceeded: {str(error)}")
        return False
    
    def handle_api_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle API errors with exponential backoff and detailed logging.
        
        Args:
            error: The exception that was raised
            operation: Description of the operation that failed
            
        Returns:
            Error information dictionary including type, status, message
        """
        error_info = {
            'error_type': 'unknown',
            'status_code': None,
            'message': str(error),
            'operation': operation,
            'timestamp': time.time()
        }
        
        if isinstance(error, googleapiclient.errors.HttpError):
            status_code = error.resp.status
            error_info['status_code'] = status_code
            
            # Try to parse the error details
            try:
                error_details = json.loads(error.content.decode())
                error_reason = error_details.get('error', {}).get('errors', [{}])[0].get('reason', 'unknown')
                error_info['error_type'] = error_reason
                error_info['details'] = error_details
            except Exception as e:
                error_info['parse_error'] = str(e)
            
            # Handle rate limiting (429) with exponential backoff
            if status_code == 429:
                error_info['error_type'] = 'rateLimitExceeded'
                debug_log(f"Rate limit exceeded during {operation}. Implementing backoff...")
                
                # Start with a 1-second delay and add jitter
                for attempt in range(1, 4):  # Try up to 3 times
                    # Calculate exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    debug_log(f"Backing off for {delay:.2f} seconds (attempt {attempt})")
                    
                    # Sleep for the calculated delay
                    time.sleep(delay)
                    
                    # Record backoff attempt
                    error_info[f'backoff_attempt_{attempt}'] = delay
                    
                    try:
                        # Try the operation again (this would be handled by the caller)
                        error_info['backoff_complete'] = True
                        break
                    except googleapiclient.errors.HttpError as retry_error:
                        # If we get another rate limit error, continue the backoff loop
                        if retry_error.resp.status == 429:
                            continue
                        else:
                            # If it's a different error, record it
                            error_info['backoff_error'] = str(retry_error)
                            break
            
            # Handle quota exceeded errors
            elif error_reason == 'quotaExceeded':
                error_info['error_type'] = 'quotaExceeded'
                self.logger.error(f"Quota exceeded during {operation}")
                
                # Update session state if available
                if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                    st.session_state.quota_exceeded = True
                    st.session_state.last_quota_error = {
                        'timestamp': time.time(),
                        'operation': operation,
                        'message': str(error)
                    }
            
            # Handle other HTTP errors
            error_message = f"YouTube API error during {operation}: {error.resp.status} {error.resp.reason}"
            self.logger.error(error_message)
            
        else:
            # Handle non-HTTP errors
            self.logger.error(f"Error during {operation}: {str(error)}")
            error_info['error_type'] = error.__class__.__name__
        
        # Track error count
        self._error_count += 1
        
        # Log detailed error information
        debug_log(f"Error details for {operation}", error_info)
        
        return error_info
    
    def handle_channel_request_error(self, error: Exception, channel_data: Dict[str, Any], resolved_channel_id: str) -> Dict[str, Any]:
        """
        Handle errors during channel data requests.
        
        Args:
            error: The exception that was raised
            channel_data: Current channel data being built
            resolved_channel_id: The channel ID being processed
            
        Returns:
            Updated channel data with error information
        """
        # Get basic error info
        error_info = self.handle_api_error(error, f"channel request for {resolved_channel_id}")
        
        # Save error information to channel data
        if not channel_data.get('error'):
            channel_data['error'] = f"Error: {str(error)}"
        
        # Make sure channel_id is set
        if 'channel_id' not in channel_data:
            channel_data['channel_id'] = resolved_channel_id
            
        # Add status code if it exists
        if error_info['status_code']:
            channel_data['error_status_code'] = error_info['status_code']
            
        # Handle quota exceeded errors
        if error_info['error_type'] == 'quotaExceeded':
            channel_data['quota_exceeded'] = True
            
        return channel_data
    
    def handle_video_request_error(self, error: Exception, channel_data: Dict[str, Any], resolved_channel_id: str, db=None) -> Dict[str, Any]:
        """
        Handle errors during video data requests.
        
        Args:
            error: The exception that was raised
            channel_data: Current channel data being built
            resolved_channel_id: The channel ID being processed
            db: Optional database connection for saving partial data
            
        Returns:
            Updated channel data with error information
        """
        # Get basic error info
        error_info = self.handle_api_error(error, f"video request for {resolved_channel_id}")
        
        # Save error information to channel data
        channel_data['error_videos'] = f"Error: {str(error)}"
        
        # Try to save partial data to database
        if db:
            try:
                db.store_channel_data(channel_data)
                if not hasattr(self, '_db_channel_saved'):
                    self._db_channel_saved = {}
                self._db_channel_saved[resolved_channel_id] = True
            except Exception as db_error:
                self.logger.error(f"Failed to save partial data to DB: {str(db_error)}")
                channel_data['error_database'] = str(db_error)
                
        return channel_data
    
    def handle_comment_request_error(self, error: Exception, channel_data: Dict[str, Any], resolved_channel_id: str, db=None) -> Dict[str, Any]:
        """
        Handle errors during comment data requests.
        
        Args:
            error: The exception that was raised
            channel_data: Current channel data being built
            resolved_channel_id: The channel ID being processed
            db: Optional database connection for saving partial data
            
        Returns:
            Updated channel data with error information
        """
        # Get basic error info
        error_info = self.handle_api_error(error, f"comment request for {resolved_channel_id}")
        
        # Save error information to channel data
        channel_data['error_comments'] = f"Error: {str(error)}"
        
        # Try to save partial data to database
        if db and not hasattr(self, '_db_channel_saved'):
            try:
                db.store_channel_data(channel_data)
                self._db_channel_saved = {resolved_channel_id: True}
            except Exception as db_error:
                self.logger.error(f"Failed to save partial data to DB after comment error: {str(db_error)}")
                channel_data['error_database'] = str(db_error)
                
        return channel_data
    
    def log_error(self, error: Exception, component: Optional[str] = None, additional_info: Any = None) -> None:
        """
        Log error with traceback and contextual information
        
        Args:
            error: The exception object
            component: Optional name of the component where the error occurred
            additional_info: Optional additional information about the context
        """
        # Format the error message
        error_message = f"ERROR: {str(error)}"
        if component:
            error_message = f"[{component}] {error_message}"
            
        # Get the stack trace
        stack_trace = traceback.format_exc()
        
        # Log the error
        self.logger.error(error_message)
        self.logger.error(f"Stack trace:\n{stack_trace}")
        
        # Log additional info if provided
        if additional_info:
            self.logger.error(f"Additional info: {additional_info}")
            
        # In debug mode, also output to debug log for test access
        debug_log(error_message, {'stack_trace': stack_trace, 'additional_info': additional_info})
    
    def check_api_key(self, api_client, api_key: str) -> Tuple[bool, str]:
        """
        Validate YouTube API key by making a simple test call
        
        Args:
            api_client: YouTube API client instance
            api_key: YouTube API key to check
            
        Returns:
            Tuple of (is_valid, message)
        """
        debug_log("Checking API key validity")
        
        if not api_key:
            return False, "No API key provided"
            
        # If not yet initialized, can't proceed
        if not api_client or not api_client.is_initialized():
            return False, "API client not initialized"
        
        try:
            # Make a simple call to the API to check if key is valid
            request = api_client.youtube.channels().list(
                part="snippet",
                id="UC_x5XG1OV2P6uZZ5FSM9Ttw"  # This is Google's YouTube channel ID
            )
            response = request.execute()
            
            # For debugging purposes, store the raw response
            if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
                st.session_state.api_last_response = response
                
            debug_log("API key validation successful")
            return True, "API key is valid"
            
        except googleapiclient.errors.HttpError as e:
            # Get basic error info
            error_info = self.handle_api_error(e, "API key validation")
            error_reason = error_info['error_type']
            
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

# Create a singleton instance
error_handling_service = YouTubeErrorHandlingService() 