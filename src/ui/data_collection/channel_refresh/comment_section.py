"""
This module handles the comment section of the channel refresh UI.
"""
import streamlit as st
import pandas as pd
from src.utils.debug_utils import debug_log

def render_comment_section(comments_data):
    """
    Render the comment section of the channel refresh UI.
    
    Args:
        comments_data: List of comment data from the API
    """
    st.subheader("Step 4: Comment Collection Results")
    
    if not comments_data:
        st.info("No comments found or comments have not been loaded yet.")
        return
    
    st.write(f"Successfully collected {len(comments_data)} comments")
    
    # Display a sample of comments
    st.subheader("Sample Comments")
    
    # Create a dataframe for comments
    comment_data_for_display = []
    for i, comment in enumerate(comments_data[:10]):  # Show up to 10 comments
        author = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('authorDisplayName', 'Unknown')
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', 'No text')
        published = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('publishedAt', 'Unknown')
        
        comment_data_for_display.append({
            "Author": author,
            "Comment": text[:100] + "..." if len(text) > 100 else text,
            "Published": published
        })
    
    if comment_data_for_display:
        comment_df = pd.DataFrame(comment_data_for_display)
        st.dataframe(comment_df)

def configure_comment_collection():
    """
    Configure comment collection options.
    
    Returns:
        dict: Options for comment collection
    """
    st.subheader("Comment Collection Options")
    
    # Enhanced UI controls for comment collection settings
    st.write("Configure how many comments to collect:")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        max_comments_per_video = st.slider(
            "Top-Level Comments Per Video",
            min_value=0,
            max_value=100,
            value=20,
            help="Set to 0 to skip comment collection entirely"
        )
        st.caption("Controls how many primary comments to collect for each video")
    
    with col2:
        max_replies_per_comment = st.slider(
            "Replies Per Top-Level Comment",
            min_value=0,
            max_value=50, 
            value=5,
            help="Set to 0 to skip fetching replies"
        )
        st.caption("Controls how many replies to collect for each primary comment")
    
    # Add explanatory text about API quota impact
    st.info("💡 Higher values will provide more comprehensive data but may consume more API quota.")
    
    optimize_quota = st.checkbox(
        "Optimize API quota usage",
        value=True,
        help="When enabled, only videos with comments will be queried"
    )
    
    # Create options for comments
    options = {
        'fetch_channel_data': False,
        'fetch_videos': False,
        'fetch_comments': True,
        'analyze_sentiment': False,
        'max_videos': 10,  # Limit for comments collection
        'max_comments_per_video': max_comments_per_video,
        'max_replies_per_comment': max_replies_per_comment,
        'optimize_quota': optimize_quota
    }
    
    return options
