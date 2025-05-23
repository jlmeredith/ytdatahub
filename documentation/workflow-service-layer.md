# Service Layer Architecture - YouTube Data Collection

This document details the service layer architecture that powers both the New Channel and Refresh Channel workflows in YTDataHub.

## Overview

The service layer provides a clean abstraction between the UI workflows and the underlying YouTube API operations. It follows a modular design with specialized services handling different aspects of data collection.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    UI Layer (Workflows)                        │
├─────────────────────────────────────────────────────────────────┤
│                   YouTube Service (Main)                       │
├─────────────────────────────────────────────────────────────────┤
│  Channel Service │ Video Service │ Comment Service │ Delta Service │
├─────────────────────────────────────────────────────────────────┤
│              Storage Service │ Quota Service                    │
├─────────────────────────────────────────────────────────────────┤
│                     API Layer (YouTube Data API)               │
├─────────────────────────────────────────────────────────────────┤
│                   Database Layer (SQLite)                      │
└─────────────────────────────────────────────────────────────────┘
```

## Core Service Methods

### Primary Collection Methods

#### `collect_channel_data(channel_id, options, existing_data=None)`
**Used by:** New Channel Workflow  
**Purpose:** Fresh data collection from YouTube API  
**File:** `/src/services/youtube/service_impl/data_collection.py`

```python
def collect_channel_data(self, channel_id, options=None, existing_data=None):
    """
    Collect channel data including videos and comments
    
    Args:
        channel_id (str): YouTube channel ID
        options (dict): Collection configuration
        existing_data (dict, optional): Pre-existing channel data
        
    Returns:
        dict: Complete channel data structure
    """
```

**Options Structure:**
```python
options = {
    'fetch_channel_data': bool,    # Get channel info
    'fetch_videos': bool,          # Get video list
    'fetch_comments': bool,        # Get comments
    'max_videos': int,             # Video limit
    'max_comments_per_video': int  # Comment limit per video
}
```

#### `update_channel_data(channel_id, options, interactive=False, existing_data=None)`
**Used by:** Refresh Channel Workflow  
**Purpose:** Update existing data with delta calculation  
**File:** `/src/services/youtube_service.py`

```python
def update_channel_data(self, channel_id, options, interactive=False, existing_data=None):
    """
    Update channel data with comparison and delta calculation
    
    Args:
        channel_id (str): YouTube channel ID
        options (dict): Update configuration  
        interactive (bool): Enable interactive prompts
        existing_data (dict, optional): Database data to compare against
        
    Returns:
        dict: Comparison structure with db_data, api_data, and deltas
    """
```

**Return Structure:**
```python
{
    'db_data': {...},      # Original database data
    'api_data': {...},     # Fresh API data
    'delta': {...},        # Calculated changes
    'channel': {...}       # Combined data with delta information
}
```

## Specialized Services

### Channel Service
**File:** `/src/services/youtube/channel_service.py`

**Responsibilities:**
- Channel ID validation and resolution
- Basic channel information retrieval
- Channel URL parsing and normalization

**Key Methods:**
```python
def get_channel_info(self, channel_id: str) -> Dict
def validate_and_resolve_channel_id(self, channel_id: str) -> Tuple[bool, str]  
def parse_channel_input(self, channel_input: str) -> Optional[str]
```

### Video Service
**File:** `/src/services/youtube/video_service.py`

**Responsibilities:**
- Video list collection from channels
- Video details and statistics retrieval
- Video metadata processing

**Key Methods:**
```python
def collect_channel_videos(self, channel_data, max_results=50) -> Dict
def refresh_video_details(self, channel_data: Dict) -> Dict
def get_video_details_batch(self, video_ids: List[str]) -> Dict
```

**Video Data Processing:**
1. **Statistics Extraction**: Views, likes, comments from various API response locations
2. **Metadata Processing**: Title, description, publish date, thumbnails
3. **Error Handling**: Private/deleted video detection and graceful handling

### Comment Service  
**File:** `/src/services/youtube/comment_service.py`

**Responsibilities:**
- Comment collection from videos
- Comment threading and reply handling
- Comment metadata processing

**Key Methods:**
```python
def collect_video_comments(self, channel_data) -> Dict
def get_video_comments(self, video_id, max_comments=100) -> Dict
```

### Delta Service
**File:** `/src/services/youtube/delta_service.py`

**Responsibilities:**
- Change calculation between data snapshots
- Delta categorization and quantification
- Trend analysis and acceleration calculation

**Key Methods:**
```python
def calculate_deltas(self, api_data, db_data) -> Dict
def _calculate_channel_deltas(self, api_data, db_data) -> Dict
def _calculate_video_deltas(self, api_data, db_data) -> Dict
```

## Data Processing Mixins

### DataCollectionMixin
**File:** `/src/services/youtube/service_impl/data_collection.py`

**Purpose:** Core data collection logic shared between workflows

**Key Features:**
- API response processing
- Data structure normalization  
- Error handling and retry logic
- Debug logging and quota tracking

### DataRefreshMixin
**File:** `/src/services/youtube/service_impl/data_refresh.py`

**Purpose:** Data refresh and update operations

**Key Features:**
- Existing data comparison
- Incremental updates
- Delta calculation integration
- Conflict resolution

### DataProcessingMixin
**File:** `/src/services/youtube/service_impl/data_processing.py`

**Purpose:** Data transformation and cleanup operations

**Key Features:**
- Comment deduplication
- Video statistics normalization
- Data validation and cleanup
- Format standardization

## Storage Service Integration

### Storage Operations
**File:** `/src/services/youtube/service_impl/core.py`

```python
def save_channel_data(self, channel_data, storage_type, config=None) -> bool
def get_channel_data(self, channel_id_or_name, storage_type, config=None) -> dict
def get_channels_list(self, storage_type, config=None) -> list
```

### Database Abstraction
The storage service provides database-agnostic operations:
- **SQLite**: Default local storage
- **Future**: PostgreSQL, MySQL support
- **Caching**: In-memory caching for frequently accessed data

## API Layer Integration

### YouTube API Client
**File:** `/src/api/youtube/channel.py`, `/src/api/youtube/video.py`, `/src/api/youtube/comment.py`

**Features:**
- Rate limiting and quota management
- Batch request optimization
- Error handling and retries
- Response caching

### Quota Management
**File:** `/src/services/youtube/quota_service.py`

**Responsibilities:**
- API quota tracking and estimation
- Request optimization
- Quota exceeded handling
- Usage reporting

## Error Handling Strategy

### Error Categories
1. **API Errors**: Rate limits, invalid requests, network issues
2. **Data Errors**: Malformed responses, missing fields
3. **Database Errors**: Connection issues, constraint violations
4. **Business Logic Errors**: Invalid workflow states, data conflicts

### Error Recovery
```python
# Example error handling pattern
try:
    result = api_call()
except YouTubeAPIError as e:
    if e.error_type == 'quotaExceeded':
        return {'error_videos': 'API quota exceeded'}
    else:
        log_error(e)
        return {'error_videos': str(e)}
```

## Performance Considerations

### Optimization Strategies
1. **Batch Processing**: Group API requests when possible
2. **Caching**: Cache frequently accessed data
3. **Lazy Loading**: Load data only when needed
4. **Pagination**: Handle large datasets efficiently

### Resource Management
1. **Memory Usage**: Stream large datasets
2. **API Quota**: Optimize request patterns
3. **Database Connections**: Connection pooling
4. **Concurrent Operations**: Async processing where applicable

## Configuration Management

### Service Configuration
```python
# Service initialization with configuration
youtube_service = YouTubeService(
    api_key="your_api_key",
    db_config=db_settings,
    quota_config=quota_settings
)
```

### Option Passing
```python
# Workflow-specific options
new_channel_options = {
    'fetch_channel_data': True,
    'fetch_videos': True,
    'fetch_comments': True,
    'max_videos': 50,
    'max_comments_per_video': 25
}

refresh_options = {
    'fetch_channel_data': True,
    'fetch_videos': False,  # Skip videos if only updating channel info
    'fetch_comments': False,
    'delta_calculation': True
}
```

## Testing Strategy

### Service Layer Testing
1. **Unit Tests**: Individual service method testing
2. **Integration Tests**: Service interaction testing
3. **Mock Testing**: API response simulation
4. **End-to-End Tests**: Complete workflow testing

### Test Files
- `/tests/services/youtube/test_data_collection.py`
- `/tests/services/youtube/test_data_refresh.py` 
- `/tests/unit/services/test_youtube_service.py`

## Related Documentation
- [YouTube API Integration](youtube-api-guide.md)
- [Database Operations](database-operations.md)
- [Delta Calculation System](delta-calculation-system.md)
- [Error Handling Guide](troubleshooting.md)
