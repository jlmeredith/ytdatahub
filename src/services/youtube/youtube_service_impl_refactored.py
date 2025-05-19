"""
Implementation of the YouTubeService facade using modular service components.
Provides the same interface as the original YouTube service for backward compatibility.

This file imports and re-exports the refactored YouTubeServiceImpl class from the service_impl package.
"""
from src.services.youtube.service_impl import YouTubeServiceImpl

# Re-export for backward compatibility
__all__ = ['YouTubeServiceImpl']
