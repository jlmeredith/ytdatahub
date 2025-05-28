"""
Debug UI components for data collection.
Provides debug panel and logging functionality.
"""
import streamlit as st
import logging
import io
import random
import time
import json
from src.utils.helpers import debug_log

class StringIOHandler(logging.StreamHandler):
    """Custom logging handler that captures logs in a StringIO buffer."""
    def __init__(self):
        self.string_io = io.StringIO()
        super().__init__(self.string_io)
        
    def activate(self):
        """Add this handler to the root logger."""
        logging.getLogger().addHandler(self)
        logging.getLogger().setLevel(logging.DEBUG)
        
    def deactivate(self):
        """Remove this handler from the root logger."""
        logging.getLogger().removeHandler(self)
        
    def getvalue(self):
        """Get the current log content."""
        return self.string_io.getvalue()

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

def generate_unique_key(prefix):
    """
    Generate a unique key for Streamlit elements to avoid duplicate ID errors.
    
    Args:
        prefix (str): A prefix for the key to make it more readable
        
    Returns:
        str: A unique key string
    """
    return f"{prefix}_{time.time()}_{random.randint(0, 10000)}"

def render_debug_panel():
    """
    Render debug information panel when debug mode is enabled
    """
    try:
        with st.expander("Debug Information", expanded=True):
            debug_tabs = st.tabs(["API Status", "Session State", "Logs", "Raw Data", "Performance"])
            
            # Tab 1: API Status
            with debug_tabs[0]:
                st.subheader("YouTube API Status")
                api_client_initialized = st.session_state.get('api_client_initialized', False)
                api_initialized = st.session_state.get('api_initialized', False)
                last_api_call = st.session_state.get('last_api_call', None)
                api_last_error = st.session_state.get('api_last_error', None)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("API Client Status", "Initialized" if api_client_initialized else "Not Initialized")
                with col2:
                    st.metric("API Call Made", "Yes" if api_initialized else "No")
                if last_api_call:
                    st.info(f"Last API call: {last_api_call}")
                if api_last_error:
                    st.error(f"Last API error: {api_last_error}")
            
            # Tab 2: Session State Variables
            with debug_tabs[1]:
                st.subheader("Session State Variables")
                debug_vars = []
                key_vars = [
                    "channel_input", "channel_data_fetched", "videos_fetched", 
                    "comments_fetched", "collection_step", "collection_mode", 
                    "api_initialized", "api_client_initialized", "debug_mode",
                    "existing_channel_id", "channel_data_saved", "videos_fetched",
                    "refresh_workflow_step"
                ]
                for k in key_vars:
                    debug_vars.append({"Variable": k, "Value": str(st.session_state.get(k, None))})
                st.table(debug_vars)
                
                # Add button to show all session state variables
                button_key = generate_unique_key("show_all_vars_btn")
                if st.button("Show All Session State Variables", key=button_key):
                    st.write("All Session State Variables:")
                    all_vars = []
                    for k, v in st.session_state.items():
                        # Skip large data structures and objects
                        if k not in ['debug_raw_data', 'debug_delta_data', 'api_data', 'db_data']:
                            value_str = str(v)
                            if len(value_str) > 100:
                                value_str = value_str[:100] + '...'
                            all_vars.append({"Variable": k, "Value": value_str})
                    st.dataframe(all_vars)
            
            # Tab 3: Debug Logs
            with debug_tabs[2]:
                st.subheader("Debug Logs")
                logs = st.session_state.get('ui_debug_logs', [])
                if logs:
                    st.write("**Recent Debug Logs:**")
                    for log in logs[-20:]:
                        st.write(log)
                else:
                    st.info("No debug logs available.")
                
                render_debug_logs()
            
            # Tab 4: Raw Response Data
            with debug_tabs[3]:
                st.subheader("Raw Data")
                
                # Safely get debug data from session state
                debug_raw_data = st.session_state.get('debug_raw_data', {})
                debug_delta_data = st.session_state.get('debug_delta_data', {})
                
                # Show all raw data in debug state
                raw_data_tabs = st.tabs(["Channel", "Playlist", "Videos", "Comments", "Delta"])
                
                # Channel Raw Data
                with raw_data_tabs[0]:
                    st.subheader("Channel Raw Data")
                    channel_data = debug_raw_data.get('channel', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Database Record:**")
                        safe_display_json(channel_data.get('db'))
                    with col2:
                        st.write("**API Response:**")
                        safe_display_json(channel_data.get('api'))
                
                # Playlist Raw Data
                with raw_data_tabs[1]:
                    st.subheader("Playlist Raw Data")
                    playlist_data = debug_raw_data.get('playlist', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Database Record:**")
                        safe_display_json(playlist_data.get('db'))
                    with col2:
                        st.write("**API Response:**")
                        safe_display_json(playlist_data.get('api'))
                
                # Videos Raw Data
                with raw_data_tabs[2]:
                    st.subheader("Videos Raw Data")
                    video_data = debug_raw_data.get('video', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Database Records:**")
                        if video_data.get('db') is not None:
                            video_count = len(video_data.get('db', [])) if isinstance(video_data.get('db'), list) else 0
                            if video_count > 10:
                                st.write(f"Showing first 10 of {video_count} videos")
                                safe_display_json(video_data.get('db', [])[:10])
                            else:
                                safe_display_json(video_data.get('db'))
                        else:
                            st.info("No database records available")
                    with col2:
                        st.write("**API Response:**")
                        if video_data.get('api') is not None:
                            video_count = len(video_data.get('api', [])) if isinstance(video_data.get('api'), list) else 0
                            if video_count > 10:
                                st.write(f"Showing first 10 of {video_count} videos")
                                safe_display_json(video_data.get('api', [])[:10])
                            else:
                                safe_display_json(video_data.get('api'))
                        else:
                            st.info("No API response available")
                
                # Comments Raw Data
                with raw_data_tabs[3]:
                    st.subheader("Comments Raw Data")
                    comment_data = debug_raw_data.get('comment', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Database Records:**")
                        if comment_data.get('db') is not None:
                            safe_display_json(comment_data.get('db'))
                        else:
                            st.info("No database records available")
                    with col2:
                        st.write("**API Response:**")
                        if comment_data.get('api') is not None:
                            safe_display_json(comment_data.get('api'))
                        else:
                            st.info("No API response available")
                
                # Delta Reports
                with raw_data_tabs[4]:
                    st.subheader("Delta Reports")
                    
                    delta_tabs = st.tabs(["Channel", "Playlist", "Videos", "Comments"])
                    
                    with delta_tabs[0]:
                        st.write("**Channel Delta:**")
                        delta = debug_delta_data.get('channel', {}).get('delta')
                        if delta is not None:
                            safe_display_json(delta)
                        else:
                            st.info("No channel delta available")
                    
                    with delta_tabs[1]:
                        st.write("**Playlist Delta:**")
                        delta = debug_delta_data.get('playlist', {}).get('delta')
                        if delta is not None:
                            safe_display_json(delta)
                        else:
                            st.info("No playlist delta available")
                    
                    with delta_tabs[2]:
                        st.write("**Videos Delta:**")
                        delta = debug_delta_data.get('video', {}).get('delta')
                        if delta is not None:
                            safe_display_json(delta)
                        else:
                            st.info("No videos delta available")
                    
                    with delta_tabs[3]:
                        st.write("**Comments Delta:**")
                        delta = debug_delta_data.get('comment', {}).get('delta')
                        if delta is not None:
                            safe_display_json(delta)
                        else:
                            st.info("No comments delta available")
            
            # Tab 5: Performance Metrics
            with debug_tabs[4]:
                st.subheader("Performance Metrics")
                perf_metrics = st.session_state.get('performance_metrics', {})
                perf_list = []
                if isinstance(perf_metrics, dict):
                    perf_list = list(perf_metrics.values())
                elif isinstance(perf_metrics, list):
                    perf_list = perf_metrics
                if perf_list:
                    try:
                        import pandas as pd
                        df = pd.DataFrame(perf_list)
                        st.dataframe(df.tail(10), use_container_width=True)
                    except Exception:
                        st.write(perf_list[-10:])
                else:
                    st.info("No performance metrics available.")
        
        # Add a warning about debug mode
        st.warning("⚠️ Debug mode is enabled. This may affect performance and display sensitive information. Disable it in production environments.")
    
    except Exception as e:
        st.error(f"Error rendering debug panel: {str(e)}")
        debug_log(f"Debug panel error: {str(e)}")

def safe_display_json(data):
    """
    Safely display JSON data without triggering Streamlit serialization errors.
    
    Args:
        data: Data to display as JSON
    """
    try:
        if data is None:
            st.info("No data available")
            return
            
        if isinstance(data, str):
            # Try to parse string as JSON
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # If it's not valid JSON, just display as text
                st.text(data)
                return
                
        # Use Streamlit's JSON display
        st.json(data)
    except Exception as e:
        # If JSON display fails, fall back to text representation
        st.error(f"Error displaying data as JSON: {str(e)}")
        st.text(str(data)[:1000] + "..." if len(str(data)) > 1000 else str(data))