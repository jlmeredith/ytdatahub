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
import re
from src.utils.debug_utils import debug_log

class HtmlFormatter(logging.Formatter):
    """Custom formatter to output logs as HTML for Streamlit display."""
    FORMATS = {
        logging.DEBUG: '<span style="color:#808080; padding:1px 5px; border-radius:3px; background-color:#f8f9fa;"><b>[%(levelname)s]</b></span> <span style="color:#0088cc">[%(filename)s:%(lineno)d]</span> <span style="color:#333">%(message)s</span>',
        logging.INFO: '<span style="color:#fff; background-color:#28a745; padding:1px 5px; border-radius:3px;"><b>[%(levelname)s]</b></span> <span style="color:#808080">[%(filename)s:%(lineno)d]</span> <span style="color:#333">%(message)s</span>',
        logging.WARNING: '<span style="color:#fff; background-color:#ffc107; padding:1px 5px; border-radius:3px;"><b>[%(levelname)s]</b></span> <span style="color:#808080">[%(filename)s:%(lineno)d]</span> <span style="color:#333">%(message)s</span>',
        logging.ERROR: '<span style="color:#fff; background-color:#dc3545; padding:1px 5px; border-radius:3px;"><b>[%(levelname)s]</b></span> <span style="color:#808080">[%(filename)s:%(lineno)d]</span> <span style="color:#333">%(message)s</span>',
        logging.CRITICAL: '<span style="color:#fff; background-color:#dc3545; padding:1px 5px; border-radius:3px;"><b>[%(levelname)s]</b></span> <span style="color:#808080">[%(filename)s:%(lineno)d]</span> <span style="color:#333">%(message)s</span>',
    }
    
    # Icons for different log categories
    ICONS = {
        'api': '🌐',
        'db': '💾',
        'ui': '🖥️',
        'perf': '⏱️',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'video': '🎬',
        'channel': '📺',
        'playlist': '📋',
        'comment': '💬',
        'auth': '🔑',
        'config': '⚙️',
        'start': '▶️',
        'end': '⏹️',
        'delta': '📊',
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatted_msg = formatter.format(record)
        
        # Add decorative styling based on log content
        styled_msg = self._apply_styling(formatted_msg, record)
        
        # Create a nice card-like container for each log entry
        timestamp = self.formatTime(record)
        return f'''<div style="margin-bottom:4px; padding:6px; border-left:3px solid {'#dc3545' if record.levelno >= logging.WARNING else '#28a745' if record.levelno == logging.INFO else '#0088cc'}; background-color:#{'fff0f0' if record.levelno >= logging.WARNING else 'f0fff0' if record.levelno == logging.INFO else 'f8f9fa'};">
            <small style="color:#666; font-size:0.85em">{timestamp}</small><br>
            {styled_msg}
        </div>'''
    
    def _apply_styling(self, message, record):
        """Apply additional styling based on message content"""
        msg = record.getMessage().lower()
        
        # Add an icon based on message content
        for key, icon in self.ICONS.items():
            if key in msg:
                # Insert the icon at the beginning, after any HTML tags
                parts = message.split('</span>', 3)
                if len(parts) >= 4:
                    # Insert after the level, filename, and before the message content
                    message = f"{parts[0]}</span>{parts[1]}</span>{parts[2]}</span> {icon} {parts[3]}"
                break
        
        # Highlight any durations mentioned in the message
        message = re.sub(r'(\d+\.\d+)s', r'<span style="font-weight:bold; color:#E74C3C">\1s</span>', message)
        
        # Highlight API keys (partial, for security)
        message = re.sub(r'(API key|api_key)([^<]*)', r'<span style="color:#8E44AD">\1\2</span>', message)
        
        # Highlight any file paths or URLs
        message = re.sub(r'(\/[a-zA-Z0-9_\/.]+)', r'<span style="color:#2C3E50">\1</span>', message)
        
        return message
    
    def formatTime(self, record):
        return time.strftime('%H:%M:%S', time.localtime(record.created))

class StringIOHandler(logging.StreamHandler):
    """Custom logging handler that captures logs in a StringIO buffer."""
    def __init__(self):
        self.string_io = io.StringIO()
        super().__init__(self.string_io)
        self.setFormatter(HtmlFormatter())
        
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
        # Use a unique key for the container to avoid duplicate ID errors
        key = generate_unique_key("debug_logs_container")
        
        # Create a stylish container with search functionality
        st.markdown(
            f'''
            <div style="position:relative">
                <div style="height:400px; overflow-y:auto; background-color:#f8f9fa; 
                padding:10px; border-radius:5px; border:1px solid #dee2e6; font-size:0.9em;">
                    {log_content}
                </div>
                <div style="position:absolute; top:10px; right:10px; background:rgba(255,255,255,0.8); 
                padding:5px; border-radius:3px; font-size:0.8em;">
                    <span style="color:#28a745">■</span> INFO 
                    <span style="color:#ffc107">■</span> WARNING 
                    <span style="color:#dc3545">■</span> ERROR
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        # Add controls for the log viewer
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Clear Logs", key=generate_unique_key("clear_logs")):
                if st.session_state.get('debug_log_handler'):
                    # Create a new handler to clear logs
                    st.session_state.debug_log_handler.deactivate()
                    st.session_state.debug_log_handler = StringIOHandler()
                    st.session_state.debug_log_handler.activate()
                    st.rerun()
        with col2:
            if st.download_button(
                "Download Logs",
                log_content.replace("<", "&lt;").replace(">", "&gt;"), 
                file_name="ytdatahub_debug_logs.html",
                mime="text/html",
                key=generate_unique_key("download_logs")
            ):
                pass  # Download handled by Streamlit
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
    Safely display JSON data with error handling.
    Formats the data nicely for display in the UI.
    
    Args:
        data: The data to display
    """
    if data is None:
        st.info("No data available")
        return
    
    try:
        # Convert to JSON string with nice formatting
        if isinstance(data, (dict, list)):
            # Create a formatted JSON string with syntax highlighting
            json_str = json.dumps(data, indent=2)
            
            # Apply color highlighting based on data type
            # Replace patterns with HTML-styled versions
            formatted_json = json_str
            
            # Add color to keys (anything in quotes followed by a colon)
            formatted_json = re.sub(r'("([^"]+)"\s*:)', r'<span style="color:#2E86C1">\1</span>', formatted_json)
            
            # Add color to string values (anything in quotes not followed by a colon)
            formatted_json = re.sub(r':\s*"([^"]+)"', r': <span style="color:#27AE60">"\1"</span>', formatted_json)
            
            # Add color to numbers
            formatted_json = re.sub(r':\s*(-?\d+\.?\d*)', r': <span style="color:#8E44AD">\1</span>', formatted_json)
            
            # Add color to booleans and null
            formatted_json = re.sub(r':\s*(true|false|null)', r': <span style="color:#E74C3C">\1</span>', formatted_json)
            
            # Display the formatted JSON with syntax highlighting
            st.markdown(
                f'<pre style="background-color:#f8f9fa; padding:10px; border-radius:5px; '
                f'border:1px solid #dee2e6; max-height:400px; overflow:auto; font-family:monospace;">'
                f'{formatted_json}</pre>', 
                unsafe_allow_html=True
            )
        else:
            # For non-JSON data, use regular display
            st.write(str(data))
    except Exception as e:
        # If any error occurs, display the data as plain text
        try:
            st.warning(f"Could not format as JSON: {str(e)}")
            st.text(str(data))
        except:
            st.error("Unable to display data")