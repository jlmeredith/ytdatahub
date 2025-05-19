"""
Test configuration initialization module.

Centralizes and initializes all test configuration components.
"""

import os
import sys
from .environment import configure_test_environment
from .test_settings import *


def init_test_config():
    """Initialize test configuration."""
    # Configure test environment
    env = configure_test_environment()
    
    # Add project root to Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Initialize test settings
    settings = {
        "TEST_ENV": env,
        "TEST_DATABASE_PATH": os.environ.get("TEST_DATABASE_URI", TEST_DATABASE_PATH),
        "MOCK_API_RESPONSES": os.environ.get("USE_MOCK_API", "true").lower() == "true",
    }
    
    return settings
