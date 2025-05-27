# YTDataHub Troubleshooting Guide

This document provides solutions for common issues you might encounter when using YTDataHub.

## API Key Problems

1. **Invalid API Key**:

   - Verify your API key is correctly entered
   - Check that you've enabled the YouTube Data API v3 in Google Cloud Console
   - Ensure you have sufficient quota available for your API key

2. **API Quota Exceeded**:

   - YouTube API has daily quotas - wait 24 hours for them to reset
   - Consider implementing a quota management strategy for large data collection jobs
   - Split large collection jobs across multiple days

3. **API Key Configuration**:
   - Check that your API key is stored correctly in the `.env` file or entered properly in the UI
   - Verify the API key has the proper permissions for YouTube Data API v3
   - If using environment variables, ensure the application can access them

## Installation Issues

1. **Dependency Problems**:

   - Make sure you're using Python 3.8 or higher
   - Try reinstalling dependencies: `pip install --force-reinstall -r requirements.txt`
   - Check for any error messages during installation and search for specific solutions

2. **Virtual Environment Issues**:

   - Ensure your virtual environment is properly activated before installing dependencies
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

3. **Package Conflicts**:
   - Try creating a fresh virtual environment if you encounter package conflicts
   - Use `pip list` to verify installed package versions
   - Install packages one by one if you encounter dependency resolution issues

## Data Collection Errors

1. **"Comments disabled" Messages**:

   - This is normal for videos with comments turned off by the channel owner
   - You can still collect and analyze other video metrics
   - Filter your analysis to videos with available comments

2. **Channel Not Found**:

   - If custom URLs fail, try using the channel ID instead
   - Look for the channel ID in the page source of the YouTube channel page
   - Use a channel ID lookup tool if necessary

3. **Comment Pagination Issues**:

   - Ensure you're using the latest version of YTDataHub (version 0.9.5 or later)
   - The application properly handles pagination of comments across multiple pages

4. **Incomplete Video Lists**:
   - YouTube API might not return all videos for very large channels
   - Try using date ranges to break up collection into smaller chunks
   - Use the "Fetch All Videos" option, which implements pagination for large collections

## Comment Collection Issues

### Missing Comment Storage

**Symptoms**: 
- Comments not appearing in database after collection
- Error: `CommentRepository errors: object has no attribute 'store_comment'`

**Solution**:
If you encounter this issue in an older version, ensure the CommentRepository class has a `store_comment` method to handle storing a single comment. The standard implementation should delegate to the existing `store_comments` method like this:

```python
def store_comment(self, comment, video_db_id, fetched_at):
    """Store a single comment by calling the plural form with a list of one item."""
    return self.store_comments([comment], video_db_id, fetched_at)
```

### Customizing Comment Collection Depth

**Feature**:
YTDataHub allows you to control how many comments are collected:

- **Top-Level Comments Per Video**: Controls how many primary comments to collect for each video (0-100)
- **Replies Per Top-Level Comment**: Controls how many replies to collect for each primary comment (0-50)

**Usage Tips**:
- Setting either value to 0 will skip collecting that level of comments
- Higher values provide more comprehensive data but consume more API quota
- For a representative sample, 10-25 top comments and 5-10 replies is often sufficient
- For in-depth analysis, use higher values or the "Fetch All Available" option

**Common Configurations**:

| Focus Area                 | Top-Level Comments | Replies Per Comment | Best For                              |
|----------------------------|--------------------|--------------------|---------------------------------------|
| Quick Overview             | 10                 | 0                  | Basic sentiment analysis              |
| General Analysis           | 20                 | 5                  | Balanced data collection              |
| Detailed Engagement        | 50                 | 10                 | Engagement metrics and trends         |
| Comprehensive Research     | 100                | 20                 | Academic research, audience studies   |

**Advanced Usage**:
For detailed examples and scenarios, see the [Comment Collection Scenarios](../guides/comment-collection-scenarios.md) guide.

**Troubleshooting Collection Issues**:
- If no comments are collected, check if comments are disabled on the videos
- For videos with large comment sections, pagination is handled automatically
- If "Fetch All Available" returns fewer comments than expected, the remaining comments might require additional API quota

### Missing Video Metadata When Collecting Comments

**Symptoms**:
- Error when trying to collect comments for a video ID that exists in the comments table but not in the videos table
- Missing related video data when analyzing comments

**Solution**:
Make sure the comment collection workflow checks for the existence of the video metadata and fetches it if needed before attempting to collect comments.

### Missing Comment Replies

**Symptoms**:
- Only top-level comments appear in the database
- Reply counts show non-zero values but no replies are stored

**Solution**:
Check that the comment collection process includes a specific call to fetch replies using the YouTube API's `commentThreads.list` method with the `part=replies` parameter.

Note: These issues were addressed and fixed in version 2.3.0 (May 2025) of YTDataHub.

## Database Issues

1. **Connection Errors**:

   - For SQLite, check that the database file exists and is not corrupted
   - For MongoDB/PostgreSQL, verify connection strings and credentials
   - Ensure you have proper permissions to write to the database location

2. **Database Locked**:

   - Close any other applications that might be accessing the database
   - Wait a few seconds and try again
   - In rare cases, you might need to restart the application

3. **Missing Data**:
   - Check that data was properly saved after collection
   - Use the data coverage analysis to identify missing content
   - Consider running a delta update to fill in gaps

## Performance Issues

1. **Slow Data Collection**:

   - Large channels with many videos will naturally take longer to process
   - Consider adjusting collection parameters for a smaller sample size
   - Use background processing for large collection jobs

2. **UI Responsiveness**:

   - Adjust the results per page settings in the UI to show fewer items
   - Toggle off thumbnail display for faster rendering of video lists
   - Close unused browser tabs to free up resources

3. **Memory Usage**:
   - Very large datasets may require more system resources
   - Consider filtering your dataset before analysis
   - For extremely large datasets, use a database rather than JSON storage

## Debugging

Enable debug logging by adding this code at the beginning of your application:

```python
st.session_state.debug_mode = True
st.session_state.log_level = logging.DEBUG
```

This will display detailed logging information that can help identify issues.

## Common Error Messages

1. **"API key not valid"**:

   - Your API key is incorrect or has been revoked
   - Generate a new API key in the Google Cloud Console

2. **"Quota exceeded"**:

   - You've reached your daily API quota limit
   - Wait 24 hours for the quota to reset

3. **"Comments are disabled for this video"**:

   - The video owner has turned off comments
   - This is normal and the application will handle it appropriately

4. **"Error 429: Too Many Requests"**:
   - You're making API requests too quickly
   - The application will automatically implement backoff strategies

## Still Need Help?

If you're encountering issues not covered in this guide:

1. Check the [Documentation Index](index.md) for more specific guides
2. Look for error messages in the application interface or console
3. Open an issue on our GitHub repository with:
   - A description of the problem
   - Steps to reproduce the issue
   - Any error messages you're seeing
   - Your environment details (OS, Python version)
