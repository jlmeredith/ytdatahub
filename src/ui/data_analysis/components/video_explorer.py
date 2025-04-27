"""
Video explorer component for the data analysis UI.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.helpers import paginate_dataframe, render_pagination_controls
from src.ui.data_analysis.utils.session_state import initialize_pagination, get_pagination_state, update_pagination_state

def render_video_explorer(channel_data):
    """
    Render the video explorer component.
    
    Args:
        channel_data: Dictionary containing channel data
    """
    # Initialize analysis
    analysis = YouTubeAnalysis()
    
    # Get video statistics
    video_stats = analysis.get_video_statistics(channel_data)
    
    if video_stats['df'] is None or video_stats['df'].empty:
        st.info("No video data available for this channel.")
        return
        
    df = video_stats['df']
    
    # Create dashboard-style header with metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Videos", f"{len(df):,}")
    
    with col2:
        total_views = int(df['Views'].sum()) if 'Views' in df.columns else 0
        st.metric("Total Views", f"{total_views:,}")
    
    with col3:
        avg_views = int(df['Views'].mean()) if 'Views' in df.columns and len(df) > 0 else 0
        st.metric("Average Views", f"{avg_views:,}")
    
    # Add a performance distribution chart
    st.subheader("Video Performance Distribution")
    
    perf_col1, perf_col2 = st.columns([3, 2])
    
    with perf_col1:
        # Create a distribution chart of views
        if 'Views' in df.columns:
            try:
                # Set a reasonable upper limit to prevent skewing by outliers
                views_upper_limit = np.percentile(df['Views'], 95) * 1.5
                views_filtered = df[df['Views'] <= views_upper_limit]
                
                # Create histogram
                views_fig = px.histogram(
                    views_filtered, 
                    x='Views',
                    nbins=20, 
                    title="Views Distribution",
                    labels={'Views': 'View Count'},
                    opacity=0.8,
                    color_discrete_sequence=['#1E88E5']
                )
                
                # Improve layout
                views_fig.update_layout(
                    xaxis_title="Views",
                    yaxis_title="Number of Videos",
                    bargap=0.1,
                    plot_bgcolor='rgba(245, 245, 245, 0.95)',
                    height=300
                )
                
                st.plotly_chart(views_fig, use_container_width=True)
                
                # Add explanation for the distribution
                if np.percentile(df['Views'], 75) > (np.percentile(df['Views'], 50) * 2):
                    st.info("Your views distribution shows a long tail, which is typical for YouTube channels. A few videos drive most of your views.")
            except Exception as e:
                st.error(f"Error generating views distribution: {str(e)}")
    
    with perf_col2:
        # Create a ratio chart (likes/views)
        if 'Likes' in df.columns and 'Views' in df.columns:
            try:
                # Calculate like/view ratio and filter out NaN values
                df['LikeViewRatio'] = df['Likes'] / df['Views'] * 100
                # Remove infinite values and NaNs
                df['LikeViewRatio'] = df['LikeViewRatio'].replace([np.inf, -np.inf], np.nan)
                ratio_df = df.dropna(subset=['LikeViewRatio'])
                
                if not ratio_df.empty:
                    # Calculate average ratio
                    avg_ratio = ratio_df['LikeViewRatio'].mean()
                    
                    # Create scatter plot of likes vs views
                    ratio_fig = px.scatter(
                        ratio_df,
                        x='Views',
                        y='Likes',
                        hover_name='Title',
                        log_x=True,
                        log_y=True,
                        title=f"Likes vs Views (Avg Ratio: {avg_ratio:.2f}%)",
                        opacity=0.7,
                        color='LikeViewRatio',
                        color_continuous_scale='Viridis',
                        size='LikeViewRatio',
                        size_max=15
                    )
                    
                    # Improve layout
                    ratio_fig.update_layout(
                        height=300,
                        plot_bgcolor='rgba(245, 245, 245, 0.95)',
                        coloraxis_colorbar=dict(
                            title="Like/View %"
                        )
                    )
                    
                    st.plotly_chart(ratio_fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating engagement ratio chart: {str(e)}")
    
    # Add filter and sort options
    st.subheader("Video Explorer")
    
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    
    with filter_col1:
        # Search filter
        search_term = st.text_input("Search in video titles:", "")
    
    with filter_col2:
        # Sort options
        sort_options = {
            "Newest First": ("Published", False),
            "Oldest First": ("Published", True),
            "Most Views": ("Views", False),
            "Least Views": ("Views", True),
            "Most Likes": ("Likes", False),
            "Least Likes": ("Likes", True),
            "Most Comments": ("Comments", False),
            "Least Comments": ("Comments", True),
            "Longest Duration": ("Duration_Seconds", False),
            "Shortest Duration": ("Duration_Seconds", True)
        }
        
        # Use the preferred sort from session state
        default_sort = st.session_state.get("video_sort_by", "Published (Newest)")
        # Map old sort names to new ones
        if default_sort == "Published (Newest)":
            default_sort = "Newest First"
        elif default_sort == "Published (Oldest)":
            default_sort = "Oldest First"
        elif default_sort == "Views (Highest)":
            default_sort = "Most Views"
        elif default_sort == "Views (Lowest)":
            default_sort = "Least Views"
        elif default_sort == "Likes (Highest)":
            default_sort = "Most Likes"
        elif default_sort == "Duration (Longest)":
            default_sort = "Longest Duration"
        
        # Get index, defaulting to 0 if not found
        default_index = list(sort_options.keys()).index(default_sort) if default_sort in sort_options else 0
        
        sort_by = st.selectbox("Sort by:", options=list(sort_options.keys()), index=default_index)
        
        # Update session state with selection
        if sort_by == "Newest First":
            st.session_state.video_sort_by = "Published (Newest)"
        elif sort_by == "Oldest First":
            st.session_state.video_sort_by = "Published (Oldest)"
        elif sort_by == "Most Views":
            st.session_state.video_sort_by = "Views (Highest)"
        elif sort_by == "Least Views":
            st.session_state.video_sort_by = "Views (Lowest)"
        elif sort_by == "Most Likes":
            st.session_state.video_sort_by = "Likes (Highest)"
        elif sort_by == "Longest Duration":
            st.session_state.video_sort_by = "Duration (Longest)"
        else:
            st.session_state.video_sort_by = sort_by
    
    with filter_col3:
        # Date range filter if we have dates
        if 'Published' in df.columns:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_dtype(df['Published']):
                try:
                    df['Published'] = pd.to_datetime(df['Published'])
                except:
                    pass
            
            try:
                min_date = df['Published'].min()
                max_date = df['Published'].max()
                
                # Only show date filter if we have valid dates
                if min_date and max_date:
                    # For better UX, we'll use a single-select dropdown for common date ranges
                    date_ranges = [
                        "All Time",
                        "Last 90 Days",
                        "Last 180 Days",
                        "Last Year",
                        "Last 2 Years",
                        "Last 3 Years"
                    ]
                    
                    date_filter = st.selectbox("Date Range:", date_ranges)
            except:
                date_filter = "All Time"
        else:
            date_filter = "All Time"
    
    # Apply filters and sorting
    filtered_df = df.copy()
    
    # Apply search filter
    if search_term:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search_term, case=False)]
    
    # Apply date filter if available
    if 'Published' in filtered_df.columns and date_filter != "All Time":
        try:
            # Make sure Published is datetime
            if not pd.api.types.is_datetime64_dtype(filtered_df['Published']):
                filtered_df['Published'] = pd.to_datetime(filtered_df['Published'])
            
            today = datetime.now()
            
            if date_filter == "Last 90 Days":
                start_date = today - timedelta(days=90)
            elif date_filter == "Last 180 Days":
                start_date = today - timedelta(days=180)
            elif date_filter == "Last Year":
                start_date = today - timedelta(days=365)
            elif date_filter == "Last 2 Years":
                start_date = today - timedelta(days=730)
            elif date_filter == "Last 3 Years":
                start_date = today - timedelta(days=1095)
            
            filtered_df = filtered_df[filtered_df['Published'] >= start_date]
        except Exception as e:
            st.error(f"Error applying date filter: {str(e)}")
    
    # Apply sorting
    if sort_by in sort_options:
        sort_col, sort_asc = sort_options[sort_by]
        if sort_col in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=sort_asc)
    
    # Initialize pagination with page size from session state
    initialize_pagination("video", page=1, page_size=st.session_state.get("video_page_size", 10))
    
    # Get current pagination values
    current_page, page_size = get_pagination_state("video")
    
    # Render pagination for videos table
    new_page = render_pagination_controls(
        len(filtered_df), 
        page_size, 
        current_page,
        "video"
    )
    
    # Update page state if changed
    if update_pagination_state("video", new_page):
        current_page = new_page
    
    # Get paginated dataframe
    paginated_df = paginate_dataframe(filtered_df, page_size, current_page)
    
    # Show results count
    st.write(f"Showing {len(paginated_df)} of {len(filtered_df)} videos")
    
    # Display toggle for view mode
    display_options = ["Grid View", "Table View", "Card View"]
    selected_view = st.radio("Display as:", display_options, horizontal=True)
    
    # Display videos based on view mode
    if selected_view == "Grid View":
        render_videos_grid(paginated_df)
    elif selected_view == "Card View":
        render_videos_cards(paginated_df)
    else:
        # Enhanced table view
        render_videos_table(paginated_df)

def render_videos_table(df):
    """
    Render videos in a well-formatted table view.
    
    Args:
        df: DataFrame containing video data
    """
    # Format columns for better readability
    display_df = df.copy()
    
    # Make date column human-readable
    if 'Published' in display_df.columns:
        if pd.api.types.is_datetime64_dtype(display_df['Published']):
            display_df['Published'] = display_df['Published'].dt.strftime('%b %d, %Y')
    
    # Format numeric columns
    if 'Views' in display_df.columns:
        display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}")
    if 'Likes' in display_df.columns:
        display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}")
    if 'Comments' in display_df.columns:
        display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}")
    
    # Truncate title if too long
    if 'Title' in display_df.columns:
        display_df['Title'] = display_df['Title'].apply(lambda x: (x[:80] + '...') if len(x) > 80 else x)
    
    # Select columns to display
    columns_to_display = ['Title', 'Published', 'Views', 'Likes', 'Comments', 'Duration']
    columns_to_display = [col for col in columns_to_display if col in display_df.columns]
    
    # Display as table
    st.dataframe(display_df[columns_to_display], use_container_width=True)
    
    # Add export option
    if st.button("Export to CSV"):
        # Create a CSV download link
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"youtube_videos_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def render_videos_grid(df):
    """
    Render videos in a responsive grid layout.
    
    Args:
        df: DataFrame containing video data
    """
    # Check if thumbnail display is enabled
    show_thumbnails = st.session_state.get("show_video_thumbnails", True)
    
    # Add CSS for grid layout
    st.markdown("""
    <style>
    .video-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        grid-gap: 20px;
        margin-bottom: 20px;
    }
    .video-item {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        background-color: #fff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .video-header {
        display: flex;
        margin-bottom: 10px;
    }
    .video-thumbnail {
        width: 120px;
        height: 67px;
        margin-right: 10px;
        background-color: #eee;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        overflow: hidden;
    }
    .video-thumbnail img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .placeholder-thumbnail {
        width: 100%;
        height: 100%;
        background-color: #eee;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .video-title {
        flex: 1;
    }
    .video-title h3 {
        margin: 0;
        font-size: 16px;
        line-height: 1.3;
        margin-bottom: 5px;
    }
    .video-date {
        font-size: 12px;
        color: #666;
    }
    .video-stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-bottom: 10px;
    }
    .stat-item {
        font-size: 14px;
    }
    .stat-label {
        font-weight: bold;
        margin-right: 5px;
    }
    .video-links {
        text-align: right;
    }
    .video-link {
        display: inline-block;
        padding: 5px 10px;
        background-color: #f5f5f5;
        border-radius: 4px;
        font-size: 14px;
        color: #065fd4;
        text-decoration: none;
    }
    .video-link:hover {
        background-color: #e5e5e5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a list of rows for the grid
    items_per_row = 3
    num_rows = (len(df) + items_per_row - 1) // items_per_row
    
    # Start the grid container
    st.markdown('<div class="video-grid">', unsafe_allow_html=True)
    
    # Render each video as a grid item
    for _, video in df.iterrows():
        # Format date
        published_date = ""
        if 'Published' in video:
            if hasattr(video['Published'], 'strftime'):
                published_date = video['Published'].strftime('%b %d, %Y')
            else:
                published_date = str(video['Published'])
        
        # Format video ID
        video_id = video.get('Video ID', '')
        video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else "#"
        
        # Format thumbnail URL (either from the data or generate from video ID)
        thumbnail_url = video.get('Thumbnail', '')
        if not thumbnail_url and video_id:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
        
        # Create thumbnail HTML based on settings
        thumbnail_html = ""
        if show_thumbnails:
            if thumbnail_url:
                thumbnail_html = f'<div class="video-thumbnail"><img src="{thumbnail_url}" alt="{video.get("Title", "Video")}"></div>'
            else:
                thumbnail_html = '<div class="video-thumbnail"><div class="placeholder-thumbnail">No Thumbnail</div></div>'
        
        # Render grid item
        st.markdown(f"""
        <div class="video-item">
            <div class="video-header">
                {thumbnail_html}
                <div class="video-title">
                    <h3>{video.get('Title', 'Untitled Video')}</h3>
                    <div class="video-date">{published_date}</div>
                </div>
            </div>
            <div class="video-stats">
                <div class="stat-item">
                    <span class="stat-label">Views:</span> {video.get('Views', 0):,}
                </div>
                <div class="stat-item">
                    <span class="stat-label">Likes:</span> {video.get('Likes', 0):,}
                </div>
                <div class="stat-item">
                    <span class="stat-label">Comments:</span> {video.get('Comments', 0):,}
                </div>
                <div class="stat-item">
                    <span class="stat-label">Duration:</span> {video.get('Duration', 'N/A')}
                </div>
            </div>
            <div class="video-links">
                <a href="{video_url}" target="_blank" class="video-link">Watch on YouTube</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close the grid container
    st.markdown('</div>', unsafe_allow_html=True)

def render_videos_cards(df):
    """
    Render videos in a card layout with expandable details.
    
    Args:
        df: DataFrame containing video data
    """
    # Show thumbnails based on setting
    show_thumbnails = st.session_state.get("show_video_thumbnails", True)
    
    # Process each video
    for _, video in df.iterrows():
        # Format date
        published_date = ""
        if 'Published' in video:
            if hasattr(video['Published'], 'strftime'):
                published_date = video['Published'].strftime('%b %d, %Y')
            else:
                published_date = str(video['Published'])
        
        # Create a card with expander for each video
        with st.expander(f"{video.get('Title', 'Untitled Video')} - {published_date}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display thumbnail if available and enabled
                if show_thumbnails:
                    video_id = video.get('Video ID', '')
                    thumbnail_url = video.get('Thumbnail', '')
                    
                    if not thumbnail_url and video_id:
                        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                    
                    if thumbnail_url:
                        st.image(thumbnail_url, use_column_width=True)
                
                # Display key metrics
                st.metric("Views", f"{video.get('Views', 0):,}")
                st.metric("Likes", f"{video.get('Likes', 0):,}")
            
            with col2:
                # Video details
                st.subheader("Video Details")
                
                details_col1, details_col2 = st.columns(2)
                
                with details_col1:
                    st.markdown(f"**Duration:** {video.get('Duration', 'N/A')}")
                    st.markdown(f"**Comments:** {video.get('Comments', 0):,}")
                
                with details_col2:
                    # Calculate engagement rate
                    views = video.get('Views', 0)
                    likes = video.get('Likes', 0)
                    comments = video.get('Comments', 0)
                    
                    if views > 0:
                        engagement_rate = (likes + comments) / views * 100
                        st.markdown(f"**Engagement Rate:** {engagement_rate:.2f}%")
                    
                    # Calculate like/view ratio
                    if views > 0:
                        like_view_ratio = likes / views * 100
                        st.markdown(f"**Like/View Ratio:** {like_view_ratio:.2f}%")
                
                # Display video link
                video_id = video.get('Video ID', '')
                if video_id:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    st.markdown(f"[Watch on YouTube]({video_url})")
                
                # Display description if available
                if 'Description' in video and video['Description']:
                    with st.expander("Video Description"):
                        st.markdown(video['Description'])