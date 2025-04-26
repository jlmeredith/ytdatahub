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

# Initialize session state variables if they don't exist
def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ''
    
    if 'channel_id' not in st.session_state:
        st.session_state.channel_id = ''
    
    if 'max_videos' not in st.session_state:
        st.session_state.max_videos = DEFAULT_MAX_VIDEOS
    
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = DEFAULT_DEBUG_MODE
    
    if 'fetch_channel_data' not in st.session_state:
        st.session_state.fetch_channel_data = True
    
    if 'fetch_videos' not in st.session_state:
        st.session_state.fetch_videos = True
    
    if 'fetch_comments' not in st.session_state:
        st.session_state.fetch_comments = True
    
    if 'api_cache' not in st.session_state:
        st.session_state.api_cache = {}