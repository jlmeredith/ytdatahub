"""
YouTube API error definitions.
This module contains error classes used throughout the YouTube API and services.
"""

class YouTubeAPIError(Exception):
    """
    Custom exception class for YouTube API errors.
    Provides structured error information with status code and error type.
    """
    def __init__(self, message, status_code=None, error_type=None, additional_info=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.additional_info = additional_info or {}
    
    def __str__(self):
        base_message = f"{self.message} (Status: {self.status_code}, Type: {self.error_type})"
        if self.additional_info:
            base_message += f" Additional info: {self.additional_info}"
        return base_message
