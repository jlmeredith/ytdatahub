"""
Error handling utilities for data collection workflows.

This module provides consistent error handling across workflows.
"""
import streamlit as st
from src.utils.debug_utils import debug_log

def handle_collection_error(error, action_description, debug=True):
    """
    Handle errors consistently during data collection.
    
    Args:
        error (Exception): The error that occurred
        action_description (str): Description of what was being attempted
        debug (bool): Whether to log detailed debug info
    
    Returns:
        None: But displays error message to the user
    """
    error_message = f"Error {action_description}: {str(error)}"
    st.error(error_message)
    
    if debug:
        debug_log(f"Collection Error - {action_description}: {str(error)}")
        
        # Add detailed error information in an expander for troubleshooting
        with st.expander("Debug Information"):
            st.code(f"""
Error Type: {type(error).__name__}
Error Message: {str(error)}
Action: {action_description}
            """)
    
    # Suggest common solutions based on error type
    if "quota" in str(error).lower():
        st.info("This may be a YouTube API quota issue. Try again later or check your quota usage.")
    elif "network" in str(error).lower() or "connection" in str(error).lower():
        st.info("This appears to be a network issue. Check your internet connection.")
    elif "not found" in str(error).lower():
        st.info("The requested resource was not found. Please check the channel ID/URL.")
    elif "rerun" in str(error).lower():
        st.info("There was an issue with the application workflow. This has been fixed, please try again.")
