"""
Top performing videos analysis for the analytics dashboard.
"""
import streamlit as st
import pandas as pd
import time
from src.utils.helpers import debug_log

def render_top_videos(channels_dict, analysis, use_cache, is_multi_channel):
    """
    Render the top performing videos section of the dashboard.
    
    Args:
        channels_dict: Dictionary mapping channel names to channel data
        analysis: YouTubeAnalysis instance
        use_cache: Boolean indicating if caching should be used
        is_multi_channel: Boolean indicating if we're in multi-channel mode
    """
    # Performance analysis dashboard
    if st.session_state.get('show_performance_metrics', True):
        st.subheader("Performance Analysis")
        
        if is_multi_channel:
            render_multi_channel_top_videos(channels_dict, analysis, use_cache)
        else:
            render_single_channel_top_videos(channels_dict, analysis, use_cache)

def render_multi_channel_top_videos(channels_dict, analysis, use_cache):
    """Render top videos for multiple channels with a selector."""
    # For multi-channel mode, we need to show top videos from all channels or let user select a channel
    st.info("Select a channel to see its top performing videos")
    
    # Add a channel selector for top videos
    analysis_channel = st.selectbox(
        "Select channel for performance analysis",
        options=list(channels_dict.keys()),
        key="performance_analysis_channel"
    )
    
    # Get data for the selected channel
    selected_channel_data = channels_dict.get(analysis_channel)
    if selected_channel_data:
        # Generate or retrieve cached top videos data
        top_videos_cache_key = f"analysis_top_videos_{analysis_channel}"
        if use_cache and top_videos_cache_key in st.session_state:
            top_views = st.session_state[f"{top_videos_cache_key}_views"]
            top_likes = st.session_state[f"{top_videos_cache_key}_likes"]
        else:
            with st.spinner(f"Finding top performing videos for {analysis_channel}..."):
                top_views = analysis.get_top_videos(selected_channel_data, n=5, by='Views')
                top_likes = analysis.get_top_videos(selected_channel_data, n=5, by='Likes')
                if use_cache:
                    st.session_state[f"{top_videos_cache_key}_views"] = top_views
                    st.session_state[f"{top_videos_cache_key}_likes"] = top_likes
        
        perf_col1, perf_col2 = st.columns([1, 1])
        
        with perf_col1:
            # Top videos by views
            if top_views['df'] is not None and not top_views['df'].empty:
                st.subheader(f"Top Videos by Views - {analysis_channel}")
                top_views_df = top_views['df'][['Title', 'Views', 'Published']].copy()
                top_views_df['Views'] = top_views_df['Views'].apply(lambda x: f"{x:,}")
                # Format publish date to be more readable
                if 'Published' in top_views_df.columns and pd.api.types.is_datetime64_dtype(top_views_df['Published']):
                    top_views_df['Published'] = top_views_df['Published'].dt.strftime('%b %d, %Y')
                st.dataframe(top_views_df, use_container_width=True)
        
        with perf_col2:
            # Top videos by likes
            if top_likes['df'] is not None and not top_likes['df'].empty:
                st.subheader(f"Top Videos by Likes - {analysis_channel}")
                top_likes_df = top_likes['df'][['Title', 'Likes', 'Published']].copy()
                top_likes_df['Likes'] = top_likes_df['Likes'].apply(lambda x: f"{x:,}")
                # Format publish date to be more readable
                if 'Published' in top_likes_df.columns and pd.api.types.is_datetime64_dtype(top_likes_df['Published']):
                    top_likes_df['Published'] = top_likes_df['Published'].dt.strftime('%b %d, %Y')
                st.dataframe(top_likes_df, use_container_width=True)

def render_single_channel_top_videos(channels_dict, analysis, use_cache):
    """Render top videos for a single channel."""
    # Single channel case - use the original code
    channel_name = list(channels_dict.keys())[0]
    channel_data = channels_dict[channel_name]
    
    # Generate or retrieve cached top videos data
    top_videos_cache_key = f"analysis_top_videos_{channel_name}"
    if use_cache and top_videos_cache_key in st.session_state:
        top_views = st.session_state[f"{top_videos_cache_key}_views"]
        top_likes = st.session_state[f"{top_videos_cache_key}_likes"]
    else:
        with st.spinner("Finding top performing videos..."):
            top_views = analysis.get_top_videos(channel_data, n=5, by='Views')
            top_likes = analysis.get_top_videos(channel_data, n=5, by='Likes')
            if use_cache:
                st.session_state[f"{top_videos_cache_key}_views"] = top_views
                st.session_state[f"{top_videos_cache_key}_likes"] = top_likes
    
    perf_col1, perf_col2 = st.columns([1, 1])
    
    with perf_col1:
        # Top videos by views
        if top_views['df'] is not None and not top_views['df'].empty:
            st.subheader("Top Videos by Views")
            top_views_df = top_views['df'][['Title', 'Views', 'Published']].copy()
            top_views_df['Views'] = top_views_df['Views'].apply(lambda x: f"{x:,}")
            # Format publish date to be more readable
            if 'Published' in top_views_df.columns and pd.api.types.is_datetime64_dtype(top_views_df['Published']):
                top_views_df['Published'] = top_views_df['Published'].dt.strftime('%b %d, %Y')
            st.dataframe(top_views_df, use_container_width=True)
    
    with perf_col2:
        # Top videos by likes
        if top_likes['df'] is not None and not top_likes['df'].empty:
            st.subheader("Top Videos by Likes")
            top_likes_df = top_likes['df'][['Title', 'Likes', 'Published']].copy()
            top_likes_df['Likes'] = top_likes_df['Likes'].apply(lambda x: f"{x:,}")
            # Format publish date to be more readable
            if 'Published' in top_likes_df.columns and pd.api.types.is_datetime64_dtype(top_likes_df['Published']):
                top_likes_df['Published'] = top_likes_df['Published'].dt.strftime('%b %d, %Y')
            st.dataframe(top_likes_df, use_container_width=True)
