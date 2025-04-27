# YTDataHub

A powerful YouTube data collection and analysis tool that helps you gather, store, and analyze channel data, videos, and comments with an intuitive step-by-step workflow.

![YTDataHub Homepage](documentation/homepage.png)

## Quick Start Guide

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Launch the app**: `streamlit run youtube.py`
3. **Enter your YouTube API key** and a channel ID
4. **Follow the 3-step workflow**:
   - Step 1: Fetch channel information
   - Step 2: Download videos
   - Step 3: Collect comments
5. **Store the data** in SQLite (or other supported databases)
6. **Analyze the data** using the built-in reports and visualizations

## Features

YTDataHub offers a range of features to help you extract and analyze data from YouTube:

### Data Collection

- **Improved Comment Handling**: View comment counts immediately after video import, then optionally download actual comment content
- **Step-by-step workflow**: Intuitive three-step process (channel → videos → comments) with each step building on the previous
- **Direct "Next Step" Navigation**: Clear guidance on what to do next after completing each step
- **Channel information**: Subscriber count, total views, video count, description, and more
- **Video retrieval**: Fetch any number of videos with options to retrieve all available content
- **Comment collection**: Download comments for each video with customizable limits
- **Flexible sampling**: Adjust how many videos and comments to fetch with options to refetch with different parameters
- **Unavailable content handling**: Clear reporting on private or deleted videos and videos with disabled comments
- **Direct YouTube links**: Easy access to channels, videos, and comments on YouTube

### Data Organization & Display

- **Modern interface**: Clean, card-based layout optimized for wide-screen viewing
- **Sorting capabilities**: Arrange videos by recency, views, likes, or comment count
- **Video thumbnails**: Visual previews for each video
- **Engagement metrics**: Comment-to-video ratio calculations and statistics
- **Video metadata**: View counts, like counts, publication dates, and duration
- **Comment previews**: Read sample comments with expandable sections
- **Collection summaries**: Detailed breakdown of collected data after each step

### Data Storage & Analysis

- **Multiple storage options**: Store data in SQLite, local JSON files, MongoDB, or PostgreSQL
- **Flexible retrieval**: Access stored data for further analysis and visualization
- **Channel statistics**: Overall performance metrics and trends
- **Video analytics**: Identify top-performing content and patterns
- **Visual reports**: Generate charts and graphs for better insights
- **Modular architecture**: Clean separation of concerns with domain-specific modules

### System Features

- **Quota estimation**: Calculate API usage before making requests
- **Caching system**: Minimize redundant API calls
- **Debugging tools**: Troubleshooting options for development
- **Component-based architecture**: Independently testable, maintainable components
- **Robust error handling**: Graceful recovery from API timeouts and errors

## Complete Project Structure

YTDataHub follows a modular architecture with clear separation of concerns:

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
  - `youtube_api.py` - YouTube Data API client with quota management and error handling
- `src/database/` - Database abstraction and operations
  - `__init__.py` - Package initialization for database components
  - `sqlite.py` - SQLite database operations, schema management, and query functions
- `src/models/` - Data models and object representations
  - `__init__.py` - Package initialization for data models
  - `youtube.py` - Data models for YouTube entities (channels, videos, comments)
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

### Data Storage

- `data/` - Default data storage location
  - `youtube_data.db` - Default SQLite database file for data storage

### Documentation

- `documentation/` - Detailed documentation files
  - `api-implementation-guide.md` - Guide for implementing a REST API
  - `architecture.md` - Detailed architecture documentation
  - `data-analysis-options.png` - Screenshot of analysis options
  - `data-analysis.png` - Data analysis feature diagram
  - `data-storage.png` - Data storage options diagram
  - `homepage.png` - Application homepage screenshot
  - `utilities.png` - Utilities and settings screenshot
  - `youtube-api-quota-md.md` - YouTube API quota information
  - `youtube-channel-api-quota-md.md` - Channel API quota details
  - `youtube-video-api-quota-md.md` - Video API quota details

### Package Information

- `ytdatahub.egg-info/` - Package installation metadata
  - `dependency_links.txt` - Package dependency information
  - `PKG-INFO` - Package metadata
  - `SOURCES.txt` - Source file listing
  - `top_level.txt` - Top-level package information

## Detailed Documentation

For more detailed information about the application, please refer to the documentation folder:

- [Architecture Documentation](documentation/architecture.md) - Detailed explanation of the application architecture
- [API Implementation Guide](documentation/api-implementation-guide.md) - Guide for implementing a REST API
- [YouTube API Quota Information](documentation/youtube-api-quota-md.md) - Information about YouTube API quotas

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

## Using YTDataHub: Step-by-Step Guide

### 1. Data Collection

#### Step 1: Channel Information

- Enter your YouTube API key and a channel ID
- Click "Fetch Channel Data" to retrieve basic channel information
- Review channel statistics before proceeding

#### Step 2: Video Data

- Choose how many videos to download (or select "Fetch All Videos")
- Click "Fetch Videos" to download video information
- Videos are immediately displayed with thumbnails, views, likes, and comment counts
- Sort videos by recency, views, likes, or comment count

#### Step 3: Comments Data

- Select how many comments to fetch per video (up to 100, or skip by setting to 0)
- Click "Fetch Comments" to download comment content
- After comments are fetched, a summary will show key statistics
- Click the "Go to Data Storage Tab" button to proceed to the next step

### 2. Data Storage

- Select a storage option (SQLite is recommended for beginners)
- Name your dataset
- Click "Save Data" to store the collected information
- A confirmation message will appear upon successful storage

### 3. Data Analysis

- Select your storage type and dataset
- Choose from various analysis options:
  - Channel Statistics
  - Video Statistics
  - Top 10 Most Viewed Videos
  - Video Publication Over Time
  - Video Duration Analysis
  - Comment Analysis
- View the generated charts and insights

## Troubleshooting

If you encounter any issues:

1. Check that your API key is correct and has the necessary permissions
2. Ensure you've properly configured any database connections
3. Look for any error messages in the application interface
4. Enable "Debug Mode" in the application for more detailed logs

## License

The YTDataHub is released under the MIT License. Feel free to modify and use the code according to the terms of the license.

---

For more details about the project architecture, technical implementation, and future plans, see [Architecture Documentation](documentation/architecture.md).
