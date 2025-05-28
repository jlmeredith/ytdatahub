# Refresh Channel Workflow - Step-by-Step Guide

This document provides a detailed breakdown of the Refresh Channel Workflow for updating existing YouTube channels in YTDataHub with fresh data and delta calculations.

## Overview

**Class:** `RefreshChannelWorkflow` in `/src/ui/data_collection/refresh_channel_workflow.py`

**Purpose:** Update existing channel data with fresh information from YouTube API and calculate detailed change deltas.

**Total Steps:** 4 (Channel Selection → Channel Update → Video Update → Comment Update)

## Workflow Sequence

### Step 1: Channel Selection (Unique to Refresh Workflow)

#### Channel Discovery
1. **Database Query**: Load existing channels via `youtube_service.get_channels_list("sqlite")`
2. **Channel List Validation**: Check if any channels exist in database
3. **User Interface**: Dropdown with format "Channel Name (Channel ID)"

#### Initial Comparison Setup
1. **Channel Selection**: User selects from dropdown
2. **Comparison Initiation**: "Compare with YouTube API" button triggers:

```python
options = {
    'fetch_channel_data': True,
    'fetch_videos': False,
    'fetch_comments': False,
    'max_videos': 0,
    'max_comments_per_video': 0,
    'comparison_level': 'comprehensive',  # Always use comprehensive for complete analysis
    'track_keywords': [
        'copyright', 'disclaimer', 'new owner', 'ownership', 'management', 
        'rights', 'policy', 'terms', 'agreement', 'takeover', 'acquired',
        'shutdown', 'closing', 'terminated', 'notice', 'warning'
    ],
    'alert_on_significant_changes': True,
    'persist_change_history': True,
    'compare_all_fields': True  # Ensure all fields are compared regardless of content
}
```

3. **API Call**: `youtube_service.update_channel_data(channel_id, options, interactive=False)`
4. **Extract & Validate**: Fields are extracted and validated for UI parity
5. **Delta Processing**: Delta information is promoted to top-level in API data

### Step 2: Channel Data Review (Updated with Save Confirmation)

#### Data Comparison Display
1. **Side-by-Side View**: Database and API data shown in columns
2. **Detailed Delta Analysis**: Field-by-field changes highlighted
3. **Change Dashboard**: Comprehensive display of metrics changes with indicators

#### Save Operation
1. **Save Button**: User initiates save operation with "Save Channel Data"
2. **Database Update**: `youtube_service.save_channel_data(api_data, "sqlite")`
3. **Visual Confirmation**: UI displays success message with details of saved data:
   ```
   Channel data for 'Channel Name' saved successfully!
   
   Data saved to database:
   Channel Name: Example Channel
   Channel ID: UC12345
   Subscribers: 1,234,567
   Views: 98,765,432
   Videos: 250
   Last Updated: 2023-06-01 14:30:45
   ```

### Step 3: Video Collection & Update (Enhanced)

#### Video Data Refresh
1. **Video Collection Controls**: User can adjust:
   - Maximum number of videos to collect (slider up to channel's video count)
   - Comparison detail level (basic/standard/comprehensive) 
   - Keywords to track (comma-separated list)
   - Alert preferences for significant changes

2. **API Call Configuration**:
   ```python
   options = {
       'fetch_channel_data': False,
       'fetch_videos': True,
       'fetch_comments': False,
       'max_videos': user_selected_count,
       'comparison_level': user_selected_level,
       'track_keywords': user_selected_keywords,
       'alert_on_significant_changes': user_preference,
       'persist_change_history': True,
       'compare_all_fields': True  # Ensure all fields are compared
   }
   ```

3. **Service Call**: `youtube_service.update_channel_data(channel_id, options)`
4. **Success Confirmation**: Displays count of videos collected and summary statistics

#### Video-Level Delta Calculation
1. **Video Comparison Process**:
   ```python
   db_videos = db_data.get('video_id', [])
   api_videos = video_response.get('video_id', [])
   db_video_map = {v.get('video_id'): v for v in db_videos}
   ```

2. **Delta Calculation for Each Video**:
   - View count delta: `new_views - old_views`
   - Like count delta: `new_likes - old_likes`
   - Comment count delta: `new_comments - old_comments`
   - Custom fields delta (when compare_all_fields=True)

### Step 4: Comment Collection & Sentiment Analysis

1. **API Call Configuration**:
   ```python
   options = {
       'fetch_channel_data': False,
       'fetch_videos': False,
       'fetch_comments': True,
       'analyze_sentiment': True,
       'max_comments_per_video': 100  # or user-defined
   }
   ```

2. **Service Call**: `youtube_service.update_channel_data(channel_id, options)`

3. **Comment-Level Delta Calculation**:
   - Comment text changes
   - Likes on comments
   - Reply count changes
   - Sentiment score changes

## Enhanced Features

### Comprehensive Comparison
- The system now compares all available fields regardless of content type through the `compare_all_fields` option
- This ensures capturing changes in important fields like channel ownership, descriptions, etc.

### Visual Save Confirmation
- After save operations, detailed summaries are displayed showing what was saved
- This includes key metrics and timestamps to confirm the successful operation

### Dynamic Video Collection
- Video collection now uses dynamic sliders based on the channel's actual video count
- Enhanced comparison options for videos mirror those available for channel data

## Related Documentation
- [Service Layer Architecture](workflow-service-layer.md)
- [YouTube API Integration](youtube-api-guide.md)
- [Data Storage Format](database-operations.md)

## Video Data Storage (2024-06 Update)
- The `videos` table now only stores fields present in the public YouTube API response for non-owners.
- All other/nested/rare fields are preserved in `videos_history` as full JSON.
- The workflow now guarantees schema alignment with the official API and robust time series storage for all video data.
