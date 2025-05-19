"""
Channel selector component package.
This package contains modules for different parts of the channel selector component.
"""

# Re-export main functions for backward compatibility
from .core import render_channel_selector
from .filter import filter_channels, handle_search_update
from .display import render_channel_table, render_metadata_card
from .selection import handle_channel_selection, apply_selection_action
from .loading import load_channel_data

__all__ = [
    'render_channel_selector',
    'filter_channels',
    'handle_search_update',
    'render_channel_table',
    'render_metadata_card',
    'handle_channel_selection',
    'apply_selection_action',
    'load_channel_data',
]
