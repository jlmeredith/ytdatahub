"""
Testing fixtures for streamlit-based tests.
This module provides fixtures to handle Streamlit's session state and script run context in tests.
"""
import pytest
import streamlit as st
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit's st module for testing."""
    with patch('streamlit.session_state', new_callable=dict) as mock_session_state:
        # Create a mock for script_run_context to avoid warnings
        with patch('streamlit.runtime.scriptrunner.script_run_context') as mock_context:
            # Mock the get_script_run_ctx function
            mock_context.get_script_run_ctx = MagicMock(return_value=MagicMock())
            
            # Mock the StreamlitContext class to avoid warnings
            with patch('streamlit.runtime.state.session_state_proxy') as mock_proxy:
                yield st
                
@pytest.fixture
def setup_session_state():
    """Initialize a fresh session_state for each test."""
    # Save original session state
    original_session_state = st.session_state._state.copy() if hasattr(st, 'session_state') else {}
    
    # Clear session state
    if hasattr(st, 'session_state'):
        st.session_state._state.clear()
    
    yield st.session_state
    
    # Restore original session state
    if hasattr(st, 'session_state'):
        st.session_state._state.clear()
        st.session_state._state.update(original_session_state)
