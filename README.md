# YTDataHub
***Development Note:  This entire application is 100% "vibe" or agentically coded.  I developed the specification and have modified it along the way, but 100% of the code is NOT written by me.  This has been a thought and learning exercise in understanding how to make agentic coding tools do what I want through simple language.  It is actually really great and I hope otherse find it useful once I get to v1.  

The latest code push has the collection system mapping all Youtube public API details to a local database for personal analytics.  The idea behind the project is to create a local system that I can use to surface relevant content. Think advanced Youtube search but taylored to your subscription list.  ***

> **Development Status**: This project is under active development as of May 2025. While most of the core functionality is working, some features may be experimental. A stable release version (1.0) is planned for June 2025.

## 📋 Project Guidelines

**IMPORTANT**: Please read [PROJECT_CONVENTIONS.md](PROJECT_CONVENTIONS.md) for file organization guidelines and conventions. This helps maintain a clean, organized codebase.

## Codebase Improvements

The codebase has undergone significant refactoring to improve maintainability and performance:

- **Consolidated utilities**: Merged redundant queue management functionality into a single module
- **Removed deprecated code**: Eliminated deprecated utility re-exports and helpers
- **Centralized services**: Created dedicated services for error handling and quota management
- **Optimized imports**: Removed unnecessary imports and moved large dependencies into function scope
- **Enhanced documentation**: Updated documentation to reflect architectural improvements

For more details, see [Refactoring Progress](documentation/reference/source_to_sink_analysis/refactor_progress.md).

## Overview

A powerful YouTube data collection and analysis tool that helps you gather, store, and analyze channel data, videos, and comments with an intuitive step-by-step workflow.

![YTDataHub Homepage](documentation/homepage.png)

YTDataHub makes it simple to collect data from YouTube channels, organize it efficiently, and generate insightful analytics. With a step-by-step workflow and flexible storage options, you can quickly gather the data you need for content analysis, market research, or audience insights.

## Key Features

- **Complete Data Collection**: Collect comprehensive channel, video, and comment data
- **Interactive Analytics**: Visualize performance metrics with customizable charts
- **Delta Reporting**: Track changes between data refreshes to monitor growth
- **Multiple Storage Options**: Support for SQLite, JSON, MongoDB, and PostgreSQL
- **Intuitive UI**: Modern, responsive interface with streamlined workflow

## Documentation

For full documentation, please visit:

- [Getting Started Guide](documentation/getting-started/index.md)
- [User Guide](documentation/user-guide/index.md)
- [Technical Reference](documentation/reference/index.md)
- [Troubleshooting](documentation/troubleshooting/index.md)
- [Documentation Index](documentation/index.md)

## Quick Start Guide

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Launch the app**: `streamlit run youtube.py`
3. **Enter your YouTube API key** and a channel ID
4. **Follow the workflow**:
   - Fetch channel information
   - Download videos
   - Collect comments
5. **Store the data** in SQLite (or other supported databases)
6. **Analyze the data** using the built-in analytics components

## Installation

### Prerequisites

1. **Python 3.8+** - Ensure you have Python 3.8 or later installed
2. **Google Cloud Account** - Required for accessing the YouTube Data API
3. **YouTube Data API Key** - Needed to retrieve data from YouTube

```bash
# Clone the repository
git clone https://github.com/yourusername/ytdatahub.git
cd ytdatahub

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch the application
streamlit run youtube.py
```

For detailed installation and setup instructions, see the [Getting Started Guide](documentation/getting-started/index.md).

## Quick Start Guide

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Launch the app**: `streamlit run youtube.py`
3. **Enter your YouTube API key** and a channel ID
4. **Follow the workflow**:
   - Fetch channel information
   - Download videos
   - Collect comments
5. **Store the data** in SQLite (or other supported databases)
6. **Analyze the data** using the built-in analytics components

## Setup and Installation

### Prerequisites

1. **Python 3.8+** - Ensure you have Python 3.8 or later installed
2. **Google Cloud Account** - Required for accessing the YouTube Data API
3. **YouTube Data API Key** - Needed to retrieve data from YouTube

## Troubleshooting

If you encounter any issues with YTDataHub, please refer to our comprehensive [Troubleshooting Guide](documentation/troubleshooting/index.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

For a complete history of changes and improvements, see our [CHANGELOG.md](CHANGELOG.md).

YTDataHub provides powerful analytics capabilities designed to help content creators, marketers, and researchers extract meaningful insights from YouTube data:

- **Channel Performance Analysis**: Track growth and engagement metrics over time
- **Content Coverage Assessment**: Visualize data completeness and identify collection gaps
- **Video Performance Deep-Dive**: Examine videos by various metrics and dimensions
- **Audience Engagement Insights**: Analyze audience sentiment and engagement patterns

For a comprehensive overview of the analytics features, see [Analytics Features Documentation](documentation/analytics-features.md).

## Features

YTDataHub offers a range of features to help you extract and analyze data from YouTube:

### Data Analysis

YTDataHub offers a sophisticated analytics suite with four main components:

- **Analytics Dashboard**: Interactive charts showing channel growth and engagement over time
- **Data Coverage Analysis**: Visual indicators showing data completeness and collection gaps
- **Video Explorer**: Browse, filter, and analyze video performance with customizable views
- **Comment Analysis**: Analyze comment sentiment and discover audience engagement patterns

For detailed information about analytics features, see the [Analytics Features Documentation](documentation/analytics-features.md).

### Data Collection

YTDataHub provides a structured approach to collecting YouTube data:

- **Step-by-step workflow**: Intuitive process for collecting channel, video, and comment data
- **Flexible collection options**: Configure how much data to collect based on your needs
- **Delta reporting**: Track changes between data refreshes to monitor channel growth
- **Bulk import**: Process multiple channels at once with shared collection parameters
- **Comprehensive metadata**: Collect rich information for channels, videos, and comments

For detailed information about data collection, see the [Data Collection Workflow Documentation](documentation/data-collection-workflow.md).

### Data Storage & Organization

YTDataHub ensures your YouTube data is properly stored and easily accessible:

- **Multiple storage options**: Support for SQLite, JSON, MongoDB, and PostgreSQL
- **Enhanced schema**: Rich data model designed for analytical queries
- **Automatic backups**: Prevent data loss with built-in backup functionality
- **Multi-channel storage**: Store data from multiple channels for comparative analysis
- **Data versioning**: Track changes in channel performance over time

## Resetting the Database (Development/Testing)

YTDataHub provides two ways to completely clear and reset your database (all records, all tables):

### 1. Using the UI (Recommended for Most Users)
- Go to the **Utilities** tab in the Streamlit app.
- Scroll to **Database Management Tools**.
- Use the **Clear Database** section:
  - Confirm the warning and type 'CLEAR ALL DATA' to enable the button.
  - Click **Clear Database**. The app will:
    - Create a backup of your current database file (with a timestamp).
    - Drop all tables and recreate the schema.
    - You can immediately start collecting/importing new data.

### 2. Using the CLI (For Automation/Advanced Users)
- Run the following command to clear and reset the database from the terminal:

```bash
venv/bin/python scripts/clear_and_reset_db.py
```
- This will:
  - Create a backup of your database file.
  - Drop all tables and recreate the schema.

**Note:** This operation is destructive and should only be used in development or when you want to start fresh. All data will be lost, but a backup is created for safety.

For more details, see [Database Operations Documentation](documentation/reference/database-operations.md).

### Workflow Parity: Playlist ID Handling

- Both the **New Channel** and **Update Channel** workflows always fetch, log, and store the YouTube uploads playlist ID before any video fetch.
- All playlist ID actions (fetch, store, error) are logged and visible in the UI debug panel.
- This parity is enforced by automated tests and code review to prevent regressions.

## Recent Improvements

### Codebase Cleanup and Modernization (May 2025)

The codebase has undergone significant cleanup and modernization:

1. **Removed Legacy Code**: Eliminated deprecated utility modules and legacy UI wrappers
2. **Improved Channel Resolution**: Enhanced the channel input parsing to robustly handle various input formats
3. **Fixed API Error Handling**: Added proper error handling for API calls and improved resilience
4. **Improved Test Coverage**: Added comprehensive unit and integration tests
5. **Documentation**: Added detailed documentation of the cleanup process

For a complete list of changes, see [Cleanup Summary](documentation/reference/cleanup_summary.md).

## Features

- Collection of YouTube channel data via the YouTube Data API
- Storage and analysis of channel statistics, videos, and comments
- Visualization of channel growth and engagement metrics
- Detection of significant changes in channel performance
- Identification of high-performing content and audience engagement patterns

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your YouTube API key in `.env`
4. Run the application: `streamlit run youtube.py`

## Environment Setup

Create a `.env` file in the project root with the following content:

```
YOUTUBE_API_KEY=your_api_key_here
```

## Usage

1. Start the application: `streamlit run youtube.py`
2. Enter a YouTube channel ID, URL, or handle in the data collection tab
3. Select the data you want to collect (channel info, videos, comments)
4. Analyze the collected data in the analysis dashboard

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.


