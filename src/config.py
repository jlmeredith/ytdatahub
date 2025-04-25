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