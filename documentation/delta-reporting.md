# Delta Reporting in YTDataHub

## Overview

Delta reporting is a powerful feature in YTDataHub that provides detailed insights into how channel data changes over time. Using the DeepDiff library, YTDataHub tracks and displays changes between data collection sessions, allowing you to monitor the growth and evolution of YouTube channels.

## How It Works

When updating an existing channel in the database, YTDataHub:

1. Loads the previously stored data as a baseline
2. Fetches fresh data from the YouTube API
3. Uses DeepDiff to perform a deep comparison between the two datasets
4. Generates a user-friendly report showing exactly what has changed

This process happens automatically when you select the "Update Existing Channel" option in the Data Collection tab.

## Types of Changes Tracked

The delta reporting system tracks several types of changes:

- **Value Changes**: When metrics such as views, likes, or subscriber counts change
- **New Items**: When new videos or comments are added to a channel
- **Removed Items**: When videos or comments are no longer available
- **Dictionary/List Changes**: When nested data structures are modified

## Delta Report Display

For each type of data (channel, videos, comments), YTDataHub presents changes in a clear, structured format:

### Channel Data Changes

- Subscriber count increases/decreases
- View count changes
- Channel description updates
- Other metadata changes

### Video Data Changes

- New videos added to the channel
- Changes in view counts for existing videos
- Changes in like counts
- Changes in comment counts
- Video metadata updates (titles, descriptions, etc.)

### Comment Data Changes

- New comments added to videos
- Changed or removed comments
- Comment engagement metrics

## Percentage Change Calculation

For numerical values like views and likes, the delta report includes percentage changes to help you understand the relative significance of the changes:

```
Old Value → New Value (+X%)
```

For example, if a video's views increased from 10,000 to 12,000, the report would show:

```
10K → 12K (+20%)
```

## Technical Implementation

The delta reporting feature is powered by the DeepDiff Python library, which is integrated into the `render_delta_report` function in `src/ui/data_collection.py`. This function:

1. Takes the previous and updated data objects as input
2. Uses DeepDiff to perform a deep comparison with `ignore_order=True` to focus on content changes
3. Processes the raw diff output into a user-friendly format
4. Displays the results in the Streamlit UI using appropriate visualizations

The implementation includes special handling for numerical values, with formatting for large numbers and calculation of percentage changes.

## Using Delta Reports

Delta reports appear automatically when updating existing channels. Look for expandable sections labeled "View Changes in Channel Data", "View Changes in Videos", and "View Changes in Comments" in the respective steps of the data collection process.

### Best Practices

- **Regular Updates**: For trending channels, update data weekly to track growth patterns
- **Pre/Post Campaign Comparison**: Update before and after marketing campaigns to measure impact
- **Historical Analysis**: Update rarely-changing channels less frequently (monthly or quarterly)
- **Thumbnail Verification**: The system now has improved thumbnail handling with multiple fallback options

## Requirements

The delta reporting feature requires the DeepDiff package, which is included in the `requirements.txt` file:

```
deepdiff>=6.3.0
```

If the package is not installed, the system will gracefully fall back to basic reporting.

## Future Enhancements

Planned improvements to the delta reporting system include:

- Time-series visualization of changes over multiple updates
- Configurable thresholds for highlighting significant changes
- Export options for delta reports
- Integration with notification systems for alerting on major changes
