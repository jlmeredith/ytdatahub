"""
Debug UI components for data collection.
Provides debug panel and logging functionality.
"""
import streamlit as st
import logging
import io
from src.utils.helpers import debug_log

class StringIOHandler(logging.Handler):
    """A logging handler that writes to a StringIO object."""
    
    def __init__(self):
        super().__init__()
        self.string_io = io.StringIO()
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        self.string_io.write(self.format(record) + '\n')
    
    def getvalue(self):
        return self.string_io.getvalue()
    
    def activate(self):
        """Activate this handler by adding it to the root logger."""
        root_logger = logging.getLogger()
        root_logger.addHandler(self)
        return self
    
    def deactivate(self):
        """Deactivate this handler by removing it from the root logger."""
        root_logger = logging.getLogger()
        if self in root_logger.handlers:
            root_logger.removeHandler(self)

def render_debug_logs():
    """
    Display debug logs in the UI when debug mode is enabled
    """
    if st.session_state.get('debug_log_handler') is None:
        st.session_state.debug_log_handler = StringIOHandler()
        st.session_state.debug_log_handler.activate()
    
    log_content = st.session_state.debug_log_handler.getvalue()
    if log_content:
        st.text_area("Debug Logs", log_content, height=400)
    else:
        st.info("No debug logs captured yet.")

def render_debug_panel():
    """
    Render debug information panel when debug mode is enabled
    """
    with st.expander("Debug Information", expanded=True):
        # Create tabs for different debug info categories
        debug_tabs = st.tabs(["API Status", "Session State", "Logs", "Response Data"])
        
        # API Status Tab
        with debug_tabs[0]:
            st.subheader("YouTube API Status")
            
            # Check multiple keys for API status
            api_client_initialized = st.session_state.get('api_client_initialized', False)
            api_initialized = st.session_state.get('api_initialized', False)
            last_api_call = st.session_state.get('last_api_call', None)
            api_last_error = st.session_state.get('api_last_error', None)
            
            # Display API initialization status
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="API Client Status", 
                    value="Initialized" if api_client_initialized else "Not Initialized"
                )
            with col2:
                st.metric(
                    label="API Call Made", 
                    value="Yes" if api_initialized else "No"
                )
            
            # Display last API call time
            if last_api_call:
                st.info(f"Last API call: {last_api_call}")
            else:
                st.info("Last API call: None")
            
            # Display any API errors
            if api_last_error:
                st.error(f"Last API error: {api_last_error}")
        
        # Session State Tab
        with debug_tabs[1]:
            st.subheader("Session State Variables")
            
            # IMPORTANT: Cache all these values before creating the table
            # This ensures consistent display even if values change during rendering
            channel_input = str(st.session_state.get('channel_input', 'Not set'))
            channel_data_fetched = str(st.session_state.get('channel_data_fetched', False))
            videos_fetched = str(st.session_state.get('videos_fetched', False))
            comments_fetched = str(st.session_state.get('comments_fetched', False))
            collection_mode = str(st.session_state.get('collection_mode', 'new_channel'))
            api_initialized = str(st.session_state.get('api_initialized', False))
            api_client_initialized = str(st.session_state.get('api_client_initialized', False))
            debug_mode = str(st.session_state.get('debug_mode', False))
            show_iteration_prompt = str(st.session_state.get('show_iteration_prompt', False))
            iteration_response = str(st.session_state.get('iteration_response', None))
            
            # Display relevant session state variables in a table
            debug_vars = [
                {"Variable": "channel_input", "Value": channel_input},
                {"Variable": "channel_data_fetched", "Value": channel_data_fetched},
                {"Variable": "videos_fetched", "Value": videos_fetched},
                {"Variable": "comments_fetched", "Value": comments_fetched},
                {"Variable": "collection_mode", "Value": collection_mode},
                {"Variable": "api_initialized", "Value": api_initialized},
                {"Variable": "api_client_initialized", "Value": api_client_initialized},
                {"Variable": "debug_mode", "Value": debug_mode},
                {"Variable": "show_iteration_prompt", "Value": show_iteration_prompt}, 
                {"Variable": "iteration_response", "Value": iteration_response}
            ]
            
            # Add channel data summary if available
            channel_info = None
            if 'channel_info_temp' in st.session_state and st.session_state.channel_info_temp:
                channel_info = st.session_state.channel_info_temp
            elif 'current_channel_data' in st.session_state and st.session_state.current_channel_data:
                channel_info = st.session_state.current_channel_data
                
            if channel_info:
                channel_name = str(channel_info.get('channel_name', 'Unknown'))
                channel_id = str(channel_info.get('channel_id', 'Unknown'))
                total_videos = str(channel_info.get('total_videos', '0'))
                
                debug_vars.append({"Variable": "channel_name", "Value": channel_name})
                debug_vars.append({"Variable": "channel_id", "Value": channel_id})
                debug_vars.append({"Variable": "total_videos", "Value": total_videos})
            
            # Display the debug variables table
            st.table(debug_vars)
        
        # Logs Tab
        with debug_tabs[2]:
            st.subheader("Debug Logs")
            
            # Check for debug logs in session state first
            debug_logs = st.session_state.get('debug_logs', [])
            if debug_logs:
                st.write("**Debug Messages:**")
                for i, log in enumerate(debug_logs, 1):
                    st.write(f"{i}. {log}")
            
            # Also display logs from string IO handler if available
            if 'debug_log_handler' in st.session_state:
                log_content = st.session_state.debug_log_handler.getvalue()
                if log_content:
                    st.write("**System Logs:**")
                    st.text_area("Log Output", log_content, height=200)
            
            # If no logs at all
            if not debug_logs and not st.session_state.get('debug_log_handler'):
                st.info("No logs captured yet. Debug logging will appear here during API operations.")
        
        # Response Data Tab
        with debug_tabs[3]:
            st.subheader("API Response Data")
            
            # Check for response data in multiple possible keys
            response_data = None
            if 'response_data' in st.session_state and st.session_state.response_data:
                response_data = st.session_state.response_data
            elif 'api_last_response' in st.session_state and st.session_state.api_last_response:
                response_data = st.session_state.api_last_response
            
            if response_data:
                st.json(response_data)
            else:
                st.info("No API response data captured yet.")