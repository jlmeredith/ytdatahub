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

# Note: st.set_page_config has been moved to youtube.py to ensure it's called first

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
        
        # Note: st.set_page_config has been moved to the top of youtube.py
    
    def _initialize_data_directory(self):
        """Create necessary data directories."""
        self.settings.data_dir.mkdir(exist_ok=True)
    
    def _initialize_database(self):
        """Initialize the SQLite database."""
        sqlite_db = StorageFactory.get_storage_provider("SQLite Database", self.settings)
        sqlite_db.initialize_db()
    
    def run(self):
        """Run the YTDataHub application."""
        # Apply custom styling
        self._apply_custom_styling()
        
        # Create a sidebar for navigation
        self._create_sidebar()
        
        # Render main content
        self._render_main_content()
    
    def _apply_custom_styling(self):
        """Apply custom CSS styling to the application."""
        # Custom CSS for better UI
        st.markdown("""
        <style>
        /* Improve the sidebar styling */
        div[data-testid="stSidebarNav"] {
            background-color: rgba(240, 242, 246, 0.1);
            border-radius: 10px;
            padding: 1rem;
        }
        
        /* Style for cards */
        div.card {
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background-color: rgba(255, 255, 255, 0.05);
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }
        
        div.card:hover {
            transform: translateY(-5px);
        }
        
        /* Dashboard containers */
        div.dashboard-container {
            background-color: rgba(240, 242, 246, 0.1);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Custom metric styles */
        div.custom-metric {
            background-color: rgba(240, 242, 246, 0.1);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        
        /* Custom header */
        div.custom-header {
            margin-bottom: 2rem;
        }
        
        /* Improved section dividers */
        hr {
            margin-top: 2rem;
            margin-bottom: 2rem;
            border: 0;
            height: 1px;
            background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0));
        }
        
        /* Responsive fixes */
        @media (max-width: 768px) {
            div.card {
                padding: 1rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _create_sidebar(self):
        """Create a sidebar for navigation."""
        with st.sidebar:
            # App title and logo
            st.title("YTDataHub")
            st.markdown("---")
            
            # Navigation
            st.subheader("Navigation")
            
            # Define tab names
            tabs = ["Data Collection", "Data Storage", "Data Analysis", "Utilities"]
            
            # Set default tab if not present in session state
            if 'active_tab' not in st.session_state:
                st.session_state.active_tab = "Data Collection"
            
            # Create basic radio button navigation
            selected_tab = st.radio(
                "Select a section:",
                tabs,
                index=tabs.index(st.session_state.active_tab),
                label_visibility="collapsed"
            )
            
            # Update session state based on selection
            if selected_tab != st.session_state.active_tab:
                st.session_state.active_tab = selected_tab
                st.rerun()
            
            # Simple theme selector
            st.markdown("---")
            st.subheader("Settings")
            
            # Initialize theme state if not present
            if 'theme' not in st.session_state:
                st.session_state.theme = "Light"
            
            # Theme selection with simple radio buttons
            st.session_state.theme = st.radio(
                "Theme:",
                ["Light", "Dark"],
                index=0 if st.session_state.theme == "Light" else 1
            )
            
            # Add version info
            st.markdown("---")
            st.caption("Version 1.0.0")
            st.caption("© 2025 YTDataHub")
    
    def _render_main_content(self):
        """Render the main content based on the active tab."""
        # Display a title 
        st.title(f"{st.session_state.active_tab}")
        st.markdown("---")
        
        # Render the appropriate tab content based on active_tab
        if st.session_state.active_tab == "Data Collection":
            render_data_collection_tab()
        elif st.session_state.active_tab == "Data Storage":
            render_data_storage_tab()
        elif st.session_state.active_tab == "Data Analysis":
            render_data_analysis_tab()
        elif st.session_state.active_tab == "Utilities":
            render_utilities_tab()