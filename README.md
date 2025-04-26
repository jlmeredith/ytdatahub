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

### System Features

- **Quota estimation**: Calculate API usage before making requests
- **Caching system**: Minimize redundant API calls
- **Debugging tools**: Troubleshooting options for development
- **Modular architecture**: Easy to extend and maintain
- **Robust error handling**: Graceful recovery from API timeouts and errors

## Detailed Documentation

For more detailed information about the application, please refer to the documentation folder:

- [API Implementation Guide](documentation/api-implementation-guide.md)
- [Data Analysis Features](documentation/data-analysis.png)
- [Data Storage Options](documentation/data-storage.png)
- [Utilities and Settings](documentation/utilities.png)

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

For more details about the project architecture, technical implementation, and future plans, see [Project Architecture](documentation/api-implementation-guide.md).
