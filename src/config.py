"""
Configuration settings for the YouTube scraper application.
"""
import os
from pathlib import Path
import streamlit as st

# API configuration
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Application paths
BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / 'data'
CHANNELS_FILE = DATA_DIR / 'channels.json'
SQLITE_DB_PATH = DATA_DIR / 'youtube_data.db'

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Default application settings
DEFAULT_MAX_VIDEOS = 25
DEFAULT_DEBUG_MODE = False

class Settings:
    """
    Settings class for managing application configuration and environment variables.
    """
    def __init__(self):
        # Database availability flags
        self.mongodb_available = os.getenv('MONGO_URI') is not None
        self.postgres_available = all([
            os.getenv('PG_HOST') is not None,
            os.getenv('PG_USER') is not None,
            os.getenv('PG_PASSWORD') is not None,
            os.getenv('PG_DATABASE') is not None
        ])
        
        # Default storage settings
        self.default_to_local_storage = not (self.mongodb_available or self.postgres_available)
        
        # API settings
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY', '')
        
        # Application paths
        self.data_dir = DATA_DIR
        self.sqlite_db_path = SQLITE_DB_PATH
        self.channels_file = CHANNELS_FILE
    
    def get_available_storage_options(self):
        """Returns a list of available storage options based on environment"""
        options = ["SQLite Database", "Local Storage (JSON)"]
        
        if self.mongodb_available:
            options.append("MongoDB")
            
        if self.postgres_available:
            options.append("PostgreSQL")
            
        return options

# Session state variables by category
SESSION_STATE_VARS = {
    # API related
    'api': {
        'api_key': '',
        'api_cache': {}
    },
    
    # Data collection related
    'collection': {
        'channel_id': '',
        'max_videos': DEFAULT_MAX_VIDEOS,
        'max_comments_per_video': 10,
        'fetch_channel_data': True,
        'fetch_videos': True,
        'fetch_comments': True,
        'collection_step': 1,
        'channel_data_fetched': False,
        'videos_fetched': False,
        'comments_fetched': False,
        'show_all_videos': False,
        'current_channel_data': None,
        'channel_info_temp': None
    },
    
    # UI state related
    'ui': {
        'active_tab': "Data Collection",
        'debug_mode': DEFAULT_DEBUG_MODE,
        'theme': "Light"
    },
    
    # Data analysis related
    'analysis': {
        'show_views_chart': True,
        'show_likes_chart': True,
        'show_comments_chart': True,
        'show_duration_chart': True,
        'selected_channel': None,
        'video_page': 1,
        'video_page_size': 25,
        'sort_by': "recent",
        'search_term': "",
        'date_filter': ""
    },
    
    # Statistics
    'stats': {
        'app_stats': {
            'data_collections': 0,
            'analyses': 0,
            'api_calls': 0,
            'channels': 0
        }
    },
    
    # Performance tracking
    'performance': {
        'performance_timers': {},
        'performance_metrics': {},
        'ui_timing_metrics': [],
        'ui_freeze_thresholds': {
            'warning': 1.0,
            'critical': 3.0,
            'ui_blocking': 0.5
        }
    }
}

def init_session_state():
    """Initialize Streamlit session state variables in a centralized way"""
    # Initialize all session state variables
    for category, variables in SESSION_STATE_VARS.items():
        for var_name, default_value in variables.items():
            if var_name not in st.session_state:
                st.session_state[var_name] = default_value
    
    # Direct initialization of performance variables at root level
    # This is needed because they're referenced directly in the code
    if 'performance_timers' not in st.session_state:
        st.session_state.performance_timers = {}
    
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {}
    
    if 'ui_timing_metrics' not in st.session_state:
        st.session_state.ui_timing_metrics = []
    
    if 'ui_freeze_thresholds' not in st.session_state:
        st.session_state.ui_freeze_thresholds = {
            'warning': 1.0,
            'critical': 3.0,
            'ui_blocking': 0.5
        }