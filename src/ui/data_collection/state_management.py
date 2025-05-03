"""
Session state management for data collection UI.
Handles initialization and toggling of session state variables.
"""
import streamlit as st
from src.utils.helpers import debug_log

def initialize_session_state():
    """Initialize all session state variables needed for data collection."""
    if 'collection_step' not in st.session_state:
        st.session_state.collection_step = 1  # Step 1: Channel, Step 2: Videos, Step 3: Comments
    if 'channel_data_fetched' not in st.session_state:
        st.session_state.channel_data_fetched = False
    if 'videos_fetched' not in st.session_state:
        st.session_state.videos_fetched = False
    if 'comments_fetched' not in st.session_state:
        st.session_state.comments_fetched = False
    if 'show_all_videos' not in st.session_state:
        st.session_state.show_all_videos = False
    if 'collection_mode' not in st.session_state:
        st.session_state.collection_mode = "new_channel"  # "new_channel" or "existing_channel"
    if 'previous_channel_data' not in st.session_state:
        st.session_state.previous_channel_data = None
    if 'api_call_status' not in st.session_state:
        st.session_state.api_call_status = None
    if 'compare_data_view' not in st.session_state:
        st.session_state.compare_data_view = False
    if 'db_data' not in st.session_state:
        st.session_state.db_data = None
    if 'api_data' not in st.session_state:
        st.session_state.api_data = None

def toggle_debug_mode():
    """
    Toggle the debug mode and configure logging accordingly.
    This function is called when the debug mode checkbox state changes.
    """
    if st.session_state.debug_mode:
        # Set log level to DEBUG
        debug_log("Debug mode enabled")
    else:
        # Set log level to INFO
        debug_log("Debug mode disabled")
        
def reset_collection_state():
    """Reset collection-related session state variables."""
    st.session_state.channel_data_fetched = False
    st.session_state.videos_fetched = False
    st.session_state.comments_fetched = False
    st.session_state.show_all_videos = False
    st.session_state.collection_mode = "new_channel"
    if 'channel_info_temp' in st.session_state:
        del st.session_state.channel_info_temp
    if 'current_channel_data' in st.session_state:
        del st.session_state.current_channel_data
    if 'previous_channel_data' in st.session_state:
        del st.session_state.previous_channel_data
    if 'existing_channel_id' in st.session_state:
        del st.session_state.existing_channel_id