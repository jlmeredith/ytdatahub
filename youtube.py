"""
YTDataHub - YouTube Data Collection, Storage, and Analysis Application.
Entry point for the Streamlit application.
"""
import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse

# Set Streamlit page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="YTDataHub",
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Created by Jamie Meredith 'https://www.linkedin.com/in/jlmeredith/'"
    }
)

# These imports must come after st.set_page_config
from src.config import init_session_state, Settings
from src.database.sqlite import SQLiteDatabase
from src.storage.factory import StorageFactory
from src.ui.data_collection import render_data_collection_tab
from src.ui.data_analysis import render_data_analysis_tab
from src.ui.utilities import render_utilities_tab
from src.ui.bulk_import import render_bulk_import_tab
from src.ui.components.ui_utils import load_css_file, apply_security_headers

def init_application():
    """Initialize application environment and state."""
    # Load environment variables
    load_dotenv()
    
    # Initialize session state
    init_session_state()
    
    # Initialize application settings
    settings = Settings()
    
    # Create necessary data directories
    settings.data_dir.mkdir(exist_ok=True)
    
    # Initialize database
    sqlite_db = StorageFactory.get_storage_provider("SQLite Database", settings)
    sqlite_db.initialize_db()
    
    return settings

def process_url_params():
    """Process URL query parameters to restore app state."""
    # Get query parameters from the URL
    params = st.query_params
    
    # Set active tab from URL if present
    if 'tab' in params:
        tab = params['tab']
        valid_tabs = ["Data Collection", "Data Analysis", "Utilities"]
        # URL-decode the tab name
        tab = urllib.parse.unquote(tab)
        if tab in valid_tabs:
            st.session_state.active_tab = tab
            
    # Set channel from URL if present
    if 'channel' in params:
        channel = params['channel']
        # URL-decode the channel name
        channel = urllib.parse.unquote(channel)
        st.session_state.selected_channel = channel
        
    # Set analytics report options
    if 'views' in params:
        st.session_state.show_views_chart = params['views'].lower() == 'true'
        
    if 'likes' in params:
        st.session_state.show_likes_chart = params['likes'].lower() == 'true'
        
    if 'comments' in params:
        st.session_state.show_comments_chart = params['comments'].lower() == 'true'
        
    if 'duration' in params:
        st.session_state.show_duration_chart = params['duration'].lower() == 'true'
    
    # Set page and filter parameters if present
    if 'page' in params:
        try:
            st.session_state.video_page = int(params['page'])
        except ValueError:
            pass
            
    if 'page_size' in params:
        try:
            st.session_state.video_page_size = int(params['page_size'])
        except ValueError:
            pass
            
    if 'sort' in params:
        st.session_state.sort_by = urllib.parse.unquote(params['sort'])
        
    if 'search' in params:
        st.session_state.search_term = urllib.parse.unquote(params['search'])
        
    if 'date_filter' in params:
        st.session_state.date_filter = urllib.parse.unquote(params['date_filter'])

def update_url_params():
    """Update URL parameters based on current app state."""
    # Use the new st.query_params directly
    params = st.query_params
    
    # Add active tab to URL
    if 'active_tab' in st.session_state:
        params.tab = st.session_state.active_tab
        
    # Add selected channel to URL if in Data Analysis tab
    if st.session_state.active_tab == "Data Analysis" and 'selected_channel' in st.session_state:
        # Only add if it's a valid value that's not None
        if st.session_state.selected_channel:
            params.channel = st.session_state.selected_channel
        
        # Add analytics report options to URL with shorter parameter names
        if 'show_views_chart' in st.session_state:
            params.views = str(st.session_state.show_views_chart).lower()
            
        if 'show_likes_chart' in st.session_state:
            params.likes = str(st.session_state.show_likes_chart).lower()
            
        if 'show_comments_chart' in st.session_state:
            params.comments = str(st.session_state.show_comments_chart).lower()
            
        if 'show_duration_chart' in st.session_state:
            params.duration = str(st.session_state.show_duration_chart).lower()
            
        # Add pagination and filtering parameters
        if 'video_page' in st.session_state:
            params.page = str(st.session_state.video_page)
            
        if 'video_page_size' in st.session_state:
            params.page_size = str(st.session_state.video_page_size)
            
        if 'sort_by' in st.session_state:
            params.sort = st.session_state.sort_by
            
        if 'search_term' in st.session_state and st.session_state.search_term:
            params.search = st.session_state.search_term
            
        if 'date_filter' in st.session_state and st.session_state.date_filter:
            params.date_filter = st.session_state.date_filter

def create_sidebar():
    """Create the sidebar navigation."""
    with st.sidebar:
        # App title and logo
        st.title("YTDataHub")
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        
        # Define tab names
        tabs = ["Data Collection", "Data Analysis", "Utilities", "Bulk Import"]
        
        # Set default tab if not present in session state
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "Data Collection"
        
        # Create a Streamlit button for each tab
        for tab in tabs:
            # Set button type based on active tab
            button_type = "primary" if tab == st.session_state.active_tab else "secondary"
            button_key = f"nav_{tab.lower().replace(' ', '_')}"
            
            # Use Streamlit's native button component
            if st.button(tab, key=button_key, type=button_type, use_container_width=True):
                st.session_state.active_tab = tab
                # Update URL parameters
                st.query_params.tab = tab
                st.rerun()
        
        # Add version info
        st.markdown("---")
        st.caption("Version 1.0.0")
        st.caption("© 2025 YTDataHub")

def render_main_content():
    """Render the main content based on the active tab."""
    # Display a title 
    st.title(f"{st.session_state.active_tab}")
    st.markdown("---")
    
    # Render the appropriate tab content based on active_tab
    if st.session_state.active_tab == "Data Collection":
        render_data_collection_tab()
    elif st.session_state.active_tab == "Data Analysis":
        render_data_analysis_tab()
    elif st.session_state.active_tab == "Utilities":
        render_utilities_tab()
    elif st.session_state.active_tab == "Bulk Import":
        render_bulk_import_tab()

def render_footer(settings):
    """Render the footer with version information."""
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("YouTube Data Hub v1.0 | © 2025 | [Documentation](https://github.com/yourusername/ytdatahub)")
    with col2:
        # Show stats if enabled
        if hasattr(settings, 'show_app_stats') and settings.show_app_stats and 'app_stats' in st.session_state:
            with st.expander("App Stats"):
                st.write(f"Data Collections: {st.session_state.app_stats['data_collections']}")
                st.write(f"Analyses Run: {st.session_state.app_stats['analyses']}")
                st.write(f"API Calls: {st.session_state.app_stats['api_calls']}")
                st.write(f"Channels: {st.session_state.app_stats['channels']}")

def main():
    """Main application entry point."""
    # Apply custom styling from external CSS file
    load_css_file()
    
    # Add security headers using template
    apply_security_headers()
    
    # Initialize application
    settings = init_application()
    
    # Process URL parameters
    process_url_params()
    
    # Create sidebar
    create_sidebar()
    
    # Render main content
    render_main_content()
    
    # Render footer
    render_footer(settings)
    
    # Update URL parameters
    update_url_params()

if __name__ == "__main__":
    main()

