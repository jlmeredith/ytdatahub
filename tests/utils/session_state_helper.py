"""
Fixed SessionState implementation for Streamlit tests.
"""
import logging
import streamlit as st

def fix_session_state_for_tests():
    """
    Sets up a proper session_state mock for tests that correctly handles
    both attribute access and dictionary style access patterns.
    
    This should be called at the beginning of tests that use Streamlit's session_state.
    """
    if "session_state" not in st.__dict__:
        # Create a dictionary-like object that allows attribute access
        class SessionStateDict(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._dict = {}  # Add an internal dict for storing attributes
            
            def __getattr__(self, name):
                if name.startswith('__') and name.endswith('__'):
                    raise AttributeError(f"SessionStateDict has no attribute '{name}'")
                # First try to get it from the internal dict
                if name in self._dict:
                    return self._dict[name]
                # Then try to get it from self as a dict key
                if name in self:
                    return self[name]
                # Otherwise initialize it
                self[name] = None
                return self[name]
                
            def __setattr__(self, name, value):
                if name == '_dict':
                    # Allow setting _dict attribute during initialization
                    super().__setattr__(name, value)
                else:
                    # Store other attributes in the dict
                    self[name] = value
                
            def __getitem__(self, key):
                if isinstance(key, str) and key.startswith('__') and key.endswith('__'):
                    raise AttributeError(f"SessionStateDict has no key '{key}'")
                if key not in self:
                    self[key] = None
                return super().__getitem__(key)
        
        # Initialize with common default values
        session_state = SessionStateDict()
        session_state['debug_mode'] = True
        session_state['log_level'] = logging.DEBUG
        
        st.session_state = session_state
        return session_state
    
    return st.session_state
