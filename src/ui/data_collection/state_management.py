"""
Session state management for data collection UI.
Handles initialization and toggling of session state variables.
"""
import streamlit as st
import logging
from src.utils.debug_utils import debug_log

def initialize_session_state():
    """
    Initialize all session state variables needed for data collection.
    """
    # Basic data collection state
    if 'collection_step' not in st.session_state:
        st.session_state['collection_step'] = 1
    
    # API state
    if 'api_initialized' not in st.session_state:
        st.session_state['api_initialized'] = False
    if 'api_client_initialized' not in st.session_state:
        st.session_state['api_client_initialized'] = False
    
    # Channel data state
    if 'channel_data_fetched' not in st.session_state:
        st.session_state['channel_data_fetched'] = False
    if 'channel_fetch_failed' not in st.session_state:
        st.session_state['channel_fetch_failed'] = False
    
    # Debug mode
    if 'debug_mode' not in st.session_state:
        st.session_state['debug_mode'] = False
    if 'debug_raw_data' not in st.session_state:
        st.session_state['debug_raw_data'] = {}
    if 'debug_delta_data' not in st.session_state:
        st.session_state['debug_delta_data'] = {}

def toggle_debug_mode():
    """
    Toggle the debug mode and configure logging accordingly.
    This function is called when the debug mode checkbox state changes.
    """
    # Ensure debug_mode exists in session state
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    # Get the new state from the checkbox
    debug_enabled = st.session_state.get('debug_mode_toggle', st.session_state.debug_mode)
    
    # Update the primary debug_mode flag
    st.session_state.debug_mode = debug_enabled
    
    # Set appropriate log level based on debug mode
    if debug_enabled:
        # Set log level to DEBUG
        if 'log_level' not in st.session_state:
            st.session_state.log_level = logging.DEBUG
        debug_log("Debug mode enabled")
    else:
        # Set log level to INFO
        if 'log_level' not in st.session_state:
            st.session_state.log_level = logging.INFO
        debug_log("Debug mode disabled")
    
    # Display status message (will only be shown when rerun happens)
    if debug_enabled:
        st.success("Debug mode enabled - detailed information will be shown")
    else:
        st.info("Debug mode disabled - detailed information hidden")
        
def reset_collection_state():
    """Reset collection-related session state variables."""
    st.session_state.channel_data_fetched = False
    st.session_state.videos_fetched = False
    st.session_state.comments_fetched = False
    st.session_state.show_all_videos = False
    
    # Default to new_channel mode unless explicitly setting to another mode
    if 'collection_mode' not in st.session_state or st.session_state.collection_mode not in ["existing_channel", "refresh_channel"]:
        st.session_state.collection_mode = "new_channel"
        
    if 'channel_info_temp' in st.session_state:
        del st.session_state.channel_info_temp
    if 'current_channel_data' in st.session_state:
        del st.session_state.current_channel_data
    if 'previous_channel_data' in st.session_state:
        del st.session_state.previous_channel_data
    if 'existing_channel_id' in st.session_state:
        del st.session_state.existing_channel_id