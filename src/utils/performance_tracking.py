"""
Performance tracking utilities for the application.
This module contains functions for tracking and logging performance metrics.
"""
import time
import sys
import logging
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
from typing import Any, Dict, Optional, List, Union

def initialize_performance_tracking():
    """Initialize performance tracking system."""
    if 'performance_timers' not in st.session_state:
        st.session_state.performance_timers = {}
    
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {}

def start_timer(tag: str, message: str = None):
    """
    Start a timer for performance tracking
    
    Args:
        tag: The tag to identify this timer
        message: Optional message to log when starting the timer
    """
    if STREAMLIT_AVAILABLE:
        st.session_state[f"timer_{tag}"] = time.time()
    else:
        globals()[f"timer_{tag}"] = time.time()
    
    if message and st.session_state.get('debug_mode', False):
        logging.debug(f"⏱️ START TIMER [{tag}]: {message}")

def end_timer(tag: str, message: str = None) -> float:
    """
    End a timer and log the elapsed time
    
    Args:
        tag: The tag that identifies this timer (must match a previous start_timer call)
        message: Optional message to log along with the elapsed time
    
    Returns:
        float: The elapsed time in seconds
    """
    if STREAMLIT_AVAILABLE:
        start = st.session_state.get(f"timer_{tag}", None)
    else:
        start = globals().get(f"timer_{tag}", None)
    if start is None:
        logging.warning(f"Timer {tag} ended but no timers have been initialized")
        return 0.0
    
    if tag not in st.session_state.performance_timers:
        logging.warning(f"Timer {tag} ended but was never started")
        return 0.0
    
    # Calculate elapsed time
    elapsed = time.time() - start
    
    # Store metrics
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {}
    
    # Store metrics with timestamp to allow multiple measurements of the same tag
    st.session_state.performance_metrics[f"{tag}_{time.time()}"] = {
        'tag': tag,
        'duration': elapsed,
        'timestamp': time.time()
    }
    
    # Log if in debug mode
    if message and st.session_state.get('debug_mode', False):
        logging.debug(f"⏱️ END TIMER [{tag}]: {message} - took {elapsed:.3f} seconds")
    
    return elapsed

def get_performance_report():
    """
    Generate a performance report based on collected metrics
    
    Returns:
        dict: A dictionary containing performance statistics by tag
    """
    if 'performance_metrics' not in st.session_state or not st.session_state.performance_metrics:
        return {}
    
    # Group metrics by tag
    metrics_by_tag = {}
    for key, metric in st.session_state.performance_metrics.items():
        tag = metric['tag']
        if tag not in metrics_by_tag:
            metrics_by_tag[tag] = []
        metrics_by_tag[tag].append(metric['duration'])
    
    # Calculate statistics for each tag
    report = {}
    for tag, durations in metrics_by_tag.items():
        report[tag] = {
            'count': len(durations),
            'total': sum(durations),
            'average': sum(durations) / len(durations),
            'min': min(durations),
            'max': max(durations)
        }
    
    return report
