"""
Performance metrics functionality for the analytics dashboard.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import time
from src.utils.helpers import debug_log

def render_performance_metrics(combined_df, channels_dict, aggregated_metrics, channel_colors, is_multi_channel):
    """
    Render the performance metrics section of the analytics dashboard.
    
    Args:
        combined_df: DataFrame with combined data from all channels
        channels_dict: Dictionary mapping channel names to channel data
        aggregated_metrics: List of dictionaries containing channel metrics
        channel_colors: Dictionary mapping channel names to colors
        is_multi_channel: Boolean indicating if we're in multi-channel mode
    """
    section_start_time = time.time()
    st.subheader("Performance Metrics")
    
    if is_multi_channel:
        # For multiple channels, display a metric comparison chart
        try:
            metrics_df = pd.DataFrame(aggregated_metrics)
            
            # Create bar charts for key metrics
            metrics_to_plot = ['Avg Views', 'Engagement Rate']
            for metric in metrics_to_plot:
                if metric in metrics_df.columns:
                    # Show loading indicator
                    chart_load = st.empty()
                    with chart_load.container():
                        st.info(f"⏳ Generating {metric} chart...")
                    
                    # Create and display chart
                    fig = px.bar(
                        metrics_df,
                        x='Channel',
                        y=metric,
                        title=f"{metric} by Channel",
                        color='Channel',
                        color_discrete_map=channel_colors
                    )
                    
                    # Clear loading indicator and show chart
                    chart_load.empty()
                    st.plotly_chart(fig, use_container_width=True)
            
            debug_log(f"Performance metrics charts rendered in {time.time() - section_start_time:.2f} seconds",
                     performance_tag="end_metrics_charts")
        except Exception as e:
            st.error(f"Error generating metrics comparison: {str(e)}")
            debug_log(f"Metrics comparison error: {str(e)}")
            debug_log("Metrics comparison chart generation failed", performance_tag="end_metrics_charts_error")
    else:
        # For single channel, display metrics as before
        channel_name = list(channels_dict.keys())[0]
        df = combined_df[combined_df['Channel'] == channel_name] if is_multi_channel else combined_df
        
        # Calculate metrics
        avg_views = int(df['Views'].mean())
        avg_likes = int(df['Likes'].mean())
        avg_comments = int(df['Comments'].mean())
        
        # Calculate ratios
        like_view_ratio = avg_likes / avg_views * 100 if avg_views > 0 else 0
        comment_view_ratio = avg_comments / avg_views * 100 if avg_views > 0 else 0
        
        # Display metrics in a cleaner format using columns
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Avg. Views", f"{avg_views:,}")
            st.metric("Avg. Likes", f"{avg_likes:,}")
            st.metric("Avg. Comments", f"{avg_comments:,}")
        
        with metric_col2:
            st.metric("Like/View Ratio", f"{like_view_ratio:.2f}%")
            st.metric("Comment/View Ratio", f"{comment_view_ratio:.2f}%")
            
            # Add engagement rate calculation
            engagement_rate = (avg_likes + avg_comments) / avg_views * 100 if avg_views > 0 else 0
            st.metric("Engagement Rate", f"{engagement_rate:.2f}%")
        
        debug_log(f"Single channel metrics rendered in {time.time() - section_start_time:.2f} seconds",
                 performance_tag="end_single_channel_metrics")
