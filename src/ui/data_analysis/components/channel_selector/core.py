"""
Core functionality for the channel selector component.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.debug_utils import debug_log

from .filter import filter_channels, handle_search_update
from .display import render_channel_table, render_metadata_card
from .selection import handle_channel_selection, apply_selection_action
from .loading import load_channel_data

def render_channel_selector(channels, db):
    """
    Render the channel selector as a sortable table with only the last 5 imported channels.
    
    Args:
        channels: List of channel names
        db: Database connection
        
    Returns:
        Tuple of (selected_channels, channel_data_dict)
    """
    # Initialize caching settings if not already set
    if 'use_data_cache' not in st.session_state:
        st.session_state.use_data_cache = True
    
    # Initialize selected_channels as a list in session state for multi-selection
    if 'selected_channels' not in st.session_state:
        st.session_state.selected_channels = []
        
    # Initialize channel_search_query for search functionality
    if 'channel_search_query' not in st.session_state:
        st.session_state.channel_search_query = ""
    
    # Initialize channel_display_limit for pagination, but don't override an existing value
    default_limit = 5
    if 'channel_display_limit' not in st.session_state:
        st.session_state.channel_display_limit = default_limit  # Default to showing 5 channels
    
    # Initialize user's selected display limit if not set
    if 'user_selected_display_limit' not in st.session_state:
        st.session_state.user_selected_display_limit = st.session_state.channel_display_limit
    
    # Initialize YouTube Analysis for channel metrics
    analysis = YouTubeAnalysis()
    
    debug_log("Starting channel list processing", performance_tag="start_channel_selector")
    
    # Load and process channel data
    channels_df, full_channels_df, recent_channels_df = load_channel_data(channels, db, analysis)
    
    # Get the list of recent channel names
    recent_channel_names = recent_channels_df['Channel'].tolist() if not recent_channels_df.empty else []
    
    # Filter selected channels to only include recent ones shown in current view
    st.session_state.selected_channels = [ch for ch in st.session_state.selected_channels if ch in recent_channel_names]
    
    # Create a collapsible container for the channel selector
    with st.expander("Channel Selection", expanded=True):
        total_channels = len(full_channels_df) if not full_channels_df.empty else 0
        st.write(f"Available channels: {total_channels}. Showing the most recent {len(recent_channels_df)}.")
        
        # Add search and display controls
        st.write("Find and select channels to analyze:")
        
        # Handle search and filtering
        filtered_df = filter_channels(recent_channels_df)
        
        # Render the interactive channel table
        selected_channels = render_channel_table(filtered_df)
        
        # Handle selection actions
        selected_channel_data = apply_selection_action(selected_channels, db)
    
    debug_log("Finished channel selector rendering", performance_tag="end_channel_selector")
    
    return selected_channels, selected_channel_data
