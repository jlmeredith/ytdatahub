# YTDataHub User Interface

YTDataHub features a modern, intuitive interface designed for efficient YouTube data analysis. This document details the user interface components and their functionality.

## UI Overview

The YTDataHub interface is built with Streamlit, providing a clean, responsive design that works well on both desktop and mobile devices. The interface is organized around the core workflow of data collection, storage, and analysis.

## Main UI Components

### Channel Selector

The channel selector allows users to:

- View a list of all channels in the database
- Sort channels by various metrics (subscriber count, video count, etc.)
- Filter channels by name or other attributes
- Select channels for analysis or updating

### Navigation Sidebar

The sidebar provides access to the main functional areas of the application:

- **Data Collection**: For fetching new YouTube data
- **Data Storage**: For saving and managing collected data
- **Data Analysis**: For exploring and visualizing data
- **Utilities & Settings**: For configuring application behavior

### Data Collection Interface

The data collection interface guides users through a step-by-step process:

1. **Channel Information**: Enter a YouTube channel ID or URL and fetch basic channel data
2. **Video Collection**: Choose how many videos to retrieve from the selected channel
3. **Comment Collection**: Set parameters for comment retrieval
4. **Bulk Import**: Import multiple channels at once with shared parameters

Features include:

- **Clear Progress Indicators**: Visual feedback on the collection process
- **Delta Reporting**: Highlights changes when updating existing channels
- **Error Handling**: Clear messages for API errors or data access issues
- **Direct "Next Step" Navigation**: Guidance on proceeding through the workflow

### Data Storage Interface

The storage interface provides options for saving collected data:

- **Storage Backend Selection**: Choose between SQLite, JSON, MongoDB, or PostgreSQL
- **Dataset Naming**: Specify names for your datasets
- **Save Controls**: Buttons for initiating save operations
- **Confirmation Messages**: Clear feedback on successful storage

### Data Analysis Interface

The analysis interface is divided into four main sections:

#### 1. Dashboard

- Performance charts showing views, likes, comments over time
- Toggle controls for different metrics
- Trend line options for pattern identification

#### 2. Data Coverage

- Visual indicators showing the completeness of data collection
- Recommendations for improving data coverage
- Controls for initiating background data updates

#### 3. Videos

- Paginated list of videos with thumbnails and key metrics
- Sorting and filtering options
- Detailed information on each video

#### 4. Comments

- Comment browser with pagination support
- Sentiment visualization
- Word cloud for topic identification

### Utilities & Settings

The utilities section provides:

- **API Key Management**: Securely store and manage YouTube API keys
- **Debug Panel**: Diagnostic information for troubleshooting
- **Theme Selection**: Toggle between light and dark mode
- **Export Options**: Export data for use in external tools

## Utilities Tab: Clear Database Feature

The Utilities tab provides a powerful tool for development and testing: **Clear Database**.

- **Location:** Utilities tab → Database Management Tools → Clear Database
- **How it works:**
  - You must confirm your intent by checking a box and typing 'CLEAR ALL DATA'.
  - When you click **Clear Database**:
    - The app creates a backup of your current database file (with a timestamp).
    - All tables are dropped and the schema is recreated.
    - You can immediately start collecting/importing new data.
- **Warning:** This operation is destructive! Only use it in development or when you want to start with a clean slate. All data will be lost, but a backup is created for safety.
- **Alternative:** You can also reset the database from the command line using the CLI script (`scripts/clear_and_reset_db.py`).

## UI Design Principles

The YTDataHub interface follows several key design principles:

### 1. Progressive Disclosure

Information is presented in a progressive manner, starting with high-level overviews and allowing users to drill down into details as needed.

### 2. Contextual Guidance

The interface provides contextual help and guidance based on the user's current task and progress through the workflow.

### 3. Responsive Feedback

Users receive immediate feedback on their actions through visual indicators, progress bars, and confirmation messages.

### 4. Consistent Layout

Common UI elements maintain consistent positioning and behavior throughout the application.

### 5. Customizable Views

Users can adjust display preferences to match their workflow and information priorities.

## Mobile Responsiveness

The interface is designed to be responsive across different screen sizes:

- **Desktop**: Full-featured experience with multi-column layouts
- **Tablet**: Adjusted layouts with preserved functionality
- **Mobile**: Streamlined views with focused information display

## Accessibility Features

YTDataHub includes several accessibility features:

- **High Contrast Mode**: Enhanced visibility for users with visual impairments
- **Keyboard Navigation**: Full functionality accessible through keyboard shortcuts
- **Screen Reader Compatibility**: Semantic markup for assistive technologies
- **Configurable Text Size**: Adjustable font sizing for improved readability

## Future UI Enhancements

Planned improvements to the YTDataHub interface include:

- Customizable dashboards with drag-and-drop widgets
- Enhanced visualization options with additional chart types
- Improved notification system for long-running operations
- More advanced filtering and search capabilities

### Debug Panel: Playlist ID Logging Parity

- Both the **New Channel** and **Update Channel** workflows always log playlist ID actions:
  - When the playlist ID is fetched from the API
  - When it is stored in the database
  - When an error occurs (e.g., missing playlist ID, API failure)
- These logs are always visible in the UI debug panel for full transparency.
- This parity is enforced by automated tests and code review.
