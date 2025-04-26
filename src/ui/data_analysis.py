"""
UI components for the Data Analysis tab.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.services.youtube_service import YouTubeService
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.config import Settings
from src.storage.factory import StorageFactory

def render_data_analysis_tab():
    """
    Render the Data Analysis tab UI.
    """
    st.header("Data Analysis")
    
    # Initialize application settings
    app_settings = Settings()
    
    # Source selection
    data_source = st.radio(
        "Select Data Source:",
        app_settings.get_available_storage_options()
    )
    
    # Get the list of channels based on the selected source
    try:
        # Use the StorageFactory directly instead of YouTubeService
        storage_provider = StorageFactory.get_storage_provider(data_source, app_settings)
        channels = storage_provider.get_channels_list()
    except Exception as e:
        st.error(f"Error accessing {data_source}: {str(e)}")
        channels = []
    
    if channels:
        # Channel selection
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_channel = st.selectbox("Select Channel:", channels)
        
        # Add refresh button
        with col2:
            if st.button("Refresh Channel Data", key="refresh_channel_button"):
                try:
                    youtube_service = YouTubeService(app_settings)
                    with st.spinner(f"Refreshing data for {selected_channel}..."):
                        # Get channel ID from storage
                        channel_data = storage_provider.get_channel_data(selected_channel)
                        channel_id = channel_data.get('id')
                        if channel_id:
                            # Fetch fresh data from YouTube API
                            youtube_service.fetch_channel_data(channel_id, selected_channel)
                            st.success(f"Channel data for {selected_channel} has been refreshed!")
                            st.experimental_rerun()
                        else:
                            st.error("Could not find channel ID in stored data.")
                except Exception as e:
                    st.error(f"Error refreshing data: {str(e)}")
        
        if selected_channel:
            try:
                # Get channel data directly from storage provider
                channel_data = storage_provider.get_channel_data(selected_channel)
                
                if channel_data:
                    # Analysis options
                    analysis_option = st.selectbox(
                        "Select Analysis:",
                        [
                            "Dashboard Overview",
                            "Channel Statistics",
                            "Video Statistics",
                            "Top 10 Most Viewed Videos",
                            "Video Publication Over Time",
                            "Video Duration Analysis",
                            "Comment Analysis"
                        ]
                    )
                    
                    # Create an analyzer instance
                    analyzer = YouTubeAnalysis()
                    
                    if analysis_option == "Dashboard Overview":
                        _render_dashboard_overview(analyzer, channel_data)
                    
                    elif analysis_option == "Channel Statistics":
                        _render_channel_statistics(analyzer, channel_data)
                    
                    elif analysis_option == "Video Statistics":
                        _render_video_statistics(analyzer, channel_data)
                    
                    elif analysis_option == "Top 10 Most Viewed Videos":
                        _render_top_videos(analyzer, channel_data)
                    
                    elif analysis_option == "Video Publication Over Time":
                        _render_publication_timeline(analyzer, channel_data)
                    
                    elif analysis_option == "Video Duration Analysis":
                        _render_duration_analysis(analyzer, channel_data)
                    
                    elif analysis_option == "Comment Analysis":
                        _render_comment_analysis(analyzer, channel_data)
                else:
                    st.error(f"Failed to retrieve data for channel: {selected_channel}")
            except Exception as e:
                st.error(f"Error retrieving data for channel: {str(e)}")
    else:
        st.info("No channels found in the selected data source. Please collect and store data first.")


def _render_dashboard_overview(analyzer, channel_data):
    """Render a comprehensive dashboard overview with multiple visualizations."""
    # Get all needed statistics
    channel_stats = analyzer.get_channel_statistics(channel_data)
    video_stats = analyzer.get_video_statistics(channel_data)
    top_videos = analyzer.get_top_videos(channel_data, n=5)
    timeline = analyzer.get_publication_timeline(channel_data)
    duration_analysis = analyzer.get_duration_analysis(channel_data)
    
    # Channel header with key metrics
    st.subheader(f"Dashboard: {channel_stats['name']}")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Subscribers", f"{channel_stats['subscribers']:,}")
    with col2:
        st.metric("Total Views", f"{channel_stats['views']:,}")
    with col3:
        st.metric("Videos", channel_stats['total_videos'])
    with col4:
        if video_stats['df'] is not None:
            st.metric("Avg. Views/Video", f"{video_stats['avg_views']:,}")
        else:
            st.metric("Avg. Views/Video", "0")
    
    # First row of visualizations
    if top_videos['df'] is not None and timeline['monthly_df'] is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top 5 Videos")
            # Create a more visually appealing bar chart with Plotly
            if not top_videos['df'].empty:
                fig = px.bar(
                    top_videos['df'],
                    x='Views',
                    y='Title',
                    orientation='h',
                    color='Views',
                    color_continuous_scale='Viridis',
                    title="Top 5 Videos by Views"
                )
                fig.update_layout(height=350, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Publication Timeline")
            # Create an area chart for video publications
            if not timeline['monthly_df'].empty:
                fig = px.line(
                    timeline['monthly_df'], 
                    x='Month-Year', 
                    y='Count',
                    markers=True,
                    title="Videos Published Over Time"
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
    
    # Second row of visualizations
    if duration_analysis['category_df'] is not None and video_stats['df'] is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Video Duration Distribution")
            if not duration_analysis['category_df'].empty:
                # Create a pie chart for duration categories
                fig = px.pie(
                    duration_analysis['category_df'],
                    values='Count',
                    names='Duration Category',
                    title="Video Duration Distribution",
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Views vs. Likes Correlation")
            if not video_stats['df'].empty and 'Likes' in video_stats['df'].columns:
                fig = px.scatter(
                    video_stats['df'], 
                    x='Views', 
                    y='Likes',
                    color='Duration',
                    hover_data=['Title'],
                    title="Views vs. Likes",
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)


def _render_channel_statistics(analyzer, channel_data):
    """Render channel statistics analysis."""
    # Get channel statistics using the analyzer
    stats = analyzer.get_channel_statistics(channel_data)
    
    # Display channel stats with cards
    st.subheader(f"Channel: {stats['name']}")
    
    # Create a metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Subscribers", f"{stats['subscribers']:,}")
    with col2:
        st.metric("Total Views", f"{stats['views']:,}")
    with col3:
        st.metric("Total Videos", stats['total_videos'])
    
    # Channel description in an expandable section
    with st.expander("Channel Description", expanded=True):
        st.write(stats['description'])
    
    # Create a gauge chart for subscriber milestone
    subscriber_milestone = 1000000  # 1M subscribers milestone
    milestone_percentage = min(100, (stats['subscribers'] / subscriber_milestone) * 100)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=stats['subscribers'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Subscribers"},
        gauge={
            'axis': {'range': [None, subscriber_milestone]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, subscriber_milestone/2], 'color': "lightgray"},
                {'range': [subscriber_milestone/2, subscriber_milestone], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': subscriber_milestone
            }
        }
    ))
    
    st.plotly_chart(fig, use_container_width=True)


def _render_video_statistics(analyzer, channel_data):
    """Render video statistics analysis."""
    # Get video statistics using the analyzer
    stats = analyzer.get_video_statistics(channel_data)
    
    if stats['df'] is not None:
        # Display stats with cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Videos", stats['total_videos'])
        with col2:
            st.metric("Total Views", f"{stats['total_views']:,}")
        with col3:
            st.metric("Average Views", f"{stats['avg_views']:,}")
        
        # Create a histogram of views distribution
        if not stats['df'].empty:
            fig = px.histogram(
                stats['df'], 
                x='Views',
                nbins=20,
                title="Video Views Distribution",
                color_discrete_sequence=['#3366CC']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show sortable, filterable table
        st.subheader("All Videos")
        st.dataframe(stats['df'], use_container_width=True)
    else:
        st.info("No videos found for this channel")


def _render_top_videos(analyzer, channel_data):
    """Render top videos analysis."""
    # Get top videos using the analyzer
    top_videos = analyzer.get_top_videos(channel_data, n=10)
    
    if top_videos['df'] is not None:
        st.subheader("Top 10 Most Viewed Videos")
        
        # Create a horizontal bar chart with Plotly
        if not top_videos['df'].empty:
            fig = px.bar(
                top_videos['df'],
                x='Views',
                y='Title',
                orientation='h',
                color='Views',
                color_continuous_scale='Viridis',
                hover_data=['Likes', 'Published'],
                title="Top 10 Videos by Views"
            )
            fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Show table with additional metrics
        st.subheader("Detailed Data")
        st.dataframe(top_videos['df'], use_container_width=True)
        
        # Calculate likes-to-views ratio if data is available
        if 'Likes' in top_videos['df'].columns and 'Views' in top_videos['df'].columns:
            top_videos['df']['Likes/Views Ratio'] = (top_videos['df']['Likes'] / top_videos['df']['Views'] * 100).round(2)
            
            st.subheader("Engagement Analysis")
            fig = px.bar(
                top_videos['df'],
                x='Title',
                y='Likes/Views Ratio',
                color='Likes/Views Ratio',
                title="Likes to Views Ratio (%)",
                labels={'Likes/Views Ratio': 'Likes/Views (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No videos found for this channel")


def _render_publication_timeline(analyzer, channel_data):
    """Render publication timeline analysis."""
    # Get publication timeline using the analyzer
    timeline = analyzer.get_publication_timeline(channel_data)
    
    if timeline['monthly_df'] is not None:
        st.subheader("Video Publication Timeline")
        
        # Create an area chart for monthly publications
        if not timeline['monthly_df'].empty:
            fig = px.area(
                timeline['monthly_df'], 
                x='Month-Year', 
                y='Count',
                title="Videos Published by Month",
                color_discrete_sequence=['#3366CC']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Create a bar chart for yearly publications
        if not timeline['yearly_df'].empty:
            fig = px.bar(
                timeline['yearly_df'], 
                x='Year', 
                y='Videos',
                title="Videos Published by Year",
                color='Videos',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show the underlying data
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Monthly Data")
            st.dataframe(timeline['monthly_df'], use_container_width=True)
        with col2:
            st.subheader("Yearly Data")
            st.dataframe(timeline['yearly_df'], use_container_width=True)
    else:
        st.info("No videos found for this channel")


def _render_duration_analysis(analyzer, channel_data):
    """Render video duration analysis."""
    # Get duration analysis using the analyzer
    duration_analysis = analyzer.get_duration_analysis(channel_data)
    
    if duration_analysis['category_df'] is not None:
        st.subheader("Video Duration Analysis")
        
        # Display metrics
        stats = duration_analysis['stats']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Duration", stats['avg_duration_human'])
        with col2:
            st.metric("Shortest Video", stats['min_duration_human'])
        with col3:
            st.metric("Longest Video", stats['max_duration_human'])
        
        # Create visualization row
        col1, col2 = st.columns(2)
        
        with col1:
            # Create a pie chart for duration categories
            if not duration_analysis['category_df'].empty:
                fig = px.pie(
                    duration_analysis['category_df'],
                    values='Count',
                    names='Duration Category',
                    title="Video Duration Distribution",
                    color_discrete_sequence=px.colors.sequential.Viridis,
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Create a bar chart for the same data
            if not duration_analysis['category_df'].empty:
                fig = px.bar(
                    duration_analysis['category_df'],
                    x='Duration Category',
                    y='Count',
                    color='Count',
                    title="Video Count by Duration Category",
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No videos found for this channel")


def _render_comment_analysis(analyzer, channel_data):
    """Render comment analysis."""
    # Get comment analysis using the analyzer
    comment_analysis = analyzer.get_comment_analysis(channel_data)
    
    if comment_analysis['df'] is not None and comment_analysis['total_comments'] > 0:
        st.subheader("Comment Analysis")
        
        # Display total comments metric
        st.metric("Total Comments", comment_analysis['total_comments'])
        
        # Get comment counts per video if possible
        if 'Video' in comment_analysis['df'].columns:
            video_comment_counts = comment_analysis['df'].groupby('Video').size().reset_index(name='Comment Count')
            
            # Create a bar chart of comments per video
            if not video_comment_counts.empty:
                fig = px.bar(
                    video_comment_counts.sort_values('Comment Count', ascending=False).head(10),
                    x='Video',
                    y='Comment Count',
                    color='Comment Count',
                    title="Top 10 Videos by Comment Count",
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Show sample comments in an expandable section
        with st.expander("View Comment Data", expanded=False):
            st.dataframe(comment_analysis['df'], use_container_width=True)
    else:
        st.info("No comments found for the videos in this channel")