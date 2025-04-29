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
        
        # Initialize performance tracking variables
        if 'performance_timers' not in st.session_state:
            st.session_state.performance_timers = {}
            
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}
            
        if 'ui_timing_metrics' not in st.session_state:
            st.session_state.ui_timing_metrics = []
            
        if 'ui_freeze_thresholds' not in st.session_state:
            st.session_state.ui_freeze_thresholds = {
                'warning': 1.0,  # Operations taking longer than 1 second get a warning
                'critical': 3.0,  # Operations taking longer than 3 seconds are critical
                'ui_blocking': 0.5  # Operations that may block UI if longer than this
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

        # Initialize critical session state variables to prevent attribute errors
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = 'collection'

        # Background task tracking
        if 'background_tasks_status' not in st.session_state:
            st.session_state.background_tasks_status = {}

        if 'background_tasks_running' not in st.session_state:
            st.session_state.background_tasks_running = False

        if 'background_task_queue' not in st.session_state:
            import queue
            st.session_state.background_task_queue = queue.Queue()

        if 'background_task_results' not in st.session_state:
            st.session_state.background_task_results = {}

        # Data analysis settings
        if 'use_data_cache' not in st.session_state:
            st.session_state.use_data_cache = True

        if 'active_analysis_section' not in st.session_state:
            st.session_state.active_analysis_section = None

        # Chart visibility settings
        if 'show_views_chart' not in st.session_state:
            st.session_state.show_views_chart = True
            
        if 'show_likes_chart' not in st.session_state:
            st.session_state.show_likes_chart = True
            
        if 'show_comments_chart' not in st.session_state:
            st.session_state.show_comments_chart = True
            
        if 'show_duration_chart' not in st.session_state:
            st.session_state.show_duration_chart = False

        # Debug mode
        if 'debug_mode' not in st.session_state:
            st.session_state.debug_mode = True
    
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