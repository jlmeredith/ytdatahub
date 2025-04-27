"""
YouTube API client implementation for the YouTube scraper application.
This module is maintained for backward compatibility and delegates
to the specialized modules in the youtube/ directory.
"""
from typing import Dict, List, Any, Optional, Tuple

from src.api.youtube import YouTubeAPI as ModularYouTubeAPI

# For backward compatibility
class YouTubeAPI(ModularYouTubeAPI):
    """
    YouTube Data API client for fetching channel and video data.
    This implementation delegates to the specialized YouTube API modules.
    """
    pass

# Maintain backward compatibility
__all__ = ['YouTubeAPI']