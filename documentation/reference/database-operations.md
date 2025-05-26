# Database Operations Guide

This document provides detailed information about the database operations in YTDataHub, with a particular focus on how the system manages data collection iterations.

## Overview

YTDataHub uses SQLite as its primary database for storing YouTube data. The database implementation provides features for managing data collection, including tracking collection attempts and implementing policies to prevent excessive API calls.

## Database Schema

In addition to the tables for storing YouTube data (channels, videos, comments), the database includes tables for tracking metadata about data collection operations:

```sql
CREATE TABLE IF NOT EXISTS channel_iterations (
    channel_id TEXT PRIMARY KEY,
    last_attempt TIMESTAMP,
    attempt_count INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT 0,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
);
```

## Key Database Operations

### Iteration Management

The database includes functionality for managing data collection iterations, particularly for channel data:

#### continue_iteration Method

The `continue_iteration` method is a critical component that determines whether data collection should proceed for a given channel. This method implements a time-based policy to prevent excessive API calls and manage quota usage efficiently.

```python
def continue_iteration(self, channel_id):
    """
    Determines if data collection should continue for the specified channel.

    This method implements a time-based policy to prevent excessive API calls:
    - If a channel has been successfully processed recently, skip it
    - If multiple failed attempts have occurred, implement an exponential backoff
    - Track all attempts for auditing and debugging

    Args:
        channel_id (str): The YouTube channel ID to check

    Returns:
        bool: True if data collection should proceed, False otherwise
    """
    # Implementation details...
```

#### How It Works

1. **Checking Recent Activity**:

   - Queries the `channel_iterations` table to retrieve the last attempt time and count
   - If the channel was successfully processed recently (within the configured threshold), returns False

2. **Exponential Backoff**:

   - For failed attempts, implements an exponential backoff strategy
   - Increases the waiting period between attempts based on the number of previous failures
   - Formula: wait_time = BASE_WAIT_TIME \* (2 ^ attempt_count)

3. **Tracking Attempts**:

   - Increments the attempt counter for each channel
   - Records the timestamp of the most recent attempt
   - Updates the success status based on the outcome

4. **Thresholds**:
   - Configurable maximum number of attempts
   - Adjustable base wait time between attempts
   - Optional maximum backoff period

### Benefits of Iteration Management

This approach provides several important benefits:

1. **API Quota Conservation**:

   - Prevents excessive API calls to the same channel
   - Distributes quota usage more evenly across channels
   - Reduces wasted quota on consistently failing requests

2. **Performance Optimization**:

   - Avoids reprocessing recently updated channels
   - Prioritizes channels that haven't been processed recently
   - Implements appropriate wait times for transient failures

3. **Error Recovery**:
   - Gracefully handles API errors through backoff strategy
   - Allows recovery from temporary network or service issues
   - Provides clear logging of attempts for troubleshooting

## Usage Example

```python
# Example of how to use continue_iteration in a data collection workflow
def collect_channel_data(channel_id):
    db = SQLiteDB()

    # Check if we should proceed with data collection
    if not db.continue_iteration(channel_id):
        logging.info(f"Skipping channel {channel_id} based on iteration policy")
        return False

    try:
        # Perform data collection
        # ...

        # Record successful attempt
        db.update_iteration_status(channel_id, success=True)
        return True
    except Exception as e:
        # Record failed attempt
        db.update_iteration_status(channel_id, success=False)
        logging.error(f"Failed to collect data for channel {channel_id}: {str(e)}")
        return False
```

## Configuration Options

The iteration management system is configurable through the following settings in `config.py`:

- `MAX_ATTEMPT_COUNT`: Maximum number of collection attempts before giving up permanently
- `BASE_WAIT_TIME`: Base waiting time in hours between attempts
- `MAX_BACKOFF_TIME`: Maximum backoff time regardless of attempt count
- `SUCCESS_COOLDOWN_PERIOD`: Time to wait before recollecting data for a channel after successful collection

## Best Practices

1. **Always check continue_iteration before making API calls**:

   ```python
   if db.continue_iteration(channel_id):
       # Proceed with API calls
   ```

2. **Always update iteration status after attempts**:

   ```python
   db.update_iteration_status(channel_id, success=True|False)
   ```

3. **Use appropriate error handling**:

   ```python
   try:
       # API calls
   except QuotaExceededError:
       # Special handling for quota issues
   except Exception as e:
       # General error handling
   ```

4. **Monitor iteration metrics**:
   - Track success/failure rates
   - Analyze channels with repeated failures
   - Adjust configuration parameters as needed

## Related Components

- **YouTubeAPI**: Works in conjunction with the database iteration system to manage API calls
- **YouTubeService**: Orchestrates the data collection process using the database iteration system
- **Config**: Provides configuration parameters for the iteration management system

## Clearing and Resetting the Database

YTDataHub allows you to completely clear all data from your database and reset the schema. This is useful for development, testing, or when you want to start with a clean slate.

### How to Clear the Database

#### 1. Using the UI
- Go to the **Utilities** tab in the Streamlit app.
- In the **Database Management Tools** section, use the **Clear Database** feature.
- Confirm the warning and type 'CLEAR ALL DATA' to enable the button.
- The app will:
  - Create a backup of your database file (with a timestamp).
  - Drop all tables and recreate the schema.

#### 2. Using the CLI
- Run the following command:

```bash
venv/bin/python scripts/clear_and_reset_db.py
```

- This will:
  - Create a backup of your database file.
  - Drop all tables and recreate the schema.

### What Happens During a Reset?
- **Backup:** Your existing database file is backed up with a timestamp before any destructive operation.
- **Drop Tables:** All tables (channels, videos, comments, etc.) are dropped.
- **Schema Recreation:** The schema is recreated so you can immediately start collecting new data.

### When to Use
- During development or testing
- When you want to start with a fresh database
- **Not recommended** for production environments unless you have a backup

## Workflow Parity: Playlist ID Handling

Both the **New Channel** and **Update Channel** workflows in YTDataHub are designed for full parity regarding the YouTube uploads playlist ID:

- The uploads playlist ID is **always fetched** from the YouTube API if not present in the channel info or database.
- The playlist ID is **stored** in both the in-memory channel data and the database (`uploads_playlist_id` column).
- All playlist ID actions (fetch, store, error) are **logged** and visible in the UI debug panel.
- If the playlist ID cannot be fetched, the error is logged and surfaced to the user, and video fetching is skipped.
- This parity is enforced by automated tests and code review to prevent regressions.

**See also:** Debugging and error handling sections for more details on log visibility and error surfacing.
