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
        debug_tabs = st.tabs(["API Status", "Session State", "Logs", "Response Data"])
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
        with debug_tabs[1]:
            st.subheader("Session State Variables")
            debug_vars = []
            for k in ["channel_input", "channel_data_fetched", "videos_fetched", "comments_fetched", "collection_mode", "api_initialized", "api_client_initialized", "debug_mode"]:
                debug_vars.append({"Variable": k, "Value": str(st.session_state.get(k, None))})
            st.table(debug_vars)
        with debug_tabs[2]:
            st.subheader("Debug Logs")
            logs = st.session_state.get('ui_debug_logs', [])
            if logs:
                st.write("**Recent Debug Logs:**")
                for log in logs[-20:]:
                    st.write(log)
            else:
                st.info("No debug logs available.")
        with debug_tabs[3]:
            st.subheader("API Response Data")
            response_data = st.session_state.get('response_data', None)
            if response_data:
                st.json(response_data)
            else:
                st.info("No API response data captured yet.")
    st.subheader("Recent Performance Metrics")
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