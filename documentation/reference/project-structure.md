# YTDataHub Project Structure

YTDataHub follows a modular architecture with clear separation of concerns. This document provides a detailed overview of the project's directory structure and file organization.

## Directory Structure Overview

### Entry Points

- `youtube.py` - Main application entry point that initializes Streamlit and configures the application
- `setup.py` - Package installation script for setting up YTDataHub as a Python package

### Core Application

- `src/app.py` - Main application setup, page routing, and session state management
- `src/config.py` - Configuration settings, environment variable handling, and application constants
- `src/__init__.py` - Package initialization and version information

### Analysis Layer

- `src/analysis/` - Data analysis modules
  - `base_analyzer.py` - Abstract base class with common analysis utilities and helper methods
  - `channel_analyzer.py` - Processes and analyzes channel-level statistics and growth metrics
  - `video_analyzer.py` - Handles video data processing, statistical analysis, and content patterns
  - `comment_analyzer.py` - Processes comment text, sentiment, engagement analysis, and temporal patterns
  - `youtube_analysis.py` - Facade providing backward compatibility with legacy code
  - `visualization/` - Chart generation utilities
    - `__init__.py` - Package initialization for visualization components
    - `trend_line.py` - Statistical trend line generation and time series analysis tools
    - `chart_helpers.py` - Reusable chart configuration functions and layout standardization

### Data Access

- `src/api/` - API client implementations
  - `__init__.py` - Package initialization for API components
  - `youtube_api.py` - Main YouTube Data API client wrapper for backward compatibility
  - `youtube/` - Modular YouTube API clients
    - `__init__.py` - Package initialization exposing the unified API
    - `base.py` - Base API client with common functionality
    - `channel.py` - Channel-specific API operations
    - `video.py` - Video-specific API operations
    - `comment.py` - Comment-specific API operations
    - `resolver.py` - Channel URL and handle resolution
- `src/database/` - Database abstraction and operations
  - `__init__.py` - Package initialization for database components
  - `sqlite.py` - SQLite database operations, schema management, and query functions
  - `migrate_schema.py` - Schema migration utilities
- `src/models/` - Data models and object representations
  - `__init__.py` - Package initialization for data models
  - `youtube.py` - Enhanced data models for YouTube entities (channels, videos, comments, locations)
- `src/services/` - Service layer coordinating business logic
  - `youtube_service.py` - Service layer coordinating API and storage operations
- `src/storage/` - Data persistence implementations
  - `__init__.py` - Package initialization for storage components
  - `factory.py` - Factory pattern for storage backend selection and initialization
  - `local_storage.py` - File-based storage implementation for JSON data

### User Interface

- `src/ui/` - UI components for each application section
  - `__init__.py` - Package initialization for UI components and main tab exports
  - `data_collection.py` - **LEGACY**: Wrapper that delegates to the modern implementation
  - `data_storage.py` - Data persistence interface and storage options configuration
  - `data_analysis.py` - **LEGACY**: Wrapper that delegates to the modern implementation
  - `bulk_import.py` - **LEGACY**: Wrapper that delegates to the modern implementation
  - `utilities.py` - Settings, configuration UI, and debugging tools
  - `components/` - **LEGACY**: Contains older reusable UI components
    - `ui_utils.py` - Utility functions still used by some parts of the codebase
  - `legacy/` - **LEGACY**: Directory for clearly marked legacy components
    - `README.md` - Documentation explaining legacy component status and migration plan
  - `data_analysis/` - **CURRENT**: Modern analytics UI components
    - `main.py` - Entry point for analytics dashboard
    - `components/` - Specialized analytics UI components
      - `analytics_dashboard.py` - Main analytics dashboard component
      - `channel_selector.py` - Channel selection component
      - `comment_explorer.py` - Comment analysis component 
      - `data_coverage.py` - Data coverage visualization component
      - `video_explorer.py` - Video exploration component
    - `utils/` - Utilities specific to data analysis UI
  - `data_collection/` - **CURRENT**: Modern data collection UI components
    - `main.py` - Entry point for data collection workflow
    - `steps_ui.py` - Step-by-step collection workflow
    - `comparison_ui.py` - API vs DB comparison views
    - `channel_refresh_ui.py` - Channel refresh functionality
    - `debug_ui.py` - Debug panel component
    - `queue_ui.py` - Queue status display
    - `state_management.py` - Session state management
  - `bulk_import/` - **CURRENT**: Modern bulk import UI components
    - `render.py` - Main bulk import component

For more information about UI components and their status, see the [UI Components Documentation](ui_components.md).

### Static Assets

- `src/static/` - Static assets for UI rendering
  - `css/` - Stylesheets for UI components
    - `dashboard.css` - Styles for analytics dashboard
    - `styles.css` - Global application styles
  - `templates/` - HTML templates for UI components
    - `analytics_dashboard_styles.html` - Styles for analytics dashboard
    - `analytics_dashboard.html` - Main dashboard template
    - `channel_info.html` - Channel information display template
    - `data_collection_summary.html` - Summary template for collection results
    - `duration_chart.html` - Video duration chart template
    - `duration_metrics.html` - Duration metrics display template
    - `engagement_metrics.html` - Engagement analysis template
    - `engagement_timeline_chart.html` - Timeline chart for engagement metrics
    - `security_headers.html` - Security headers template
    - `storage_options_info.html` - Information about storage options
    - `storage_options.html` - Storage configuration template
    - `video_item.html` - Template for individual video display

### Utilities

- `src/utils/` - Common utility functions
  - `__init__.py` - Package initialization for utilities with direct imports from specialized modules
  - `debug_utils.py` - Debug logging and error reporting utilities
  - `validation.py` - Input validation and data verification utilities
  - `formatters.py` - Data formatting and display utilities
  - `duration_utils.py` - Time and duration formatting utilities
  - `background_tasks.py` - Background task management and execution
  - `queue_manager.py` - Unified queue management system for tracking data operations
  - `performance_tracking.py` - Performance monitoring and timing utilities
  - `logging_utils.py` - Centralized logging utilities
  - `cache_utils.py` - Cache management utilities
  - `ui_helpers.py` - UI-specific helper functions
  - `ui_performance.py` - UI performance tracking utilities

The utilities modules have undergone significant refactoring to improve maintainability:

1. **Consolidated Queue Management**: All queue functionality has been merged into `queue_manager.py`
2. **Removed Re-exports**: The deprecated `helpers.py` module has been removed
3. **Direct Imports**: Code now imports directly from specialized utility modules
4. **Optimized Imports**: Heavy dependencies like NumPy are now imported only when needed

For more details on these changes, see the [Refactoring Progress](source_to_sink_analysis/refactor_progress.md) document.

### Data Storage

- `data/` - Default data storage location
  - `youtube_data.db` - Default SQLite database file for data storage
  - `youtube_data.db_*.bak` - Backup files for the database

### Documentation

- `documentation/` - Detailed documentation files
  - See [Documentation Index](index.md) for a complete list of documentation files

### Package Information

- `ytdatahub.egg-info/` - Package installation metadata
  - `dependency_links.txt` - Package dependency information
  - `PKG-INFO` - Package metadata
  - `SOURCES.txt` - Source file listing
  - `top_level.txt` - Top-level package information

## Architecture Design Principles

The project structure follows several key design principles:

1. **Separation of Concerns**: Clear boundaries between UI, business logic, and data access
2. **Modular Design**: Components are organized into cohesive modules
3. **Abstraction Layers**: Service and repository patterns abstract implementation details
4. **Backward Compatibility**: Legacy code support while evolving the architecture

For more information about the technical architecture, see the [Architecture Documentation](architecture.md).

## Queue System

YTDataHub includes a queue management system to track and stage data operations (channels, videos, comments) before committing them to the database. This system is designed to support both manual and future automated (scheduled) processing of data collection and update tasks.

### Purpose
- Allows users to queue channels, videos, or comments for later processing or saving.
- Enables batch operations and future background task automation (e.g., scheduled updates).
- Provides a clear UI for monitoring what is pending in the queue.

### Implementation
- Core logic: [`src/utils/queue_manager.py`](../../src/utils/queue_manager.py)
  - Tracks items in session state queues for 'channels', 'videos', 'comments', and 'analytics'.
  - Provides functions: `add_to_queue`, `remove_from_queue`, `clear_queue`, `get_queue_items`, `get_queue_stats`, and `render_queue_status_sidebar`.
  - Includes test helpers: `set_test_mode`, `set_queue_hooks`, `clear_queue_hooks`.
- UI integration:
  - In the data collection workflows (new channel and refresh/update), users can:
    - Save channel, video, or comment data directly to the queue for later processing ("Save to Queue for Later" or "Queue ... for Later" buttons).
    - View queue status in the sidebar at each workflow step.
  - The queue status dialog is rendered once per step for clarity.

> **Note:** Previous implementations used separate modules (`queue_tracker.py` and `queue_manager.py`), which have been consolidated into a single `queue_manager.py` module as part of the refactoring process. For more details, see the [Refactoring Progress](source_to_sink_analysis/refactor_progress.md) document.

### Usage in the UI
- At each step (channel, videos, comments), users can choose to:
  - Save data immediately to the database
  - Continue to the next step
  - **Queue the current data for later** (using the provided button)
- The queue can be reviewed and managed from the "Queue Status" tab in the main data collection interface.

### Future Automation
- The queue system is designed to support future enhancements:
  - Background task runners can process queued items on a schedule.
  - Users will be able to select multiple queued items for batch processing or scheduled updates.

For more details, see the code in [`src/utils/queue_manager.py`](../../src/utils/queue_manager.py) and the data collection workflow UIs.

### channels
- Stores basic channel metadata and now includes a `raw_channel_info` column (TEXT/JSON) that contains the full public YouTube API response for each channel. This enables all API fields to be available for analysis and export, even after reloading from the database.
