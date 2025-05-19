"""
Test environment configuration loader.

This module loads the appropriate test configuration based on the
test environment (local, CI, etc.) and provides it to the test suite.
"""

import os
import sys

# Add the project root to the Python path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Default test environment
DEFAULT_TEST_ENV = "local"

# Test environments
TEST_ENVIRONMENTS = {
    "local": {
        "description": "Local development environment",
        "use_mocks": True,
        "database": ":memory:",
    },
    "ci": {
        "description": "Continuous Integration environment",
        "use_mocks": True,
        "database": ":memory:",
    },
    "staging": {
        "description": "Staging environment tests",
        "use_mocks": False,
        "database": "file:test_db?mode=memory&cache=shared",
    }
}


def get_test_environment():
    """Get the current test environment configuration."""
    env_name = os.environ.get("TEST_ENV", DEFAULT_TEST_ENV)
    if env_name not in TEST_ENVIRONMENTS:
        print(f"Warning: Unknown test environment '{env_name}'. Using default.")
        env_name = DEFAULT_TEST_ENV
    
    return TEST_ENVIRONMENTS[env_name]


def configure_test_environment():
    """Configure the test environment based on settings."""
    env = get_test_environment()
    print(f"Setting up {env['description']} test environment")
    
    # Set environment variables for tests
    os.environ["USE_MOCK_API"] = str(env["use_mocks"]).lower()
    os.environ["TEST_DATABASE_URI"] = env["database"]
    
    # Return the configured environment
    return env
