# YouTube API Quota Management Guide

This document provides comprehensive information on YouTube API quota usage and optimization strategies for YTDataHub.

## Understanding YouTube API Quota

The YouTube Data API uses a quota system where different operations consume different amounts of your daily quota (default is 10,000 units).

### Core API Operation Costs

| Operation Type              | API Methods                                                            | Quota Cost | Notes                                          |
| --------------------------- | ---------------------------------------------------------------------- | ---------- | ---------------------------------------------- |
| **Read Operations**         | `channels.list`, `videos.list`, `commentThreads.list`, `comments.list` | 1 unit     | Most read operations cost only 1 unit          |
| **Write/Update Operations** | `comments.update`, `channels.update`, `videos.update`                  | 50 units   | Modifying data is significantly more expensive |
| **Search Operations**       | `search.list`                                                          | 100 units  | Searching is very expensive                    |
| **Upload Operations**       | `videos.insert`                                                        | 1600 units | Video uploads have the highest quota cost      |

## Quota Optimization by Resource Type

### Channel API Optimization

- **Efficient Reads**: `channels.list` costs only 1 unit per call
- **Batch Channel Requests**: Retrieve up to 50 channels in a single call using comma-separated IDs
- **Username Limitation**: `forUsername` parameter accepts only one username per call
- **Expensive Updates**: `channels.update` costs 50 units, so minimize update operations

### Video API Optimization

- **Efficient Reads**: `videos.list` costs only 1 unit
- **Batch Video Requests**: Fetch up to 50 videos in a single call with comma-separated video IDs
- **Part Parameter**: Request only needed parts (`snippet`, `contentDetails`, `statistics`, etc.)
- **Expensive Operations**:
  - `videos.insert` (upload): 1600 units
  - `videos.update`: 50 units
  - `videos.delete`: 50 units
  - `videos.rate`: 50 units

### Comment API Optimization

- **Pagination Strategy**: Set `maxResults=100` (the maximum) to minimize API calls
- **Efficient Retrieval**: Both `commentThreads.list` and `comments.list` cost only 1 unit per call
- **Expensive Operations**: Comment modifications (`insert`, `update`, `delete`) cost 50 units each
- **Batching Limitations**:
  - Can retrieve comments for only one video per `commentThreads.list` call
  - Can retrieve replies for only one parent comment per `comments.list` call
  - Can batch retrieve specific comments by ID using comma-separated values (up to 50)

#### Comment Collection Parameters

YTDataHub provides two key parameters to optimize comment collection:

1. **max_comments_per_video**: Controls how many top-level comments to collect per video (0-100)
   - Each increment of ~20 comments requires approximately one additional API call
   - Setting to 0 skips comment collection entirely

2. **max_replies_per_comment**: Controls how many replies to collect per top-level comment (0-50)
   - Higher values increase data completeness but also increase API usage
   - Setting to 0 skips collecting replies

**Quota Impact Formula:**
```
API calls ≈ (videos * (ceil(max_comments_per_video/100) + has_replies * ceil(top_comments_with_replies * max_replies_per_comment/100)))
```

**Optimization Strategy:**
- For lightweight collection: max_comments_per_video=10, max_replies_per_comment=0
- For balanced collection: max_comments_per_video=20, max_replies_per_comment=5
- For comprehensive analysis: max_comments_per_video=50, max_replies_per_comment=20

## General Optimization Techniques

### Use Parts Parameter Wisely

Only request the specific data parts you need:

```python
# Good: Only request needed parts
video_response = youtube.videos().list(
    part="snippet,statistics",
    id=video_id
).execute()

# Avoid: Requesting unnecessary parts
video_response = youtube.videos().list(
    part="snippet,statistics,contentDetails,status,player,topicDetails,recordingDetails",
    id=video_id
).execute()
```

### Implement Efficient Pagination

```python
def get_all_comments(youtube, video_id):
    comments = []
    next_page_token = None

    while True:
        # Get maximum results per page (100) to minimize API calls
        response = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token
        ).execute()

        comments.extend(response['items'])

        # Check if there are more pages
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return comments
```

### Consider ETag Caching

Add ETag handling to save bandwidth and potentially reduce quota for certain operations:

```python
def get_video_with_etag(youtube, video_id, etag=None):
    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )

    # Set ETag if we have one from previous request
    if etag:
        request.headers['If-None-Match'] = etag

    try:
        response = request.execute()
        return {
            'data': response,
            'etag': response.get('etag'),
            'status': 200
        }
    except HttpError as e:
        if e.resp.status == 304:  # Not Modified
            return {
                'data': None,
                'etag': etag,
                'status': 304
            }
        raise
```

### Batch Requests Where Possible

```python
# Efficient: Get data for multiple videos in one request
video_ids = "abc123,def456,ghi789"
videos_response = youtube.videos().list(
    part="snippet,statistics",
    id=video_ids
).execute()
```

## YTDataHub Implementation

YTDataHub incorporates these optimization strategies in its API client architecture:

1. **Specialized Clients**: Separate clients for channel, video, and comment operations
2. **Caching Layer**: Implements ETag and response caching to minimize quota usage
3. **Batched Requests**: Automatically batches requests when possible
4. **Efficient Pagination**: Properly accumulates results across paginated responses

For more information on the client architecture, see [YouTube API Architecture](youtube-api-architecture.md).
