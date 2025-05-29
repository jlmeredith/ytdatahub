"""
This module handles the data refresh functionality.
"""
import streamlit as st
from src.utils.debug_utils import debug_log
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH

def refresh_channel_data(channel_id, youtube_service, options):
    """
    Refresh channel data from the YouTube API.
    
    Args:
        channel_id: Channel ID
        youtube_service: YouTube service instance
        options: Options for data collection
        
    Returns:
        dict: Updated channel data or None if error occurred
    """
    # Initialize state variables if not present
    if 'update_in_progress' not in st.session_state:
        st.session_state['update_in_progress'] = False
    
    if 'show_iteration_prompt' not in st.session_state:
        st.session_state['show_iteration_prompt'] = False
        
    if 'iteration_choice' not in st.session_state:
        st.session_state['iteration_choice'] = None
        
    if 'iteration_complete' not in st.session_state:
        st.session_state['iteration_complete'] = False
    
    def iteration_prompt_callback():
        debug_log("Iteration prompt callback triggered")
        
        # Set flag to show the prompt
        st.session_state['show_iteration_prompt'] = True
        
        # If choice has already been made, return it and reset for next iteration
        if st.session_state['iteration_choice'] is not None:
            choice = st.session_state['iteration_choice']
            debug_log(f"Retrieved user choice: {choice}")
            
            # Reset choice for next iteration
            st.session_state['iteration_choice'] = None
            
            # If user chose not to continue, mark as complete
            if not choice:
                st.session_state['iteration_complete'] = True
                
            return choice
        
        # Otherwise return None to indicate waiting for user input
        debug_log("Waiting for user input - returning None")
        return None
    
    # Get database data for the channel
    db = SQLiteDatabase(SQLITE_DB_PATH)
    existing_data = db.get_channel_data(channel_id)
    
    if not existing_data:
        debug_log(f"No existing data found for channel {channel_id}")
        return None
    
    # Convert DB format to API format
    from ..utils.data_conversion import convert_db_to_api_format
    api_format_data = convert_db_to_api_format(existing_data)
    
    # Display existing data before update
    if st.session_state.get('show_data_before_update', False):
        st.subheader("Current Data (Before Update)")
        st.json(api_format_data)
    
    # If we're showing the iteration prompt, display it
    if st.session_state['show_iteration_prompt'] and st.session_state['iteration_choice'] is None:
        st.subheader("Data Collection Progress")
        st.write("Continue to iterate?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes", key="iter_yes"):
                debug_log("User selected 'Yes' to continue iteration")
                st.session_state['iteration_choice'] = True
                st.session_state['show_iteration_prompt'] = False
                st.rerun()
        with col2:
            if st.button("No", key="iter_no"):
                debug_log("User selected 'No' to stop iteration")
                st.session_state['iteration_choice'] = False
                st.session_state['show_iteration_prompt'] = False
                st.session_state['iteration_complete'] = True
                st.rerun()
        
        # Show progress message while waiting for user input
        st.info("Waiting for your decision to continue data collection...")
        return None
    
    # Check if iteration is complete
    if st.session_state['iteration_complete']:
        st.success("Data collection completed!")
        
        # Reset all state variables for next run
        st.session_state['iteration_complete'] = False
        st.session_state['show_iteration_prompt'] = False
        st.session_state['update_in_progress'] = False
        st.session_state['iteration_choice'] = None
        
        return api_format_data  # Return the collected data
    
    # Set flag to indicate update is in progress
    if not st.session_state['update_in_progress']:
        st.session_state['update_in_progress'] = True
        debug_log("Starting channel data update process")
    
    # Update channel data with interactive mode enabled
    with st.spinner("Collecting data from YouTube API..."):
        try:
            # First, ensure we have fresh channel info with the correct playlist ID
            debug_log(f"Getting fresh channel info for {channel_id}")
            fresh_channel_info = youtube_service.get_basic_channel_info(channel_id)
            
            if not fresh_channel_info:
                st.error(f"Could not fetch fresh channel info for {channel_id}")
                debug_log(f"Failed to get fresh channel info for {channel_id}")
                return None
                
            # Make sure the playlist ID is available
            playlist_id = fresh_channel_info.get('playlist_id') or fresh_channel_info.get('uploads_playlist_id')
            if not playlist_id:
                st.error(f"Could not determine uploads playlist ID for {channel_id}")
                debug_log(f"Missing playlist ID for {channel_id}")
                return None
                
            # Update the api_format_data with the fresh channel info
            api_format_data.update({
                'channel_id': channel_id,
                'playlist_id': playlist_id,
                'uploads_playlist_id': playlist_id,
                'raw_channel_info': fresh_channel_info.get('raw_channel_info')
            })
            
            debug_log(f"Using playlist_id: {playlist_id} for update")
            
            # Now update channel data with interactive mode enabled
            updated_data = youtube_service.update_channel_data(
                channel_id, 
                options, 
                existing_data=api_format_data,
                interactive=True
            )
            
            # Log the structure of the updated data for debugging
            if updated_data:
                debug_log(f"update_channel_data returned data with keys: {list(updated_data.keys())}")
                if 'api_data' in updated_data:
                    debug_log(f"api_data has keys: {list(updated_data['api_data'].keys()) if updated_data['api_data'] else 'empty'}")
                    
                # If api_data is empty but we have fresh_channel_info, use that
                if not updated_data.get('api_data') and fresh_channel_info:
                    debug_log(f"api_data is empty, using fresh_channel_info")
                    updated_data['api_data'] = fresh_channel_info
                    updated_data['channel'] = fresh_channel_info
            
            # If we completed without showing the prompt, reset the state
            if not st.session_state['show_iteration_prompt']:
                st.session_state['update_in_progress'] = False
                debug_log("Channel data update completed without iteration prompt")
                
            return updated_data
        except Exception as e:
            st.error(f"Error updating channel data: {str(e)}")
            debug_log(f"Error in refresh_channel_data: {str(e)}")
            
            # Reset state variables on error
            st.session_state['update_in_progress'] = False
            st.session_state['show_iteration_prompt'] = False
            
            return None
