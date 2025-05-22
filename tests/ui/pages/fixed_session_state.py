"""
Improved SessionStateMock class for tests
"""
import logging

class SessionStateMock(dict):
    """A mock for streamlit.session_state that allows attribute access"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dict = {}  # Add an internal dict for storing attributes
        self['debug_mode'] = True  # Initialize debug_mode to prevent KeyError
        self['log_level'] = logging.DEBUG  # Use proper integer value
        
    def __getattr__(self, name):
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
        if key not in self:
            self[key] = None
        return super().__getitem__(key)
