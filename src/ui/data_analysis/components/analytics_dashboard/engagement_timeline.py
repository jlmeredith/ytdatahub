"""
Engagement timeline chart functionality for the analytics dashboard.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import timedelta
from src.utils.helpers import debug_log
from src.analysis.visualization.trend_line import add_trend_line
from src.analysis.visualization.chart_helpers import (
    configure_time_series_layout,
    add_percentage_annotations
)

def create_engagement_timeline_chart(df, template_context, channel_colors=None, is_multi_channel=False):
    """
    Create engagement timeline charts showing video performance over time.
    
    Args:
        df: DataFrame containing video data
        template_context: Dictionary containing template context variables
        channel_colors: Dictionary mapping channel names to colors (for multi-channel mode)
        is_multi_channel: Boolean indicating if we're in multi-channel mode
        
    Returns:
        Plotly figure object
    """
    debug_log("Generating engagement timeline chart", performance_tag="start_engagement_chart")
    
    # Check if we have data for the chart
    if df is None or df.empty or 'Published' not in df.columns:
        # Create a simple empty chart with an error message
        fig = go.Figure()
        fig.add_annotation(
            text="No video data available for timeline chart",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            height=400,
            title="Video Performance Over Time",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0.03)",
            margin=dict(l=10, r=10, t=50, b=10)
        )
        debug_log("Empty engagement timeline chart created", performance_tag="end_engagement_chart")
        return fig
    
    # Ensure datetime type for Published column
    df['Published'] = pd.to_datetime(df['Published'])
    
    # Sort by published date for line charts
    chart_df = df.sort_values('Published')
    
    # Create color mapping for multi-channel mode
    color_mapping = None
    if is_multi_channel and channel_colors:
        color_mapping = channel_colors
    
    # Create engagement timeline chart
    if is_multi_channel:
        # Multi-channel mode - group by channel
        fig = px.scatter(
            chart_df, 
            x='Published', 
            y='Views',
            color='Channel',
            color_discrete_map=color_mapping,
            size='Views',
            size_max=15,
            hover_name='Title',
            hover_data={
                'Views': ':,',
                'Likes': ':,',
                'Comments': ':,',
                'Channel': True,
                'Published': '|%b %d, %Y',
                'Title': False  # Using hover_name instead
            },
            title="Video Performance Over Time"
        )
        
        # Add trend lines for each channel
        for channel_name in chart_df['Channel'].unique():
            channel_data = chart_df[chart_df['Channel'] == channel_name]
            fig = add_trend_line(fig, channel_data, 'Published', 'Views', 
                                name=f"{channel_name} Trend", 
                                color=channel_colors.get(channel_name) if channel_colors else None)
        
    else:
        # Single channel mode - simpler chart
        fig = px.scatter(
            chart_df, 
            x='Published', 
            y='Views',
            size='Views',
            size_max=20,
            hover_name='Title',
            hover_data={
                'Views': ':,',
                'Likes': ':,',
                'Comments': ':,',
                'Published': '|%b %d, %Y',
                'Title': False  # Using hover_name instead
            },
            title="Video Performance Over Time"
        )
        
        # Add trend line if enabled
        if template_context.get('show_trend_lines', True):
            trend_window = template_context.get('trend_window', 'Medium')
            window_sizes = {'Small': 5, 'Medium': 10, 'Large': 20}
            window = window_sizes.get(trend_window, 10)
            
            fig = add_trend_line(fig, chart_df, 'Published', 'Views', window=window)
    
    # Configure layout
    fig = configure_time_series_layout(
        fig,
        title="Video Performance Over Time",
        x_title="Publication Date",
        y_title="Views"
    )
    
    debug_log("Engagement timeline chart generated successfully", 
             performance_tag="end_engagement_chart")
    
    return fig
