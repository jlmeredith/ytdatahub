# Getting Started with YTDataHub

This section helps you get started with YTDataHub quickly and efficiently.

## Overview

YTDataHub is a powerful YouTube data collection and analysis tool that helps you gather, store, and analyze channel data, videos, and comments with an intuitive step-by-step workflow.

## Contents

- [Data Collection Workflow](data-collection-workflow.md) - Step-by-step guide for collecting YouTube data

## Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Launch the app**: `streamlit run youtube.py`
3. **Enter your YouTube API key** and a channel ID
4. **Follow the workflow**:
   - Fetch channel information
   - Download videos
   - Collect comments
5. **Store the data** in SQLite (or other supported databases)
6. **Analyze the data** using the built-in analytics components

## Resetting the Database (Development Only)

If you want to start with a clean database (for development/testing):
- Use the **Clear Database** tool in the Utilities tab of the app, or
- Run `venv/bin/python scripts/clear_and_reset_db.py` from the command line.

This will back up your current database, drop all tables, and recreate the schema so you can start fresh.

## Setup and Installation

### Prerequisites

1. **Python 3.8+** - Ensure you have Python 3.8 or later installed
2. **Google Cloud Account** - Required for accessing the YouTube Data API
3. **YouTube Data API Key** - Needed to retrieve data from YouTube

### Detailed Installation Steps

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/ytdatahub.git
cd ytdatahub
```

2. **Create a Virtual Environment**

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Set Up YouTube API Key**

   - Visit the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the "YouTube Data API v3" for your project
   - Create API credentials:
     - Go to "APIs & Services" > "Credentials"
     - Click "Create Credentials" > "API Key"
     - Copy your API key

   You can set up your API key in one of two ways:

   - Create a `.env` file in the project root and add: `YOUTUBE_API_KEY=your_api_key_here`
   - Or enter it directly in the application interface when prompted

5. **Launch the Application**

```bash
streamlit run youtube.py
```

The application should open in your default web browser at `http://localhost:8501`.

## Next Steps

After setting up YTDataHub, you may want to explore the [User Guide](../user-guide/index.md) to learn more about the features and capabilities of the application.
