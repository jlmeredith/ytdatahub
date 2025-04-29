"""
Session state management utilities for data analysis UI.
"""
import streamlit as st

def initialize_chart_toggles():
    """Initialize session state variables for chart display toggles."""
    if 'show_views_chart' not in st.session_state:
        st.session_state.show_views_chart = False
    if 'show_likes_chart' not in st.session_state:
        st.session_state.show_likes_chart = False
    if 'show_comments_chart' not in st.session_state:
        st.session_state.show_comments_chart = False
    if 'show_duration_chart' not in st.session_state:
        st.session_state.show_duration_chart = False
    # Additional chart toggles
    if 'show_engagement_ratios' not in st.session_state:
        st.session_state.show_engagement_ratios = False
    if 'show_performance_metrics' not in st.session_state:
        st.session_state.show_performance_metrics = False
    if 'show_trend_lines' not in st.session_state:
        st.session_state.show_trend_lines = False
    if 'trend_window' not in st.session_state:
        st.session_state.trend_window = "Medium"
    if 'show_video_thumbnails' not in st.session_state:
        st.session_state.show_video_thumbnails = False
    if 'show_comment_sentiment' not in st.session_state:
        st.session_state.show_comment_sentiment = False
    if 'show_word_clouds' not in st.session_state:
        st.session_state.show_word_clouds = False
    if 'video_sort_by' not in st.session_state:
        st.session_state.video_sort_by = "Published (Newest)"

def initialize_analysis_section():
    """Initialize the active analysis section in session state."""
    if 'active_analysis_section' not in st.session_state:
        st.session_state.active_analysis_section = None

def initialize_pagination(prefix, page=1, page_size=10):
    """
    Initialize pagination session state variables.
    
    Args:
        prefix: Prefix for the session state keys
        page: Initial page number
        page_size: Initial page size
    """
    if f"{prefix}_page" not in st.session_state:
        st.session_state[f"{prefix}_page"] = page
    if f"{prefix}_page_size" not in st.session_state:
        st.session_state[f"{prefix}_page_size"] = page_size
        
def get_pagination_state(prefix):
    """
    Get current pagination state.
    
    Args:
        prefix: Prefix for the session state keys
        
    Returns:
        Tuple of (current_page, page_size)
    """
    current_page = st.session_state.get(f"{prefix}_page", 1)
    page_size = st.session_state.get(f"{prefix}_page_size", 10)
    return current_page, page_size
    
def update_pagination_state(prefix, new_page):
    """
    Update pagination state if changed.
    
    Args:
        prefix: Prefix for the session state keys
        new_page: New page number
        
    Returns:
        Boolean indicating if state was changed
    """
    current_page = st.session_state.get(f"{prefix}_page", 1)
    if new_page != current_page:
        st.session_state[f"{prefix}_page"] = new_page
        return True
    return False