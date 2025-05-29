"""
Error handling functionality for the YouTube service implementation.
This is a wrapper around the centralized error handling service.
"""
import logging
from src.services.youtube.error_handling_service import error_handling_service

class ErrorHandlingMixin:
    """
    Mixin class providing error handling functionality for the YouTube service.
    Delegates to the centralized error handling service.
    """
    
    def handle_retriable_error(self, error, current_attempt, max_attempts):
        """
        Handle errors that can be retried.
        
        Args:
            error (Exception): The exception that was raised
            current_attempt (int): Current retry attempt number
            max_attempts (int): Maximum number of retry attempts
            
        Returns:
            bool: True if the operation should be retried, False otherwise
        """
        return error_handling_service.handle_retriable_error(error, current_attempt, max_attempts)
    
    def handle_channel_request_error(self, error, channel_data, resolved_channel_id):
        """
        Handle errors during channel data requests.
        
        Args:
            error (Exception): The exception that was raised
            channel_data (dict): Current channel data being built
            resolved_channel_id (str): The channel ID being processed
            
        Returns:
            dict: Updated channel data with error information
        """
        return error_handling_service.handle_channel_request_error(error, channel_data, resolved_channel_id)
    
    def handle_video_request_error(self, error, channel_data, resolved_channel_id):
        """
        Handle errors during video data requests.
        
        Args:
            error (Exception): The exception that was raised
            channel_data (dict): Current channel data being built
            resolved_channel_id (str): The channel ID being processed
            
        Returns:
            dict: Updated channel data with error information
        """
        # Pass the database if we have it
        db = getattr(self, 'db', None)
        return error_handling_service.handle_video_request_error(error, channel_data, resolved_channel_id, db)
    
    def handle_comment_request_error(self, error, channel_data, resolved_channel_id):
        """
        Handle errors during comment data requests.
        
        Args:
            error (Exception): The exception that was raised
            channel_data (dict): Current channel data being built
            resolved_channel_id (str): The channel ID being processed
            
        Returns:
            dict: Updated channel data with error information
        """
        # Pass the database if we have it
        db = getattr(self, 'db', None)
        return error_handling_service.handle_comment_request_error(error, channel_data, resolved_channel_id, db)
