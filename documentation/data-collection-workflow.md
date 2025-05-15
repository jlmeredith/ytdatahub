# YTDataHub Data Collection Workflow

This document provides a detailed guide for collecting YouTube data using YTDataHub, including both individual channel collection and bulk import options.

## Data Collection Overview

YTDataHub offers a structured approach to collecting YouTube data that ensures you have comprehensive information for analysis. The collection process follows a step-by-step workflow that guides you through collecting channel information, videos, and comments.

## Collection Features

- **Step-by-step workflow**: Intuitive three-step process (channel → videos → comments) with each step building on the previous
- **Direct "Next Step" Navigation**: Clear guidance on what to do next after completing each step
- **Channel information**: Subscriber count, total views, video count, description, and more
- **Video retrieval**: Fetch any number of videos with options to retrieve all available content
- **Comment collection**: Download comments for each video with customizable limits
- **Flexible sampling**: Adjust how many videos and comments to fetch with options to refetch with different parameters
- **Unavailable content handling**: Clear reporting on private or deleted videos and videos with disabled comments
- **Direct YouTube links**: Easy access to channels, videos, and comments on YouTube
- **Advanced metadata**: Comprehensive data collection including video dimensions, definition, license information, and more
- **Location data support**: Future-ready structure for analyzing video location information
- **Delta reporting**: View detailed changes between data refreshes using DeepDiff to track metrics over time
- **Smart thumbnail handling**: Robust thumbnail URL extraction with multiple fallback options for reliable display
- **Update existing channels**: Compare and refresh data for channels already in your database
- **Bulk import**: Efficiently import multiple channels at once with shared collection parameters

## Individual Channel Collection

### Step 1: Channel Information

1. Enter your YouTube API key and a channel ID or URL
2. Click "Fetch Channel Data" to retrieve basic channel information
3. Review channel statistics before proceeding
4. For existing channels, you'll see a delta report showing changes since the last update

### Step 2: Video Data

1. Choose how many videos to download (or select "Fetch All Videos")
2. Click "Fetch Videos" to download video information
3. Videos are immediately displayed with thumbnails, views, likes, and comment counts
4. Sort videos by recency, views, likes, or comment count
5. When updating existing channels, a detailed comparison will show new videos and metric changes

### Step 3: Comments Data

1. Select how many comments to fetch per video (up to 100, or skip by setting to 0)
2. Click "Fetch Comments" to download comment content
3. After comments are fetched, a summary will show key statistics
4. Click the "Go to Data Storage Tab" button to proceed to the next step

## Bulk Import

The bulk import feature allows you to import multiple channels at once, streamlining the data collection process when you need to analyze multiple channels.

### Using Bulk Import

1. Navigate to the "Bulk Import" tab in the main interface
2. Enter multiple channel IDs/URLs or upload a file containing them
3. Set global parameters for all channels:
   - Videos per channel
   - Comments per video
   - Storage options
4. Click "Start Bulk Import" to begin the process
5. Monitor progress as channels are imported
6. View summary statistics when the import completes

For more detailed information about bulk importing, see: [Bulk Import Documentation](bulk-import.md)

## Delta Reporting

When updating existing channels, YTDataHub provides detailed delta reports that show what has changed since the last data collection:

### What Delta Reports Show

- **Channel Statistics**: Changes in subscriber count, total views, video count
- **New Videos**: Videos added since the last update
- **Video Metrics**: Changes in view count, like count, comment count for existing videos
- **Metadata Changes**: Updates to titles, descriptions, or other metadata
- **Comment Count**: Changes in comment counts and new comments

### How Delta Reporting Works

1. YTDataHub loads previously stored data as a baseline
2. Fresh information is fetched from the YouTube API
3. The DeepDiff library compares the two datasets to identify changes
4. Changes are categorized, quantified, and displayed with percentage calculations

For more comprehensive documentation on delta reporting, see:
[Delta Reporting Documentation](delta-reporting.md)

## API Quota Usage

YouTube API has daily quota limits that affect how much data you can collect. YTDataHub is designed to optimize quota usage:

- **Efficient API Calls**: Minimizes unnecessary API requests
- **Batch Processing**: Groups requests when possible
- **Quota Estimation**: Provides estimates of quota usage before operations
- **Quota Monitoring**: Tracks quota usage during collection

For more information about API quota management, see:
[YouTube API Guide](youtube-api-guide.md)

## Best Practices for Data Collection

1. **Start Small**: Begin with a limited number of videos and comments to test your workflow
2. **Use Delta Reports**: Update existing channels regularly to track changes over time
3. **Optimize Comment Collection**: Target comments on high-engagement videos first
4. **Consider API Quotas**: Plan large collection jobs with API quota limits in mind
5. **Use Bulk Import**: For collecting data from multiple channels with similar parameters

## Troubleshooting Collection Issues

- **API Key Problems**: Verify your API key is correct and has necessary permissions
- **Channel Not Found**: Try using the channel ID instead of a custom URL
- **Comments Disabled**: This is normal for videos with comments turned off
- **Pagination Issues**: For comment pagination problems, make sure you're using the latest version
- **Quota Exceeded**: If you hit API quota limits, wait 24 hours before trying again

For more detailed troubleshooting help, see the [Troubleshooting Guide](../README.md#troubleshooting) in the main README.
