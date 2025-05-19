"""
UI helper functions for the YouTube Data Hub application.
"""
import streamlit as st
import pandas as pd
import math

def paginate_dataframe(df, page_size, page_num):
    """
    Paginate a dataframe
    
    Args:
        df: The dataframe to paginate
        page_size: Number of items per page
        page_num: The page number to show (0-indexed)
        
    Returns:
        A slice of the dataframe for the requested page
    """
    if df.empty:
        return df
        
    total_pages = math.ceil(len(df) / page_size)
    page_num = max(0, min(page_num, total_pages - 1))  # Ensure valid page number
    
    start_idx = page_num * page_size
    end_idx = min(start_idx + page_size, len(df))
    
    return df.iloc[start_idx:end_idx].copy()

def render_pagination_controls(total_items, page_size, current_page, key_prefix):
    """
    Render pagination controls
    
    Args:
        total_items: Total number of items
        page_size: Number of items per page
        current_page: Current page number (0-indexed)
        key_prefix: Prefix for widget keys to avoid duplicates
        
    Returns:
        New page number based on user interaction
    """
    if total_items <= page_size:
        return 0  # Only one page, so return page 0
        
    total_pages = math.ceil(total_items / page_size)
    
    # Ensure current page is within valid range
    current_page = max(0, min(current_page, total_pages - 1))
    
    # Show pagination information
    st.write(f"Page {current_page + 1} of {total_pages} ({total_items} items)")
    
    # Create columns for pagination controls
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    
    # Render pagination buttons
    with col1:
        if st.button("⏮️ First", disabled=(current_page == 0), key=f"{key_prefix}_first"):
            return 0
            
    with col2:
        if st.button("⏪ Prev", disabled=(current_page == 0), key=f"{key_prefix}_prev"):
            return max(0, current_page - 1)
            
    with col3:
        # Allow direct page selection if there are many pages
        if total_pages > 3:
            page_options = list(range(1, total_pages + 1))
            selected_page = st.selectbox(
                "Go to page",
                page_options,
                index=current_page,
                key=f"{key_prefix}_select"
            )
            if selected_page != current_page + 1:
                return selected_page - 1
                
    with col4:
        if st.button("Next ⏩", disabled=(current_page >= total_pages - 1), key=f"{key_prefix}_next"):
            return min(total_pages - 1, current_page + 1)
            
    return current_page

def initialize_pagination_state(key_prefix, default_page_size=10):
    """
    Initialize pagination state variables
    
    Args:
        key_prefix: Prefix for pagination state variables
        default_page_size: Default number of items per page
    """
    # Initialize current page if not set
    if f"{key_prefix}_page" not in st.session_state:
        st.session_state[f"{key_prefix}_page"] = 0
        
    # Initialize page size if not set
    if f"{key_prefix}_page_size" not in st.session_state:
        st.session_state[f"{key_prefix}_page_size"] = default_page_size
        
def get_pagination_state(key_prefix):
    """
    Get current pagination state
    
    Args:
        key_prefix: Prefix for pagination state variables
        
    Returns:
        Tuple of (current_page, page_size)
    """
    initialize_pagination_state(key_prefix)
    return (
        st.session_state[f"{key_prefix}_page"],
        st.session_state[f"{key_prefix}_page_size"]
    )
    
def update_pagination_state(key_prefix, page=None, page_size=None):
    """
    Update pagination state variables
    
    Args:
        key_prefix: Prefix for pagination state variables
        page: New page number (or None to keep current)
        page_size: New page size (or None to keep current)
    """
    # Initialize state if not already done
    initialize_pagination_state(key_prefix)
    
    # Update page if specified
    if page is not None:
        st.session_state[f"{key_prefix}_page"] = page
        
    # Update page size if specified
    if page_size is not None:
        st.session_state[f"{key_prefix}_page_size"] = page_size
        # Reset to page 0 when page size changes
        st.session_state[f"{key_prefix}_page"] = 0
