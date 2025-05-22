import pytest
import os
from pathlib import Path
import streamlit as st
from unittest.mock import Mock
from src.app import YTDataHubApp
from src.config import Settings

@pytest.fixture
def app():
    """Create a YTDataHubApp instance for testing."""
    return YTDataHubApp()

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv('YOUTUBE_API_KEY', 'test_api_key')
    monkeypatch.setenv('DATA_DIR', 'test_data')

def test_app_initialization(app):
    """Test that the app initializes correctly."""
    assert app is not None
    assert isinstance(app.settings, Settings)

def test_environment_initialization(app, mock_env):
    """Test environment initialization."""
    app._initialize_environment()
    assert os.getenv('YOUTUBE_API_KEY') == 'test_api_key'
    assert os.getenv('DATA_DIR') == 'test_data'

def test_app_state_initialization(app):
    """Test that all required session state variables are initialized."""
    app._init_app_state()
    
    # Test basic session state variables
    assert 'api_cache' in st.session_state
    assert 'debug_mode' in st.session_state
    assert 'app_stats' in st.session_state
    
    # Test app stats structure
    stats = st.session_state.app_stats
    assert isinstance(stats, dict)
    assert 'data_collections' in stats
    assert 'analyses' in stats
    assert 'api_calls' in stats
    assert 'channels' in stats
    
    # Test performance tracking variables
    assert 'performance_timers' in st.session_state
    assert 'performance_metrics' in st.session_state
    assert 'ui_timing_metrics' in st.session_state
    assert 'ui_freeze_thresholds' in st.session_state
    
    # Test UI freeze thresholds
    thresholds = st.session_state.ui_freeze_thresholds
    assert isinstance(thresholds, dict)
    assert 'warning' in thresholds
    assert 'critical' in thresholds
    assert 'ui_blocking' in thresholds
    
    # Test analytics report options
    assert 'show_views_chart' in st.session_state
    assert 'show_likes_chart' in st.session_state
    assert 'show_comments_chart' in st.session_state
    assert 'show_duration_chart' in st.session_state
    
    # Test critical session state variables
    assert 'active_tab' in st.session_state
    assert st.session_state.active_tab == 'Data Collection'
    
    # Test background task tracking
    assert 'background_tasks_status' in st.session_state
    assert 'background_tasks_running' in st.session_state
    assert 'background_task_queue' in st.session_state
    assert 'background_task_results' in st.session_state
    
    # Test data analysis settings
    assert 'use_data_cache' in st.session_state
    assert 'active_analysis_section' in st.session_state

def test_data_directory_initialization(app, tmp_path):
    """Test data directory initialization."""
    # Mock the data directory to use a temporary path
    app.settings.data_dir = tmp_path / "test_data"
    
    # Initialize the data directory
    app._initialize_data_directory()
    
    # Verify the directory was created
    assert app.settings.data_dir.exists()
    assert app.settings.data_dir.is_dir()

def test_database_initialization(app, monkeypatch):
    """Test database initialization."""
    # Mock the database initialization
    mock_initialize = Mock()
    monkeypatch.setattr('src.storage.factory.StorageFactory.get_storage_provider', 
                       lambda *args, **kwargs: type('MockDB', (), {'initialize_db': mock_initialize})())
    
    # Initialize the database
    app._initialize_database()
    
    # Verify the database was initialized
    assert mock_initialize.called

def test_get_settings(app):
    """Test getting application settings."""
    settings = app.get_settings()
    assert isinstance(settings, Settings)
    assert settings == app.settings 