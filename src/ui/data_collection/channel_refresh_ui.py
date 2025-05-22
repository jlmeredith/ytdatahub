"""
Channel refresh UI components for data collection.
This module has been refactored into the channel_refresh package.
This file now re-exports functions from the new modules for backward compatibility.
"""
import streamlit as st
from .channel_refresh import (
    channel_refresh_section,
    refresh_channel_data,
    display_comparison_results, 
    compare_data,
    render_video_section,
    configure_video_collection,
    render_comment_section,
    configure_comment_collection
)
from src.utils.formatters import format_number
from src.utils.debug_utils import debug_log

# Re-export all the necessary functions for backward compatibility
__all__ = [
    'channel_refresh_section',
    'refresh_channel_data',
    'display_comparison_results', 
    'compare_data',
    'render_video_section',
    'configure_video_collection',
    'render_comment_section',
    'configure_comment_collection',
]

# Re-export format_number for backward compatibility
__all__.append('format_number')

# Add debug_log to the re-export list
__all__.append('debug_log')
