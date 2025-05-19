"""
Channel selector component for the data analysis UI.

This module has been refactored into the channel_selector package.
This file now re-exports functions from the new modules for backward compatibility.
"""
import streamlit as st  # Keep this import for backward compatibility

# Re-export all public functions from the new modules
from .channel_selector import (
    render_channel_selector,
    filter_channels,
    handle_search_update,
    render_channel_table,
    render_metadata_card,
    handle_channel_selection,
    apply_selection_action,
    load_channel_data
)

# Maintain backward compatibility with any other exported functions/classes
__all__ = [
    'render_channel_selector',
    'filter_channels',
    'handle_search_update',
    'render_channel_table',
    'render_metadata_card',
    'handle_channel_selection',
    'apply_selection_action',
    'load_channel_data'
]