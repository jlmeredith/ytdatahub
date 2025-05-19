# filepath: /Users/jamiemeredith/Projects/ytdatahub/src/services/youtube/youtube_service_impl.py
"""
Implementation of the YouTubeService facade using modular service components.
Provides the same interface as the original YouTube service for backward compatibility.

This file has been refactored into a modular structure in the service_impl package.
It re-exports the same interface for backward compatibility.
"""

# Import the refactored implementation
from src.services.youtube.service_impl import YouTubeServiceImpl

# This file now serves as a compatibility layer, re-exporting the YouTubeServiceImpl class
__all__ = ['YouTubeServiceImpl']
