"""
Video duration analysis for the analytics dashboard.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import traceback
from src.utils.helpers import debug_log, format_duration_human_friendly
from src.analysis.visualization.chart_helpers import configure_bar_chart_layout

def render_duration_analysis(combined_df, channels_dict, analysis, use_cache, is_multi_channel):
    """
    Render the duration analysis section of the dashboard.
    
    Args:
        combined_df: DataFrame with combined data from all channels
        channels_dict: Dictionary mapping channel names to channel data
        analysis: YouTubeAnalysis instance
        use_cache: Boolean indicating if caching should be used
        is_multi_channel: Boolean indicating if we're in multi-channel mode
    """
    st.subheader("Video Duration Analysis")
    
    channel_name = list(channels_dict.keys())[0]  # Get first channel for single channel display
    channel_data = channels_dict[channel_name]
    
    # Generate or retrieve cached duration data
    duration_cache_key = f"analysis_duration_{channel_name}"
    if use_cache and duration_cache_key in st.session_state:
        duration_analysis = st.session_state[duration_cache_key]
    else:
        with st.spinner("Analyzing video durations..."):
            duration_analysis = analysis.get_duration_analysis(channel_data)
            if use_cache:
                st.session_state[duration_cache_key] = duration_analysis
    
    duration_col1, duration_col2 = st.columns([3, 2])
    
    with duration_col1:
        render_duration_chart(duration_analysis)
    
    with duration_col2:
        render_duration_stats(duration_analysis, combined_df, channel_name, is_multi_channel)

def render_duration_chart(duration_analysis):
    """Render the duration distribution chart."""
    if duration_analysis['category_df'] is not None:
        try:
            # Create duration distribution chart
            category_df = duration_analysis['category_df'].copy()
            duration_fig = px.bar(
                category_df,
                x='Duration Category',
                y='Count',
                title="Video Duration Distribution",
                labels={'Count': 'Number of Videos', 'Duration Category': 'Duration'},
                color='Count',
                color_continuous_scale='Viridis'
            )
            duration_fig = configure_bar_chart_layout(
                duration_fig,
                title="Video Duration Distribution",
                x_title="Duration",
                y_title="Number of Videos"
            )
            duration_fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(duration_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating duration distribution chart: {str(e)}")
            import traceback
            debug_log(f"Duration chart error: {traceback.format_exc()}")

def render_duration_stats(duration_analysis, combined_df, channel_name, is_multi_channel):
    """Render the duration statistics."""
    # Display duration metrics
    if duration_analysis['stats']:
        stats = duration_analysis['stats']
        st.subheader("Duration Stats")
        st.markdown(f"**Shortest Video:** {stats.get('min_duration_human', 'N/A')}")
        st.markdown(f"**Average Duration:** {stats.get('avg_duration_human', 'N/A')}")
        st.markdown(f"**Longest Video:** {stats.get('max_duration_human', 'N/A')}")
        
        # Add more detailed duration analysis
        if is_multi_channel:
            # In multi-channel mode, use the channel_data for the current channel
            channel_df = combined_df[combined_df['Channel'] == channel_name]
            if channel_df is not None and 'Duration_Seconds' in channel_df.columns:
                # Calculate what percentage of videos are under 10 minutes
                under_10_min = (channel_df['Duration_Seconds'] < 600).sum()
                under_10_pct = under_10_min / len(channel_df) * 100 if len(channel_df) > 0 else 0
                
                # Calculate median duration
                median_duration = channel_df['Duration_Seconds'].median()
                median_formatted = format_duration_human_friendly(median_duration) if not pd.isna(median_duration) else "N/A"
                
                st.markdown(f"**Median Duration:** {median_formatted}")
                st.markdown(f"**Videos Under 10 min:** {under_10_pct:.1f}% ({under_10_min} videos)")
        elif combined_df is not None and 'Duration_Seconds' in combined_df.columns:
            # Single channel mode
            # Calculate what percentage of videos are under 10 minutes
            under_10_min = (combined_df['Duration_Seconds'] < 600).sum()
            under_10_pct = under_10_min / len(combined_df) * 100 if len(combined_df) > 0 else 0
            
            # Calculate median duration
            median_duration = combined_df['Duration_Seconds'].median()
            median_formatted = format_duration_human_friendly(median_duration) if not pd.isna(median_duration) else "N/A"
            
            st.markdown(f"**Median Duration:** {median_formatted}")
            st.markdown(f"**Videos Under 10 min:** {under_10_pct:.1f}% ({under_10_min} videos)")
