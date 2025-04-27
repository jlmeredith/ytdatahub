"""
Comment explorer component for the data analysis UI.
"""
import streamlit as st
import pandas as pd
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
    st.subheader("Comment Analysis")
    
    # Initialize analysis
    analysis = YouTubeAnalysis()
    
    # Get comment data
    comment_analysis = analysis.get_comment_analysis(channel_data)
    
    if comment_analysis['df'] is None or comment_analysis['df'].empty:
        st.info("No comment data available for this channel. Try collecting data for more videos.")
        return
        
    total_comments = comment_analysis['total_comments']
    df = comment_analysis['df']
    
    # Summary of comments
    st.write(f"Total comments analyzed: {total_comments:,}")
    
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
    st.subheader("Comment Explorer")
    
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
    
    # Display format
    display_formats = ["Flat Table", "Threaded View"]
    display_format = st.radio("Display format:", display_formats, horizontal=True)
    
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
    initialize_pagination("comment_explorer", page=1, page_size=10)
    
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
    
    # Get page size (might have been updated in the controls)
    _, page_size = get_pagination_state("comment_explorer")
    
    # Get the paginated dataframe
    paginated_df = paginate_dataframe(filtered_df, page_size, current_page)
    
    # Show results count
    st.write(f"Showing {len(paginated_df)} of {len(filtered_df)} comments")
    
    # Display filtered and sorted data as a flat table
    st.dataframe(paginated_df, use_container_width=True)

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
        
        # Initialize pagination for threaded view
        initialize_pagination("thread_explorer", page=1, page_size=5)
        
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
            
            # Get page size (might have been updated in the controls)
            _, page_size = get_pagination_state("thread_explorer")
            
            # Get paginated threads
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(root_comments))
            paginated_root_comments = root_comments[start_idx:end_idx]
            
            # Show results count
            st.write(f"Showing {len(paginated_root_comments)} of {len(root_comments)} comment threads")
            
            # Display each thread as a card with native Streamlit components
            for root_comment in paginated_root_comments:
                comment_id = root_comment['Comment ID']
                thread = filtered_threads.get(comment_id, {'replies': []})
                
                # Display root comment in a nicer format
                with st.container():
                    # Create a more visually appealing comment box
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
                    </style>
                    
                    <div class="comment-box">
                        <div class="comment-header">
                            <span class="comment-author">{author}</span>
                            <span class="comment-likes">👍 {likes}</span>
                        </div>
                        <div class="comment-text">{text}</div>
                    </div>
                    """.format(
                        author=root_comment['Author'],
                        likes=root_comment['Likes'],
                        text=root_comment['Text']
                    ), unsafe_allow_html=True)
                    
                    # Display replies if any
                    if thread['replies']:
                        with st.expander(f"View {len(thread['replies'])} replies"):
                            for reply in thread['replies']:
                                st.markdown("""
                                <div class="comment-box" style="margin-left: 20px; background-color: #e6f0ff;">
                                    <div class="comment-header">
                                        <span class="comment-author">{author}</span>
                                        <span class="comment-likes">👍 {likes}</span>
                                    </div>
                                    <div class="comment-text">{text}</div>
                                </div>
                                """.format(
                                    author=reply['Author'],
                                    likes=reply['Likes'],
                                    text=reply['Text']
                                ), unsafe_allow_html=True)
                
                st.divider()
        else:
            st.warning("No comments match your filters.")
    else:
        st.warning("Threaded view not available. Try using Flat Table view instead.")