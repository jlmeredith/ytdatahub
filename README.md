# YTDataHub

> **Development Status**: This project is under active development as of May 2025. While most of the core functionality is working, some features may be experimental. A stable release version (1.0) is planned for June 2025.

A powerful YouTube data collection and analysis tool that helps you gather, store, and analyze channel data, videos, and comments with an intuitive step-by-step workflow.

![YTDataHub Homepage](documentation/homepage.png)

## Overview

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


