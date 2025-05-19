# YTDataHub Test Files Overview

**Generated:** May 19, 2025  
**Project:** YTDataHub

This document provides a comprehensive list of all test files in the YTDataHub project, organized by test type and subdirectory, to ensure our analysis is complete.

## Unit Tests

### API Tests

- `/tests/unit/api/test_youtube_api_video_fetching.py`: Tests YouTube API video fetching functionality
- `/tests/unit/api/youtube/`: Subdirectory with additional YouTube API tests

### Database Tests

- `/tests/unit/database/test_sqlite.py`: Tests SQLite database operations
- `/tests/unit/database/test_repositories.py`: Tests repository functionality

### Service Tests

- `/tests/unit/services/test_sequential_delta_updates.py`: Tests sequential delta updates functionality
- `/tests/unit/services/test_youtube_service.py`: Tests YouTube service functionality
- `/tests/unit/services/sequential_delta/`: Subdirectory with delta testing components

### UI Tests

- `/tests/unit/ui/test_channel_selector.py`: Tests channel selector component
- `/tests/unit/ui/test_video_collection_display.py`: Tests video collection display component

### Utility Tests

- `/tests/unit/utils/test_helpers.py`: Tests helper utility functions
- `/tests/unit/utils/test_video_views.py`: Tests video views functionality

## Integration Tests

### Workflow Tests

- `/tests/integration/workflow/test_data_collection_workflow.py`: Tests data collection workflow
- `/tests/integration/workflow/test_data_collection_workflow_steps.py`: Tests individual steps in data collection
- `/tests/integration/workflow/test_end_to_end_workflow.py`: Tests end-to-end workflow
- `/tests/integration/workflow/edge_cases/`: Subdirectory with edge case tests
- `/tests/integration/workflow/error_handling/`: Subdirectory with error handling tests

### Database Integration Tests

- `/tests/integration/database/test_database_integration.py`: Tests integration between components and database
- `/tests/integration/workflow/test_add_vs_refresh_parity.py`: Tests parity between add and refresh operations

### UI Integration Tests

- `/tests/integration/api/test_channel_refresh_video_data.py`: Tests refreshing video data for channels
- `/tests/integration/api/test_api_db_comparison_view.py`: Tests API vs database comparison views

### Error Handling Tests

- `/tests/integration/workflow/test_error_handling.py`: Tests error handling across components
- `/tests/integration/api/test_video_with_empty_api_response.py`: Tests handling of empty API responses

### Quota Management Tests

- `/tests/integration/services/test_quota_estimation.py`: Tests quota estimation
- `/tests/integration/services/test_quota_optimization.py`: Tests quota optimization
- `/tests/integration/services/test_quota_optimization_strategies.py`: Tests different quota optimization strategies
- `/tests/integration/services/test_slider_quota_management.py`: Tests quota management UI sliders
- `/tests/integration/services/quota_optimization/`: Subdirectory with quota optimization strategies

### Performance Tests

- `/tests/integration/services/test_pagination_batch.py`: Tests pagination and batch processing
- `/tests/integration/services/test_optimization_techniques.py`: Tests various optimization techniques

### Miscellaneous Integration Tests

- `/tests/integration/database/test_delta_reporting.py`: Tests delta reporting functionality
- `/tests/integration/services/test_queue_management.py`: Tests queue management
- `/tests/integration/workflow/test_minimal.py`: Basic minimal integration test
- `/tests/integration/workflow/test_data_collection_edge_cases.py`: Tests edge cases in data collection

## UI Tests

- `/tests/ui/pages/test_api_data_display.py`: Tests API data display
- `/tests/ui/pages/test_channel_refresh.py`: Tests channel refresh functionality
- `/tests/ui/pages/test_channel_refresh_ui.py`: Tests channel refresh UI components
- `/tests/ui/components/test_channel_selection.py`: Tests channel selection functionality
- `/tests/ui/pages/test_channel_selection_ui.py`: Tests channel selection UI components
- `/tests/ui/pages/test_comparison_view.py`: Tests comparison view
- `/tests/ui/pages/test_data_conversion.py`: Tests data conversion for UI
- `/tests/ui/components/test_debug_panel.py`: Tests debug panel
- `/tests/ui/pages/test_display_comparison_results.py`: Tests display of comparison results
- `/tests/ui/pages/test_tab_navigation.py`: Tests tab navigation
- `/tests/ui/components/test_video_views_display.py`: Tests video views display

## Standalone Tests

- `/simple_test_repos.py`: Simple repository test outside the pytest framework
- `/test_repositories.py`: Repository integration test

## Test Utilities

- `/tests/utils/youtube_test_factory.py`: Factory for creating test data
- `/tests/fixtures/`: Directory containing test fixtures
- `/tests/conftest.py`: Pytest configuration and fixtures
