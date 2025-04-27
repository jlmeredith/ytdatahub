"""
Core application module for YTDataHub.
This module contains utility classes and functions but doesn't directly render the UI.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse
import streamlit as st

from src.config import init_session_state, Settings
from src.database.sqlite import SQLiteDatabase
from src.storage.factory import StorageFactory

class YTDataHubApp:
    """
    Application class for YTDataHub.
    Handles application initialization and configuration.
    """
    
    def __init__(self):
        """Initialize the YTDataHub application."""
        # Initialize environment
        self._initialize_environment()
        
        # Initialize session state
        init_session_state()
        self._init_app_state()
        
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
    
    def _init_app_state(self):
        """Initialize application state variables."""
        if 'api_cache' not in st.session_state:
            st.session_state.api_cache = {}
            
        if 'debug_mode' not in st.session_state:
            st.session_state.debug_mode = False
            
        if 'app_stats' not in st.session_state:
            st.session_state.app_stats = {
                'data_collections': 0,
                'analyses': 0,
                'api_calls': 0,
                'channels': 0
            }
        
        # Initialize analytics report options with default values
        if 'show_views_chart' not in st.session_state:
            st.session_state.show_views_chart = True
        if 'show_likes_chart' not in st.session_state:
            st.session_state.show_likes_chart = True
        if 'show_comments_chart' not in st.session_state:
            st.session_state.show_comments_chart = True
        if 'show_duration_chart' not in st.session_state:
            st.session_state.show_duration_chart = True
    
    def _initialize_data_directory(self):
        """Create necessary data directories."""
        self.settings.data_dir.mkdir(exist_ok=True)
    
    def _initialize_database(self):
        """Initialize the SQLite database."""
        sqlite_db = StorageFactory.get_storage_provider("SQLite Database", self.settings)
        sqlite_db.initialize_db()
    
    def get_settings(self):
        """Get the application settings."""
        return self.settings