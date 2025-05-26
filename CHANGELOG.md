# Changelog

All notable changes to YTDataHub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Bulk import functionality for processing multiple channels at once
- Background task system for non-blocking data collection
- Enhanced data storage options including MongoDB and PostgreSQL support
- Comprehensive UI display system for channel data with collapsible field explorer
- Save operation manager with detailed operation tracking and feedback
- UI integration for comprehensive display and save operation components

### Improved

- Data visualization with customizable trend lines and time windows
- Dashboard UI with better responsiveness and theme support
- Comment collection with improved reliability and pagination
- Channel selection interface with better filtering and display options
- Delta visualization with structured comparison features and significance classification
- Save metadata tracking with operation history and detailed summaries
- Parameter handling with consistent sliders across all workflow steps

### Fixed

- Comment pagination handling to properly collect all available comments
- Data coverage calculation for accurate collection status reporting
- UI tab navigation visibility in dark mode
- Date formatting in channel selection table
- Metrics tracking service tests for statsmodels import handling
- TrendAnalyzer anomaly detection for volatile test data
- UI implementation gaps in workflow components
- Integration between comprehensive display and refresh channel workflow
- Missing implementation in save operation feedback system
- Inconsistencies in delta reporting visualization
- Channel and playlist data are now fully persisted, with all fields mapped and saved correctly.
- UI now uses summary cards and collapsible explorers for reviewing channel and playlist data.
- Database save logic for channels and playlists to handle type conversions and dot-to-underscore key mapping.
- Full API responses are now saved in both main and history tables for channels and playlists.
- Fixed missing/mismatched fields and ensured all numeric fields are stored as integers.
- Added/expanded tests to verify all required fields are saved and persisted.

## [0.9.0] - 2025-04-30

### Added

- Delta reporting system using DeepDiff
- Data coverage analysis with visual indicators
- Enhanced Tab Navigation with better theme support
- One-click update functionality for data collection

### Improved

- Channel selection table with clickable channel names
- UI styling with better light/dark mode support
- Video explorer sorting and filtering capabilities
- Comment analysis with sentiment visualization

### Fixed

- Data coverage percentage calculations
- Channel lookup queries for more accurate creation dates
- Number formatting for large values in data tables

## [0.8.0] - 2025-03-15

### Added

- Analytics dashboard with interactive timeline charts
- Video performance comparison tools
- Comment sentiment analysis
- Word cloud visualization for comment topics

### Improved

- Data collection workflow with clear step navigation
- Storage provider selection interface
- Performance optimization for large datasets
- Video thumbnail handling with multiple fallback options

### Fixed

- Session state management for persistent settings
- API error handling and quota management
- Database connection issues

## [0.7.0] - 2025-02-01

### Added

- Three-step data collection workflow
- Support for YouTube channel data retrieval
- Video and comment collection capabilities
- SQLite database storage implementation

### Improved

- Initial UI implementation with sidebar navigation
- Basic video list display with thumbnails
- Simple channel information display

### Fixed

- Initial API integration issues
- Basic error handling for failed requests
