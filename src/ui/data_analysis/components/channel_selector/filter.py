"""
Filter functionality for the channel selector component.
"""
import streamlit as st
import pandas as pd
from src.utils.debug_utils import debug_log

def filter_channels(channels_df):
    """
    Filter the channels dataframe based on the search query.
    
    Args:
        channels_df: DataFrame containing channel information
        
    Returns:
        Filtered DataFrame
    """
    # Create a search box
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Use a callback to handle search updates
        st.text_input(
            "Search Channels", 
            value=st.session_state.channel_search_query,
            key="channel_search_input",
            on_change=handle_search_update,
            placeholder="Enter channel name..."
        )
    
    with col2:
        # Allow user to control how many channels to display
        display_options = [5, 10, 25, 50, 100, "All"]
        selected_limit = st.selectbox(
            "Show",
            options=display_options,
            index=display_options.index(st.session_state.user_selected_display_limit 
                                       if st.session_state.user_selected_display_limit in display_options 
                                       else 5),
            key="display_limit_selector",
            help="Number of channels to display"
        )
        
        # Update the session state with the new limit
        if selected_limit != st.session_state.user_selected_display_limit:
            st.session_state.user_selected_display_limit = selected_limit
            if selected_limit == "All":
                st.session_state.channel_display_limit = 10000  # Large number to show all
            else:
                st.session_state.channel_display_limit = selected_limit
    
    # Filter channels based on search query if provided
    if st.session_state.channel_search_query:
        search_term = st.session_state.channel_search_query.lower()
        debug_log(f"Filtering channels with search term: {search_term}")
        
        # Check if the expected column exists and use an appropriate column for filtering
        if 'Channel' in channels_df.columns:
            channel_column = 'Channel'
        elif 'channel_name' in channels_df.columns:
            channel_column = 'channel_name'
        elif 'name' in channels_df.columns:
            channel_column = 'name'
        else:
            # If no appropriate column found, return unfiltered data
            debug_log(f"Warning: No channel name column found for filtering. Available columns: {channels_df.columns.tolist()}")
            return channels_df
            
        # Apply the filter to channel names (case-insensitive)
        filtered_df = channels_df[channels_df[channel_column].str.lower().str.contains(search_term)]
        
        # Show filter results message
        if len(filtered_df) != len(channels_df):
            st.caption(f"Showing {len(filtered_df)} channels matching '{search_term}'")
        
        return filtered_df
    else:
        return channels_df

def handle_search_update():
    """Handle updates to the search query."""
    st.session_state.channel_search_query = st.session_state.channel_search_input
