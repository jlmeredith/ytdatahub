"""
Logger module for bulk import operations.
This module provides functions for logging debug information during bulk imports.
"""
import streamlit as st
from datetime import datetime
import streamlit.errors

def update_debug_log(log_container, message, is_error=False, is_success=False):
    """
    Update the debug log with a new message.
    
    Args:
        log_container: Streamlit container to display the log in
        message: The message to add to the log
        is_error: Whether this is an error message (displayed in red)
        is_success: Whether this is a success message (displayed in green)
    """
    # Get existing log content if any
    if 'import_log' not in st.session_state:
        st.session_state.import_log = ""
    
    # Add timestamp to message
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Format message based on type
    if is_error:
        formatted_message = f"<div style='color:red'>[{timestamp}] ❌ {message}</div>"
    elif is_success:
        formatted_message = f"<div style='color:green'>[{timestamp}] ✅ {message}</div>"
    else:
        formatted_message = f"<div>[{timestamp}] ℹ️ {message}</div>"
    
    # Append to log in session state instead of updating UI directly
    st.session_state.import_log += formatted_message
    
    # Add message to a queue of pending log messages
    if 'pending_log_messages' not in st.session_state:
        st.session_state.pending_log_messages = []
    
    st.session_state.pending_log_messages.append({
        'message': message,
        'is_error': is_error,
        'is_success': is_success,
        'timestamp': timestamp
    })
    
    # Only try to update the UI if in the main thread (not in background thread)
    try:
        log_container.markdown(
            f"<div style='height:400px;overflow-y:auto;background-color:#f0f2f6;padding:10px;border-radius:5px'>{st.session_state.import_log}</div>", 
            unsafe_allow_html=True
        )
    except streamlit.errors.NoSessionContext:
        # Silently ignore NoSessionContext errors - we'll update the UI on the next rerun
        pass
