# YTDataHub Test Suite

This directory contains the test suite for the YTDataHub project. The tests are organized according to best practices for Python projects, with clear separation between unit, integration, and UI tests.

## Test Organization Structure

```
tests/
  ├── config/                 # Test configuration files
  ├── fixtures/               # Reusable test fixtures
  ├── unit/                   # Unit tests
  │   ├── analysis/           # Tests for the analysis module
  │   ├── api/                # Tests for the API clients
  │   ├── database/           # Tests for database operations
  │   ├── models/             # Tests for data models
  │   ├── services/           # Tests for service layer
  │   ├── storage/            # Tests for storage implementations
  │   ├── ui/                 # Unit tests for UI components
  │   └── utils/              # Tests for utility functions
  ├── integration/            # Integration tests
  │   ├── api/                # API integration tests
  │   ├── database/           # Database integration tests
  │   ├── services/           # Service layer integration tests
  │   └── workflow/           # End-to-end workflow tests
  ├── ui/                     # UI tests
  │   ├── components/         # Tests for individual UI components
  │   └── pages/              # Tests for entire UI pages/workflows
  └── utils/                  # Test utility functions
```

## Running Tests

### Running All Tests

```bash
pytest
```

### Running Specific Test Categories

```bash
# Run all unit tests
pytest tests/unit

# Run all integration tests
pytest tests/integration

# Run all UI tests
pytest tests/ui
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/unit/api/test_youtube_api_video_fetching.py

# Run tests with specific name pattern
pytest -k "test_channel"
```

## Test Naming Conventions

- **Unit Tests**: `test_<module_name>.py`
- **Integration Tests**: `test_<feature>_integration.py`
- **UI Tests**: `test_<component/feature>_ui.py`

## Test Writing Guidelines

### Unit Tests

- Test one function or method at a time
- Mock external dependencies
- Use appropriate fixtures for test setup
- Focus on testing behavior, not implementation details

### Integration Tests

- Test interactions between multiple components
- Minimize mocking, test actual integrations when possible
- Focus on workflow validation and component interaction

### UI Tests

- Test both component functionality and page workflows
- Separate component-level tests from page-level tests
- Use page object patterns where appropriate

## Test Coverage

The goal is to maintain high test coverage across all modules:

- Run coverage reports with: `pytest --cov=src`
- Focus on critical paths and business logic
- Document any intentional coverage gaps in `documentation/test-coverage-gaps.md`

## Fixtures and Utilities

- Place reusable test fixtures in `tests/fixtures/`
- Common utilities should go in `tests/utils/`
- Global fixtures are defined in `conftest.py`
