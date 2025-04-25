import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import modules from src directory
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from src.models.youtube import YouTubeChannel, YouTubeVideo, VideoComment
from src.storage.local_storage import LocalStorage
from src.utils.helpers import debug_log, duration_to_seconds, clear_cache

# Setting page layout - this MUST be the first Streamlit command in the script
st.set_page_config(
    page_title = "YTDataHub",
    layout = "centered",
    page_icon = ":dna:",
    menu_items = {
    'About' : "Created by Jamie Meredith 'https://www.linkedin.com/in/jlmeredith/'"
    }
)

# Try to load environment variables from .env file
load_dotenv()

# Debug mode is stored in session state so it persists between page refreshes
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Initialize session state variables for data fetch options
if 'fetch_channel_data' not in st.session_state:
    st.session_state.fetch_channel_data = True
if 'fetch_videos' not in st.session_state:
    st.session_state.fetch_videos = True
if 'fetch_comments' not in st.session_state:
    st.session_state.fetch_comments = False
if 'max_videos' not in st.session_state:
    st.session_state.max_videos = 50
if 'api_cache' not in st.session_state:
    st.session_state.api_cache = {}

# Check if database credentials exist in environment variables
MONGODB_AVAILABLE = os.getenv('MONGO_URI') is not None
POSTGRES_AVAILABLE = all([
    os.getenv('PG_HOST') is not None,
    os.getenv('PG_USER') is not None,
    os.getenv('PG_PASSWORD') is not None,
    os.getenv('PG_DATABASE') is not None
])

# Set default storage mode based on available credentials
DEFAULT_TO_LOCAL_STORAGE = not (MONGODB_AVAILABLE or POSTGRES_AVAILABLE)

# Create a data directory for local storage if it doesn't exist
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# Path for SQLite database
SQLITE_DB_PATH = str(DATA_DIR / "youtube_data.db")

# Function to estimate YouTube API quota usage
def estimate_quota_usage():
    """Estimates YouTube API quota points that will be used with current settings"""
    # Base quota for channel info
    quota = 1 if st.session_state.fetch_channel_data else 0
    
    # Quota for video list
    # Each page of playlist items costs 1 unit, each page has 50 videos
    if st.session_state.fetch_videos:
        video_pages = (st.session_state.max_videos + 49) // 50  # Ceiling division
        quota += video_pages
        
        # Each batch of 50 videos costs 1 unit for details
        video_batches = (st.session_state.max_videos + 49) // 50
        quota += video_batches
        
        # Comments cost 1 unit per video
        if st.session_state.fetch_comments:
            quota += st.session_state.max_videos
    
    return quota

# Initialize the storage options
local_storage = LocalStorage(DATA_DIR)
sqlite_db = SQLiteDatabase(SQLITE_DB_PATH)

# Initialize the database on startup
sqlite_db.initialize_db()

def main():
    """Main application entry point"""
    st.title('YTDataHub')
    
    # Create tabs for the application
    tab1, tab2, tab3, tab4 = st.tabs(["Data Collection", "Data Storage", "Data Analysis", "Utilities"])
    
    with tab1:
        st.header("YouTube Data Collection")
        
        # API Key input
        api_key = os.getenv('YOUTUBE_API_KEY', '')
        user_api_key = st.text_input("Enter YouTube API Key:", value=api_key, type="password")
        
        if user_api_key:
            # Initialize the YouTube API client
            youtube_api = YouTubeAPI(user_api_key)
            
            # Channel ID input
            channel_id = st.text_input("Enter YouTube Channel ID:")
            
            # Data fetch options
            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state.fetch_channel_data = st.checkbox(
                    "Fetch Channel Data", 
                    value=st.session_state.fetch_channel_data
                )
            with col2:
                st.session_state.fetch_videos = st.checkbox(
                    "Fetch Videos", 
                    value=st.session_state.fetch_videos
                )
            with col3:
                st.session_state.fetch_comments = st.checkbox(
                    "Fetch Comments", 
                    value=st.session_state.fetch_comments
                )
                
            st.session_state.max_videos = st.slider(
                "Maximum Videos to Fetch", 
                min_value=1, 
                max_value=200, 
                value=st.session_state.max_videos
            )
            
            st.info(f"Estimated API quota cost: {estimate_quota_usage()} units")
            
            # Debug mode toggle
            st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
            
            # Data collection button
            if st.button("Collect Data", type="primary"):
                if channel_id:
                    with st.spinner("Collecting data from YouTube..."):
                        # Fetch channel data
                        if st.session_state.fetch_channel_data:
                            channel_info = youtube_api.get_channel_info(channel_id)
                            
                            if channel_info:
                                # Fetch videos if needed
                                if st.session_state.fetch_videos:
                                    channel_info = youtube_api.get_channel_videos(
                                        channel_info, 
                                        max_videos=st.session_state.max_videos
                                    )
                                    
                                    # Fetch comments if needed
                                    if st.session_state.fetch_comments and channel_info:
                                        channel_info = youtube_api.get_video_comments(
                                            channel_info,
                                            max_comments_per_video=10
                                        )
                                
                                # Display the collected data
                                if channel_info:
                                    st.success(f"Successfully collected data for channel: {channel_info.get('channel_name')}")
                                    
                                    with st.expander("Channel Details"):
                                        st.write({
                                            k: v for k, v in channel_info.items() 
                                            if k != 'video_id' and k != 'channel_description'
                                        })
                                        st.write("Channel Description:", channel_info.get('channel_description', ''))
                                    
                                    # Show video information in an expander
                                    videos = channel_info.get('video_id', [])
                                    with st.expander(f"Videos ({len(videos)})"):
                                        for i, video in enumerate(videos[:5]):  # Show only the first 5 videos
                                            st.write(f"Video {i+1}: {video.get('title')}")
                                        
                                        if len(videos) > 5:
                                            st.write(f"... and {len(videos) - 5} more videos")
                                    
                                    # Store the data in session state for the storage tab
                                    st.session_state.current_channel_data = channel_info
                                    st.info("Switch to the 'Data Storage' tab to save this data")
                        else:
                            st.error("Please check 'Fetch Channel Data' option to collect data.")
                else:
                    st.error("Please enter a YouTube Channel ID")
        else:
            st.error("Please enter a YouTube API Key")
    
    with tab2:
        st.header("Data Storage Options")
        
        # Check if we have data to store
        if 'current_channel_data' in st.session_state and st.session_state.current_channel_data:
            channel_data = st.session_state.current_channel_data
            st.success(f"Data ready for storage: {channel_data.get('channel_name')}")
            
            # Storage options
            storage_option = st.radio(
                "Select Storage Option:", 
                ["SQLite Database", "Local Storage (JSON)"] + 
                (["MongoDB"] if MONGODB_AVAILABLE else []) + 
                (["PostgreSQL"] if POSTGRES_AVAILABLE else [])
            )
            
            if st.button("Save Data", type="primary"):
                with st.spinner("Saving data..."):
                    if storage_option == "SQLite Database":
                        success = sqlite_db.store_channel_data(channel_data)
                        if success:
                            st.success("Data saved to SQLite database successfully!")
                        else:
                            st.error("Failed to save data to SQLite database")
                    
                    elif storage_option == "Local Storage (JSON)":
                        success = local_storage.store_channel_data(channel_data)
                        if success:
                            st.success("Data saved to local storage successfully!")
                        else:
                            st.error("Failed to save data to local storage")
                    
                    elif storage_option == "MongoDB" and MONGODB_AVAILABLE:
                        from src.database.mongodb import MongoDB
                        mongo_db = MongoDB(os.getenv('MONGO_URI'))
                        success = mongo_db.store_channel_data(channel_data)
                        if success:
                            st.success("Data saved to MongoDB successfully!")
                        else:
                            st.error("Failed to save data to MongoDB")
                    
                    elif storage_option == "PostgreSQL" and POSTGRES_AVAILABLE:
                        from src.database.postgres import PostgreSQL
                        pg_db = PostgreSQL(
                            host=os.getenv('PG_HOST'),
                            user=os.getenv('PG_USER'),
                            password=os.getenv('PG_PASSWORD'),
                            database=os.getenv('PG_DATABASE'),
                            port=os.getenv('PG_PORT', '5432')
                        )
                        success = pg_db.store_channel_data(channel_data)
                        if success:
                            st.success("Data saved to PostgreSQL successfully!")
                        else:
                            st.error("Failed to save data to PostgreSQL")
        else:
            st.info("No data available for storage. Collect data first from the 'Data Collection' tab.")
    
    with tab3:
        st.header("Data Analysis")
        
        # Source selection
        data_source = st.radio(
            "Select Data Source:",
            ["SQLite Database", "Local Storage (JSON)"] + 
            (["MongoDB"] if MONGODB_AVAILABLE else []) + 
            (["PostgreSQL"] if POSTGRES_AVAILABLE else [])
        )
        
        # Get the list of channels based on the selected source
        channels = []
        if data_source == "SQLite Database":
            channels = sqlite_db.get_channels_list()
        elif data_source == "Local Storage (JSON)":
            channels = local_storage.get_channels_list()
        elif data_source == "MongoDB" and MONGODB_AVAILABLE:
            from src.database.mongodb import MongoDB
            mongo_db = MongoDB(os.getenv('MONGO_URI'))
            channels = mongo_db.get_channels_list()
        elif data_source == "PostgreSQL" and POSTGRES_AVAILABLE:
            from src.database.postgres import PostgreSQL
            pg_db = PostgreSQL(
                host=os.getenv('PG_HOST'),
                user=os.getenv('PG_USER'),
                password=os.getenv('PG_PASSWORD'),
                database=os.getenv('PG_DATABASE'),
                port=os.getenv('PG_PORT', '5432')
            )
            channels = pg_db.get_channels_list()
        
        if channels:
            # Channel selection
            selected_channel = st.selectbox("Select Channel:", channels)
            
            if selected_channel:
                # Get channel data
                channel_data = None
                if data_source == "SQLite Database":
                    channel_data = sqlite_db.get_channel_data(selected_channel)
                elif data_source == "Local Storage (JSON)":
                    channel_data = local_storage.get_channel_data(selected_channel)
                elif data_source == "MongoDB" and MONGODB_AVAILABLE:
                    from src.database.mongodb import MongoDB
                    mongo_db = MongoDB(os.getenv('MONGO_URI'))
                    channel_data = mongo_db.get_channel_data(selected_channel)
                elif data_source == "PostgreSQL" and POSTGRES_AVAILABLE:
                    from src.database.postgres import PostgreSQL
                    pg_db = PostgreSQL(
                        host=os.getenv('PG_HOST'),
                        user=os.getenv('PG_USER'),
                        password=os.getenv('PG_PASSWORD'),
                        database=os.getenv('PG_DATABASE'),
                        port=os.getenv('PG_PORT', '5432')
                    )
                    channel_data = pg_db.get_channel_data(selected_channel)
                
                if channel_data:
                    # Analysis options
                    analysis_option = st.selectbox(
                        "Select Analysis:",
                        [
                            "Channel Statistics",
                            "Video Statistics",
                            "Top 10 Most Viewed Videos",
                            "Video Publication Over Time",
                            "Video Duration Analysis",
                            "Comment Analysis"
                        ]
                    )
                    
                    if analysis_option == "Channel Statistics":
                        # Display channel stats
                        st.subheader(f"Channel: {channel_data.get('channel_name')}")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Subscribers", f"{int(channel_data.get('subscribers', 0)):,}")
                        with col2:
                            st.metric("Total Views", f"{int(channel_data.get('views', 0)):,}")
                        with col3:
                            st.metric("Total Videos", channel_data.get('total_videos', 0))
                        
                        st.write("Channel Description:", channel_data.get('channel_description', ''))
                    
                    elif analysis_option == "Video Statistics":
                        # Display video stats in a table
                        videos = channel_data.get('video_id', [])
                        if videos:
                            # Create DataFrame
                            df = pd.DataFrame([
                                {
                                    'Title': v.get('title', ''),
                                    'Views': int(v.get('views', 0)),
                                    'Likes': int(v.get('likes', 0)),
                                    'Published': v.get('published_at', '').split('T')[0],
                                    'Duration': duration_to_seconds(v.get('duration', 'PT0S'))
                                }
                                for v in videos
                            ])
                            
                            # Display stats
                            st.write(f"Total Videos: {len(videos)}")
                            st.write(f"Total Views: {df['Views'].sum():,}")
                            st.write(f"Average Views per Video: {int(df['Views'].mean()):,}")
                            
                            # Show table
                            st.dataframe(df)
                        else:
                            st.info("No videos found for this channel")
                    
                    elif analysis_option == "Top 10 Most Viewed Videos":
                        # Show top 10 videos by view count
                        videos = channel_data.get('video_id', [])
                        if videos:
                            # Sort videos by views
                            sorted_videos = sorted(videos, key=lambda x: int(x.get('views', 0)), reverse=True)[:10]
                            
                            # Create DataFrame
                            df = pd.DataFrame([
                                {
                                    'Title': v.get('title', ''),
                                    'Views': int(v.get('views', 0)),
                                    'Likes': int(v.get('likes', 0)),
                                    'Published': v.get('published_at', '').split('T')[0]
                                }
                                for v in sorted_videos
                            ])
                            
                            # Display chart
                            st.bar_chart(df.set_index('Title')['Views'])
                            
                            # Show table
                            st.dataframe(df)
                        else:
                            st.info("No videos found for this channel")
                    
                    elif analysis_option == "Video Publication Over Time":
                        # Analyze video publication patterns
                        videos = channel_data.get('video_id', [])
                        if videos:
                            # Extract publication dates and create DataFrame
                            dates = [v.get('published_at', '').split('T')[0] for v in videos]
                            df = pd.DataFrame({'Publication Date': dates})
                            
                            # Convert to datetime
                            df['Publication Date'] = pd.to_datetime(df['Publication Date'])
                            
                            # Create date columns
                            df['Year'] = df['Publication Date'].dt.year
                            df['Month'] = df['Publication Date'].dt.month
                            df['Month-Year'] = df['Publication Date'].dt.strftime('%Y-%m')
                            
                            # Group by month
                            monthly_counts = df.groupby('Month-Year').size().reset_index(name='Count')
                            
                            # Display chart
                            st.line_chart(monthly_counts.set_index('Month-Year')['Count'])
                            
                            # Publication frequency stats
                            st.write("Publication Frequency:")
                            yearly_counts = df.groupby('Year').size().reset_index(name='Videos')
                            st.dataframe(yearly_counts)
                        else:
                            st.info("No videos found for this channel")
                    
                    elif analysis_option == "Video Duration Analysis":
                        # Analyze video durations
                        videos = channel_data.get('video_id', [])
                        if videos:
                            # Calculate durations in seconds
                            durations_sec = [duration_to_seconds(v.get('duration', 'PT0S')) for v in videos]
                            
                            # Create duration categories
                            duration_categories = []
                            for d in durations_sec:
                                if d < 60:
                                    category = "< 1 min"
                                elif d < 300:  # 5 minutes
                                    category = "1-5 mins"
                                elif d < 600:  # 10 minutes
                                    category = "5-10 mins"
                                elif d < 1200:  # 20 minutes
                                    category = "10-20 mins"
                                else:
                                    category = "> 20 mins"
                                duration_categories.append(category)
                            
                            # Create DataFrame
                            df = pd.DataFrame({
                                'Duration Category': duration_categories
                            })
                            
                            # Group by category
                            category_counts = df.groupby('Duration Category').size().reset_index(name='Count')
                            
                            # Display chart
                            st.bar_chart(category_counts.set_index('Duration Category')['Count'])
                            
                            # Display stats
                            avg_duration = sum(durations_sec) / len(durations_sec)
                            min_duration = min(durations_sec)
                            max_duration = max(durations_sec)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Average Duration", f"{int(avg_duration / 60)} mins {int(avg_duration % 60)} secs")
                            with col2:
                                st.metric("Shortest Video", f"{int(min_duration / 60)} mins {int(min_duration % 60)} secs")
                            with col3:
                                st.metric("Longest Video", f"{int(max_duration / 60)} mins {int(max_duration % 60)} secs")
                        else:
                            st.info("No videos found for this channel")
                    
                    elif analysis_option == "Comment Analysis":
                        # Analyze video comments
                        videos = channel_data.get('video_id', [])
                        if videos:
                            # Collect all comments
                            all_comments = []
                            for video in videos:
                                video_comments = video.get('comments', [])
                                for comment in video_comments:
                                    comment['video_title'] = video.get('title', '')
                                    all_comments.append(comment)
                            
                            if all_comments:
                                # Create DataFrame
                                df = pd.DataFrame([
                                    {
                                        'Video': c.get('video_title', ''),
                                        'Author': c.get('comment_authorc', ''),
                                        'Comment': c.get('comment_text', ''),
                                        'Date': c.get('comment_published_at', '').split('T')[0],
                                    }
                                    for c in all_comments
                                ])
                                
                                # Display stats
                                st.write(f"Total Comments: {len(all_comments)}")
                                
                                # Show sample comments
                                st.dataframe(df)
                            else:
                                st.info("No comments found for the videos in this channel")
                        else:
                            st.info("No videos found for this channel")
                else:
                    st.error(f"Failed to retrieve data for channel: {selected_channel}")
        else:
            st.info("No channels found in the selected data source. Please collect and store data first.")
    
    with tab4:
        st.header("Utilities")
        
        # Cache Management Section
        st.subheader("Cache Management")
        st.write("Clear different types of caches in the application.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            clear_api = st.checkbox("Clear API Cache", value=True, 
                                   help="Clears the YouTube API response cache")
        with col2:
            clear_python = st.checkbox("Clear Python Cache", value=True, 
                                      help="Removes __pycache__ directories")
        with col3:
            clear_db = st.checkbox("Clear DB Cache", value=True, 
                                  help="Clears database caches and optimizes storage")
        
        verbose_logging = st.checkbox("Verbose Logging", value=True,
                                     help="Show detailed information about what was cleared")
        
        if st.button("Clear Caches", type="primary"):
            with st.spinner("Clearing caches..."):
                # Use the clear_cache function from helpers.py
                results = clear_cache(
                    clear_api_cache=clear_api,
                    clear_python_cache=clear_python,
                    clear_db_cache=clear_db,
                    verbose=verbose_logging
                )
                
                # Show the results
                st.success(f"Cache clearing complete! Total items cleared: {results['total_items_cleared']}")
                
                if verbose_logging:
                    with st.expander("Cache Clearing Details"):
                        if results["api_cache_cleared"]:
                            st.write("✅ API cache cleared")
                        
                        if results["python_cache_cleared"]:
                            st.write("✅ Python cache directories removed:")
                            for cache_dir in results["python_cache_dirs_removed"]:
                                st.write(f"  - {cache_dir}")
                        
                        if results["db_cache_cleared"]:
                            st.write("✅ Database cache cleared")
        
        # Add separator
        st.markdown("---")
if __name__ == "__main__":
    main()

