"""
YTDataHub - YouTube Data Collection, Storage, and Analysis Application.
Entry point for the Streamlit application.
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse
import time
from datetime import datetime

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

# Import directly from the modern implementations instead of legacy wrappers
from src.ui.data_collection.main import render_data_collection_tab
from src.ui.data_analysis.main import render_data_analysis_tab
from src.ui.utilities import render_utilities_tab
from src.ui.bulk_import.render import render_bulk_import_tab
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
        valid_tabs = ["📈 Analytics Dashboard", "📥 Data Collection", "📋 Bulk Import", "⚙️ Utilities"]
        # URL-decode the tab name
        tab = urllib.parse.unquote(tab)
        # Also handle legacy tab names for backward compatibility
        legacy_tab_mapping = {
            "Data Analysis": "📈 Analytics Dashboard",
            "Data Collection": "📥 Data Collection", 
            "Bulk Import": "📋 Bulk Import",
            "Utilities": "⚙️ Utilities"
        }
        if tab in legacy_tab_mapping:
            tab = legacy_tab_mapping[tab]
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

def main():
    """Main application entry point."""
    try:
        # Initialize the application
        settings = init_application()
        
        # Apply CSS styling
        load_css_file()
        apply_security_headers()
        
        # Process URL parameters
        process_url_params()
        
        # Application header
        st.title("📊 YTDataHub")
        st.markdown("*YouTube Analytics and Insights Platform*")
        
        # Check if we have existing channels to guide the user experience
        sqlite_db = StorageFactory.get_storage_provider("SQLite Database", settings)
        existing_channels = sqlite_db.get_channels_list()
        
        # Display welcome message based on data availability
        if not existing_channels:
            st.info("👋 **Welcome to YTDataHub!** Start by collecting some YouTube channel data to unlock powerful analytics insights.")
        else:
            st.success(f"🎯 **Ready for Analysis!** You have data from {len(existing_channels)} channel{'s' if len(existing_channels) != 1 else ''} ready to explore.")
        
        # Main navigation tabs - Analytics first to emphasize the primary purpose
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Analytics Dashboard", "📥 Data Collection", "📋 Bulk Import", "⚙️ Utilities"])
        
        with tab1:
            if not existing_channels:
                st.warning("🔍 **No data available for analysis yet.** Switch to the 'Data Collection' tab to start gathering YouTube data.")
                st.markdown("### What you can do with YTDataHub Analytics:")
                st.markdown("""
                - 📊 **Performance Dashboard**: Track views, likes, comments, and engagement over time
                - 📹 **Video Explorer**: Browse and analyze your video collection with advanced filtering
                - 💬 **Comment Analysis**: Understand audience sentiment and engagement patterns  
                - 📈 **Data Coverage**: Visualize the completeness of your data collection
                """)
            else:
                render_data_analysis_tab()
            
        with tab2:
            render_data_collection_tab()
            
        with tab3:
            render_bulk_import_tab()
            
        with tab4:
            render_utilities_tab()
            
    except Exception as e:
        st.error(f"Application Error: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
