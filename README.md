# YTDataHub

> **Development Status**: This project is under active development as of May 2025. While most of the core functionality is working, some features may be experimental. A stable release version (1.0) is planned for June 2025.

A powerful YouTube data collection and analysis tool that helps you gather, store, and analyze channel data, videos, and comments with an intuitive step-by-step workflow.

![YTDataHub Homepage](documentation/homepage.png)

## Table of Contents

- [Quick Start Guide](#quick-start-guide)
- [Setup and Installation](#setup-and-installation)
- [Key Features](#key-features)
- [Analytics Capabilities](#analytics-capabilities)
- [Features](#features)
  - [Data Analysis](#data-analysis)
  - [Data Collection](#data-collection)
  - [Data Storage & Organization](#data-storage--organization)
  - [User Interface](#user-interface)
- [Using YTDataHub: Overview](#using-ytdatahub-overview)
- [Delta Reporting](#delta-reporting)
- [Project Structure](#project-structure)
- [Technical Architecture](#technical-architecture)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [License](#license)

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

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/ytdatahub.git
cd ytdatahub
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up YouTube API Key

1. Visit the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "YouTube Data API v3" for your project
4. Create API credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key

You can set up your API key in one of two ways:

- Create a `.env` file in the project root and add: `YOUTUBE_API_KEY=your_api_key_here`
- Or enter it directly in the application interface when prompted

### Step 5: Launch the Application

```bash
streamlit run youtube.py
```

The application should open in your default web browser at `http://localhost:8501`.

## Troubleshooting

If you encounter any issues with YTDataHub, please refer to our comprehensive [Troubleshooting Guide](documentation/troubleshooting.md) which covers:

- API key problems
- Installation issues
- Data collection errors
- Database connection problems
- Performance optimization
- Common error messages

For quick debugging, you can enable debug mode by adding this code at the beginning of your application:

```python
st.session_state.debug_mode = True
st.session_state.log_level = logging.DEBUG
```

If you need additional help, please open an issue on our repository with details about your problem.

## Key Features

YTDataHub provides comprehensive tools for YouTube data analysis:

### Data Collection

- Complete three-step workflow for channel → videos → comments
- Bulk import for processing multiple channels at once
- Delta reporting for tracking changes between data refreshes
- Flexible sampling options for videos and comments

### Analytics

- Interactive dashboard with performance metrics and trends
- Video explorer with advanced sorting and filtering
- Comment analysis with sentiment and topic visualization
- Data coverage analysis with update recommendations

### User Experience

- Modern UI with light and dark mode support
- Customizable visualizations and display options
- Background processing for uninterrupted workflow
- Comprehensive documentation and troubleshooting guides

For a complete history of changes and improvements, see our [Changelog](CHANGELOG.md).

## Analytics Capabilities

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

For more details about data storage options, see the [Database Operations Documentation](documentation/database-operations.md).

### User Interface

YTDataHub features a modern, intuitive interface designed for efficient YouTube data analysis:

- **Clean, organized layout**: Simple navigation between functional areas
- **Interactive visualizations**: Customizable charts and data displays
- **Responsive design**: Works well on both desktop and mobile devices
- **Contextual controls**: Relevant tools available when you need them
- **Performance optimized**: Fast rendering even with large datasets

For more details about the user interface, see the [UI Features Documentation](documentation/ui-features.md).

## Using YTDataHub: Overview

YTDataHub follows a straightforward workflow for collecting, storing, and analyzing YouTube data:

### 1. Data Collection

- **Individual Channel Collection**: Follow a three-step process to collect channel info, videos, and comments
- **Bulk Import**: Process multiple channels at once with shared collection parameters

### 2. Data Storage

- Choose your preferred storage option (SQLite, JSON, MongoDB, or PostgreSQL)
- Name your dataset and save the collected information

### 3. Data Analysis

- **Analytics Dashboard**: Visualize channel performance metrics and trends
- **Data Coverage Analysis**: Check completeness of your data collection
- **Video Explorer**: Browse and analyze individual video performance
- **Comment Analysis**: Explore audience sentiment and engagement

For a detailed step-by-step guide, see the [Data Collection Workflow Documentation](documentation/data-collection-workflow.md).

## Delta Reporting

YTDataHub includes a robust delta reporting system that tracks changes between data collection sessions, helping you understand channel growth and content performance over time.

Key capabilities include tracking subscriber growth, view count increases, new videos, engagement changes, and comment activity. The system provides clear visual reporting with percentage calculations and trend indicators.

For detailed information about delta reporting, see the [Delta Reporting Documentation](documentation/delta-reporting.md).

## Project Structure

YTDataHub follows a modular architecture with clear separation of concerns between data collection, storage, and analysis components. The project is organized into logical modules that handle specific aspects of functionality:

- **Core Application**: Main entry points and configuration
- **Analysis Layer**: Data processing and visualization components
- **Data Access**: API clients and database operations
- **User Interface**: UI components and interaction handlers
- **Utilities**: Helper functions and background task management
- **Documentation**: Comprehensive guides and references

For a complete and detailed breakdown of the project structure, please refer to the [Project Structure Documentation](documentation/project-structure.md).

## Documentation

YTDataHub comes with comprehensive documentation organized into several categories:

### User Documentation

- **[Data Collection Workflow](documentation/data-collection-workflow.md)** - Step-by-step guide for collecting data
- **[Bulk Import Guide](documentation/bulk-import.md)** - How to import multiple channels at once
- **[Analytics Features](documentation/analytics-features.md)** - Overview of analytics capabilities
- **[Troubleshooting Guide](documentation/troubleshooting.md)** - Solutions for common issues

### Technical Documentation

- **[Architecture](documentation/architecture.md)** - System design and component relationships
- **[Project Structure](documentation/project-structure.md)** - Codebase organization
- **[Delta Reporting](documentation/delta-reporting.md)** - How change tracking works
- **[YouTube API Guide](documentation/youtube-api-guide.md)** - Working with the YouTube API
- **[UI Features](documentation/ui-features.md)** - User interface components

For a complete list of documentation resources, see the **[Documentation Index](documentation/index.md)**.

## Technical Architecture

YTDataHub features a modern, modular architecture with several key technical components:

- **Enhanced Database Schema**: Rich data model for comprehensive YouTube data storage
- **Modular API Client**: Specialized components for efficient YouTube API interaction
- **Service Layer**: Clean separation between UI, business logic, and data access
- **Background Processing**: Asynchronous task handling for improved performance

For detailed technical information, see the [Architecture Documentation](documentation/architecture.md).

## License

The YTDataHub is released under the MIT License. Feel free to modify and use the code according to the terms of the license.

---

For more details about the project architecture, technical implementation, and future plans, see [Architecture Documentation](documentation/architecture.md).

## Testing

YTDataHub includes a comprehensive test suite to ensure functionality and reliability across all components. Tests cover utility functions, database operations, UI components, and integration workflows.
