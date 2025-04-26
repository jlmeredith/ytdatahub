"""
UI components for the Data Analysis tab.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
from streamlit_extras.metric_cards import style_metric_cards
# Removed the unsupported import for chart_container
from streamlit_extras.colored_header import colored_header
# Removed the unsupported import for grid

from src.services.youtube_service import YouTubeService
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.config import Settings
from src.storage.factory import StorageFactory

def render_data_analysis_tab():
    """
    Render the Data Analysis tab UI.
    """
    # Initialize application settings
    app_settings = Settings()
    
    # Create a container for the filters
    with st.container():
        st.markdown("<div class='dashboard-container'>", unsafe_allow_html=True)
        
        # Source and channel selection in a cleaner layout
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Source selection
            data_source = st.selectbox(
                "Data Source:",
                app_settings.get_available_storage_options(),
                key="data_source_selector"
            )
        
        # Get the list of channels based on the selected source
        try:
            # Use the StorageFactory directly
            storage_provider = StorageFactory.get_storage_provider(data_source, app_settings)
            channels = storage_provider.get_channels_list()
        except Exception as e:
            st.error(f"Error accessing {data_source}: {str(e)}", icon="🚨")
            channels = []
        
        if channels:
            with col2:
                # Channel selection
                selected_channel = st.selectbox(
                    "Channel:",
                    channels,
                    key="channel_selector"
                )
            
            with col3:
                # Add refresh button with loading animation
                refresh_clicked = st.button(
                    "Refresh Data",
                    key="refresh_channel_button",
                    use_container_width=True
                )
                
                if refresh_clicked:
                    try:
                        youtube_service = YouTubeService(app_settings)
                        
                        # Show a progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Update status
                        for i in range(101):
                            if i < 30:
                                status_text.text("Connecting to YouTube API...")
                            elif i < 60:
                                status_text.text("Retrieving channel data...")
                            elif i < 90:
                                status_text.text("Processing information...")
                            else:
                                status_text.text("Finalizing...")
                            
                            progress_bar.progress(i)
                            time.sleep(0.02)
                        
                        # Get channel ID from storage
                        channel_data = storage_provider.get_channel_data(selected_channel)
                        channel_id = channel_data.get('id')
                        
                        if channel_id:
                            # Fetch fresh data from YouTube API
                            youtube_service.fetch_channel_data(channel_id, selected_channel)
                            
                            # Clear progress indicators
                            progress_bar.empty()
                            status_text.empty()
                            
                            st.success(f"Channel data for {selected_channel} has been refreshed!", icon="✅")
                            
                            # Increment the stats counter
                            if 'app_stats' in st.session_state:
                                st.session_state.app_stats['data_collections'] += 1
                            
                            # Add a slight delay before rerunning to show the success message
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Could not find channel ID in stored data.", icon="🚨")
                    except Exception as e:
                        st.error(f"Error refreshing data: {str(e)}", icon="🚨")
            
            if selected_channel:
                try:
                    # Get channel data from storage provider
                    channel_data = storage_provider.get_channel_data(selected_channel)
                    
                    if channel_data:
                        # Analysis options
                        analysis_options = [
                            "Dashboard Overview",
                            "Channel Statistics",
                            "Video Statistics",
                            "Top 10 Most Viewed Videos",
                            "Video Publication Over Time",
                            "Video Duration Analysis",
                            "Comment Analysis"
                        ]
                        
                        # Create a horizontal tabs-like interface
                        tab_cols = st.columns(len(analysis_options))
                        
                        # Store selected analysis in session state if not already present
                        if 'selected_analysis' not in st.session_state:
                            st.session_state.selected_analysis = "Dashboard Overview"
                        
                        # Create buttons for each analysis option
                        for i, option in enumerate(analysis_options):
                            with tab_cols[i]:
                                if st.button(
                                    option,
                                    key=f"btn_{option}",
                                    use_container_width=True,
                                    type="primary" if st.session_state.selected_analysis == option else "secondary"
                                ):
                                    st.session_state.selected_analysis = option
                                    # Count as an analysis for stats
                                    if 'app_stats' in st.session_state:
                                        st.session_state.app_stats['analyses'] += 1
                                    st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Create an analyzer instance
                        analyzer = YouTubeAnalysis()
                        
                        # Display content based on selected analysis
                        st.markdown(f"<h2>{st.session_state.selected_analysis}</h2>", unsafe_allow_html=True)
                        
                        # Render the selected analysis
                        if st.session_state.selected_analysis == "Dashboard Overview":
                            _render_dashboard_overview(analyzer, channel_data)
                        
                        elif st.session_state.selected_analysis == "Channel Statistics":
                            _render_channel_statistics(analyzer, channel_data)
                        
                        elif st.session_state.selected_analysis == "Video Statistics":
                            _render_video_statistics(analyzer, channel_data)
                        
                        elif st.session_state.selected_analysis == "Top 10 Most Viewed Videos":
                            _render_top_videos(analyzer, channel_data)
                        
                        elif st.session_state.selected_analysis == "Video Publication Over Time":
                            _render_publication_timeline(analyzer, channel_data)
                        
                        elif st.session_state.selected_analysis == "Video Duration Analysis":
                            _render_duration_analysis(analyzer, channel_data)
                        
                        elif st.session_state.selected_analysis == "Comment Analysis":
                            _render_comment_analysis(analyzer, channel_data)
                    else:
                        st.error(f"Failed to retrieve data for channel: {selected_channel}", icon="🚨")
                        st.markdown("</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error retrieving data for channel: {str(e)}", icon="🚨")
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No channels found in the selected data source. Please collect and store data first.", icon="ℹ️")
            st.markdown("</div>", unsafe_allow_html=True)


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
        
        # Create tabs for different views of the data
        video_tabs = st.tabs(["Overview", "Performance Metrics", "Correlation Analysis", "Data Explorer"])
        
        # TAB 1: OVERVIEW
        with video_tabs[0]:
            # Calculate additional overview metrics
            if not stats['df'].empty:
                if 'Likes' in stats['df'].columns:
                    total_likes = stats['df']['Likes'].sum()
                    avg_likes = stats['df']['Likes'].mean()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Likes", f"{int(total_likes):,}")
                    with col2:
                        st.metric("Average Likes per Video", f"{int(avg_likes):,}")
                
                if 'Comments' in stats['df'].columns:
                    total_comments = stats['df']['Comments'].sum()
                    avg_comments = stats['df']['Comments'].mean()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Comments", f"{int(total_comments):,}")
                    with col2:
                        st.metric("Average Comments per Video", f"{int(avg_comments):,}")
                
                # Create distribution visualizations for views
                st.subheader("Video Views Distribution")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Histogram of views
                    fig = px.histogram(
                        stats['df'], 
                        x='Views',
                        nbins=20,
                        title="Views Distribution",
                        color_discrete_sequence=['#3366CC']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Box plot of views
                    fig = px.box(
                        stats['df'],
                        y='Views',
                        title="Views Box Plot",
                        points="all"  # Show all points
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Add duration information if available
                if 'Duration_Seconds' in stats['df'].columns:
                    st.subheader("Video Duration Analysis")
                    
                    # Calculate total duration and averages
                    total_duration_seconds = stats['df']['Duration_Seconds'].sum()
                    avg_duration_seconds = stats['df']['Duration_Seconds'].mean()
                    
                    # Convert to more readable formats
                    from src.utils.helpers import format_duration_human_friendly
                    total_duration = format_duration_human_friendly(total_duration_seconds)
                    avg_duration = format_duration_human_friendly(avg_duration_seconds)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Video Duration", total_duration)
                    with col2:
                        st.metric("Average Video Duration", avg_duration)
                    
                    # Scatter plot of duration vs views
                    fig = px.scatter(
                        stats['df'],
                        x='Duration_Seconds',
                        y='Views',
                        hover_data=['Title'],
                        title="Video Duration vs Views",
                        trendline="ols",  # Add trend line
                        color='Duration_Seconds',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(xaxis_title="Duration (seconds)")
                    st.plotly_chart(fig, use_container_width=True)
        
        # TAB 2: PERFORMANCE METRICS
        with video_tabs[1]:
            if not stats['df'].empty:
                # Add engagement metrics when available
                if all(col in stats['df'].columns for col in ['Views', 'Likes', 'Comments']):
                    st.subheader("Video Engagement Metrics")
                    
                    # Create engagement metrics
                    engagement_df = stats['df'].copy()
                    
                    # Add likes-to-views ratio
                    engagement_df['Likes/Views (%)'] = (engagement_df['Likes'] / engagement_df['Views'] * 100).round(2)
                    
                    # Add comments-to-views ratio
                    engagement_df['Comments/Views (%)'] = (engagement_df['Comments'] / engagement_df['Views'] * 100).round(2)
                    
                    # Add overall engagement score (weighted)
                    engagement_df['Engagement Score'] = (
                        (engagement_df['Likes'] / engagement_df['Views'] * 100) * 0.7 + 
                        (engagement_df['Comments'] / engagement_df['Views'] * 100) * 0.3
                    ).round(2)
                    
                    # Display top videos by engagement score
                    st.subheader("Top Videos by Engagement Score")
                    top_engagement = engagement_df.sort_values('Engagement Score', ascending=False).head(10)
                    
                    fig = px.bar(
                        top_engagement,
                        x='Engagement Score',
                        y='Title',
                        orientation='h',
                        color='Engagement Score',
                        color_continuous_scale='Viridis',
                        title="Top 10 Videos by Engagement",
                        hover_data=['Views', 'Likes', 'Comments', 'Published']
                    )
                    fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display average engagement metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avg. Like Rate", f"{engagement_df['Likes/Views (%)'].mean():.2f}%")
                    with col2:
                        st.metric("Avg. Comment Rate", f"{engagement_df['Comments/Views (%)'].mean():.2f}%")
                    with col3:
                        st.metric("Avg. Engagement Score", f"{engagement_df['Engagement Score'].mean():.2f}")
                    
                    # Add views performance trend over time if published dates are available
                    if 'Published' in stats['df'].columns:
                        st.subheader("Performance Trends Over Time")
                        
                        # Ensure date is in datetime format
                        try:
                            trend_df = stats['df'].copy()
                            trend_df['Published'] = pd.to_datetime(trend_df['Published'])
                            trend_df = trend_df.sort_values('Published')
                            
                            # Create trend visualization
                            fig = px.scatter(
                                trend_df,
                                x='Published',
                                y='Views',
                                size='Likes',
                                color='Comments',
                                hover_data=['Title'],
                                title="Video Performance Over Time",
                                color_continuous_scale='Viridis'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Add rolling average trendline
                            if len(trend_df) >= 5:  # Only calculate if we have enough data
                                trend_df['Rolling Avg Views (5 videos)'] = trend_df['Views'].rolling(window=5, min_periods=1).mean()
                                
                                fig = px.line(
                                    trend_df,
                                    x='Published',
                                    y='Rolling Avg Views (5 videos)',
                                    title="Rolling Average Views (5 Video Window)",
                                    markers=True
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not analyze trends over time: {str(e)}")
                else:
                    st.info("Engagement metrics require views, likes, and comments data.")
        
        # TAB 3: CORRELATION ANALYSIS
        with video_tabs[2]:
            if not stats['df'].empty and len(stats['df']) >= 5:  # Only show if we have enough data
                st.subheader("Correlation Analysis")
                
                # Get numerical columns for correlation
                numerical_cols = stats['df'].select_dtypes(include=['number']).columns.tolist()
                # Remove non-relevant columns for correlation
                for col in ['Video ID', 'Year', 'Month', 'Day']:
                    if col in numerical_cols:
                        numerical_cols.remove(col)
                
                if len(numerical_cols) >= 2:
                    # Calculate correlation matrix
                    corr_matrix = stats['df'][numerical_cols].corr()
                    
                    # Plot heatmap
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        color_continuous_scale='RdBu_r',
                        title="Correlation Between Metrics",
                        aspect="auto"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Optional scatter plots for key correlations
                    st.subheader("Key Correlations")
                    
                    # Determine most interesting pairs to show
                    key_pairs = [
                        ('Views', 'Likes'),
                        ('Views', 'Comments'),
                        ('Duration_Seconds', 'Views'),
                        ('Duration_Seconds', 'Comments'),
                        ('Likes', 'Comments')
                    ]
                    
                    # Filter to pairs that actually exist in the data
                    available_pairs = [pair for pair in key_pairs if pair[0] in numerical_cols and pair[1] in numerical_cols]
                    
                    if available_pairs:
                        # Create dropdown to select correlation pair
                        pair_labels = [f"{p[0]} vs {p[1]}" for p in available_pairs]
                        selected_pair_idx = st.selectbox(
                            "Select metrics to compare:",
                            range(len(pair_labels)),
                            format_func=lambda i: pair_labels[i]
                        )
                        
                        selected_pair = available_pairs[selected_pair_idx]
                        x_col, y_col = selected_pair
                        
                        # Create scatter plot with trendline
                        fig = px.scatter(
                            stats['df'],
                            x=x_col,
                            y=y_col,
                            trendline="ols",
                            hover_data=['Title', 'Published'],
                            title=f"{x_col} vs {y_col} Correlation",
                            color='Duration_Seconds' if 'Duration_Seconds' in numerical_cols else None,
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show correlation value
                        correlation = corr_matrix.loc[x_col, y_col]
                        st.metric(f"Correlation Coefficient", f"{correlation:.3f}")
                        
                        # Interpret the correlation
                        if abs(correlation) < 0.2:
                            st.info("No meaningful correlation detected.")
                        elif abs(correlation) < 0.4:
                            st.info("Weak correlation detected.")
                        elif abs(correlation) < 0.6:
                            st.info("Moderate correlation detected.")
                        elif abs(correlation) < 0.8:
                            st.info("Strong correlation detected.")
                        else:
                            st.info("Very strong correlation detected.")
                else:
                    st.info("Not enough numerical data for correlation analysis.")
            else:
                st.info("Correlation analysis requires at least 5 videos with numerical metrics.")
        
        # TAB 4: DATA EXPLORER
        with video_tabs[3]:
            st.subheader("Video Data Explorer")
            
            # Allow filtering by various metrics
            col1, col2 = st.columns(2)
            
            with col1:
                # Date range filter
                if 'Published' in stats['df'].columns:
                    try:
                        date_df = stats['df'].copy()
                        date_df['Published'] = pd.to_datetime(date_df['Published'])
                        date_min = date_df['Published'].min().date()
                        date_max = date_df['Published'].max().date()
                        
                        selected_date_range = st.date_input(
                            "Filter by Publish Date:",
                            value=(date_min, date_max),
                            min_value=date_min,
                            max_value=date_max
                        )
                    except:
                        st.warning("Could not parse dates for filtering.")
                        selected_date_range = None
            
            with col2:
                # Add view count range filter
                if 'Views' in stats['df'].columns:
                    views_min = int(stats['df']['Views'].min())
                    views_max = int(stats['df']['Views'].max())
                    views_range = st.slider(
                        "Filter by Views:",
                        min_value=views_min,
                        max_value=views_max,
                        value=(views_min, views_max)
                    )
            
            # Add duration filter if available
            if 'Duration_Seconds' in stats['df'].columns:
                duration_min = int(stats['df']['Duration_Seconds'].min())
                duration_max = int(stats['df']['Duration_Seconds'].max())
                duration_range = st.slider(
                    "Filter by Duration (seconds):",
                    min_value=duration_min,
                    max_value=duration_max,
                    value=(duration_min, duration_max)
                )
            
            # Sort options
            if not stats['df'].empty:
                col1, col2 = st.columns(2)
                with col1:
                    sort_options = {
                        "Most Recent": "Published",
                        "Oldest First": "Published (asc)",
                        "Most Views": "Views",
                        "Most Likes": "Likes",
                        "Most Comments": "Comments",
                        "Longest Duration": "Duration_Seconds",
                        "Shortest Duration": "Duration_Seconds (asc)"
                    }
                    
                    # Filter sort options to only include columns that exist
                    valid_sort_options = {}
                    for label, field in sort_options.items():
                        field_name = field.split(' ')[0]  # Remove (asc) if present
                        if field_name in stats['df'].columns:
                            valid_sort_options[label] = field
                    
                    sort_by = st.selectbox("Sort By:", list(valid_sort_options.keys()))
                
                # Apply filters and sorting
                filtered_df = stats['df'].copy()
                
                # Date filter
                if 'Published' in filtered_df.columns and selected_date_range and len(selected_date_range) == 2:
                    try:
                        filtered_df['Published'] = pd.to_datetime(filtered_df['Published'])
                        filter_start = pd.to_datetime(selected_date_range[0])
                        filter_end = pd.to_datetime(selected_date_range[1])
                        filtered_df = filtered_df[
                            (filtered_df['Published'] >= filter_start) & 
                            (filtered_df['Published'] <= filter_end)
                        ]
                    except:
                        st.warning("Could not apply date filter.")
                
                # Views filter
                if 'Views' in filtered_df.columns and 'views_range' in locals():
                    filtered_df = filtered_df[
                        (filtered_df['Views'] >= views_range[0]) & 
                        (filtered_df['Views'] <= views_range[1])
                    ]
                
                # Duration filter
                if 'Duration_Seconds' in filtered_df.columns and 'duration_range' in locals():
                    filtered_df = filtered_df[
                        (filtered_df['Duration_Seconds'] >= duration_range[0]) & 
                        (filtered_df['Duration_Seconds'] <= duration_range[1])
                    ]
                
                # Sorting
                if sort_by in valid_sort_options:
                    sort_field = valid_sort_options[sort_by]
                    ascending = "(asc)" in sort_field
                    sort_field = sort_field.split(' ')[0]  # Remove (asc) if present
                    
                    if sort_field in filtered_df.columns:
                        filtered_df = filtered_df.sort_values(by=sort_field, ascending=ascending)
                
                # Display filtered data
                st.text(f"Showing {len(filtered_df)} of {len(stats['df'])} videos")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Add export functionality
                if st.button("Export Video Data to CSV"):
                    # Convert to CSV
                    csv = filtered_df.to_csv(index=False)
                    
                    # Create a download button
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="youtube_videos_export.csv",
                        mime="text/csv"
                    )
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
        
        # Main metrics in the header
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Comments", comment_analysis['total_comments'])
        
        # Add metrics for threads if available
        if comment_analysis['thread_data']:
            with col2:
                thread_data = comment_analysis['thread_data']
                top_level = thread_data.get('top_level_count', 0)
                st.metric("Top-level Comments", top_level)
            with col3:
                replies = thread_data.get('reply_count', 0)
                st.metric("Replies", replies)
                
        # Add metrics for likes if available
        if comment_analysis['engagement_data']:
            engagement = comment_analysis['engagement_data']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Comment Likes", f"{int(engagement['total_likes']):,}")
            with col2:
                st.metric("Avg. Likes per Comment", f"{engagement['avg_likes']:.2f}")
            with col3:
                st.metric("Most Likes on a Comment", f"{engagement['max_likes']:,}")
                
            # Show YouTube API limitation notice for comment likes
            if engagement['max_likes'] == 0 or engagement['total_likes'] == 0:
                st.info("**Note about comment likes:** YouTube API has limited access to comment like counts. " + 
                      "Even popular comments may show zero likes due to API restrictions, not because they have no likes on YouTube.")
        
        # Analysis tabs for detailed visualizations
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Temporal Analysis", "Thread Analysis", "Engagement Analysis", "Data Explorer"])
        
        # TAB 1: OVERVIEW
        with tab1:
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
            
            # Show a summary of temporal distribution if available
            if comment_analysis['temporal_data']:
                temporal = comment_analysis['temporal_data']
                
                col1, col2 = st.columns(2)
                with col1:
                    # Day of week distribution
                    if 'weekday' in temporal and not temporal['weekday'].empty:
                        fig = px.bar(
                            temporal['weekday'],
                            x='Weekday',
                            y='Count',
                            title="Comments by Day of Week",
                            color='Count',
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Hour of day distribution
                    if 'hourly' in temporal and not temporal['hourly'].empty:
                        fig = px.line(
                            temporal['hourly'],
                            x='Hour',
                            y='Count',
                            title="Comments by Hour of Day",
                            markers=True
                        )
                        fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
                        st.plotly_chart(fig, use_container_width=True)
        
        # TAB 2: TEMPORAL ANALYSIS
        with tab2:
            if comment_analysis['temporal_data']:
                temporal = comment_analysis['temporal_data']
                
                # Time period selector
                time_period = st.radio(
                    "Select Time Period:",
                    ["Daily", "Weekly", "Monthly", "Hourly"],
                    horizontal=True
                )
                
                if time_period == "Daily" and 'daily' in temporal:
                    # Daily comments over time
                    st.subheader("Comments by Day")
                    
                    # Allow filtering the date range
                    date_range = st.slider(
                        "Select Date Range",
                        min_value=temporal['daily']['Date'].min(),
                        max_value=temporal['daily']['Date'].max(),
                        value=(temporal['daily']['Date'].min(), temporal['daily']['Date'].max())
                    )
                    
                    # Filter data based on selection
                    filtered_daily = temporal['daily'][
                        (temporal['daily']['Date'] >= date_range[0]) & 
                        (temporal['daily']['Date'] <= date_range[1])
                    ]
                    
                    # Create the visualization
                    fig = px.line(
                        filtered_daily,
                        x='Date',
                        y='Count',
                        title="Daily Comment Activity",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show daily stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Comments/Day", f"{filtered_daily['Count'].mean():.2f}")
                    with col2:
                        st.metric("Max Comments/Day", filtered_daily['Count'].max())
                    with col3:
                        st.metric("Days with Comments", len(filtered_daily))
                
                elif time_period == "Monthly" and 'monthly' in temporal:
                    # Monthly analysis
                    st.subheader("Comments by Month")
                    
                    fig = px.bar(
                        temporal['monthly'],
                        x='YearMonth', 
                        y='Count',
                        title="Monthly Comment Activity",
                        color='Count',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show monthly stats
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Average Comments/Month", f"{temporal['monthly']['Count'].mean():.2f}")
                    with col2:
                        st.metric("Max Comments/Month", temporal['monthly']['Count'].max())
                
                elif time_period == "Weekly" and 'weekday' in temporal:
                    # Weekly pattern analysis
                    st.subheader("Comments by Day of Week")
                    
                    fig = px.bar(
                        temporal['weekday'],
                        x='Weekday',
                        y='Count',
                        title="Comment Distribution by Day of Week",
                        color='Count',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calculate percentage distribution
                    total = temporal['weekday']['Count'].sum()
                    temporal['weekday']['Percentage'] = (temporal['weekday']['Count'] / total * 100).round(1)
                    
                    # Show as pie chart too
                    fig = px.pie(
                        temporal['weekday'],
                        values='Percentage',
                        names='Weekday',
                        title="Distribution of Comments by Day of Week (%)",
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif time_period == "Hourly" and 'hourly' in temporal:
                    # Hourly pattern analysis
                    st.subheader("Comments by Hour of Day")
                    
                    # Create a more visually appealing 24-hour distribution
                    fig = px.bar(
                        temporal['hourly'],
                        x='Hour',
                        y='Count',
                        title="Comment Distribution by Hour of Day",
                        color='Count',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Time periods
                    morning = temporal['hourly'][(temporal['hourly']['Hour'] >= 5) & (temporal['hourly']['Hour'] < 12)]['Count'].sum()
                    afternoon = temporal['hourly'][(temporal['hourly']['Hour'] >= 12) & (temporal['hourly']['Hour'] < 17)]['Count'].sum()
                    evening = temporal['hourly'][(temporal['hourly']['Hour'] >= 17) & (temporal['hourly']['Hour'] < 22)]['Count'].sum()
                    night = temporal['hourly'][(temporal['hourly']['Hour'] >= 22) | (temporal['hourly']['Hour'] < 5)]['Count'].sum()
                    
                    # Create a time period summary
                    time_period_df = pd.DataFrame({
                        'Time Period': ['Morning (5AM-12PM)', 'Afternoon (12PM-5PM)', 'Evening (5PM-10PM)', 'Night (10PM-5AM)'],
                        'Count': [morning, afternoon, evening, night]
                    })
                    
                    # Show as a visual
                    fig = px.pie(
                        time_period_df,
                        values='Count',
                        names='Time Period',
                        title="Distribution of Comments by Time of Day",
                        color_discrete_sequence=px.colors.sequential.Viridis
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Temporal analysis data is not available. This may be due to missing or improperly formatted timestamp data.")
        
        # TAB 3: THREAD ANALYSIS
        with tab3:
            if comment_analysis['thread_data'] and 'top_threads' in comment_analysis['thread_data']:
                thread_data = comment_analysis['thread_data']
                
                # Display metrics about conversation threads
                col1, col2, col3 = st.columns(3)
                with col1:
                    thread_count = len(thread_data.get('thread_counts', []))
                    st.metric("Conversation Threads", thread_count)
                with col2:
                    avg_replies = thread_data['reply_count'] / thread_count if thread_count > 0 else 0
                    st.metric("Avg. Replies per Thread", f"{avg_replies:.2f}")
                with col3:
                    if 'thread_counts' in thread_data and len(thread_data['thread_counts']) > 0:
                        max_replies = thread_data['thread_counts']['Reply Count'].max()
                        st.metric("Most Replies in a Thread", max_replies)
                
                # Show top threads
                st.subheader("Most Active Conversation Threads")
                
                # Create a bar chart of top threads
                if 'top_threads' in thread_data and thread_data['top_threads']:
                    # Extract data for visualization
                    top_threads_df = pd.DataFrame(thread_data['top_threads'])
                    
                    # Truncate text for display
                    top_threads_df['display_text'] = top_threads_df['parent_text'].str.slice(0, 50) + '...'
                    
                    # Create bar chart
                    fig = px.bar(
                        top_threads_df,
                        x='reply_count',
                        y='display_text',
                        orientation='h',
                        title="Top Conversation Threads by Reply Count",
                        color='reply_count',
                        color_continuous_scale='Viridis',
                        hover_data=['parent_author', 'parent_likes', 'video']
                    )
                    fig.update_layout(height=400, yaxis_title="Original Comment")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show detailed view of threads
                    with st.expander("View Thread Details", expanded=False):
                        for i, thread in enumerate(thread_data['top_threads']):
                            st.markdown(f"**Thread #{i+1} - {thread['reply_count']} replies**")
                            st.markdown(f"**Video:** {thread['video']}")
                            st.markdown(f"**Author:** {thread['parent_author']} | **Likes:** {thread['parent_likes']}")
                            st.markdown(f"**Comment:** {thread['parent_text']}")
                            st.divider()
            else:
                st.info("Thread analysis is not available. This could be because the comments don't contain reply information or there are no conversation threads in the data.")
        
        # TAB 4: ENGAGEMENT ANALYSIS
        with tab4:
            if comment_analysis['engagement_data']:
                engagement = comment_analysis['engagement_data']
                
                # Distribution of likes on comments
                st.subheader("Comment Likes Distribution")
                
                # Create a histogram of likes
                df = comment_analysis['df']
                fig = px.histogram(
                    df,
                    x='Likes',
                    nbins=30,
                    title="Distribution of Likes on Comments",
                    color_discrete_sequence=['#3366CC']
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Top liked comments
                st.subheader("Most Liked Comments")
                
                # Show a bar chart of top liked comments
                if 'top_liked_comments' in engagement:
                    top_likes = engagement['top_liked_comments']
                    
                    # Process for display
                    top_likes_display = top_likes.copy()
                    top_likes_display['Short Text'] = top_likes_display['Text'].str.slice(0, 50) + '...'
                    
                    # Create visualization
                    fig = px.bar(
                        top_likes_display.head(10),
                        x='Likes',
                        y='Short Text',
                        orientation='h',
                        title="Top 10 Most Liked Comments",
                        color='Likes',
                        color_continuous_scale='Viridis',
                        hover_data=['Author', 'Video']
                    )
                    fig.update_layout(height=400, yaxis_title="Comment")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show detailed view of top comments
                    with st.expander("View Top Comments Details", expanded=False):
                        for i, (_, comment) in enumerate(top_likes.head(10).iterrows()):
                            st.markdown(f"**#{i+1} - {comment['Likes']} likes**")
                            st.markdown(f"**Video:** {comment['Video']}")
                            st.markdown(f"**Author:** {comment['Author']}")
                            st.markdown(f"**Comment:** {comment['Text']}")
                            st.divider()
            else:
                st.info("Engagement analysis is not available. This may be due to missing like count data in the comments.")
        
        # TAB 5: DATA EXPLORER
        with tab5:
            st.subheader("Comment Data Explorer")
            
            # Show options for display format
            display_format = st.radio(
                "Display Format:",
                ["Threaded View", "Flat Table"],
                horizontal=True
            )
            
            # Allow filtering by various attributes
            col1, col2 = st.columns(2)
            with col1:
                # Filter by video
                if 'Video' in comment_analysis['df'].columns:
                    videos = comment_analysis['df']['Video'].unique()
                    selected_video = st.selectbox("Filter by Video:", ["All Videos"] + list(videos))
            
            with col2:
                # Filter by date range if available
                if 'Date' in comment_analysis['df'].columns:
                    date_min = comment_analysis['df']['Date'].min()
                    date_max = comment_analysis['df']['Date'].max()
                    selected_date_range = st.date_input(
                        "Filter by Date Range:",
                        value=(date_min, date_max),
                        min_value=date_min,
                        max_value=date_max
                    )
            
            # Additional filters
            col1, col2, col3 = st.columns(3)
            
            # Initialize likes_range with default values
            likes_min = 0
            likes_max = 0
            
            with col1:
                # Filter by likes range
                if 'Likes' in comment_analysis['df'].columns:
                    likes_max = int(comment_analysis['df']['Likes'].max())
                    if likes_max <= 0:
                        # Handle the case where max likes is 0 to avoid the slider error
                        st.write("No comments have likes")
                        likes_range = (0, 0)  # Set default range when no likes
                    else:
                        likes_range = st.slider("Filter by Likes:", 0, max(1, likes_max), (0, likes_max))
                else:
                    st.write("Like data not available")
                    likes_range = (0, 0)  # Set default range when no like data
            
            with col2:
                # Filter by comment type
                if 'Is Reply' in comment_analysis['df'].columns:
                    comment_type = st.selectbox(
                        "Comment Type:",
                        ["All Comments", "Top-level Comments Only", "Replies Only"]
                    )
            
            with col3:
                # Sort options
                sort_options = {
                    "Most Recent": ("Date", False) if "Date" in comment_analysis['df'].columns else ("Published", False),
                    "Oldest First": ("Date", True) if "Date" in comment_analysis['df'].columns else ("Published", True),
                    "Most Likes": ("Likes", False),
                    "Video (A-Z)": ("Video", True)
                }
                sort_by = st.selectbox("Sort By:", list(sort_options.keys()))
            
            # Apply filters
            filtered_df = comment_analysis['df'].copy()
            
            # Video filter
            if 'Video' in filtered_df.columns and selected_video != "All Videos":
                filtered_df = filtered_df[filtered_df['Video'] == selected_video]
            
            # Date filter if available
            if 'Date' in filtered_df.columns and len(selected_date_range) == 2:
                filtered_df = filtered_df[
                    (filtered_df['Date'] >= selected_date_range[0]) & 
                    (filtered_df['Date'] <= selected_date_range[1])
                ]
            
            # Likes filter - make sure likes_range is defined before using it
            if 'Likes' in filtered_df.columns and 'likes_range' in locals():
                filtered_df = filtered_df[
                    (filtered_df['Likes'] >= likes_range[0]) & 
                    (filtered_df['Likes'] <= likes_range[1])
                ]
            
            # Comment type filter
            if 'Is Reply' in filtered_df.columns:
                if comment_type == "Top-level Comments Only":
                    filtered_df = filtered_df[~filtered_df['Is Reply']]
                elif comment_type == "Replies Only":
                    filtered_df = filtered_df[filtered_df['Is Reply']]
            
            # Apply sorting
            if sort_by in sort_options:
                sort_col, sort_asc = sort_options[sort_by]
                if sort_col in filtered_df.columns:
                    filtered_df = filtered_df.sort_values(by=sort_col, ascending=sort_asc)
            
            # Display total count
            st.text(f"Showing {len(filtered_df)} of {len(comment_analysis['df'])} comments")
            
            # Display based on chosen format
            if display_format == "Flat Table":
                # Display filtered and sorted data as a flat table
                st.dataframe(filtered_df, use_container_width=True)
            else:
                # Display in threaded view using thread_structure
                if 'thread_data' in comment_analysis and 'thread_structure' in comment_analysis['thread_data']:
                    # Get thread structure
                    thread_structure = comment_analysis['thread_data']['thread_structure']
                    
                    # Apply filtering to thread structure
                    filtered_threads = {}
                    
                    # First get all root comments that pass the filter
                    for comment_id, thread in thread_structure.items():
                        # Extract the root comment
                        root_comment = thread['comment']
                        
                        # Check if this root comment passes all filters
                        passes_filter = True
                        
                        # Video filter
                        if 'Video' in root_comment and selected_video != "All Videos":
                            if root_comment['Video'] != selected_video:
                                passes_filter = False
                        
                        # Date filter
                        if 'Date' in root_comment and len(selected_date_range) == 2:
                            comment_date = root_comment['Date']
                            if isinstance(comment_date, str):
                                try:
                                    comment_date = pd.to_datetime(comment_date).date()
                                except:
                                    passes_filter = False
                            
                            if not (selected_date_range[0] <= comment_date <= selected_date_range[1]):
                                passes_filter = False
                        
                        # Likes filter
                        if 'Likes' in root_comment and 'likes_range' in locals():
                            if not (likes_range[0] <= root_comment['Likes'] <= likes_range[1]):
                                passes_filter = False
                        
                        # If the root comment passes filters, add it and filter its replies
                        if passes_filter and (comment_type != "Replies Only"):
                            filtered_replies = []
                            
                            # Filter replies
                            for reply in thread['replies']:
                                reply_passes = True
                                
                                # Date filter for reply
                                if 'Date' in reply and len(selected_date_range) == 2:
                                    reply_date = reply['Date']
                                    if isinstance(reply_date, str):
                                        try:
                                            reply_date = pd.to_datetime(reply_date).date()
                                        except:
                                            reply_passes = False
                                    
                                    if not (selected_date_range[0] <= reply_date <= selected_date_range[1]):
                                        reply_passes = False
                                
                                # Likes filter for reply
                                if 'Likes' in reply and 'likes_range' in locals():
                                    if not (likes_range[0] <= reply['Likes'] <= likes_range[1]):
                                        reply_passes = False
                                
                                if reply_passes:
                                    filtered_replies.append(reply)
                            
                            # Add to filtered threads if there are any replies or if showing all comments
                            if filtered_replies or comment_type != "Replies Only":
                                filtered_threads[comment_id] = {
                                    'comment': root_comment,
                                    'replies': filtered_replies
                                }
                        # Add threads if only viewing replies and it has replies that pass filter
                        elif comment_type == "Replies Only":
                            filtered_replies = []
                            
                            # Filter replies
                            for reply in thread['replies']:
                                reply_passes = True
                                
                                # Date filter for reply
                                if 'Date' in reply and len(selected_date_range) == 2:
                                    reply_date = reply['Date']
                                    if isinstance(reply_date, str):
                                        try:
                                            reply_date = pd.to_datetime(reply_date).date()
                                        except:
                                            reply_passes = False
                                    
                                    if not (selected_date_range[0] <= reply_date <= selected_date_range[1]):
                                        reply_passes = False
                                
                                # Likes filter for reply
                                if 'Likes' in reply and 'likes_range' in locals():
                                    if not (likes_range[0] <= reply['Likes'] <= likes_range[1]):
                                        reply_passes = False
                                
                                if reply_passes:
                                    filtered_replies.append(reply)
                            
                            # Add to filtered threads if there are any replies
                            if filtered_replies:
                                filtered_threads[comment_id] = {
                                    'comment': root_comment,
                                    'replies': filtered_replies
                                }
                    
                    # Display the filtered threads
                    if filtered_threads:
                        # Get a sorted list of root comments based on the selected sort option
                        root_comments = []
                        for comment_id, thread in filtered_threads.items():
                            root_comments.append(thread['comment'])
                        
                        # Sort root comments
                        if sort_by in sort_options:
                            sort_col, sort_asc = sort_options[sort_by]
                            if sort_col in root_comments[0]:
                                root_comments.sort(key=lambda x: x.get(sort_col, 0), reverse=not sort_asc)
                        
                        # Display each thread as a card with native Streamlit components
                        for root_comment in root_comments:
                            comment_id = root_comment['Comment ID']
                            thread = filtered_threads.get(comment_id, {'replies': []})
                            
                            # Create an expander for each thread - limit the preview text
                            preview_text = root_comment['Text'][:80] + "..." if len(root_comment['Text']) > 80 else root_comment['Text']
                            with st.expander(f"{root_comment['Author']}: {preview_text}", expanded=False):
                                # Display root comment
                                st.markdown(f"**{root_comment['Author']}** • ❤️ {root_comment['Likes']}")
                                st.markdown(f"_Video: {root_comment['Video']} • {root_comment['Published']}_")
                                st.markdown(root_comment['Text'])
                                st.markdown(f"_ID: {root_comment['Comment ID']}_")
                                
                                # Display replies if any
                                if thread['replies']:
                                    # Sort replies
                                    replies = thread['replies']
                                    if sort_by in sort_options:
                                        sort_col, sort_asc = sort_options[sort_by]
                                        if sort_col in replies[0]:
                                            replies.sort(key=lambda x: x.get(sort_col, 0), reverse=not sort_asc)
                                    
                                    st.markdown("### Replies")
                                    
                                    # Loop through all replies
                                    for reply in replies:
                                        # Create a container with a border for each reply
                                        with st.container():
                                            # Add indentation for replies to visually group them
                                            cols = st.columns([1, 20])
                                            
                                            # In the first column just add a vertical line for indentation
                                            with cols[0]:
                                                st.markdown("│")
                                            
                                            # In the second column show the reply content
                                            with cols[1]:
                                                st.markdown(f"**{reply['Author']}** • ❤️ {reply['Likes']}")
                                                st.markdown(f"_{reply['Published']}_")
                                                st.markdown(reply['Text'])
                                                st.markdown(f"_ID: {reply['Comment ID']}_")
                                        
                                        # Add a small separator between replies
                                        st.markdown("---")
                    else:
                        st.info("No comments match the selected filters.")
                else:
                    st.warning("Threaded view not available for this dataset. Using flat table view instead.")
                    st.dataframe(filtered_df, use_container_width=True)
            
            # Text search in comments
            st.subheader("Search in Comments")
            search_query = st.text_input("Enter search text:")
            
            if search_query:
                # Perform case-insensitive search
                search_results = comment_analysis['df'][
                    comment_analysis['df']['Text'].str.contains(search_query, case=False, na=False)
                ]
                
                st.text(f"Found {len(search_results)} comments containing '{search_query}'")
                st.dataframe(search_results, use_container_width=True)
            
            # Export options
            if st.button("Export Comment Data to CSV"):
                # Convert to CSV
                csv = filtered_df.to_csv(index=False)
                
                # Create a download button
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="youtube_comments_export.csv",
                    mime="text/csv"
                )
    else:
        st.info("No comments found for the videos in this channel")