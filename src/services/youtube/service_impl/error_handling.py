"""
Error handling functionality for the YouTube service implementation.
"""
import logging

class ErrorHandlingMixin:
    """
    Mixin class providing error handling functionality for the YouTube service.
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
        logger = logging.getLogger(__name__)
        
        # Determine if we can retry based on the attempt count
        if current_attempt < max_attempts:
            logger.warning(f"Error on attempt {current_attempt + 1}/{max_attempts + 1}: {str(error)}. Retrying...")
            return True
            
        # We've exhausted our retry attempts
        logger.error(f"Max retry attempts ({max_attempts}) exceeded: {str(error)}")
        return False
    
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
        logger = logging.getLogger(__name__)
        
        # Log the error
        logger.error(f"Error fetching channel data: {str(error)}")
        
        # Save error information to channel data
        if not channel_data.get('error'):
            channel_data['error'] = f"Error: {str(error)}"
        
        # Make sure channel_id is set
        if 'channel_id' not in channel_data:
            channel_data['channel_id'] = resolved_channel_id
            
        # Add status code if it exists
        if hasattr(error, 'status_code'):
            channel_data['error_status_code'] = error.status_code
            
        # Handle quota exceeded errors
        if hasattr(error, 'error_type') and error.error_type == 'quotaExceeded':
            channel_data['quota_exceeded'] = True
            
        return channel_data
    
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
        logger = logging.getLogger(__name__)
        
        # Log the error
        logger.error(f"Error fetching videos: {str(error)}")
        
        # Save error information to channel data
        channel_data['error_videos'] = f"Error: {str(error)}"
        
        # Try to save partial data to database
        if hasattr(self, 'db'):
            try:
                self.db.store_channel_data(channel_data)
                if not hasattr(self, '_db_channel_saved'):
                    self._db_channel_saved = {}
                self._db_channel_saved[resolved_channel_id] = True
            except Exception as db_error:
                logger.error(f"Failed to save partial data to DB: {str(db_error)}")
                channel_data['error_database'] = str(db_error)
                
        return channel_data
    
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
        logger = logging.getLogger(__name__)
        
        # Log the error
        logger.error(f"Error fetching comments: {str(error)}")
        
        # Save error information to channel data
        channel_data['error_comments'] = f"Error: {str(error)}"
        
        # Try to save partial data to database
        if hasattr(self, 'db') and not hasattr(self, '_db_channel_saved'):
            try:
                self.db.store_channel_data(channel_data)
                self._db_channel_saved = {resolved_channel_id: True}
            except Exception as db_error:
                logger.error(f"Failed to save partial data to DB after comment error: {str(db_error)}")
                channel_data['error_database'] = str(db_error)
                
        return channel_data
