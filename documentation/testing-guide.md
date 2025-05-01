# Testing Guide for YTDataHub

This guide outlines the testing infrastructure implemented for YTDataHub, focusing on the data collection and update functionality.

## Overview

YTDataHub now includes a comprehensive test suite that covers:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing how components work together
   d3. **UI Tests**: Testing user interface components and styling
3. **Helper Utilities**: Testing utility functions that support data operations

The testing framework is built on pytest and includes mock objects to simulate YouTube API responses, allowing for reliable testing without actual API calls.

## Test Structure

The tests are organized as follows:

```
tests/
├── conftest.py              # Common fixtures and configurations
├── fixtures/                # Test data fixtures
├── integration/             # Integration tests
│   └── test_data_collection_workflow.py
├── ui/                      # UI tests
│   ├── test_tab_navigation.py
│   └── test_theme_styling.py
└── unit/                    # Unit tests
    ├── api/
    │   └── youtube/
    │       └── test_youtube_api.py
    ├── services/
    │   └── test_youtube_service.py
    └── utils/
        └── test_helpers.py
```

## Implementation Status

As of April 30, 2025, we have successfully implemented:

1. **YouTube API Client Tests**:

   - Basic API initialization verification
   - Channel information retrieval tests
   - Video collection tests
   - Comment fetching tests
   - Custom URL resolution tests
   - All API client method tests are now passing successfully

2. **YouTube Service Tests**:

   - Service initialization tests
   - Channel data collection tests (full, channel-only, with existing data)
   - Channel ID validation and resolution tests
   - Data storage tests
   - Individual component save method tests

3. **UI Component Tests**:
   - Tab navigation visibility tests
   - Dark mode styling tests
   - Theme-specific styling tests for both light and dark modes
   - Tests for responsive behavior of tab components

4. **Queue Management Tests**:
   - Queue data tracking for uncommitted items
   - Tracking operations and state during data collection
   - Hook-based testing infrastructure for reliable queue operation monitoring

These tests provide a solid foundation for ensuring the reliability of the core data collection functionality and the usability of the user interface.

## Key Components Tested

1. **YouTube API Clients**:

   - Channel client (fetches channel information)
   - Video client (fetches video information)
   - Comment client (fetches comments for videos)

2. **YouTube Service**:

   - Data collection orchestration
   - Storage coordination
   - Update delta handling
   - Channel ID validation and resolution
   - Individual data saving operations

3. **Helper Functions**:
   - Duration formatting and conversion
   - Number formatting
   - Quota estimation

4. **Queue Management System**:
   - Operations tracking for database queue
   - Queue state management during collection and storage
   - Test mode for bypassing Streamlit dependencies

## Running Tests

### Running All Tests

```bash
pytest
```

### Running Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests for a specific component
pytest tests/unit/api/youtube/

# Run queue management tests
pytest tests/integration/test_data_collection_workflow.py::TestQueueManagement
```

### Test Coverage Report

Generate a test coverage report to identify untested code:

```bash
pytest --cov=src tests/
```

For a detailed HTML report:

```bash
pytest --cov=src --cov-report=html tests/
```

## Development Workflow with Tests

### TDD Approach

1. **Write a test first** that defines the expected behavior
2. **Run the test** to see it fail (as the feature doesn't exist yet)
3. **Implement the feature** to make the test pass
4. **Refactor the code** while keeping the tests passing

### When Fixing Bugs

1. **Write a test** that reproduces the bug
2. **Verify the test fails** due to the bug
3. **Fix the implementation** until the test passes
4. **Add the test to the suite** to prevent regression

### When Adding Features

1. **Create tests** for the new functionality
2. **Implement the feature** until tests pass
3. **Ensure** all existing tests still pass

## Mocking Strategy

The test suite uses strategic mocking to:

1. **Isolate components** for unit testing
2. **Simulate API responses** without actual YouTube API calls
3. **Create controlled test scenarios** that may be difficult to produce with real data

Key mocked components:

- `mock_youtube_api`: Simulates YouTube API client responses
- `mock_sqlite_db`: Simulates database operations
- `mock_streamlit`: Prevents Streamlit-related errors during testing

### Mocking Challenges Solved

Our implementation has successfully addressed several challenging mocking scenarios:

1. **Streamlit session_state**: We've implemented patching for the debug_log function to prevent Streamlit-related errors during testing.

2. **Storage Provider Factory**: Tests properly patch the StorageFactory.get_storage_provider method to return our mock database objects.

3. **Channel ID Validation**: We've successfully mocked the validation chain for both direct channel IDs and custom URLs.

4. **Queue Operation Monitoring**: Implemented a hook-based system in the queue_tracker module that allows tests to monitor queue operations without complex patching.

## Queue Management System Testing

### Hook-Based Testing Infrastructure

We've implemented a robust hook system for testing queue operations:

```python
# In queue_tracker.py
_add_to_queue_hook = None
_remove_from_queue_hook = None

def set_queue_hooks(add_hook=None, remove_hook=None):
    """
    Set hooks for testing queue operations
    
    Args:
        add_hook (callable): Function to call when add_to_queue is called
        remove_hook (callable): Function to call when remove_from_queue is called
    """
    global _add_to_queue_hook, _remove_from_queue_hook
    _add_to_queue_hook = add_hook
    _remove_from_queue_hook = remove_hook
```

This approach solves mocking challenges associated with importing functions in different modules and provides a more reliable way to test queue operations without patching complexity.

### Example Test Usage

```python
# Test setup
mock_add_hook = MagicMock()
mock_remove_hook = MagicMock()
    
# Set hooks to track queue operations
set_queue_hooks(add_hook=mock_add_hook, remove_hook=mock_remove_hook)

# Run your test operations
channel_data = service.collect_channel_data('channel_id', options)

# Verify queue operations
assert mock_add_hook.call_count == 1
args = mock_add_hook.call_args[0]
assert args[0] == 'channels'
```

### Benefits of Hook-Based Testing

1. **Reliability**: Doesn't depend on how functions are imported in different modules
2. **Simplicity**: Easier to understand than complex patching
3. **Maintainability**: More resilient to code refactoring

## Continuous Integration

Integrating these tests into a CI pipeline will help ensure code quality with each commit:

1. Run tests automatically on push/pull requests
2. Enforce passing tests before merging
3. Generate coverage reports to track test thoroughness

## Next Steps in Testing Implementation

Now that the core service tests are implemented, our next focus areas include:

1. **Expanding API Client Tests**: Implement tests for individual API client methods like get_channel_videos and get_video_comments.

2. **Database Layer Tests**: Add tests for the SQLite database operations to ensure proper data persistence.

3. **Analysis Module Tests**: Begin implementing tests for the data analysis components.

4. **Integration Tests**: Enhance the integration tests to cover full data collection workflows.

## Best Practices

1. Keep tests fast and focused
2. Use descriptive test names that explain what's being tested
3. Use fixtures to share common setup
4. Mock external dependencies
5. Test both success and failure paths
6. Test edge cases and boundary conditions
7. Use hook-based testing for complex module interactions
8. Ensure proper cleanup in tests that modify global state
