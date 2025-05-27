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

**`TODO: Update the compare options to be more verbose, such as making sure to compare all api fields regardess of content.  This is important as we want to be able to query channels daily and then surface significant changes in metrics.  This is particularly important for:  channel take overs, channels that get shutdown, change ownership, shift in message or content density, Changes in channel descriptions that update copyright or disclaimers, increase in usage of certain keywords or phrases.  Additionally, this ensures that our logic is consistant through the full workflow process and that all data is available at all points for compare as needed.`**

   ```python
   options = {
       'fetch_channel_data': True,
       'fetch_videos': False, 
       'fetch_comments': False,
       'max_videos': 0,
       'max_comments_per_video': 0
   }
   comparison_data = youtube_service.update_channel_data(channel_id, options, interactive=False)
   ```

#### Session State Setup
```python
st.session_state['db_data'] = comparison_data.get('db_data', {})
st.session_state['api_data'] = comparison_data.get('api_data', {})
st.session_state['delta'] = comparison_data.get('delta', {})
st.session_state['existing_channel_id'] = channel_id
st.session_state['collection_mode'] = "refresh_channel"
st.session_state['refresh_workflow_step'] = 2
```

### Step 2: Channel Data Review & Update

#### Data Display
1. **Channel Metrics Display** (3-column layout):
   - **Column 1**: Channel name + YouTube link
   - **Column 2**: Current subscriber count
   - **Column 3**: Current total video count

2. **Expandable Details**:
`TODO: Make sure all api details are returned here`
   - Channel description
   - Total view count
   - Channel ID
   - Last update timestamp

#### Delta Calculation & Display
1. **Channel-Level Deltas** automatically calculated:
   ```python
   delta = compare_data(db_data, api_data)
   ```
2. **Delta Summary Display**:
`TODO: Make sure all api details are returned here`
   - Subscriber changes: `old → new ⬆️/⬇️`
   - View count changes: `old → new ⬆️/⬇️`
   - Video count changes: `old → new ⬆️/⬇️`

#### Manual Refresh Option
**"Refresh Channel Info from API"** button triggers:
```python
options = {
    'fetch_channel_data': True,
    'fetch_videos': False,
    'fetch_comments': False
}
channel_info_response = youtube_service.update_channel_data(channel_id, options, interactive=False)
```

#### User Actions
- **"Save Channel Data"**: Updates database with fresh channel info
`TODO: Make sure that we have visual ui confirmation of what was saved after the operation is completed.  May need to abstract this out into a method that will be used for all save operations.  This may already be present in the codebase but we need to locate and update to always return in the UI. `

- **"Continue to Videos Data"**: Advances to Step 3

### Step 3: Video Collection & Update

#### Video Data Refresh
TODO: Apply all of the same TODO: items from channels to this workflow pattern to ensure parity of returned and visible information at each step of the process.  The only exception would be making sure that the ability to select the video and comment count should be selectable with a slider of all possible values from the prior channel api response and the response from when videos are fetched.  The same would be true for comments which should be applied below. 
1. **API Call Configuration**:
   ```python
   options = {
       'fetch_channel_data': False,
       'fetch_videos': True,
       'fetch_comments': False,
       'max_videos': 50  # or user-defined
   }
   ```
2. **Service Call**: `youtube_service.update_channel_data(channel_id, options, interactive=False)`

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

3. **Change Summary Generation**:
   ```python
   video_delta = {
       'video': video,
       'old_views': old.get('views', 0),
       'new_views': video.get('views', 0),
       'old_likes': old.get('likes', 0), 
       'new_likes': video.get('likes', 0),
       'old_comments': old.get('comment_count', 0),
       'new_comments': video.get('comment_count', 0)
   }
   ```

#### User Interface Display
1. **Video Grid** with delta indicators:
   - Thumbnail + title + video ID
   - Current metrics (views, likes, comments)
   - Change indicators for modified videos

2. **Change Summary**: `"Videos with changes: X"`

#### User Actions
- **"Save Video Data"**: Updates database with refreshed video data
- **"Continue to Comments Data"**: Advances to Step 4

### Step 4: Comment Collection & Update

#### Comment Data Refresh
1. **API Call Configuration**:
   ```python
   options = {
       'fetch_channel_data': False,
       'fetch_videos': False,
       'fetch_comments': True,
       'max_comments_per_video': user_defined
   }
   ```

#### Comment Delta Processing
1. **Comment Comparison**: Compare existing vs. new comments
2. **New Comment Detection**: Identify comments added since last update
3. **Comment Count Updates**: Update comment counts per video
4. **Comment Content Analysis**: Process new comment text and metadata

#### User Interface Display
1. **Comment Summary Statistics**:
   - Total new comments collected
   - Videos with new comments
   - Comment count changes per video

2. **Sample New Comments**: Display recently added comments

#### Completion Actions
- **"Complete Update and Save"**: Final save of all updated data
- **"View Delta Report"**: Detailed change summary

## Advanced Features

### Interactive Mode
The refresh workflow supports interactive mode with iteration prompts:
```python
updated_data = youtube_service.update_channel_data(
    channel_id, 
    options, 
    interactive=True,
    callback=iteration_prompt_callback
)
```

### Delta Reporting
Comprehensive delta tracking includes:
- **Numerical Changes**: Exact count differences
- **Percentage Changes**: Relative change calculations  
- **Directional Indicators**: ⬆️ for increases, ⬇️ for decreases
- **Time-Based Averages**: Daily/weekly change rates

### Comparison View
Side-by-side comparison of:
- Database data (before update)
- Fresh API data (after update)
- Calculated deltas (changes)

## Technical Implementation

### Service Method Integration
```python
# Main update method
youtube_service.update_channel_data(channel_id, options, interactive, existing_data)

# Returns structured comparison data:
{
    'db_data': {...},      # Original database data
    'api_data': {...},     # Fresh API data  
    'delta': {...},        # Calculated changes
    'channel': {...}       # Combined data with deltas
}
```

### Delta Calculation Process
1. **Data Retrieval**: Fetch both database and API data
2. **Structure Normalization**: Ensure consistent data formats
3. **Comparison Logic**: Use DeepDiff library for detailed comparison
4. **Delta Generation**: Calculate numerical and percentage changes
5. **Change Categorization**: Group changes by type and significance

### Session State Management
```python
# Workflow tracking
st.session_state['refresh_workflow_step'] = 1|2|3|4

# Data comparison
st.session_state['db_data'] = {...}
st.session_state['api_data'] = {...} 
st.session_state['delta'] = {...}

# Interactive features
st.session_state['show_iteration_prompt'] = True|False
st.session_state['iteration_choice'] = True|False|None
st.session_state['update_in_progress'] = True|False
```

## Error Handling & Edge Cases

### Common Scenarios
1. **No Changes Detected**: Inform user that data is current
2. **Partial Update Failures**: Save successful portions, report failures
3. **API Rate Limiting**: Graceful degradation with retry mechanisms
4. **Database Conflicts**: Merge conflict resolution strategies

### Data Integrity
1. **Validation Checks**: Ensure data consistency before saving
2. **Rollback Mechanisms**: Ability to revert problematic updates
3. **Audit Trail**: Track all changes for debugging purposes

## Best Practices

### For Users
1. **Regular Updates**: Refresh channels weekly or monthly
2. **Review Deltas**: Examine changes before saving
3. **Selective Updates**: Choose specific data types to refresh
4. **Monitor Trends**: Track changes over time for analysis

### For Developers
1. **Delta Accuracy**: Ensure comparison logic handles edge cases
2. **Performance**: Optimize for large channels with many videos
3. **User Experience**: Provide clear feedback during long operations
4. **Data Consistency**: Maintain referential integrity during updates

## Related Documentation
- [Delta Calculation System](delta-calculation-system.md)
- [Service Layer Architecture](workflow-service-layer.md)
- [Data Comparison Methods](data-comparison-methods.md)

## Migration Health Checks and Zero-Cruft Policy

- After any schema or data migration, a test is added to ensure all records are migrated (e.g., all channels have uploads_playlist_id).
- Backfill scripts are to be removed or archived after all environments are migrated and tests pass.
- No migration or fix logic is left in production code after migration is complete.
- The codebase is kept clean and modern, with no legacy cruft left behind.

## Video Data Storage (2024-06 Update)
- The `videos` table now only stores fields present in the public YouTube API response for non-owners.
- All other/nested/rare fields are preserved in `videos_history` as full JSON.
- The workflow now guarantees schema alignment with the official API and robust time series storage for all video data.
