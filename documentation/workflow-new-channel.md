# New Channel Workflow - Step-by-Step Guide

This document provides a detailed breakdown of the New Channel Workflow for adding YouTube channels to YTDataHub for the first time.

## Overview

**Class:** `NewChannelWorkflow` in `/src/ui/data_collection/new_channel_workflow.py`

**Purpose:** Collect comprehensive data for a YouTube channel that hasn't been added to the database before.

**Total Steps:** 3 (Channel Data → Videos → Comments)

## Workflow Sequence

### Step 1: Channel Data Collection

#### Initialization Process
1. **User Input**: Channel URL or ID provided by user
2. **Workflow Setup**: Initialize session state variables:
   ```python
   st.session_state['collection_step'] = 1
   st.session_state['channel_input'] = channel_input
   st.session_state['api_initialized'] = True
   ```
3. **Channel Validation**: Call `youtube_service.get_basic_channel_info(channel_input)`
4. **Data Storage**: Store fetched data in `st.session_state['channel_info_temp']`

#### User Interface Display
1. **Progress Indicator**: Shows "Step 1 of 3: Channel Data"
2. **Channel Metrics Display** (3-column layout):
   - **Column 1**: Channel name + YouTube link
   - **Column 2**: Subscriber count (formatted with commas/K/M)
   - **Column 3**: Total video count (formatted)

3. **Expandable Details Section**:
   - Channel description
   - Total view count
   - Channel ID
   - Additional metadata

#### User Actions
- **"Save Channel Data"**: 
  ```python
  success = youtube_service.save_channel_data(channel_data, "sqlite")
  ```
- **"Continue to Videos Data"**: Advances to Step 2

### Step 2: Video Collection

#### Configuration Phase
1. **Video Limit Selection**: Slider for max videos (0-500)
   - Automatically limited by actual channel video count
   - Default: 50 videos or channel total (whichever is smaller)

#### Data Collection Process
1. **API Call Configuration**:
   ```python
   options = {
       'fetch_channel_data': False,
       'fetch_videos': True, 
       'fetch_comments': False,
       'max_videos': max_videos
   }
   ```
2. **Service Call**: `youtube_service.collect_channel_data(channel_id, options, existing_data=channel_info)`
3. **Data Processing**: Videos are processed and views/likes/comments extracted
4. **Storage**: Updated data stored in `st.session_state['channel_info_temp']['video_id']`

#### User Interface Display
1. **Video Grid Layout** for each video:
   - **Column 1**: Thumbnail image (80px width)
   - **Column 2**: Video title + Video ID
   - **Column 3**: View count metric
   - **Column 4**: Like count metric  
   - **Column 5**: Comment count metric

2. **Sample Data Display**: JSON structure of first video for debugging
3. **Collection Summary**: Total videos fetched

#### User Actions
- **"Save Channel and Videos"**: Saves complete channel + video data
- **"Continue to Comments Data"**: Advances to Step 3

### Step 3: Comment Collection

#### Configuration Phase
1. **Comment Limit Selection**: Slider for max comments per video (0-100)
   - Setting to 0 skips comment collection
   - Applied per video individually

#### Data Collection Process
1. **API Call Configuration**:
   ```python
   options = {
       'fetch_channel_data': False,
       'fetch_videos': False,
       'fetch_comments': True,
       'max_comments_per_video': max_comments
   }
   ```
2. **Service Call**: `youtube_service.collect_channel_data(channel_id, options, existing_data=channel_info)`
3. **Comment Processing**: Comments fetched for each video with available comments
4. **Error Handling**: Videos with disabled comments are handled gracefully

#### User Interface Display
1. **Comment Summary Statistics**:
   - Total comments collected
   - Videos with comments vs. total videos
   - Average comments per video

2. **Sample Comments Display**: Show recent comments from various videos
3. **Collection Status**: Success/failure status for each video

#### Completion Actions
- **"Complete and Save Data"**: Final save of all collected data
- **"Go to Data Storage Tab"**: Navigation to next section

## Technical Implementation Details

### Data Flow
```
User Input → Channel Validation → Basic Channel Info → 
Video Collection → Comment Collection → Database Storage
```

### Service Method Calls
1. **Step 1**: `get_basic_channel_info(channel_input)`
2. **Step 2**: `collect_channel_data(channel_id, video_options, existing_data)`
3. **Step 3**: `collect_channel_data(channel_id, comment_options, existing_data)`
4. **Save Operations**: `save_channel_data(channel_data, "sqlite")`

### Error Handling
- **Invalid Channel**: Clear error message, option to retry
- **API Quota Exceeded**: Graceful degradation with saved partial data
- **Network Issues**: Retry mechanisms and user feedback
- **Data Corruption**: Validation and cleanup processes

### Session State Management
```python
# Step tracking
st.session_state['collection_step'] = 1|2|3

# Data storage
st.session_state['channel_info_temp'] = {...}
st.session_state['api_data'] = {...}

# Status flags
st.session_state['channel_data_fetched'] = True|False
st.session_state['videos_fetched'] = True|False
st.session_state['channel_data_saved'] = True|False
st.session_state['videos_data_saved'] = True|False
```

## Best Practices

### For Users
1. **Start Small**: Begin with 10-20 videos to test API limits
2. **Incremental Collection**: Save data after each step
3. **Monitor Quota**: Be aware of daily API limits
4. **Verify Data**: Review collected data before proceeding

### For Developers
1. **State Management**: Always check session state before operations
2. **Error Recovery**: Implement robust error handling at each step
3. **Data Validation**: Validate API responses before storage
4. **User Feedback**: Provide clear progress indicators and status messages

## Related Documentation
- [Service Layer Architecture](workflow-service-layer.md)
- [YouTube API Integration](youtube-api-guide.md)
- [Data Storage Format](database-operations.md)
