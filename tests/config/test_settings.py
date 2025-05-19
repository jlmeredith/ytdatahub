# Test Configuration Settings
#
# This file contains configuration settings specific to the test environment.
# These settings override the default application settings during test execution.

# Test Database
TEST_DATABASE_PATH = ":memory:"  # Use in-memory SQLite database for testing

# Mock API Settings
MOCK_API_RESPONSES = True  # Use mock API responses instead of actual API calls
API_FIXTURES_PATH = "tests/fixtures/api_responses"  # Path to API fixture data

# Test Environment
TEST_ENV = "testing"
DISABLE_LOGGING = True  # Disable or reduce logging during tests

# Test Output
VERBOSE_TEST_OUTPUT = False  # Set to True for more detailed test output

# Test Timeouts 
DEFAULT_TEST_TIMEOUT = 5  # Default timeout for tests in seconds
EXTENDED_TEST_TIMEOUT = 30  # Extended timeout for long-running tests

# Feature Flags for Testing
ENABLE_SLOW_TESTS = False  # Set to True to include slow tests
ENABLE_EXTERNAL_API_TESTS = False  # Set to True to include tests that call external APIs
