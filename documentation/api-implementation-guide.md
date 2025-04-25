# API Implementation Guide

This section provides guidance for implementing a REST API for YTDataHub in the future. Following this guide will allow programmatic access to the data collection and analysis capabilities of the application.

## Adding a REST API to YTDataHub

### Overview
A REST API will enable external applications to access YTDataHub functionality programmatically. This implementation leverages FastAPI to provide a modern, high-performance API that integrates with the existing codebase.

### Prerequisites
To implement the API, you'll need to install these additional dependencies:
- FastAPI - A modern, fast web framework for building APIs
- Uvicorn - ASGI server for serving the FastAPI application
- Pydantic - Data validation and settings management

### Step 1: Install Dependencies
Add these dependencies to your `requirements.txt` file:

```
fastapi>=0.95.0
uvicorn>=0.21.0
pydantic>=1.10.7
```

Then install them:

```
pip install -r requirements.txt
```

### Step 2: Create the API File
Create a new file named `api.py` in the project root with the following content:

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn
from typing import List, Optional
import os
from dotenv import load_dotenv

# Import existing components
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDB
from src.storage.local_storage import LocalStorage
# Import other necessary components as needed

# Load environment variables
load_dotenv()

app = FastAPI(
    title="YTDataHub API",
    description="REST API for retrieving and analyzing YouTube data",
    version="1.0.0"
)

# Set up API and storage instances
youtube_api = YouTubeAPI(api_key=os.getenv("YOUTUBE_API_KEY"))
sqlite_db = SQLiteDB()
local_storage = LocalStorage()

# Define data models for API requests/responses
class ChannelInfo(BaseModel):
    channel_id: str
    title: str
    description: str
    subscriber_count: int
    video_count: int
    view_count: int

class VideoInfo(BaseModel):
    video_id: str
    title: str
    description: str
    view_count: int
    like_count: Optional[int]
    comment_count: Optional[int]
    duration: str
    published_at: str

# Define API endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to YTDataHub API"}

@app.get("/channel/{channel_id}", response_model=ChannelInfo)
def get_channel_info(channel_id: str):
    """Get basic information about a YouTube channel."""
    try:
        channel_info = youtube_api.get_channel_info(channel_id)
        if not channel_info:
            raise HTTPException(status_code=404, detail="Channel not found")
        return channel_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/channel/{channel_id}/videos", response_model=List[VideoInfo])
def get_channel_videos(
    channel_id: str,
    max_results: int = Query(10, ge=1, le=50)
):
    """Get videos from a specific YouTube channel."""
    try:
        videos = youtube_api.get_channel_videos(channel_id, max_results=max_results)
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found")
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add more endpoints as needed for your specific use cases

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
```

### Step 3: Launch the API Server
To start the API server, run:

```
uvicorn api:app --reload
```

The API will be available at http://localhost:8000.

### Step 4: Access API Documentation
Once the server is running, access the auto-generated API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Extending the API
You can extend the API by adding more endpoints to cover additional functionality:

### Video Comments
Add an endpoint to retrieve comments for a specific video:

```python
@app.get("/video/{video_id}/comments")
def get_video_comments(video_id: str, max_results: int = Query(50, ge=1, le=100)):
    try:
        comments = youtube_api.get_video_comments(video_id, max_results=max_results)
        if not comments:
            raise HTTPException(status_code=404, detail="No comments found")
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Analysis Endpoints
Add endpoints for data analysis functions:

```python
@app.get("/analysis/channel/{channel_id}/statistics")
def get_channel_statistics(channel_id: str):
    # Implement channel statistics analysis
    pass
```

### Data Storage
Add endpoints to store data in different backends:

```python
@app.post("/storage/save-channel")
def save_channel_data(channel_id: str, storage_type: str = "sqlite"):
    # Implement data storage logic
    pass
```

## Security Considerations
When deploying the API in production:
- Implement authentication using OAuth2 or API keys
- Add rate limiting to prevent abuse
- Consider using HTTPS for secure communication
- Implement proper error handling and logging

## Deployment Options
For production deployment:

### Use Gunicorn with Uvicorn workers:
```
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app
```

### Consider using Docker for containerization:
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```
