# Changelog

All notable changes to YTDataHub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Bulk import functionality for processing multiple channels at once
- Background task system for non-blocking data collection
- Enhanced data storage options including MongoDB and PostgreSQL support

### Improved

- Data visualization with customizable trend lines and time windows
- Dashboard UI with better responsiveness and theme support
- Comment collection with improved reliability and pagination
- Channel selection interface with better filtering and display options

### Fixed

- Comment pagination handling to properly collect all available comments
- Data coverage calculation for accurate collection status reporting
- UI tab navigation visibility in dark mode
- Date formatting in channel selection table

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
