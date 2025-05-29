"""
Publication timeline analysis for the analytics dashboard.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import traceback
from src.utils.debug_utils import debug_log
from src.analysis.visualization.chart_helpers import configure_bar_chart_layout

def render_publication_timeline(combined_df, channels_dict, channel_colors, analysis, use_cache, is_multi_channel):
    """
    Render the publication timeline analysis section of the dashboard.
    
    Args:
        combined_df: DataFrame with combined data from all channels
        channels_dict: Dictionary mapping channel names to channel data
        channel_colors: Dictionary mapping channel names to colors
        analysis: YouTubeAnalysis instance
        use_cache: Boolean indicating if caching should be used
        is_multi_channel: Boolean indicating if we're in multi-channel mode
    """
    st.subheader("Publication Analysis")
    timeline_start_time = time.time()
    
    # Show loading indicator for timeline section
    timeline_loading = st.empty()
    with timeline_loading.container():
        st.info("⏳ Generating publication timeline analysis...")
    
    timeline_col1, timeline_col2 = st.columns([1, 1])
    
    # Generate publication timeline visualizations for each channel or combined
    if is_multi_channel:
        render_multi_channel_timeline(timeline_col1, timeline_col2, channels_dict, channel_colors, analysis, use_cache)
    else:
        render_single_channel_timeline(timeline_col1, timeline_col2, channels_dict, analysis, use_cache)
    
    # Clear the timeline loading indicator
    timeline_loading.empty()
    debug_log(f"Publication timeline analysis rendered in {time.time() - timeline_start_time:.2f} seconds",
             performance_tag="end_timeline_analysis")

def render_multi_channel_timeline(timeline_col1, timeline_col2, channels_dict, channel_colors, analysis, use_cache):
    """Render timeline visualizations for multiple channels."""
    # Process publication data for each channel separately for comparison
    with timeline_col1:
        try:
            monthly_data = []
            for channel_name, channel_data in channels_dict.items():
                # Generate or retrieve cached timeline data
                timeline_cache_key = f"analysis_timeline_{channel_name}"
                if use_cache and timeline_cache_key in st.session_state:
                    timeline_data = st.session_state[timeline_cache_key]
                else:
                    timeline_data = analysis.get_publication_timeline(channel_data)
                    if use_cache:
                        st.session_state[timeline_cache_key] = timeline_data
                
                # Process monthly data
                if timeline_data['monthly_df'] is not None:
                    monthly_df = timeline_data['monthly_df'].copy()
                    monthly_df['Channel'] = channel_name
                    monthly_data.append(monthly_df)
            
            # Combine all monthly data
            combined_monthly = pd.concat(monthly_data) if monthly_data else None
            
            if combined_monthly is not None:
                # Create monthly publication chart with channel colors
                monthly_fig = px.bar(
                    combined_monthly, 
                    x='__date',  # Use the actual date column for proper chronological ordering
                    y='Count',
                    color='Channel',
                    color_discrete_map=channel_colors,
                    title="Videos Published Per Month",
                    labels={'Count': 'Number of Videos', '__date': 'Month', 'Month-Year': 'Month'}
                )
                
                # Configure x-axis to show Month-Year format
                monthly_fig.update_xaxes(
                    ticktext=combined_monthly['Month-Year'],
                    tickvals=combined_monthly['__date'],
                    tickangle=45,
                    tickmode='array'
                )
                
                # Configure layout
                monthly_fig = configure_bar_chart_layout(
                    monthly_fig,
                    title="Videos Published Per Month",
                    x_title="Month",
                    y_title="Number of Videos"
                )
                st.plotly_chart(monthly_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating monthly publication chart: {str(e)}")
            debug_log(f"Monthly chart error: {str(e)}")
            debug_log("Monthly publication chart generation failed", performance_tag="end_monthly_chart_error")
    
    with timeline_col2:
        try:
            yearly_data = []
            for channel_name, channel_data in channels_dict.items():
                # Use the timeline data we already retrieved
                timeline_cache_key = f"analysis_timeline_{channel_name}"
                if timeline_cache_key in st.session_state:
                    timeline_data = st.session_state[timeline_cache_key]
                    
                    # Process yearly data
                    if timeline_data['yearly_df'] is not None:
                        yearly_df = timeline_data['yearly_df'].copy()
                        yearly_df['Channel'] = channel_name
                        yearly_data.append(yearly_df)
            
            # Combine all yearly data
            combined_yearly = pd.concat(yearly_data) if yearly_data else None
            
            if combined_yearly is not None:
                # Create yearly publication chart with channel colors
                yearly_fig = px.bar(
                    combined_yearly, 
                    x='Year', 
                    y='Videos',
                    color='Channel',
                    color_discrete_map=channel_colors,
                    title="Videos Published Per Year",
                    labels={'Videos': 'Number of Videos', 'Year': 'Year'}
                )
                yearly_fig = configure_bar_chart_layout(
                    yearly_fig,
                    title="Videos Published Per Year",
                    x_title="Year",
                    y_title="Number of Videos"
                )
                st.plotly_chart(yearly_fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating yearly publication chart: {str(e)}")
            debug_log(f"Yearly chart error: {str(e)}")
            debug_log("Yearly publication chart generation failed", performance_tag="end_yearly_chart_error")

def render_single_channel_timeline(timeline_col1, timeline_col2, channels_dict, analysis, use_cache):
    """Render timeline visualizations for a single channel."""
    # Single channel case - use the original code with loading indicators
    channel_name = list(channels_dict.keys())[0]
    channel_data = channels_dict[channel_name]
    
    # Generate or retrieve cached timeline data
    timeline_cache_key = f"analysis_timeline_{channel_name}"
    if use_cache and timeline_cache_key in st.session_state:
        timeline_data = st.session_state[timeline_cache_key]
    else:
        timeline_processing = st.empty()
        with timeline_processing.container():
            st.info("Analyzing publication patterns...")
        
        timeline_data = analysis.get_publication_timeline(channel_data)
        
        timeline_processing.empty()
        if use_cache:
            st.session_state[timeline_cache_key] = timeline_data
    
    with timeline_col1:
        # Get publication timeline data
        if timeline_data['monthly_df'] is not None:
            try:
                monthly_df = timeline_data['monthly_df'].copy()
                
                # Use the __date column for proper chronological ordering if it exists
                if '__date' in monthly_df.columns:
                    monthly_fig = px.bar(
                        monthly_df, 
                        x='__date', 
                        y='Count',
                        title="Videos Published Per Month",
                        labels={'Count': 'Number of Videos', '__date': 'Month'}
                    )
                    # Configure x-axis to show Month-Year format
                    monthly_fig.update_xaxes(
                        ticktext=monthly_df['Month-Year'],
                        tickvals=monthly_df['__date'],
                        tickangle=45,
                        tickmode='array'
                    )
                else:
                    # Fallback to old method if date column is not available (backward compatibility)
                    monthly_fig = px.bar(
                        monthly_df, 
                        x='Month-Year', 
                        y='Count',
                        title="Videos Published Per Month",
                        labels={'Count': 'Number of Videos', 'Month-Year': 'Month'}
                    )
                monthly_fig = configure_bar_chart_layout(
                    monthly_fig,
                    title="Videos Published Per Month",
                    x_title="Month",
                    y_title="Number of Videos"
                )
                st.plotly_chart(monthly_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating monthly publication chart: {str(e)}")
                import traceback
                debug_log(f"Monthly chart error: {traceback.format_exc()}")
                debug_log("Monthly publication chart generation failed", performance_tag="end_monthly_chart_error")
    
    with timeline_col2:
        # Create yearly publication chart if we have it
        if timeline_data['yearly_df'] is not None:
            try:
                yearly_df = timeline_data['yearly_df'].copy()
                yearly_fig = px.bar(
                    yearly_df, 
                    x='Year', 
                    y='Videos',
                    title="Videos Published Per Year",
                    labels={'Videos': 'Number of Videos', 'Year': 'Year'}
                )
                yearly_fig = configure_bar_chart_layout(
                    yearly_fig,
                    title="Videos Published Per Year",
                    x_title="Year",
                    y_title="Number of Videos"
                )
                st.plotly_chart(yearly_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating yearly publication chart: {str(e)}")
                import traceback
                debug_log(f"Yearly chart error: {traceback.format_exc()}")
                debug_log("Yearly publication chart generation failed", performance_tag="end_yearly_chart_error")
