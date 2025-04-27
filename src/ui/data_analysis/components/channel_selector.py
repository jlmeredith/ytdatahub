"""
Channel selector component for the data analysis UI.
"""
import streamlit as st
from datetime import datetime
from src.analysis.youtube_analysis import YouTubeAnalysis

def render_channel_selector(channels, db):
    """
    Render the channel selector and basic channel information.
    
    Args:
        channels: List of channel names
        db: Database connection
        
    Returns:
        Tuple of (selected_channel, channel_data)
    """
    # Store selected channel in session state for URL persistence
    if 'selected_channel' not in st.session_state and channels:
        st.session_state.selected_channel = channels[0]
    
    # Channel selector - simplified to work with the simple list of channel names
    selected_channel = st.selectbox(
        "Select a channel to analyze:",
        options=channels,
        index=channels.index(st.session_state.selected_channel) if st.session_state.selected_channel in channels else 0,
        key="channel_selector"
    )
    
    # Update session state with selected channel for URL persistence
    if selected_channel != st.session_state.selected_channel:
        st.session_state.selected_channel = selected_channel
        # Force a rerun to update the URL parameters
        st.rerun()
    
    # Load channel data
    channel_data = db.get_channel_data(selected_channel)
    
    if not channel_data:
        return selected_channel, None
        
    # Initialize analysis
    analysis = YouTubeAnalysis()
    
    # Get channel stats
    channel_stats = analysis.get_channel_statistics(channel_data)
    
    # Display channel information
    st.subheader(f"Channel: {channel_stats['name']}")
    
    # Create a clean card-like layout for channel metrics
    columns = st.columns(4)
    with columns[0]:
        st.metric("Subscribers", f"{channel_stats['subscribers']:,}")
    with columns[1]:
        st.metric("Total Views", f"{channel_stats['views']:,}")
    with columns[2]:
        st.metric("Videos", f"{channel_stats['total_videos']:,}")
    with columns[3]:
        # Add creation date if available
        if 'channel_info' in channel_data and 'snippet' in channel_data['channel_info']:
            created = channel_data['channel_info']['snippet'].get('publishedAt', 'Unknown')
            if created and created != 'Unknown':
                try:
                    # Format date
                    created_date = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    st.metric("Created", created_date.strftime('%b %d, %Y'))
                except:
                    st.metric("Created", created)
            else:
                st.metric("Created", "Unknown")
        else:
            st.metric("Created", "Unknown")
            
    return selected_channel, channel_data