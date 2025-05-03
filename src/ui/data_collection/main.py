"""
Main entry point for data collection UI.
Renders the data collection tab and orchestrates the UI components.
"""
import streamlit as st
import os
from src.utils.helpers import debug_log
from src.services.youtube_service import YouTubeService
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH

from .state_management import initialize_session_state, toggle_debug_mode
from .steps_ui import render_collection_steps
from .comparison_ui import render_comparison_view
from .channel_refresh_ui import channel_refresh_section
from .queue_ui import render_queue_status
from .debug_ui import render_debug_panel

def render_data_collection_tab():
    """
    Render the Data Collection tab UI.
    """
    st.header("YouTube Data Collection")

    # Add custom CSS to improve tab visibility and styling
    st.markdown("""
    <style>
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 5px 10px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        font-weight: 600;
        margin: 5px 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 99, 132, 0.7) !important;
        color: white !important.
    }
    
    /* Add styling for comparison tables */
    .comparison-table th {
        background-color: rgba(255, 255, 255, 0.1);
        font-weight: 600;
    }
    
    .comparison-table td.changed {
        background-color: rgba(255, 255, 0, 0.2);
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state variables if they don't exist
    initialize_session_state()
    
    # API Key input
    api_key = os.getenv('YOUTUBE_API_KEY', '')
    user_api_key = st.text_input("Enter YouTube API Key:", value=api_key, type="password")
    
    if user_api_key:
        # Initialize YouTube service
        youtube_service = YouTubeService(user_api_key)
        st.session_state.api_key = user_api_key
        
        # Store service initialization status for debug purposes
        st.session_state.api_initialized = True
        
        # MAIN UI RENDERING BASED ON VIEW STATE
        
        # Check if we're in comparison view mode
        if st.session_state.get('compare_data_view', False):
            # Render comparison view
            render_comparison_view(youtube_service)
            
            # Add a button to go back to the update channel tab
            if st.button("Back to Update Channel", key="back_to_update_from_comparison"):
                st.session_state.compare_data_view = False
                # Reset workflow step to start fresh next time
                if 'refresh_workflow_step' in st.session_state:
                    st.session_state.refresh_workflow_step = 1
                st.rerun()
        else:
            # Normal view with tabs
            tabs = st.tabs(["New Collection", "Update Channel", "Queue Status"])
            
            # Tab 1: New Collection
            with tabs[0]:
                if 'channel_info_temp' in st.session_state and st.session_state.channel_data_fetched:
                    # Render the collection steps if channel data is already fetched
                    render_collection_steps(st.session_state.channel_input, youtube_service)
                else:
                    # Channel input form
                    st.subheader("Channel Data Collection")
                    st.write("Enter a YouTube Channel URL or ID to start collecting data.")
                    
                    # Input form with better validation
                    with st.form("channel_form", clear_on_submit=False):
                        channel_input = st.text_input(
                            "Enter a YouTube Channel URL or ID:", 
                            help="For example: https://www.youtube.com/c/ChannelName or UCxxxxx"
                        )
                        
                        # Add option to fetch data from database if available
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Fetch Channel Data", type="primary"):
                                with st.spinner("Fetching channel data..."):
                                    try:
                                        # Check if this is a valid channel ID/URL
                                        is_valid, resolved_id = youtube_service.validate_and_resolve_channel_id(channel_input)
                                        
                                        if is_valid:
                                            # Check if we already have this channel in the database
                                            db = SQLiteDatabase(SQLITE_DB_PATH)
                                            existing_data = db.get_channel_data(resolved_id)
                                            
                                            if existing_data:
                                                # Ask if user wants to update existing data or start fresh
                                                st.session_state.collection_mode = "existing_channel"
                                                st.session_state.previous_channel_data = existing_data
                                                st.session_state.existing_channel_id = resolved_id
                                                
                                                st.info(f"Channel '{existing_data.get('channel_name', resolved_id)}' found in database. Using existing data as a starting point.")
                                                
                                                # Immediately collect channel data from API for comparison
                                                options = {
                                                    'fetch_channel_data': True, 
                                                    'fetch_videos': False,
                                                    'fetch_comments': False
                                                }
                                                
                                                channel_info = youtube_service.collect_channel_data(resolved_id, options)
                                                
                                                if channel_info:
                                                    st.session_state.channel_input = resolved_id
                                                    st.session_state.channel_info_temp = channel_info
                                                    st.session_state.current_channel_data = channel_info
                                                    st.session_state.channel_data_fetched = True
                                                    st.rerun()
                                                else:
                                                    st.error("Could not fetch latest channel data from YouTube API.")
                                            else:
                                                # This is a new channel, fetch from YouTube API
                                                st.session_state.collection_mode = "new_channel"
                                                options = {
                                                    'fetch_channel_data': True, 
                                                    'fetch_videos': False,
                                                    'fetch_comments': False
                                                }
                                                
                                                channel_info = youtube_service.collect_channel_data(channel_input, options)
                                                
                                                if channel_info:
                                                    st.session_state.channel_input = channel_input
                                                    st.session_state.channel_info_temp = channel_info
                                                    st.session_state.current_channel_data = channel_info
                                                    st.session_state.channel_data_fetched = True
                                                    st.rerun()
                                                else:
                                                    st.error("Could not fetch channel data from YouTube API.")
                                        else:
                                            st.error("Invalid YouTube channel URL or ID. Please check and try again.")
                                            
                                    except Exception as e:
                                        st.error(f"Error fetching channel data: {str(e)}")
                                        debug_log(f"Channel data fetch error: {str(e)}", e)
                        
                        with col2:
                            if st.form_submit_button("Clear Form", type="secondary"):
                                # Reset all session state related to channel data
                                if 'channel_info_temp' in st.session_state:
                                    del st.session_state.channel_info_temp
                                if 'current_channel_data' in st.session_state:
                                    del st.session_state.current_channel_data
                                st.session_state.channel_data_fetched = False
                                st.session_state.videos_fetched = False
                                st.session_state.comments_fetched = False
                                st.session_state.show_all_videos = False
                    
                    # Display helpful information about collection process
                    with st.expander("How Data Collection Works"):
                        st.write("""
                        ### Collection Process
                        
                        1. **Channel Data**: Basic channel information like name, description, and subscriber count.
                        2. **Videos**: Metadata for the channel's videos (titles, views, likes).
                        3. **Comments**: Comments on the videos (optional).
                        4. **Save Data**: Store collected data for analysis.
                        
                        ### YouTube API Quota
                        
                        Data collection uses YouTube API quota. Each day you have a limited number of requests.
                        - Channel data: 1 unit
                        - Videos list: 1 unit per 50 videos
                        - Comments: 1 unit per 100 comments
                        
                        Tip: Start with a small number of videos and comments to save quota.
                        """)
            
            # Tab 2: Update Channel (Refresh)
            with tabs[1]:
                # When entering the Update Channel tab, reset any leftover comparison view flag
                if not st.session_state.get('update_tab_initialized', False):
                    if 'compare_data_view' in st.session_state:
                        st.session_state.compare_data_view = False
                    st.session_state.update_tab_initialized = True
                
                channel_refresh_section(youtube_service)
            
            # Tab 3: Queue Status
            with tabs[2]:
                # When entering the Queue Status tab, reset the update tab initialization flag
                if st.session_state.get('update_tab_initialized', False):
                    st.session_state.update_tab_initialized = False
                
                render_queue_status()
        
        # Debug mode toggle at the bottom
        st.divider()
        # Use on_change callback to properly update logging when checkbox changes
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.get('debug_mode', False), on_change=toggle_debug_mode)
        
        # When debug mode is enabled, show debug information
        if st.session_state.debug_mode:
            render_debug_panel()
    else:
        st.error("Please enter a YouTube API Key")