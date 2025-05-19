"""
YouTube API quota estimation utilities.
"""
import streamlit as st

def estimate_quota_usage(fetch_channel=None, fetch_videos=None, fetch_comments=None, 
                         video_count=None, comments_count=None):
    """
    Estimates YouTube API quota points that will be used with current settings
    
    Args:
        fetch_channel: Whether to fetch channel data (defaults to session state if None)
        fetch_videos: Whether to fetch videos (defaults to session state if None)
        fetch_comments: Whether to fetch comments (defaults to session state if None)
        video_count: Number of videos to fetch (defaults to session state if None)
        comments_count: Number of comments per video (default 10 if None)
    
    Returns:
        int: Estimated quota usage
    """
    # Use parameters if provided, otherwise fall back to session state
    fetch_channel = fetch_channel if fetch_channel is not None else st.session_state.get('fetch_channel_data', False)
    fetch_videos = fetch_videos if fetch_videos is not None else st.session_state.get('fetch_videos', False)
    fetch_comments = fetch_comments if fetch_comments is not None else st.session_state.get('fetch_comments', False)
    video_count = video_count if video_count is not None else st.session_state.get('max_videos', 0)
    comments_count = comments_count if comments_count is not None else 10
    
    # Base quota for channel info - YouTube API charges 1 unit per channel request
    quota = 1 if fetch_channel else 0
    
    # Quota for video list
    # Each request for video list costs at least 1 unit
    if fetch_videos:
        # Each video request costs at least 1 unit of quota
        quota += video_count
    
    # Comments cost additional quota units per video
    # This happens whether we're fetching videos or not (if we have video IDs)
    if fetch_comments and video_count > 0:
        quota += video_count
    
    return quota
