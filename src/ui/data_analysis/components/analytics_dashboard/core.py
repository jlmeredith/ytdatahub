"""
Core functionality for the analytics dashboard.
"""
import streamlit as st
import pandas as pd
import time
import plotly.express as px
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.helpers import debug_log
from src.ui.data_analysis.components.data_coverage import render_data_coverage_summary
from src.ui.components.ui_utils import render_template_as_markdown, render_template

from .performance_metrics import render_performance_metrics
from .publication_timeline import render_publication_timeline
from .duration_analysis import render_duration_analysis
from .top_videos import render_top_videos
from .comparison import render_channel_comparison

def render_analytics_dashboard(channel_data):
    """
    Render the analytics dashboard component.
    
    Args:
        channel_data: Dictionary containing channel data. Can be:
                     - A single channel's data dictionary (for backward compatibility)
                     - A dictionary of channel_name: channel_data for multiple channels
    """
    # Initialize performance tracking variables in session state if they don't exist
    if 'performance_timers' not in st.session_state:
        st.session_state.performance_timers = {}
    
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {}
    
    # Start performance tracking for the entire dashboard render
    start_time = time.time()
    debug_log("Analytics dashboard render started", performance_tag="start_dashboard_render")
    
    # Show loading indicator at the top of the page
    loading_placeholder = st.empty()
    with loading_placeholder.container():
        st.info("⏳ Loading analytics dashboard... This may take a moment depending on the amount of data.")
    
    # Check if we're dealing with multiple channels
    if isinstance(channel_data, dict) and any(isinstance(v, dict) and 'channel_info' in v for v in channel_data.values()):
        # Multiple channels case
        channels_dict = channel_data
        is_multi_channel = True
    else:
        # Single channel case (for backward compatibility)
        channels_dict = {'Single Channel': channel_data}
        is_multi_channel = False
    
    # Use caching for analysis results if enabled
    use_cache = st.session_state.get('use_data_cache', True)
    
    # Create a data frame to store aggregated metrics across channels
    aggregated_metrics = []
    
    # Initialize analysis object
    analysis = YouTubeAnalysis()
    
    # Add data coverage summary at the top of the dashboard
    render_data_coverage_summary(channel_data, analysis)
    debug_log("Data coverage summary rendered", performance_tag="end_coverage_summary")
    
    # Process each channel and collect data
    all_video_dfs = []
    channel_colors = {}
    
    # Create a color palette for the channels
    color_palette = px.colors.qualitative.Plotly
    
    # Show processing status
    channel_progress = st.progress(0.0, text="Processing channel data...")
    
    # Process channel data and collect metrics
    for idx, (channel_name, channel_data) in enumerate(channels_dict.items()):
        # Update progress indicator
        progress_pct = (idx / len(channels_dict)) 
        channel_progress.progress(progress_pct, text=f"Processing data for channel: {channel_name}")
        
        # Generate a unique cache key for this channel
        cache_key = f"analysis_dashboard_{channel_name}"
        
        # Assign a color to the channel
        channel_colors[channel_name] = color_palette[idx % len(color_palette)]
        
        # Check if we have cached results
        if use_cache and cache_key in st.session_state:
            debug_log(f"Using cached analytics dashboard data for {channel_name}")
            video_stats = st.session_state[cache_key]
        else:
            # Log start time for this operation
            channel_start_time = time.time()
            debug_log(f"Starting video statistics processing for {channel_name}", performance_tag=f"start_video_stats_{channel_name}")
            
            # Get video statistics for charts
            video_stats = analysis.get_video_statistics(channel_data)
            
            # Log completion time
            channel_end_time = time.time()
            processing_time = channel_end_time - channel_start_time
            debug_log(f"Video statistics processed for {channel_name} in {processing_time:.2f} seconds", 
                     performance_tag=f"end_video_stats_{channel_name}")
            
            # Cache the results if caching is enabled
            if use_cache:
                st.session_state[cache_key] = video_stats
                debug_log(f"Cached analytics dashboard data for {channel_name}")
        
        # Add channel name to the dataframe for multi-channel identification
        if video_stats['df'] is not None and not video_stats['df'].empty:
            df_copy = video_stats['df'].copy()
            df_copy['Channel'] = channel_name
            all_video_dfs.append(df_copy)
            
            # Calculate channel-level metrics for the comparison table
            metrics = calculate_channel_metrics(df_copy, channel_name)
            aggregated_metrics.append(metrics)
    
    # Finalize progress and remove channel progress indicator
    channel_progress.progress(1.0, text="Channel data processing complete!")
    time.sleep(0.5)  # Short pause to show completed progress
    channel_progress.empty()
    
    # Combine all dataframes
    combined_df = pd.concat(all_video_dfs) if all_video_dfs else None
    
    # Remove loading indicator now that initial processing is complete
    loading_placeholder.empty()
    
    # Load analytics dashboard styles
    render_template_as_markdown("analytics_dashboard_styles.html")
    
    # Set up template context
    template_context = {
        'no_data': False,
        'show_duration_chart': st.session_state.show_duration_chart,
        'show_engagement_ratios': st.session_state.get('show_engagement_ratios', True),
        'show_performance_metrics': st.session_state.get('show_performance_metrics', True),
        'show_trend_lines': st.session_state.get('show_trend_lines', True),
        'trend_window': st.session_state.get('trend_window', 'Medium'),
        'is_multi_channel': is_multi_channel
    }
    
    # Check if we have video data
    if combined_df is None or combined_df.empty:
        template_context['no_data'] = True
        render_template_as_markdown("analytics_dashboard.html", template_context)
        debug_log("Analytics dashboard rendered with no data", performance_tag="end_dashboard_render")
        return
    
    # Display channel comparison table if we have multiple channels
    if is_multi_channel and len(aggregated_metrics) > 1:
        render_channel_comparison(aggregated_metrics, channel_colors)
    
    # Display performance metrics section
    render_performance_metrics(combined_df, channels_dict, aggregated_metrics, channel_colors, is_multi_channel)
    
    # Display publication timeline analysis
    render_publication_timeline(combined_df, channels_dict, channel_colors, analysis, use_cache, is_multi_channel)
    
    # Display duration analysis if enabled
    if st.session_state.show_duration_chart:
        render_duration_analysis(combined_df, channels_dict, analysis, use_cache, is_multi_channel)
    
    # Display top performing videos
    render_top_videos(channels_dict, analysis, use_cache, is_multi_channel)
    
    # Add link to data coverage dashboard for updating data
    st.divider()
    st.markdown("### Need more complete data?")
    st.markdown("If you would like to update your data or see more detailed coverage information, go to the Data Coverage Dashboard.")
    
    if st.button("Go to Data Coverage Dashboard", key="analytics_goto_coverage_btn"):
        st.session_state.active_analysis_section = "coverage"
        st.rerun()
    
    # End performance tracking
    end_time = time.time()
    total_time = end_time - start_time
    debug_log(f"Analytics dashboard rendered in {total_time:.2f} seconds", 
             performance_tag="end_dashboard_render")

def calculate_channel_metrics(df_copy, channel_name):
    """
    Calculate channel-level metrics for the comparison table.
    
    Args:
        df_copy: DataFrame containing video data for a channel
        channel_name: Name of the channel
        
    Returns:
        dict: Dictionary containing calculated metrics
    """
    # Collect metrics for this channel
    channel_metrics = {
        'Channel': channel_name,
        'Total Videos': len(df_copy),
        'Avg Views': int(df_copy['Views'].mean()),
        'Avg Likes': int(df_copy['Likes'].mean()),
        'Avg Comments': int(df_copy['Comments'].mean()),
        'Date Range': f"{pd.to_datetime(df_copy['Published']).min().strftime('%b %Y')} to {pd.to_datetime(df_copy['Published']).max().strftime('%b %Y')}"
    }
    
    # Calculate ratios
    if channel_metrics['Avg Views'] > 0:
        channel_metrics['Like/View Ratio'] = channel_metrics['Avg Likes'] / channel_metrics['Avg Views'] * 100
        channel_metrics['Comment/View Ratio'] = channel_metrics['Avg Comments'] / channel_metrics['Avg Views'] * 100
        channel_metrics['Engagement Rate'] = (channel_metrics['Avg Likes'] + channel_metrics['Avg Comments']) / channel_metrics['Avg Views'] * 100
    else:
        channel_metrics['Like/View Ratio'] = 0
        channel_metrics['Comment/View Ratio'] = 0
        channel_metrics['Engagement Rate'] = 0
    
    return channel_metrics
