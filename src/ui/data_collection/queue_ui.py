"""
Queue status UI components for data collection.
Provides functions to display queue status.
"""
import streamlit as st
from src.utils.helpers import debug_log

def render_queue_status():
    """
    Display the current queue status to help users understand the current working state
    of data fetching operations.
    """
    try:
        # Get queue stats directly from QueueTracker
        queue_stats = get_queue_stats()
        
        if not queue_stats or (queue_stats.get('total_items', 0) == 0 and 
                             queue_stats.get('channels_count', 0) == 0 and
                             queue_stats.get('videos_count', 0) == 0 and
                             queue_stats.get('comments_count', 0) == 0):
            st.info("No active queue tasks found. All data shown is from cached results.")
            return
        
        # Show a clear summary of what's happening
        st.subheader("Data Source Status")
        
        # Display metrics for each type of data
        col1, col2 = st.columns(2)
        
        with col1:
            if queue_stats.get('channels_count', 0) > 0:
                st.metric("Channels in Queue", queue_stats.get('channels_count', 0))
            if queue_stats.get('videos_count', 0) > 0:
                st.metric("Videos in Queue", queue_stats.get('videos_count', 0))
                
        with col2:
            if queue_stats.get('comments_count', 0) > 0:
                st.metric("Comments in Queue", queue_stats.get('comments_count', 0))
            if queue_stats.get('analytics_count', 0) > 0:
                st.metric("Analytics in Queue", queue_stats.get('analytics_count', 0))
        
        # Show overall status
        if queue_stats.get('total_items', 0) > 0:
            st.info(f"New data is being fetched via API calls - {queue_stats.get('total_items', 0)} items in queue")
        else:
            st.success("All data is being loaded from cache")
            
        # Show last updated time if available
        if queue_stats.get('last_updated'):
            st.caption(f"Last updated: {queue_stats.get('last_updated')}")
            
    except Exception as e:
        debug_log(f"Error displaying queue status: {str(e)}", e)
        st.warning("Could not retrieve queue status information")

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