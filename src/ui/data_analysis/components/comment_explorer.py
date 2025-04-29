"""
Comment explorer component for the data analysis UI.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.helpers import paginate_dataframe, render_pagination_controls
from src.ui.data_analysis.utils.session_state import initialize_pagination, get_pagination_state, update_pagination_state
from src.ui.data_analysis.components.comment_analysis.temporal_tab import render_temporal_tab
from src.ui.data_analysis.components.comment_analysis.commenter_tab import render_commenter_tab
from src.ui.data_analysis.components.comment_analysis.engagement_tab import render_engagement_tab

def render_comment_explorer(channel_data):
    """
    Render the comment explorer component.
    
    Args:
        channel_data: Dictionary containing channel data
    """
    # Initialize analysis
    analysis = YouTubeAnalysis()
    
    # First check if we have videos with data
    if not channel_data or 'videos' not in channel_data or not channel_data['videos']:
        st.warning("No video data available for this channel. Please collect video data first.")
        
        # Show guidance on how to collect data
        st.info("To collect video data, go to the Data Coverage Dashboard and update this channel.")
        if st.button("Go to Data Coverage Dashboard", key="no_videos_goto_coverage"):
            st.session_state.active_analysis_section = "coverage"
            st.rerun()
        return
    
    # Get comment data
    try:
        comment_analysis = analysis.get_comment_analysis(channel_data)
        
        # Check if we have any comments data
        if not comment_analysis or comment_analysis.get('df') is None or comment_analysis.get('df', pd.DataFrame()).empty:
            st.warning("No comment data available for this channel.")
            
            # Show guidance with more details about the current state
            video_count = len(channel_data.get('videos', []))
            videos_with_comments = sum(1 for video in channel_data.get('videos', []) if video.get('comments', []))
            
            if videos_with_comments == 0:
                st.info(f"""
                None of your {video_count} videos have comments collected. 
                To analyze comments, you need to collect comment data from the Data Coverage Dashboard.
                """)
            else:
                st.info(f"""
                Only {videos_with_comments} out of {video_count} videos have comments collected.
                For better analysis, collect more comments from the Data Coverage Dashboard.
                """)
            
            # Add a button to go to the data coverage dashboard
            if st.button("Go to Data Coverage Dashboard", key="no_comments_goto_coverage"):
                st.session_state.active_analysis_section = "coverage"
                st.rerun()
                
            return
            
        total_comments = comment_analysis['total_comments']
        df = comment_analysis['df']
        
    except Exception as e:
        st.error(f"Error loading comment data: {str(e)}")
        st.info("There may be an issue with your comment data. Try refreshing or updating your data collection.")
        
        # Add a button to go to the data coverage dashboard
        if st.button("Go to Data Coverage Dashboard", key="error_goto_coverage"):
            st.session_state.active_analysis_section = "coverage"
            st.rerun()
        return
    
    # Create a dashboard-style layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Comment Analysis")
        # Summary of comments with more metrics
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        with metrics_col1:
            st.metric("Total Comments", f"{total_comments:,}")
        
        with metrics_col2:
            # Calculate average comments per video
            if 'comments_per_video' in comment_analysis:
                avg_comments = comment_analysis['comments_per_video']['avg_comments']
                st.metric("Avg. Comments per Video", f"{avg_comments:.1f}")
            else:
                # Fallback calculation
                video_count = len(channel_data.get('videos', []))
                avg_comments = total_comments / video_count if video_count > 0 else 0
                st.metric("Avg. Comments per Video", f"{avg_comments:.1f}")
        
        with metrics_col3:
            # Calculate average engagement rate from comments
            if 'total_likes' in comment_analysis:
                avg_likes = comment_analysis['total_likes'] / total_comments if total_comments > 0 else 0
                st.metric("Avg. Likes per Comment", f"{avg_likes:.1f}")
            else:
                # Fallback
                avg_likes = df['Likes'].mean() if 'Likes' in df.columns else 0
                st.metric("Avg. Likes per Comment", f"{avg_likes:.1f}")
    
    with col2:
        # Display sentiment analysis if enabled
        if st.session_state.get("show_comment_sentiment", True) and 'sentiment_analysis' in comment_analysis:
            sentiment = comment_analysis['sentiment_analysis']
            if sentiment:
                st.subheader("Sentiment Overview")
                
                # Create a pie chart for sentiment distribution
                sentiment_data = {
                    'Sentiment': ['Positive', 'Neutral', 'Negative'],
                    'Count': [
                        sentiment.get('positive', 0),
                        sentiment.get('neutral', 0),
                        sentiment.get('negative', 0)
                    ]
                }
                sentiment_df = pd.DataFrame(sentiment_data)
                
                # Calculate percentages for the pie chart
                total = sentiment_df['Count'].sum()
                sentiment_df['Percentage'] = sentiment_df['Count'] / total * 100 if total > 0 else 0
                
                # Create a pie chart
                fig = px.pie(
                    sentiment_df,
                    values='Count',
                    names='Sentiment',
                    title="Comment Sentiment Distribution",
                    color='Sentiment',
                    color_discrete_map={
                        'Positive': 'green',
                        'Neutral': 'gray',
                        'Negative': 'red'
                    },
                    hole=0.3
                )
                
                # Improve layout
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=300,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Create tabs for different comment analyses
    comment_tabs = st.tabs([
        "Comment Explorer", 
        "Temporal Analysis", 
        "Top Commenters", 
        "Engagement"
    ])
    
    # Tab 1: Comment Explorer
    with comment_tabs[0]:
        render_comment_explorer_tab(df, comment_analysis)
    
    # Tab 2: Temporal Analysis
    with comment_tabs[1]:
        render_temporal_tab(comment_analysis)
    
    # Tab 3: Top Commenters
    with comment_tabs[2]:
        render_commenter_tab(comment_analysis, total_comments)
    
    # Tab 4: Engagement Analysis
    with comment_tabs[3]:
        render_engagement_tab(comment_analysis, total_comments)

def render_comment_explorer_tab(df, comment_analysis):
    """
    Render the comment explorer tab.
    
    Args:
        df: DataFrame with comment data
        comment_analysis: Dictionary with comment analysis data
    """
    # Filter and search for comments
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        comment_search = st.text_input("Search in comments:", key="comment_search")
    
    with col2:
        # Filter options
        comment_filters = ["All Comments", "Top-level Only", "Replies Only", "Most Liked"]
        selected_filter = st.selectbox("Filter by:", comment_filters, key="comment_filter")
    
    with col3:
        # Sort options
        comment_sorts = {
            "Newest First": ("Published", False),
            "Oldest First": ("Published", True),
            "Most Likes": ("Likes", False),
            "Least Likes": ("Likes", True)
        }
        
        sort_by = st.selectbox("Sort by:", options=list(comment_sorts.keys()), key="comment_sort")
    
    # Display format selection
    display_col1, display_col2 = st.columns([3, 1])
    
    with display_col1:
        display_formats = ["Flat Table", "Threaded View"]
        display_format = st.radio("Display format:", display_formats, horizontal=True)
    
    with display_col2:
        # Use slider for page size from session state
        page_size = st.session_state.get("comment_page_size", 10)
        st.caption(f"Comments per page: {page_size}")
    
    # Apply filters
    filtered_df = df.copy()
    
    # Text search
    if comment_search:
        filtered_df = filtered_df[filtered_df['Text'].str.contains(comment_search, case=False)]
    
    # Comment type filter
    if selected_filter == "Top-level Only":
        filtered_df = filtered_df[~filtered_df['Is Reply']]
    elif selected_filter == "Replies Only":
        filtered_df = filtered_df[filtered_df['Is Reply']]
    elif selected_filter == "Most Liked":
        filtered_df = filtered_df.sort_values("Likes", ascending=False).head(100)
    
    # Apply sorting
    if sort_by in comment_sorts:
        sort_col, sort_asc = comment_sorts[sort_by]
        if sort_col in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=sort_asc)
            
    # Display based on chosen format
    if display_format == "Flat Table":
        render_flat_table_view(filtered_df)
    else:
        render_threaded_view(filtered_df, comment_analysis, comment_search, selected_filter, sort_by, comment_sorts)

def render_flat_table_view(filtered_df):
    """
    Render comments as a flat table.
    
    Args:
        filtered_df: Filtered DataFrame with comment data
    """
    # Initialize pagination for flat table view
    initialize_pagination("comment_explorer", page=1, page_size=st.session_state.get("comment_page_size", 10))
    
    # Get current pagination values
    current_page, page_size = get_pagination_state("comment_explorer")
    
    # Update page based on controls
    new_page = render_pagination_controls(
        len(filtered_df), 
        page_size, 
        current_page, 
        "comment_explorer"
    )
    
    # Update page state if changed
    if update_pagination_state("comment_explorer", new_page):
        current_page = new_page
    
    # Get the paginated dataframe
    paginated_df = paginate_dataframe(filtered_df, page_size, current_page)
    
    # Show results count
    st.write(f"Showing {len(paginated_df)} of {len(filtered_df)} comments")
    
    # Create a copy for display configuration
    display_df = paginated_df.copy()
    
    # Create formatted versions of columns for display purposes
    if 'Published' in display_df.columns and pd.api.types.is_datetime64_dtype(display_df['Published']):
        display_df['Published_Display'] = display_df['Published'].dt.strftime('%Y-%m-%d %H:%M')
    
    if 'Likes' in display_df.columns:
        display_df['Likes_Display'] = display_df['Likes'].apply(lambda x: f"{x:,}")
    
    # Truncate text if too long for display
    if 'Text' in display_df.columns:
        display_df['Text_Display'] = display_df['Text'].apply(lambda x: (x[:100] + '...') if len(x) > 100 else x)
    
    # Configure columns for better display and proper sorting
    column_config = {
        "Author": st.column_config.TextColumn(
            "Author",
            help="Comment author",
            width="medium"
        ),
        "Text_Display": st.column_config.TextColumn(
            "Text",
            help="Comment text",
            width="large"
        ),
        "Published": st.column_config.DatetimeColumn(
            "Published",
            help="Publication date",
            format="%Y-%m-%d %H:%M",
            width="medium"
        ),
        "Likes": st.column_config.NumberColumn(
            "Likes",
            help="Number of likes on the comment",
            format="%d",
            width="small"
        ),
        "Is Reply": st.column_config.CheckboxColumn(
            "Is Reply",
            help="Whether this comment is a reply to another comment",
            width="small"
        )
    }
    
    # Select columns for display, preferring display versions where available
    display_columns = []
    if 'Author' in display_df.columns:
        display_columns.append('Author')
    if 'Text' in display_df.columns:
        display_columns.append('Text_Display' if 'Text_Display' in display_df.columns else 'Text')
    if 'Published' in display_df.columns:
        display_columns.append('Published')
    if 'Likes' in display_df.columns:
        display_columns.append('Likes')
    if 'Is Reply' in display_df.columns:
        display_columns.append('Is Reply')
    
    # Display filtered and sorted data as a table with proper column configuration
    st.dataframe(
        display_df[display_columns], 
        use_container_width=True,
        column_config=column_config,
        hide_index=True
    )

def render_threaded_view(filtered_df, comment_analysis, comment_search, selected_filter, sort_by, comment_sorts):
    """
    Render comments in a threaded view.
    
    Args:
        filtered_df: Filtered DataFrame with comment data
        comment_analysis: Dictionary with comment analysis data
        comment_search: Search term for filtering
        selected_filter: Selected filter option
        sort_by: Sort option
        comment_sorts: Dictionary with sort options
    """
    # Initialize custom CSS for better comment display
    st.markdown("""
    <style>
    .comment-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .comment-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .comment-author {
        font-weight: bold;
        color: #1E88E5;
    }
    .comment-likes {
        color: #666;
    }
    .comment-text {
        margin-top: 5px;
        white-space: pre-wrap;
    }
    .comment-date {
        color: #888;
        font-size: 0.8em;
        margin-top: 5px;
    }
    .reply-box {
        margin-left: 20px;
        background-color: #e6f0ff;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display in threaded view using thread_structure
    if 'thread_data' in comment_analysis and 'thread_structure' in comment_analysis['thread_data']:
        # Get thread structure
        thread_structure = comment_analysis['thread_data']['thread_structure']
        
        # Apply filtering to thread structure
        filtered_threads = {}
        
        # First get all root comments that pass the filter
        for comment_id, thread in thread_structure.items():
            # Check if the comment passes filters
            root_comment = thread['comment']
            include_thread = True
            
            # Apply text search filter if set
            if comment_search:
                # Check if root comment or any replies match the search
                root_matches = comment_search.lower() in root_comment['Text'].lower()
                reply_matches = any(comment_search.lower() in reply['Text'].lower() for reply in thread['replies'])
                
                if not (root_matches or reply_matches):
                    include_thread = False
            
            # Apply filter type
            if selected_filter == "Top-level Only" and thread['replies']:
                # Skip threads with replies in "top-level only" mode
                include_thread = False
            
            # Include this thread if it passes all filters
            if include_thread:
                filtered_threads[comment_id] = thread
        
        # Initialize pagination for threaded view with the custom page size
        initialize_pagination("thread_explorer", page=1, page_size=st.session_state.get("comment_page_size", 5))
        
        # Get current pagination values
        current_page, page_size = get_pagination_state("thread_explorer")
        
        # Display the filtered threads with pagination
        if filtered_threads:
            # Get a sorted list of root comments based on the selected sort option
            root_comments = []
            for comment_id, thread in filtered_threads.items():
                root_comments.append(thread['comment'])
            
            # Sort root comments
            if sort_by in comment_sorts:
                sort_col, sort_asc = comment_sorts[sort_by]
                if sort_col in root_comments[0]:
                    root_comments.sort(key=lambda x: x.get(sort_col, 0), reverse=not sort_asc)
            
            # Update page based on controls
            new_page = render_pagination_controls(
                len(root_comments), 
                page_size, 
                current_page, 
                "thread_explorer"
            )
            
            # Update page state if changed
            if update_pagination_state("thread_explorer", new_page):
                current_page = new_page
            
            # Get paginated threads
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(root_comments))
            paginated_root_comments = root_comments[start_idx:end_idx]
            
            # Show results count
            st.write(f"Showing {len(paginated_root_comments)} of {len(root_comments)} comment threads")
            
            # Display each thread as a card with enhanced styling
            for root_comment in paginated_root_comments:
                comment_id = root_comment['Comment ID']
                thread = filtered_threads.get(comment_id, {'replies': []})
                
                # Create clean date format if available
                published_date = ""
                if 'Published' in root_comment:
                    try:
                        # Format date more nicely
                        if isinstance(root_comment['Published'], pd.Timestamp):
                            published_date = root_comment['Published'].strftime('%Y-%m-%d %H:%M')
                        else:
                            published_date = str(root_comment['Published'])
                    except:
                        published_date = str(root_comment['Published'])
                
                # Display root comment in a nicer format
                with st.container():
                    # Create a more visually appealing comment box with date
                    st.markdown(f"""
                    <div class="comment-box">
                        <div class="comment-header">
                            <span class="comment-author">{root_comment['Author']}</span>
                            <span class="comment-likes">👍 {root_comment['Likes']}</span>
                        </div>
                        <div class="comment-text">{root_comment['Text']}</div>
                        <div class="comment-date">{published_date}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show video context if available
                    if 'Video Title' in root_comment:
                        st.caption(f"On video: {root_comment['Video Title']}")
                    
                    # Display replies if any with enhanced styling
                    if thread['replies']:
                        with st.expander(f"View {len(thread['replies'])} replies"):
                            for reply in thread['replies']:
                                # Format reply date
                                reply_date = ""
                                if 'Published' in reply:
                                    try:
                                        if isinstance(reply['Published'], pd.Timestamp):
                                            reply_date = reply['Published'].strftime('%Y-%m-%d %H:%M')
                                        else:
                                            reply_date = str(reply['Published'])
                                    except:
                                        reply_date = str(reply['Published'])
                                
                                st.markdown(f"""
                                <div class="reply-box">
                                    <div class="comment-header">
                                        <span class="comment-author">{reply['Author']}</span>
                                        <span class="comment-likes">👍 {reply['Likes']}</span>
                                    </div>
                                    <div class="comment-text">{reply['Text']}</div>
                                    <div class="comment-date">{reply_date}</div>
                                </div>
                                """, unsafe_allow_html=True)
                
                # Add divider between comment threads for better readability
                st.divider()
        else:
            st.warning("No comments match your filters.")
    else:
        st.warning("Threaded view not available. Try using Flat Table view instead.")
        
        # Provide guidance on how to get threaded view
        st.info("To enable threaded view, make sure to collect comments with replies when fetching YouTube data.")