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
  - `__init__.py` - Package initialization for UI components
  - `data_collection.py` - Data collection workflow UI with step-by-step guidance
  - `data_storage.py` - Data persistence interface and storage options configuration
  - `data_analysis.py` - Analytics dashboard and visualization interface
  - `utilities.py` - Settings, configuration UI, and debugging tools
  - `components/` - Reusable UI components and widgets
    - `channel_card.py` - Displays channel metadata in card format
    - `video_list.py` - Renders paginated video galleries with filtering options
    - `comment_display.py` - Renders comment threads with collapsible replies
    - `metrics_panel.py` - Shows key performance metrics with trend indicators
    - `navigation.py` - Step navigation and workflow guidance components
  - `data_analysis/` - Specialized analytics UI components
    - `main.py` - Entry point for analytics dashboard
    - `channel_insights.py` - Channel growth and performance visualizations
    - `video_performance.py` - Video metrics and engagement analytics
    - `comment_analysis.py` - Comment sentiment and engagement analysis
    - `trend_visualization.py` - Time-series trend visualization components

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
  - `__init__.py` - Package initialization for utilities
  - `helpers.py` - Common utility functions used across the application
  - `background_tasks.py` - Background task management and execution
  - `queue_tracker.py` - Queue management system for tracking data operations

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
- Core logic: [`src/utils/queue_tracker.py`](../../src/utils/queue_tracker.py)
  - Tracks items in session state queues for 'channels', 'videos', 'comments', and 'analytics'.
  - Provides functions: `add_to_queue`, `remove_from_queue`, `clear_queue`, `get_queue_stats`, and `render_queue_status_sidebar`.
- UI integration:
  - In the data collection workflows (new channel and refresh/update), users can:
    - Save channel, video, or comment data directly to the queue for later processing ("Save to Queue for Later" or "Queue ... for Later" buttons).
    - View queue status in the sidebar at each workflow step.
  - The queue status dialog is rendered once per step for clarity.

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

For more details, see the code in [`src/utils/queue_tracker.py`](../../src/utils/queue_tracker.py) and the data collection workflow UIs.

### channels
- Stores basic channel metadata and now includes a `raw_channel_info` column (TEXT/JSON) that contains the full public YouTube API response for each channel. This enables all API fields to be available for analysis and export, even after reloading from the database.
