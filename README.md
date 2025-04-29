# YTDataHub

# Currently being actively developed and may not work as expected. I will deliver a release version once it is functioning as expected.

A powerful YouTube data collection and analysis tool that helps you gather, store, and analyze channel data, videos, and comments with an intuitive step-by-step workflow.

![YTDataHub Homepage](documentation/homepage.png)

## Analytics Objectives

YTDataHub is designed with a comprehensive set of analytics objectives to help content creators, marketers, and researchers extract meaningful insights from YouTube data:

### 1. Channel Performance Analysis

- **Comprehensive Overview**: Visualize channel growth and engagement metrics over time
- **Trend Detection**: Identify patterns in views, likes, and comments with customizable trend windows
- **Performance Benchmarking**: Compare current performance against historical data
- **Engagement Ratios**: Analyze likes-to-views and comments-to-views ratios to understand audience behavior
- **Duration Impact Analysis**: Understand how video length correlates with engagement metrics

### 2. Content Coverage Assessment

- **Data Completeness Visualization**: Clearly see what percentage of channel data has been collected
- **Comment Coverage Analysis**: Visualize which videos have comment data and identify collection gaps
- **Temporal Distribution**: Understand the time distribution of collected videos (recent vs. historical)
- **Smart Update Recommendations**: Get actionable suggestions on what data to collect next
- **Background Data Collection**: Update data without interrupting analysis workflows

### 3. Video Performance Deep-Dive

- **Flexible Content Navigation**: Browse, filter, and sort videos with various metrics
- **Multi-Dimensional Analysis**: Examine videos by publication date, view count, engagement, and duration
- **Visual Content Preview**: See video thumbnails alongside performance metrics
- **Metadata Exploration**: Analyze titles, descriptions, tags, and other metadata elements
- **Custom Page Sizing**: Adjust result counts for performance optimization

### 4. Audience Engagement Insights

- **Comment Sentiment Analysis**: Understand audience emotional responses to content
- **Topic Discovery**: Identify common themes and keywords through word clouds
- **Temporal Engagement Patterns**: Track how engagement changes over a video's lifetime
- **Viewer Interaction Analysis**: Explore how different content types drive different engagement levels

These analytics capabilities are continuously being enhanced to provide deeper insights, more visualization options, and greater usability through an intuitive interface.

## Quick Start Guide

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Launch the app**: `streamlit run youtube.py`
3. **Enter your YouTube API key** and a channel ID
4. **Follow the 3-step workflow**:
   - Step 1: Fetch channel information
   - Step 2: Download videos
   - Step 3: Collect comments
5. **Store the data** in SQLite (or other supported databases)
6. **Analyze the data** using the built-in analytics components

## Features

YTDataHub offers a range of features to help you extract and analyze data from YouTube:

### Data Analysis

YTDataHub offers a sophisticated analytics suite with four main components:

#### 1. Analytics Dashboard

- **Performance Metrics**: Track views, likes, comments, and other engagement statistics
- **Time Series Visualization**: Interactive timeline charts showing channel performance over time
- **Configurable Display**: Toggle different metrics on/off to focus on specific aspects of performance
- **Trend Analysis**: Automatic trend line generation with adjustable analysis windows
- **Engagement Ratios**: View likes-to-views and comments-to-views ratios to measure audience interaction

#### 2. Data Coverage Analysis

- **Visual Coverage Indicators**: Color-coded visualizations showing data completeness
- **Comment Collection Status**: See which videos have comment data and which don't
- **Temporal Distribution**: Understand how your collected videos are distributed over time
- **Update Recommendations**: Get smart suggestions for what data to collect next
- **Background Collection Tasks**: Queue and monitor data updates that run in the background

#### 3. Video Explorer

- **Advanced Filtering**: Sort videos by publication date, views, likes, or duration
- **Thumbnail Previews**: Visual representation of each video alongside performance metrics
- **Paginated Results**: Navigate through your video collection with customizable page sizes
- **Metadata Inspection**: Examine titles, descriptions, tags, and other video attributes
- **Performance Comparison**: Easily identify your best and worst performing content

#### 4. Comment Analysis

- **Comment Browser**: Navigate through comments with pagination support
- **Sentiment Analysis**: Understand the emotional tone of audience feedback
- **Word Clouds**: Visualize common topics and themes in your audience's comments
- **Engagement Patterns**: Track how comment activity correlates with video performance
- **Top Commenters**: Identify your most active audience members

### Data Collection

YTDataHub provides a structured approach to collecting YouTube data that ensures you have comprehensive information for analysis:

- **Step-by-step workflow**: Intuitive three-step process (channel → videos → comments) with each step building on the previous
- **Direct "Next Step" Navigation**: Clear guidance on what to do next after completing each step
- **Channel information**: Subscriber count, total views, video count, description, and more
- **Video retrieval**: Fetch any number of videos with options to retrieve all available content
- **Comment collection**: Download comments for each video with customizable limits
- **Flexible sampling**: Adjust how many videos and comments to fetch with options to refetch with different parameters
- **Unavailable content handling**: Clear reporting on private or deleted videos and videos with disabled comments
- **Direct YouTube links**: Easy access to channels, videos, and comments on YouTube
- **Advanced metadata**: Comprehensive data collection including video dimensions, definition, license information, and more
- **Location data support**: Future-ready structure for analyzing video location information
- **Delta reporting**: View detailed changes between data refreshes using DeepDiff to track metrics over time
- **Smart thumbnail handling**: Robust thumbnail URL extraction with multiple fallback options for reliable display
- **Update existing channels**: Compare and refresh data for channels already in your database

### Data Storage & Organization

YTDataHub ensures your valuable YouTube data is properly stored and easily accessible for analysis:

- **Multiple storage options**: Store data in SQLite, local JSON files, MongoDB, or PostgreSQL
- **Enhanced schema**: Comprehensive data model with rich metadata for deeper analysis
- **Automatic backups**: Database backups are created to prevent data loss
- **Flexible retrieval**: Access stored data for further analysis and visualization
- **Channel comparison**: Store data from multiple channels for comparative analysis
- **Modular architecture**: Clean separation of concerns with domain-specific modules
- **Modern data organization**: Structured storage designed for analytical queries
- **Data versioning**: Track changes to channel data over time
- **Metadata enrichment**: Store extended information beyond the basic YouTube API data
- **Efficient storage**: Optimized storage mechanisms to minimize disk usage while maximizing analytical capabilities

### User Interface

YTDataHub features a modern, intuitive interface designed for efficient YouTube data analysis:

- **Channel selector**: Easily view and select channels with sorting and filtering options
- **Analytics dashboard**: Comprehensive visualization of channel performance metrics
- **Data coverage analysis**: Visual indicators of data completeness with enhancement recommendations
- **Video explorer**: Browse and analyze individual video performance
- **Comment analysis**: Explore audience engagement and sentiment
- **Modular interface**: Navigate between different analysis components with a consistent experience
- **Mobile-responsive design**: Access analytics on various devices
- **Customizable displays**: Toggle chart visibility and adjust visualization parameters
- **Sidebar controls**: Quick access to common functions and settings
- **Configurable preferences**: Personalize your analytics experience
- **Performance optimization**: Fast rendering and data processing for large datasets

## Using YTDataHub: Step-by-Step Guide

### 1. Data Collection

#### Step 1: Channel Information

- Enter your YouTube API key and a channel ID or URL
- Click "Fetch Channel Data" to retrieve basic channel information
- Review channel statistics before proceeding
- For existing channels, you'll see a delta report showing changes since the last update

#### Step 2: Video Data

- Choose how many videos to download (or select "Fetch All Videos")
- Click "Fetch Videos" to download video information
- Videos are immediately displayed with thumbnails, views, likes, and comment counts
- Sort videos by recency, views, likes, or comment count
- When updating existing channels, a detailed comparison will show new videos and metric changes

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

Once you've collected and stored your YouTube data, the analysis tab offers powerful insights through four main components:

#### Using the Analytics Dashboard

- Select one or more channels to analyze from the channel selector at the top
- Navigate to the Dashboard section from the sidebar
- Toggle different charts on/off using the sidebar controls:
  - Views Chart: Track view count trends over time
  - Likes Chart: Analyze audience approval
  - Comments Chart: Monitor audience engagement
  - Duration Chart: See how video length affects performance
- Enable trend lines to identify growth patterns and performance trajectories
- Adjust the trend window (Small, Medium, Large) to analyze short or long-term patterns

#### Analyzing Data Coverage

- Navigate to the Data Coverage section from the sidebar
- View the completeness of your data collection through color-coded visualizations:
  - Video Coverage: Percentage of channel videos you've collected
  - Comment Coverage: Percentage of videos with comment data
- Use the stacked bar chart to see the distribution of videos with comments, videos without comments, and uncollected videos
- Check the heatmap for a quick overview of coverage gaps
- Update your data collection based on recommendations:
  - Select a channel to update
  - Choose what content to update (channel info, videos, comments)
  - Set collection parameters (videos to collect, comments per video)
  - Start a background update process

#### Exploring Videos

- Navigate to the Videos section from the sidebar
- Adjust display options in the sidebar:
  - Results per page: Control how many videos are shown at once
  - Thumbnail display: Toggle video thumbnails on/off
  - Sort order: Arrange by publish date, views, likes, or duration
- Browse through videos with pagination controls
- Examine detailed metrics for each video including:
  - View count, like count, comment count
  - Engagement ratios
  - Publication date and duration

#### Analyzing Comments

- Navigate to the Comments section from the sidebar
- Configure display options:
  - Comments per page: Adjust how many comments are shown
  - Sentiment Analysis: Enable/disable sentiment visualization
  - Word Clouds: Toggle topic visualization on/off
- Browse through comments with pagination controls
- Identify common themes and sentiments in audience feedback
- Discover your most engaged viewers and their feedback patterns

## Complete Project Structure
