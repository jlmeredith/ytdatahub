<!-- filepath: /Users/jamiemeredith/Projects/ytdatahub/documentation/youtube-api-guide.md -->

# Comprehensive YouTube API Guide

This document provides a consolidated guide to working with the YouTube API in YTDataHub, covering architecture, quota optimization, and best practices for implementation.

## API Architecture Overview

YTDataHub implements a modular architecture for YouTube API interactions that improves maintainability, separates concerns, and optimizes API usage. The architecture consists of specialized client components that focus on specific areas of functionality.

For detailed information about the architecture, including component structure, class relationships, and implementation details, please see the [YouTube API Architecture](youtube-api-architecture.md) document.

### Core Components

1. **Base Client**: Provides common functionality for all specialized clients
2. **Channel Client**: Handles channel-specific API operations
3. **Video Client**: Manages video retrieval and processing
4. **Comment Client**: Focuses on comment retrieval and threading
5. **Channel Resolver**: Specializes in resolving various channel identifiers

## Understanding API Quota

The YouTube Data API uses a quota system where different operations consume different amounts of your daily quota (default is 10,000 units). For detailed information on quota costs and optimization strategies, please see the comprehensive [YouTube API Quota Guide](youtube-api-quota-guide.md).

### Summary of Quota Costs

| Operation Type    | Example API Methods                  | Typical Cost | Key Consideration                     |
| ----------------- | ------------------------------------ | ------------ | ------------------------------------- |
| Read operations   | `channels.list`, `videos.list`       | 1 unit       | Very efficient, use freely            |
| Write operations  | `channels.update`, `comments.update` | 50 units     | Expensive, minimize usage             |
| Search operations | `search.list`                        | 100 units    | Very expensive, use sparingly         |
| Upload operations | `videos.insert`                      | 1600 units   | Extremely expensive, carefully manage |

### General Strategy

- **Reading operations** are significantly more cost-effective than **writing/modifying operations**
- Prioritize batch retrieval operations when possible
- Use smart caching for frequently accessed data
- Implement a policy-based approach to limit unnecessary API calls

## API Optimization Techniques

YTDataHub implements several optimization strategies to maximize efficiency:

### 1. Use the `part` Parameter Wisely

Only request the parts you actually need. Common parts include:

- `snippet`: Basic details like title, description, thumbnails
- `statistics`: Numeric metrics like view count, subscriber count
- `contentDetails`: Details about content, like durations and playlists
- `status`: Publication status information
- `brandingSettings`: Channel branding information

```python
# Instead of requesting all parts:
youtube.channels().list(id=channel_id, part="snippet,contentDetails,statistics,status,topicDetails,brandingSettings")

# Request only what you need:
youtube.channels().list(id=channel_id, part="snippet,statistics")
```

### 2. Batch Requests Efficiently

The YouTube API supports batching in certain operations, which can significantly reduce quota usage:

#### For Channels:

- **channels.list**: You can retrieve up to 50 channels in a single request using a comma-separated list of IDs
  ```python
  youtube.channels().list(id="UC123,UC456,UC789", part="snippet,statistics")
  ```

#### For Videos:

- **videos.list**: You can retrieve details for up to 50 videos in a single request
  ```python
  youtube.videos().list(id="video1,video2,video3", part="snippet,statistics")
  ```

#### For Comments:

- **comments.list**: Retrieve multiple specific comments using the `id` parameter (up to 50)
- **comments.setModerationStatus**: Batch moderate multiple comments

### 3. Handle Pagination Properly

When listing large collections (videos, comments), use pagination efficiently:

```python
def get_all_items(request_function, max_results=None):
    """Generic function to handle YouTube API pagination."""
    items = []
    next_page_token = None
    total_items = 0

    while True:
        # Add the page token to the request if we have one
        if next_page_token:
            request = request_function(pageToken=next_page_token)
        else:
            request = request_function()

        response = request.execute()
        new_items = response.get('items', [])
        items.extend(new_items)
        total_items += len(new_items)

        # Check if we've reached our desired maximum
        if max_results and total_items >= max_results:
            items = items[:max_results]  # Trim to exact count
            break

        # Get the next page token and continue if there are more results
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return items
```

### 4. Implement ETag Caching

Use ETags to avoid retrieving unchanged data:

```python
def fetch_with_etag(request, etag=None):
    """Make a request with ETag support to avoid unnecessary data transfers."""
    if etag:
        # Add If-None-Match header to check if resource has changed
        request.headers['If-None-Match'] = etag

    try:
        response = request.execute()
        new_etag = response.get('etag')
        return response, new_etag, False  # Data changed
    except HttpError as e:
        if e.resp.status == 304:  # Not Modified
            return None, etag, True  # Data unchanged
        else:
            raise  # Re-raise other errors
```

### 5. Implement Request Rate Control

Control the rate of API requests to avoid triggering quota penalties:

```python
import time

def rate_limited_api_call(api_method, *args, **kwargs):
    """Make API calls with rate limiting."""
    # Get the last request time from a cache or state
    last_request_time = get_last_request_time()
    current_time = time.time()

    # Ensure minimum time between requests (e.g., 100ms)
    min_interval = 0.1  # seconds
    if last_request_time and (current_time - last_request_time) < min_interval:
        sleep_time = min_interval - (current_time - last_request_time)
        time.sleep(sleep_time)

    # Make the API call
    result = api_method(*args, **kwargs)

    # Update the last request time
    set_last_request_time(time.time())

    return result
```

## Quota Management Implementation

YTDataHub implements several strategies for managing quota usage:

### 1. Database-Driven Iteration Control

The system uses a database table to track data collection attempts and implement policies to prevent excessive API calls:

```sql
CREATE TABLE IF NOT EXISTS channel_iterations (
    channel_id TEXT PRIMARY KEY,
    last_attempt TIMESTAMP,
    attempt_count INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT 0,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
);
```

The `continue_iteration` method determines whether data collection should proceed:

```python
def continue_iteration(self, channel_id):
    """
    Determines if data collection should continue for the specified channel.
    Implements a time-based policy to prevent excessive API calls:
    - If a channel has been successfully processed recently, skip it
    - If multiple failed attempts have occurred, implement exponential backoff
    - Track all attempts for auditing and debugging
    """
    # Implementation details...
```

### 2. Exponential Backoff

For failed API calls, YTDataHub implements an exponential backoff strategy:

```python
def calculate_backoff_time(attempt_count, base_wait_time=1, max_backoff_time=24):
    """
    Calculate exponential backoff time in hours.

    Args:
        attempt_count: Number of previous attempts
        base_wait_time: Base wait time in hours
        max_backoff_time: Maximum backoff time in hours

    Returns:
        Wait time in hours
    """
    wait_time = base_wait_time * (2 ** (attempt_count - 1))
    return min(wait_time, max_backoff_time)
```

### 3. Quota Estimation

Before making expensive API calls, the system estimates quota usage:

```python
def estimate_quota_usage(channel_id, collection_options):
    """
    Estimate the quota usage for a collection operation.

    Args:
        channel_id: The YouTube channel ID
        collection_options: Dictionary of collection options

    Returns:
        Estimated quota usage
    """
    quota = 0

    # Channel info (1 unit)
    if collection_options.get('fetch_channel_info', True):
        quota += 1

    # Video listing (1 unit per 50 videos)
    if collection_options.get('fetch_videos', True):
        video_count = collection_options.get('max_videos', 0)
        if video_count > 0:
            quota += (video_count // 50) + (1 if video_count % 50 > 0 else 0)

    # Comments (1 unit per API call, typically 1 per video)
    if collection_options.get('fetch_comments', True):
        max_videos = collection_options.get('max_videos', 0)
        if max_videos > 0:
            quota += max_videos

    return quota
```

## Channel Resolution

The system implements a sophisticated channel resolver that can handle various types of YouTube channel identifiers:

### Supported Channel ID Formats

- Standard channel IDs: `UCxxxxxxxxxxxxxxxxxxxxxxxx`
- New-style handles: `@channelname`
- Custom URLs: `youtube.com/c/customname`
- Standard URLs: `youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxxxx`
- Legacy URLs: `youtube.com/user/username`

### Resolution Process

1. **Clean and normalize** the input
2. **Check if it's a direct channel ID** (starts with 'UC')
3. **Extract handles** from various URL formats
4. **Search for matching channels** using the YouTube API
5. **Prioritize matches** based on exact URL/handle match and title relevance
6. **Return the canonical channel ID** for use with other API methods

```python
def resolve_custom_channel_url(self, custom_url_or_handle):
    """
    Resolve a YouTube channel handle or custom URL to a channel ID.

    Supports multiple formats:
    - Direct channel IDs (UCxxxxxxxx)
    - Channel handles (@username)
    - Full YouTube URLs
    - Custom URLs without @ symbol

    Returns the canonical channel ID or None if not found.
    """
    # Implementation details...
```

## API Client Usage Examples

### Fetching Channel Information

```python
from src.api.youtube_api import YouTubeAPI

# Initialize the API client
api = YouTubeAPI(api_key="YOUR_API_KEY")

# Fetch channel information (supports direct IDs, handles, custom URLs)
channel_info = api.get_channel_info("@channelname")

# Access channel data
print(f"Channel Title: {channel_info['snippet']['title']}")
print(f"Subscriber Count: {channel_info['statistics']['subscriberCount']}")
print(f"Video Count: {channel_info['statistics']['videoCount']}")
```

### Retrieving Videos with Pagination

```python
# Get videos with pagination control
videos = api.get_channel_videos(
    channel_info,
    max_videos=100  # Control how many videos to fetch
)

# Process videos
for video in videos:
    print(f"Video Title: {video['snippet']['title']}")
    print(f"Views: {video['statistics']['viewCount']}")
    print(f"Published: {video['snippet']['publishedAt']}")
```

### Fetching Comments

```python
# Get comments for a specific video
comments = api.get_video_comments(
    video_id="VIDEO_ID",
    max_comments=50  # Control how many comments to fetch
)

# Process comments
for comment in comments:
    print(f"Author: {comment['snippet']['authorDisplayName']}")
    print(f"Comment: {comment['snippet']['textDisplay']}")
    print(f"Likes: {comment['snippet']['likeCount']}")
```

## Best Practices Summary

1. **Minimize Write Operations**

   - Read operations (1 unit) are much cheaper than write operations (~50 units)
   - Prioritize read-heavy workflows

2. **Batch Requests When Possible**

   - Use comma-separated IDs for channels, videos, and comments
   - Combine requests to minimize API calls

3. **Use Parts Parameter Efficiently**

   - Only request the data parts you actually need
   - Reduces response size and processing time

4. **Implement Smart Caching**

   - Use ETags to avoid fetching unchanged data
   - Cache frequently accessed data in memory or database

5. **Control API Call Frequency**

   - Implement rate limiting to avoid quota penalties
   - Use exponential backoff for failed requests

6. **Track and Monitor Usage**

   - Monitor your daily quota consumption
   - Implement alerts for approaching quota limits

7. **Handle Errors Gracefully**

   - Implement proper error handling for API errors
   - Retry transient failures with backoff strategies

8. **Use Pagination Efficiently**

   - Fetch maximum allowed items per page (usually 50-100)
   - Use page tokens to retrieve subsequent pages

9. **Implement Policy-Based Collection**

   - Use a policy to determine when to fetch updated data
   - Avoid unnecessary API calls for recently updated content

10. **Take Advantage of Batch Endpoints**
    - Use batch operations where available
    - Properly format batch requests according to API specs

## Conclusion

The YouTube API is a powerful tool for accessing YouTube data, but it requires careful management to use effectively within quota limitations. By following the architecture and best practices outlined in this guide, you can maximize the value of your API quota while building robust applications.

The modular architecture implemented in YTDataHub provides a solid foundation for YouTube API interactions, with specialized components that focus on specific areas of functionality. This approach improves maintainability, testability, and separation of concerns while providing opportunities for optimization at each level.

## Public YouTube Channel API Fields Collected by YTDataHub

YTDataHub collects and stores all publicly available data points for YouTube channels as returned by the YouTube Data API v3. The following fields are fetched and mapped (where available) for each channel:

### Top-Level Fields
- `kind`: Type of the API resource (e.g., youtube#channel)
- `etag`: ETag for caching
- `id`: Unique YouTube channel ID

### `snippet` Part
- `snippet.title`: Channel name
- `snippet.description`: Channel description
- `snippet.customUrl`: Custom URL (if set)
- `snippet.publishedAt`: Channel creation date (ISO 8601)
- `snippet.thumbnails`: Thumbnails (default, medium, high)
  - `thumbnails.default.url`, `.width`, `.height`
  - `thumbnails.medium.url`, `.width`, `.height`
  - `thumbnails.high.url`, `.width`, `.height`
- `snippet.defaultLanguage`: Default metadata language
- `snippet.localized.title`: Localized title (if available)
- `snippet.localized.description`: Localized description (if available)
- `snippet.country`: Associated country (if set and public)

### `contentDetails` Part
- `contentDetails.relatedPlaylists.uploads`: Playlist ID for uploaded public videos

### `statistics` Part
- `statistics.viewCount`: Total channel video views
- `statistics.subscriberCount`: Subscriber count (not present if hidden)
- `statistics.hiddenSubscriberCount`: Whether subscriber count is hidden
- `statistics.videoCount`: Total public videos
- `statistics.commentCount`: (DEPRECATED, may not be present)

### `topicDetails` Part
- `topicDetails.topicIds[]`: List of topic IDs (if available)
- `topicDetails.topicCategories[]`: List of Wikipedia topic URLs (if available)

### `brandingSettings` Part
- `brandingSettings.channel.title`: Channel title (can differ from snippet.title)
- `brandingSettings.channel.description`: Channel description (can differ from snippet.description)
- `brandingSettings.channel.keywords`: Space-separated keywords (may be truncated)
- `brandingSettings.channel.unsubscribedTrailer`: Video ID for unsubscribed trailer (if set)
- `brandingSettings.channel.country`: Country (if set)
- `brandingSettings.channel.defaultLanguage`: Default language
- **Deprecated fields**: Many fields in brandingSettings are deprecated and may not be present (see official docs).

### `status` Part
- `status.privacyStatus`: Privacy status (e.g., public)
- `status.isLinked`: Whether the channel is linked to a YouTube account
- `status.longUploadsStatus`: Eligibility for long uploads
- `status.madeForKids`: Whether the channel is "made for kids"
- `status.selfDeclaredMadeForKids`: (Not available to non-owners)

### `localizations` Part
- `[languageCode].title`: Localized title for each language
- `[languageCode].description`: Localized description for each language

### Notes
- Some fields may be missing or empty for non-owners or due to privacy settings.
- Deprecated fields may not be present in all responses.
- YTDataHub stores the full raw channel API response under `channel_info` for each channel, so all available fields are accessible for analysis and export.

### Code References
- API fetch: `src/api/youtube/channel.py` (`ChannelClient.get_channel_info`)
- Service mapping: `src/services/youtube_service.py` (`get_basic_channel_info`)
- UI display: All fields are accessible in the "All Channel Fields" expander in the data collection workflow.

For the most up-to-date field definitions, always refer to the [official YouTube Data API v3 documentation](https://developers.google.com/youtube/v3/docs/channels/list).

## Database Persistence of API Fields

As of the latest release, YTDataHub persists the full public YouTube channel API response for each channel in the database. This is stored in the `raw_channel_info` column of the `channels` table. All fields returned by the YouTube Data API v3 are available for analysis and export, even after reloading from the database.

- The `raw_channel_info` column contains the complete JSON response from the API for each channel.
- The UI and export features can access all public fields, including those not mapped to top-level columns.
- This ensures full parity with the API and future-proofs the system for new fields.

For more details, see the [channels table schema](../project-structure.md) and the code in `src/database/channel_repository.py`.
