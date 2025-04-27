"""
Video explorer component for the data analysis UI.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.helpers import paginate_dataframe, render_pagination_controls
from src.ui.data_analysis.utils.session_state import initialize_pagination, get_pagination_state, update_pagination_state
from src.ui.components.ui_utils import render_template_as_markdown

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
    
    if video_stats['df'] is None:
        st.info("No video data available for this channel.")
        return
        
    df = video_stats['df']
    
    # Add filter and sort options
    st.subheader("Filter and Sort Options")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Search filter
        search_term = st.text_input("Search in video titles:", "")
    
    with col2:
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
        
        sort_by = st.selectbox("Sort by:", options=list(sort_options.keys()), index=0)
    
    with col3:
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
    
    # Initialize pagination
    initialize_pagination("video")
    
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
    
    # Get page size (might have been updated in the controls)
    _, page_size = get_pagination_state("video")
    
    # Get paginated dataframe
    paginated_df = paginate_dataframe(filtered_df, page_size, current_page)
    
    # Show results count
    st.write(f"Showing {len(paginated_df)} of {len(filtered_df)} videos")
    
    # Display toggle for view mode
    view_mode = "Grid View" if "grid_view" in st.session_state and st.session_state.grid_view else "List View"
    if st.checkbox(f"Use {view_mode}", value=True):
        st.session_state.grid_view = view_mode == "List View"  # Toggle
        view_mode = "Grid View" if st.session_state.grid_view else "List View"
    
    # Display videos based on view mode
    if "grid_view" in st.session_state and st.session_state.grid_view:
        render_videos_grid(paginated_df)
    else:
        # Fallback to dataframe view
        st.dataframe(paginated_df, use_container_width=True)

def render_videos_grid(df):
    """
    Render videos in a responsive grid layout using templates.
    
    Args:
        df: DataFrame containing video data
    """
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
    .video-description {
        font-size: 14px;
        color: #333;
        margin-bottom: 10px;
        max-height: 80px;
        overflow: hidden;
        text-overflow: ellipsis;
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
    
    # Start the grid container
    st.markdown('<div class="video-grid">', unsafe_allow_html=True)
    
    # Render each video using the template
    for _, video in df.iterrows():
        # Prepare template context
        context = {
            'title': video.get('Title', 'Untitled Video'),
            'published_date': video.get('Published', '').strftime('%b %d, %Y') if hasattr(video.get('Published', ''), 'strftime') else str(video.get('Published', '')),
            'views_formatted': f"{video.get('Views', 0):,}",
            'likes_formatted': f"{video.get('Likes', 0):,}",
            'comments_formatted': f"{video.get('Comments', 0):,}",
            'duration': video.get('Duration', 'Unknown'),
            'description': video.get('Description', '')[:150] + '...' if len(video.get('Description', '')) > 150 else video.get('Description', ''),
            'video_url': f"https://www.youtube.com/watch?v={video.get('VideoId')}" if 'VideoId' in video else None,
            'thumbnail_url': video.get('Thumbnail', None)
        }
        
        # Render the video item using template
        render_template_as_markdown("video_item.html", context)
    
    # Close the grid container
    st.markdown('</div>', unsafe_allow_html=True)