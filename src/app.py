"""
Core application class for YTDataHub.
This handles application initialization and lifecycle.
"""
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

from src.config import init_session_state, Settings
from src.database.sqlite import SQLiteDatabase
from src.storage.factory import StorageFactory
from src.ui.data_collection import render_data_collection_tab
from src.ui.data_storage import render_data_storage_tab
from src.ui.data_analysis import render_data_analysis_tab
from src.ui.utilities import render_utilities_tab

class YTDataHubApp:
    """
    Main application class for YTDataHub.
    Handles application initialization, setup, and rendering.
    """
    
    def __init__(self):
        """Initialize the YTDataHub application."""
        # Initialize environment
        self._initialize_environment()
        
        # Initialize session state
        init_session_state()
        
        # Initialize application settings
        self.settings = Settings()
        
        # Initialize data directory
        self._initialize_data_directory()
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_environment(self):
        """Initialize environment variables and Streamlit configuration."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Set up Streamlit page configuration
        st.set_page_config(
            page_title="YTDataHub",
            layout="wide",  # Changed from "centered" to "wide"
            page_icon=":dna:",
            menu_items={
                'About': "Created by Jamie Meredith 'https://www.linkedin.com/in/jlmeredith/'"
            }
        )
    
    def _initialize_data_directory(self):
        """Create necessary data directories."""
        self.settings.data_dir.mkdir(exist_ok=True)
    
    def _initialize_database(self):
        """Initialize the SQLite database."""
        sqlite_db = StorageFactory.get_storage_provider("SQLite Database", self.settings)
        sqlite_db.initialize_db()
    
    def run(self):
        """Run the YTDataHub application."""
        st.title('YTDataHub')
        
        # Set default tab if not present in session state
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "Data Collection"
        
        # Define tab names
        tabs = ["Data Collection", "Data Storage", "Data Analysis", "Utilities"]
        
        # Process any tab change from redirects (like the "Go to Data Storage Tab" button)
        # This needs to happen before rendering the radio buttons
        active_tab = st.session_state.active_tab
        tab_index = tabs.index(active_tab) if active_tab in tabs else 0
        
        # Handle tab selection via radio buttons styled as tabs
        # This is a more reliable approach than using st.tabs() for programmatic switching
        selected_tab = st.radio(
            "Select a tab:",
            tabs,
            index=tab_index,
            key="tab_selector",
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Update session state based on selection
        if selected_tab != st.session_state.active_tab:
            st.session_state.active_tab = selected_tab
            st.rerun()
            
        # Display a visual separator between tabs and content
        st.markdown("<hr style='margin-top: 0; margin-bottom: 30px'>", unsafe_allow_html=True)
        
        # Render the appropriate tab content based on active_tab
        if st.session_state.active_tab == "Data Collection":
            render_data_collection_tab()
        elif st.session_state.active_tab == "Data Storage":
            render_data_storage_tab()
        elif st.session_state.active_tab == "Data Analysis":
            render_data_analysis_tab()
        elif st.session_state.active_tab == "Utilities":
            render_utilities_tab()