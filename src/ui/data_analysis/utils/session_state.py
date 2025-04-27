"""
Session state management utilities for data analysis UI.
"""
import streamlit as st

def initialize_chart_toggles():
    """Initialize session state variables for chart display toggles."""
    if 'show_views_chart' not in st.session_state:
        st.session_state.show_views_chart = True
    if 'show_likes_chart' not in st.session_state:
        st.session_state.show_likes_chart = True
    if 'show_comments_chart' not in st.session_state:
        st.session_state.show_comments_chart = True
    if 'show_duration_chart' not in st.session_state:
        st.session_state.show_duration_chart = True

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