"""
UI performance utilities for measuring and reporting UI performance.
"""
import time
import logging
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
from datetime import datetime

def report_ui_timing(operation_name: str, start_time: float, show_spinner: bool = False):
    """
    Report the timing of a UI operation and display a spinner for long-running operations.
    Use this to track operations that might cause UI freezes.
    
    Args:
        operation_name: Descriptive name of the operation
        start_time: The starting timestamp (from time.time())
        show_spinner: Whether to show a spinner for operations that exceed the UI blocking threshold
        
    Returns:
        elapsed_time: Time taken for the operation in seconds
    """
    elapsed = time.time() - start_time
    
    # Initialize thresholds if they don't exist
    if not hasattr(st.session_state, 'ui_freeze_thresholds'):
        st.session_state.ui_freeze_thresholds = {
            'warning': 1.0,
            'critical': 3.0,
            'ui_blocking': 0.5
        }
    
    # Check against thresholds
    warning_threshold = st.session_state.ui_freeze_thresholds.get('warning', 1.0)
    critical_threshold = st.session_state.ui_freeze_thresholds.get('critical', 3.0)
    ui_blocking = st.session_state.ui_freeze_thresholds.get('ui_blocking', 0.5)
    
    # Log based on severity
    if elapsed >= critical_threshold:
        logging.warning(f"🔴 UI FREEZE DETECTED: {operation_name} took {elapsed:.2f}s")
    elif elapsed >= warning_threshold:
        logging.warning(f"🟠 UI SLOWDOWN DETECTED: {operation_name} took {elapsed:.2f}s")
    elif elapsed >= ui_blocking:
        logging.info(f"🟡 UI Operation: {operation_name} took {elapsed:.2f}s")
    else:
        logging.debug(f"🟢 UI Operation: {operation_name} took {elapsed:.2f}s")
    
    # Store the timing data
    if 'ui_timing_metrics' not in st.session_state:
        st.session_state.ui_timing_metrics = []
    
    st.session_state.ui_timing_metrics.append({
        'operation': operation_name,
        'duration': elapsed,
        'timestamp': time.time(),
        'severity': 'critical' if elapsed >= critical_threshold else 
                   'warning' if elapsed >= warning_threshold else 
                   'moderate' if elapsed >= ui_blocking else 'good'
    })
    
    # Show a spinner if the operation is taking too long
    if show_spinner and elapsed >= ui_blocking:
        with st.spinner(f"Loading {operation_name}..."):
            # This doesn't actually wait, just shows the spinner now that we've measured the time
            pass
    
    return elapsed

def get_performance_summary():
    """
    Get a summary of tracked performance metrics.
    
    Returns:
        A DataFrame with performance statistics
    """
    if 'performance_metrics' not in st.session_state or not st.session_state.performance_metrics:
        return None
    
    import pandas as pd
    
    # Extract data for the dataframe
    metrics = []
    for key, data in st.session_state.performance_metrics.items():
        metrics.append({
            'Tag': data['tag'],
            'Duration (s)': data['duration'],
            'Timestamp': datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S'),
            'Message': data['message'] if 'message' in data else '',
            'UI Impact': "Yes" if data.get('ui_impact', False) else "No",
            'Severity': data.get('severity', 'unknown')
        })
    
    if not metrics:
        return None
    
    # Create dataframe and sort by duration (longest first)
    df = pd.DataFrame(metrics)
    df = df.sort_values('Duration (s)', ascending=False)
    
    return df
