"""
YouTube Data Collection UI module.
This has been refactored into smaller components.
Now it serves as an entry point that delegates to the modular components.
"""
import streamlit as st
from .data_collection.main import render_data_collection_tab

# Expose the render_collection_steps function for backward compatibility
from .data_collection.steps_ui import render_collection_steps
from .data_collection.comparison_ui import render_comparison_view, render_api_db_comparison
from .data_collection.channel_refresh_ui import channel_refresh_section, refresh_channel_data
from .data_collection.debug_ui import render_debug_panel
from .data_collection.queue_ui import render_queue_status, get_queue_stats
from .data_collection.state_management import initialize_session_state, toggle_debug_mode

__all__ = [
    'render_data_collection_tab',
    'render_collection_steps',
    'render_comparison_view',
    'render_api_db_comparison',
    'channel_refresh_section',
    'refresh_channel_data',
    'render_debug_panel',
    'render_queue_status',
    'get_queue_stats',
    'initialize_session_state',
    'toggle_debug_mode'
]