"""
Queue status UI components for data collection.
Provides functions to display queue status.
"""
import streamlit as st
from src.utils.helpers import debug_log
from src.utils.queue_tracker import render_queue_status_sidebar

def get_queue_stats():
    """
    Get current queue statistics from session state
    
    Returns:
        dict: Queue statistics including info about cached vs. API fetched data
    """
    # Initialize default stats
    if 'queue_stats' not in st.session_state:
        st.session_state.queue_stats = {
            'total_items': 0,
            'channels_count': 0,
            'videos_count': 0,
            'comments_count': 0,
            'analytics_count': 0,
            'last_updated': None
        }
    
    # Import QueueTracker to get latest queue status
    from src.utils.queue_tracker import get_queue_stats as get_tracker_stats
    
    # Get the stats from the QueueTracker
    tracker_stats = get_tracker_stats()
    
    # Combine local and tracker stats
    combined_stats = {**st.session_state.queue_stats}
    
    if tracker_stats:
        # Update with tracker data
        for key in tracker_stats:
            combined_stats[key] = tracker_stats[key]
    
    return combined_stats