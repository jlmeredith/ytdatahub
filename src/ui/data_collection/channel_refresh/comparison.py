"""
This module handles the comparison between database and API data for channels.
"""
import streamlit as st
import pandas as pd
from src.utils.helpers import debug_log

def display_comparison_results(db_data, api_data):
    """Displays a comparison between database and API data."""
    st.subheader("Data Comparison")
    # Show detailed delta report if available (move this up)
    if 'delta' in st.session_state:
        st.subheader("Detailed Change Report")
        delta = st.session_state['delta']
        # DEBUG: Show the actual delta structure
        st.info(f"DEBUG: delta = {repr(delta)}")
        # Process the delta report for display
        if delta and isinstance(delta, dict):
            # Format changes for display
            formatted_changes = []
            for field, change in delta.items():
                if isinstance(change, dict) and 'old' in change and 'new' in change:
                    formatted_changes.append({
                        'Field': field,
                        'Previous Value': str(change['old']),
                        'New Value': str(change['new'])
                    })
            if formatted_changes:
                st.table(pd.DataFrame(formatted_changes))
                return
        st.warning("Delta information is not available")
        return
    if not db_data or not api_data:
        # Skip showing the warning here since it's already shown in the workflow
        return
    
    # Extract channel info data
    db_channel = db_data.get('channel_info', {})
    api_channel = api_data
    
    # Extract basic stats for comparison
    db_stats = db_channel.get('statistics', {})
    
    # Convert values to integers for comparison
    db_subs = int(db_stats.get('subscriberCount', 0))
    db_views = int(db_stats.get('viewCount', 0))
    db_videos = int(db_stats.get('videoCount', 0))
    
    api_subs = int(api_channel.get('subscribers', 0))
    api_views = int(api_channel.get('views', 0))
    api_videos = int(api_channel.get('total_videos', 0))
    
    # Calculate deltas
    delta_subs = api_subs - db_subs
    delta_views = api_views - db_views
    delta_videos = api_videos - db_videos
    
    # Display metrics with deltas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Subscribers",
            value=f"{api_subs:,}",
            delta=f"{delta_subs:+,}",
            delta_color="normal" if delta_subs >= 0 else "inverse"
        )
    
    with col2:
        st.metric(
            label="Total Views",
            value=f"{api_views:,}",
            delta=f"{delta_views:+,}",
            delta_color="normal" if delta_views >= 0 else "inverse"
        )
    
    with col3:
        st.metric(
            label="Videos",
            value=f"{api_videos:,}",
            delta=f"{delta_videos:+,}",
            delta_color="normal" if delta_videos >= 0 else "inverse"
        )

def compare_data(db_data, api_data):
    """
    Compare database data with API data and return a delta report.
    
    Args:
        db_data: Data from the database
        api_data: Data from the API
        
    Returns:
        dict: A report of differences between the two data sources
    """
    debug_log(f"compare_data called with db_data={repr(db_data)} api_data={repr(api_data)}")
    # Initialize delta dictionary
    delta = {}
    
    # Extract channel info data
    db_channel = db_data.get('channel_info', {})
    api_channel = api_data
    
    # Compare basic channel info
    if 'title' in db_channel and 'channel_name' in api_channel:
        if db_channel['title'] != api_channel['channel_name']:
            delta['channel_name'] = {
                'old': db_channel['title'],
                'new': api_channel['channel_name']
            }
    
    # Compare statistics
    db_stats = db_channel.get('statistics', {})
    
    # Convert values to integers for comparison
    db_subs = int(db_stats.get('subscriberCount', 0))
    db_views = int(db_stats.get('viewCount', 0))
    db_videos = int(db_stats.get('videoCount', 0))
    
    api_subs = int(api_channel.get('subscribers', 0))
    api_views = int(api_channel.get('views', 0))
    api_videos = int(api_channel.get('total_videos', 0))
    
    # Record differences in statistics
    if db_subs != api_subs:
        delta['subscribers'] = {'old': db_subs, 'new': api_subs}
    
    if db_views != api_views:
        delta['views'] = {'old': db_views, 'new': api_views}
    
    if db_videos != api_videos:
        delta['videos'] = {'old': db_videos, 'new': api_videos}
    
    debug_log(f"compare_data returning delta={repr(delta)}")
    return delta
