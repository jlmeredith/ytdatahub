# Bulk Import Feature

The Bulk Import feature in YTDataHub allows you to efficiently import multiple YouTube channels at once, saving time and effort when building your initial dataset.

## Overview

The bulk import functionality provides a way to:

1. Import multiple YouTube channels in a single operation
2. Process channel data in the background without blocking the UI
3. Configure collection parameters for all channels at once
4. Monitor import progress through a unified interface

## How to Use Bulk Import

### Step 1: Access the Bulk Import Tab

Navigate to the "Bulk Import" tab in the main application interface. This tab is designed specifically for handling multiple channel imports.

### Step 2: Prepare Your Channel List

You can import channels in two ways:

1. **Direct Entry**: Enter multiple channel IDs or URLs separated by commas, line breaks, or spaces
2. **File Upload**: Upload a CSV or text file containing channel IDs/URLs (one per line)

### Step 3: Configure Import Parameters

Set global parameters for all channels being imported:

- **Videos per Channel**: Choose how many videos to fetch per channel (or select "Fetch All")
- **Comments per Video**: Specify how many comments to retrieve per video
- **Storage Option**: Select where to store the imported data (SQLite is recommended)
- **Dataset Name**: Provide a name for your bulk import dataset

### Step 4: Start the Import Process

Click the "Start Bulk Import" button to begin the process. The application will:

1. Parse and validate all channel IDs/URLs
2. Queue each channel for processing
3. Show real-time progress indicators for each channel
4. Provide summary statistics as channels are processed

### Step 5: Review Import Results

Once the import is complete, the application will display:

- Total number of channels successfully imported
- Channels that couldn't be imported (with reasons)
- Summary of collected data (total videos, comments, etc.)
- Link to view the imported channels in the analysis dashboard

## Technical Implementation

The bulk import feature is implemented in `src/ui/bulk_import.py` and leverages the background task system to avoid blocking the main UI thread during potentially lengthy import operations.

Key components include:

- Channel validation and resolution mechanism
- Parallel processing of multiple channels
- Progress tracking and reporting
- Error handling and recovery

## Best Practices

For optimal results with bulk imports:

1. **Start Small**: Test with 3-5 channels before attempting very large imports
2. **Consider API Limits**: Remember that each channel consumes YouTube API quota
3. **Use Reasonable Limits**: Setting sensible video and comment limits helps avoid quota exhaustion
4. **Monitor Progress**: The import may take time depending on the number of channels
5. **Check Results**: Review imported channels to ensure data quality
