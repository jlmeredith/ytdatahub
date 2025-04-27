"""
Analytics dashboard component for the data analysis UI.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import timedelta
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.analysis.visualization.trend_line import add_trend_line
from src.analysis.visualization.chart_helpers import (
    configure_time_series_layout,
    configure_bar_chart_layout,
    add_percentage_annotations,
    get_plotly_config
)
from src.ui.components.ui_utils import render_template_as_markdown, render_template
from src.utils.helpers import debug_log

def render_analytics_dashboard(channel_data):
    """
    Render the analytics dashboard component.
    
    Args:
        channel_data: Dictionary containing channel data. Can be:
                     - A single channel's data dictionary (for backward compatibility)
                     - A dictionary of channel_name: channel_data for multiple channels
    """
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
    
    # Process each channel and collect data
    all_video_dfs = []
    channel_colors = {}
    
    # Create a color palette for the channels
    color_palette = px.colors.qualitative.Plotly
    
    for idx, (channel_name, channel_data) in enumerate(channels_dict.items()):
        # Generate a unique cache key for this channel
        cache_key = f"analysis_dashboard_{channel_name}"
        
        # Assign a color to the channel
        channel_colors[channel_name] = color_palette[idx % len(color_palette)]
        
        # Check if we have cached results
        if use_cache and cache_key in st.session_state:
            debug_log(f"Using cached analytics dashboard data for {channel_name}")
            video_stats = st.session_state[cache_key]
        else:
            # Get video statistics for charts
            video_stats = analysis.get_video_statistics(channel_data)
            
            # Cache the results if caching is enabled
            if use_cache:
                st.session_state[cache_key] = video_stats
                debug_log(f"Cached analytics dashboard data for {channel_name}")
        
        # Add channel name to the dataframe for multi-channel identification
        if video_stats['df'] is not None and not video_stats['df'].empty:
            df_copy = video_stats['df'].copy()
            df_copy['Channel'] = channel_name
            all_video_dfs.append(df_copy)
            
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
                
            aggregated_metrics.append(channel_metrics)
    
    # Combine all dataframes
    combined_df = pd.concat(all_video_dfs) if all_video_dfs else None
    
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
        return
        
    # Display channel comparison table if we have multiple channels
    if is_multi_channel and len(aggregated_metrics) > 1:
        st.subheader("Channel Comparison")
        metrics_df = pd.DataFrame(aggregated_metrics)
        
        # Format the metrics for display
        for col in ['Avg Views', 'Avg Likes', 'Avg Comments', 'Total Videos']:
            if col in metrics_df.columns:
                metrics_df[col] = metrics_df[col].apply(lambda x: f"{int(x):,}")
                
        for col in ['Like/View Ratio', 'Comment/View Ratio', 'Engagement Rate']:
            if col in metrics_df.columns:
                metrics_df[col] = metrics_df[col].apply(lambda x: f"{x:.2f}%")
        
        # Display the comparison table
        st.dataframe(
            metrics_df,
            column_config={
                "Channel": st.column_config.TextColumn("Channel", width="medium"),
                "Total Videos": st.column_config.TextColumn("Videos", width="small"),
                "Avg Views": st.column_config.TextColumn("Avg Views", width="small"),
                "Avg Likes": st.column_config.TextColumn("Avg Likes", width="small"),
                "Avg Comments": st.column_config.TextColumn("Avg Comments", width="small"),
                "Like/View Ratio": st.column_config.TextColumn("Like Rate", width="small"),
                "Comment/View Ratio": st.column_config.TextColumn("Comment Rate", width="small"),
                "Engagement Rate": st.column_config.TextColumn("Engagement", width="small"),
                "Date Range": st.column_config.TextColumn("Date Range", width="medium")
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Create multi-column layout for better organization
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Video Performance Trends")
        
        # Generate engagement timeline chart
        if 'Published' in combined_df.columns:
            try:
                # Create the engagement timeline chart directly in Streamlit
                engagement_fig = create_engagement_timeline_chart(combined_df, template_context, channel_colors, is_multi_channel)
                st.plotly_chart(engagement_fig, use_container_width=True)
                
                # Generate note based on data
                video_count = len(combined_df)
                date_range = f"{pd.to_datetime(combined_df['Published']).min().strftime('%b %Y')} to {pd.to_datetime(combined_df['Published']).max().strftime('%b %Y')}"
                if is_multi_channel:
                    channel_count = len(channels_dict)
                    st.caption(f"Analysis based on {video_count} videos from {channel_count} channels, spanning {date_range}.")
                else:
                    st.caption(f"Analysis based on {video_count} videos from {date_range}.")
                
            except Exception as e:
                st.error(f"Error generating timeline charts: {str(e)}")
                import traceback
                debug_log(f"Timeline chart error: {traceback.format_exc()}")
    
    with col2:
        st.subheader("Performance Metrics")
        
        if is_multi_channel:
            # For multiple channels, display a metric comparison chart
            try:
                metrics_df = pd.DataFrame(aggregated_metrics)
                
                # Create bar charts for key metrics
                metrics_to_plot = ['Avg Views', 'Engagement Rate']
                for metric in metrics_to_plot:
                    if metric in metrics_df.columns:
                        fig = px.bar(
                            metrics_df,
                            x='Channel',
                            y=metric,
                            title=f"{metric} by Channel",
                            color='Channel',
                            color_discrete_map=channel_colors
                        )
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating metrics comparison: {str(e)}")
                debug_log(f"Metrics comparison error: {str(e)}")
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
    
    # Create row for publication timeline analysis
    st.subheader("Publication Analysis")
    timeline_col1, timeline_col2 = st.columns([1, 1])
    
    # Generate publication timeline visualizations for each channel or combined
    if is_multi_channel:
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
                        with st.spinner(f"Analyzing publication patterns for {channel_name}..."):
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
                        x='Month-Year', 
                        y='Count',
                        color='Channel',
                        color_discrete_map=channel_colors,
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
                debug_log(f"Monthly chart error: {str(e)}")
        
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
    else:
        # Single channel case - use the original code
        channel_name = list(channels_dict.keys())[0]
        channel_data = channels_dict[channel_name]
        
        # Generate or retrieve cached timeline data
        timeline_cache_key = f"analysis_timeline_{channel_name}"
        if use_cache and timeline_cache_key in st.session_state:
            timeline_data = st.session_state[timeline_cache_key]
        else:
            with st.spinner("Analyzing publication patterns..."):
                timeline_data = analysis.get_publication_timeline(channel_data)
                if use_cache:
                    st.session_state[timeline_cache_key] = timeline_data
        
        with timeline_col1:
            # Get publication timeline data
            if timeline_data['monthly_df'] is not None:
                # Create monthly publication chart
                try:
                    monthly_df = timeline_data['monthly_df'].copy()
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
    
    # Video duration analysis
    if st.session_state.show_duration_chart:
        st.subheader("Video Duration Analysis")
        
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
        
        with duration_col2:
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
                        from src.utils.helpers import format_duration_human_friendly
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
                    from src.utils.helpers import format_duration_human_friendly
                    median_formatted = format_duration_human_friendly(median_duration) if not pd.isna(median_duration) else "N/A"
                    
                    st.markdown(f"**Median Duration:** {median_formatted}")
                    st.markdown(f"**Videos Under 10 min:** {under_10_pct:.1f}% ({under_10_min} videos)")
    
    # Performance analysis dashboard
    if st.session_state.get('show_performance_metrics', True):
        st.subheader("Performance Analysis")
        
        if is_multi_channel:
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
        else:
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

def create_engagement_timeline_chart(df, template_context, channel_colors=None, is_multi_channel=False):
    """Create engagement timeline charts."""
    # Make a copy to avoid pandas warnings
    df = df.copy()
    
    # Ensure we have datetime objects for the Published column
    df['Published'] = pd.to_datetime(df['Published'])
    
    # Sort by published date
    df = df.sort_values('Published')
    
    # Create figure
    fig = go.Figure()
    
    # Group by channel if multi-channel
    if is_multi_channel:
        for channel in df['Channel'].unique():
            channel_df = df[df['Channel'] == channel]
            
            # Get color for this channel
            color = channel_colors.get(channel) if channel_colors else None
            
            # Add views line
            if st.session_state.show_views_chart:
                fig.add_trace(go.Scatter(
                    x=channel_df['Published'],
                    y=channel_df['Views'],
                    mode='lines+markers',
                    name=f'{channel} - Views',
                    marker=dict(
                        size=6,
                        color=color
                    ),
                    line=dict(
                        color=color,
                        width=2
                    ),
                    opacity=0.7
                ))
            
            # Add likes line
            if st.session_state.show_likes_chart:
                fig.add_trace(go.Scatter(
                    x=channel_df['Published'],
                    y=channel_df['Likes'],
                    mode='lines+markers',
                    name=f'{channel} - Likes',
                    marker=dict(
                        size=5,
                        color=color
                    ),
                    line=dict(
                        color=color,
                        width=2,
                        dash='dot'
                    ),
                    opacity=0.6
                ))
            
            # Add comments line
            if st.session_state.show_comments_chart:
                fig.add_trace(go.Scatter(
                    x=channel_df['Published'],
                    y=channel_df['Comments'],
                    mode='lines+markers',
                    name=f'{channel} - Comments',
                    marker=dict(
                        size=4,
                        color=color
                    ),
                    line=dict(
                        color=color,
                        width=2,
                        dash='dash'
                    ),
                    opacity=0.5
                ))
            
            # Add trend lines if enabled
            if template_context.get('show_trend_lines', True):
                window_size = {
                    'Small': int(max(5, len(channel_df) * 0.1)),
                    'Medium': int(max(10, len(channel_df) * 0.2)),
                    'Large': int(max(15, len(channel_df) * 0.3))
                }.get(template_context.get('trend_window', 'Medium'), 10)
                
                if st.session_state.show_views_chart and len(channel_df) > window_size:
                    fig = add_trend_line(
                        fig, 
                        channel_df['Published'], 
                        channel_df['Views'], 
                        color=color,
                        width=2,
                        name=f'{channel} - Views Trend'
                    )
    else:
        # Single channel view
        # Add views line
        if st.session_state.show_views_chart:
            fig.add_trace(go.Scatter(
                x=df['Published'],
                y=df['Views'],
                mode='lines+markers',
                name='Views',
                marker=dict(size=6),
                line=dict(width=2)
            ))
        
        # Add likes line
        if st.session_state.show_likes_chart:
            fig.add_trace(go.Scatter(
                x=df['Published'],
                y=df['Likes'],
                mode='lines+markers',
                name='Likes',
                marker=dict(size=5),
                line=dict(
                    width=2,
                    dash='dot'
                )
            ))
        
        # Add comments line
        if st.session_state.show_comments_chart:
            fig.add_trace(go.Scatter(
                x=df['Published'],
                y=df['Comments'],
                mode='lines+markers',
                name='Comments',
                marker=dict(size=4),
                line=dict(
                    width=2,
                    dash='dash'
                )
            ))
        
        # Add trend lines if enabled
        if template_context.get('show_trend_lines', True):
            window_size = {
                'Small': int(max(5, len(df) * 0.1)),
                'Medium': int(max(10, len(df) * 0.2)),
                'Large': int(max(15, len(df) * 0.3))
            }.get(template_context.get('trend_window', 'Medium'), 10)
            
            if st.session_state.show_views_chart and len(df) > window_size:
                fig = add_trend_line(
                    fig, 
                    df['Published'], 
                    df['Views'], 
                    color="red", 
                    name='Views Trend'
                )
            
            if st.session_state.show_likes_chart and len(df) > window_size:
                fig = add_trend_line(
                    fig, 
                    df['Published'], 
                    df['Likes'], 
                    color="blue", 
                    name='Likes Trend'
                )
            
            if st.session_state.show_comments_chart and len(df) > window_size:
                fig = add_trend_line(
                    fig, 
                    df['Published'], 
                    df['Comments'], 
                    color="green", 
                    name='Comments Trend'
                )
    
    # Configure layout
    fig = configure_time_series_layout(
        fig,
        title="Video Performance Over Time"
    )
    
    # Set axis titles directly with update_layout since configure_time_series_layout doesn't support them
    fig.update_layout(
        xaxis_title="Publish Date",
        yaxis_title="Count",
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig