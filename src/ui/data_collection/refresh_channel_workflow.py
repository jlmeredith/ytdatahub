"""
Channel refresh workflow implementation for data collection.
"""
import streamlit as st
import pandas as pd
import json
import sys
import logging
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow

# Set up logging
logger = logging.getLogger(__name__)
from .components.video_item import render_video_item
from .components.comprehensive_display import render_collapsible_field_explorer, render_channel_overview_card, render_detailed_change_dashboard
from .components.save_operation_manager import SaveOperationManager
from .channel_refresh.comparison import display_comparison_results, compare_data
from .utils.data_conversion import format_number, convert_db_to_api_format
from .utils.error_handling import handle_collection_error
from src.utils.video_processor import process_video_data
from src.utils.video_formatter import fix_missing_views
from src.database.channel_repository import ChannelRepository
from src.ui.data_collection.utils.delta_reporting import render_delta_report
from src.utils.data_collection.channel_normalizer import normalize_channel_data_for_save
import math
from datetime import datetime, timedelta
from src.ui.data_collection.new_channel_workflow import NewChannelWorkflow

class RefreshChannelWorkflow(BaseCollectionWorkflow):
    """
    Implementation of the workflow for refreshing data from an existing channel.
    This class follows the interface defined in BaseCollectionWorkflow.
    """
    
    def initialize_workflow(self, channel_id):
        """
        Initialize the refresh workflow with channel information.
        
        Args:
            channel_id: Channel ID to refresh
        """
        # For step 1 (refresh-specific), the initialization is done in the channel_refresh_section
        # Step 1 is unique to refresh workflow where user selects a channel from the database
        
        # Initialize workflow variables for steps 2-4 (which match steps 1-3 in the base workflow)
        if 'refresh_workflow_step' not in st.session_state:
            st.session_state['refresh_workflow_step'] = 1  # Start at selection step
        
        if 'channel_input' not in st.session_state and channel_id:
            st.session_state['channel_input'] = channel_id
    
    def render_step_1_select_channel(self):
        """Render step 1 (refresh-specific): Select channel to refresh."""
        st.subheader("Step 1: Select a Channel to Refresh")
        
        # Get list of channels from service
        channels = self.youtube_service.get_channels_list("sqlite")
        
        # Check if channels list is empty and display warning if so
        if not channels:
            st.warning("No channels found in the database.")
            return
            
        channel_options = [f"{channel['channel_name']} ({channel['channel_id']})" for channel in channels]
        
        # Add a "None" option at the beginning of the list
        channel_options.insert(0, "Select a channel...")
        
        # Create the select box
        selected_channel = st.selectbox(
            "Choose a channel to refresh:",
            channel_options,
            index=0
        )
        
        # Extract channel_id from selection (if a valid selection was made)
        channel_id = None
        if selected_channel and selected_channel != "Select a channel...":
            channel_id = selected_channel.split('(')[-1].strip(')')
        
        # Button to initiate comparison
        if st.button("Compare with YouTube API", key="refresh_compare_api_btn"):
            if channel_id:
                # Set up session state
                st.session_state['channel_input'] = channel_id
                st.session_state['api_initialized'] = True
                st.session_state['api_client_initialized'] = True
                with st.spinner("Retrieving data for comparison..."):
                    logger.info(f"Getting comparison data for channel: {channel_id}")
                    st.session_state['comparison_attempted'] = True
                    try:
                        # Enhanced comprehensive comparison options to track all changes
                        options = {
                            'fetch_channel_data': True,
                            'fetch_videos': False,
                            'fetch_comments': False,
                            'max_videos': 0,
                            'max_comments_per_video': 0,
                            'comparison_level': 'comprehensive',  # Always use comprehensive for complete analysis
                            'track_keywords': [
                                'copyright', 'disclaimer', 'new owner', 'ownership', 'management', 
                                'rights', 'policy', 'terms', 'agreement', 'takeover', 'acquired',
                                'shutdown', 'closing', 'terminated', 'notice', 'warning'
                            ],
                            'alert_on_significant_changes': True,
                            'persist_change_history': True,
                            'compare_all_fields': True  # New option to ensure all fields are compared
                        }
                        comparison_data = self.youtube_service.update_channel_data(channel_id, options, interactive=False, existing_data=None)
                        st.session_state['last_api_call'] = datetime.now().isoformat()
                        if comparison_data and isinstance(comparison_data, dict):
                            st.session_state['db_data'] = comparison_data.get('db_data', {})
                            api_data_raw = comparison_data.get('api_data', {})
                            # --- NEW: Extract and validate fields for UI parity ---
                            api_data_ui = self.extract_api_data_from_delta(api_data_raw)
                            if api_data_ui:
                                st.session_state['api_data'] = api_data_ui
                            else:
                                st.session_state['api_data'] = {}
                            debug_log_with_time(f"API data after extraction: {st.session_state['api_data']}")
                            if st.session_state['db_data'] is None:
                                st.session_state['db_data'] = {}
                            # Promote delta info from api_data if present
                            if 'delta' in api_data_raw:
                                st.session_state['delta'] = api_data_raw['delta']
                            elif 'delta' in comparison_data:
                                st.session_state['delta'] = comparison_data['delta']
                            if 'delta' not in st.session_state['api_data'] and 'delta' in st.session_state:
                                st.session_state['api_data']['delta'] = st.session_state['delta']
                            if 'channel' in st.session_state['api_data']:
                                if 'delta' in st.session_state['api_data']:
                                    st.session_state['api_data']['channel']['delta'] = st.session_state['api_data']['delta']
                                elif 'delta' in st.session_state:
                                    st.session_state['api_data']['channel']['delta'] = st.session_state['delta']
                            # Store debug logs and response data if present
                            if 'debug_logs' in comparison_data:
                                st.session_state['debug_logs'] = comparison_data['debug_logs']
                            if 'response_data' in comparison_data:
                                st.session_state['response_data'] = comparison_data['response_data']
                            if (len(st.session_state['db_data']) == 0 and len(st.session_state['api_data']) == 0):
                                st.error("No data could be retrieved from either the database or YouTube API.")
                                return
                            st.session_state['existing_channel_id'] = channel_id
                            st.session_state['collection_mode'] = "refresh_channel"
                            st.session_state['refresh_workflow_step'] = 2
                            st.rerun()
                        else:
                            st.session_state['db_data'] = {}
                            st.session_state['api_data'] = {}
                            st.error("Failed to retrieve channel data for comparison. Please try again.")
                    except Exception as e:
                        handle_collection_error(e, "retrieving channel data for comparison")
            else:
                st.warning("Please select a channel first.")
    
    def render_step_1_channel_data(self):
        """Render channel data in a clean, user-friendly format, with full parity to new workflow."""
        st.subheader("Step 2: Review and Update Channel Data")
        self.show_progress_indicator(2)
        channel_id = st.session_state.get('existing_channel_id')
        db_data_raw = st.session_state.get('db_data', {})
        api_data_raw = self.extract_api_data_from_delta(st.session_state.get('api_data', {}))
        api_data = self.convert_api_to_ui_format(api_data_raw)
        debug_log_with_time(f"[UI] Checking api_data for channel_id={channel_id}: {api_data}")
        raw_info = api_data.get('raw_channel_info')
        debug_log_with_time(f"[UI] raw_channel_info type: {type(raw_info)}, value: {raw_info}")
        db_data = convert_db_to_api_format(db_data_raw) if db_data_raw else {}
        
        # Display error if no API data is found
        if not raw_info or not isinstance(raw_info, dict):
            st.error("No API data found for this channel. Error: No API data returned. Please check your API key, quota, or network connection.")
            st.button("Retry API Fetch", on_click=self.retry_api_fetch)
            st.button("Back to Channel Selection", on_click=self.go_to_channel_selection)
            return
        
        # Display channel information in a more organized way
        channel_name = api_data.get('channel_name', db_data.get('channel_name', 'Unknown Channel'))
        st.subheader(f"Channel: {channel_name}")
        st.caption(f"Channel ID: {channel_id}")
        
        # Show comparison table with clear headers and diagnostic info
        st.markdown("### 📊 Database vs API Comparison")
        
        # Add diagnostic information about data freshness
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📦 Current Database Values**")
            if db_data_raw and 'updated_at' in db_data_raw:
                last_updated = db_data_raw.get('updated_at', 'Unknown')
                st.caption(f"Last updated: {last_updated}")
            else:
                st.caption("⚠️ No timestamp available - data may be stale")
            render_channel_overview_card(db_data)
            
        with col2:
            st.markdown("**🔄 Latest API Values**")
            api_fetch_time = st.session_state.get('last_api_call', 'Unknown time')
            st.caption(f"Fetched: {api_fetch_time}")
            render_channel_overview_card(api_data)
        
        # Add data freshness analysis
        if db_data_raw and 'updated_at' in db_data_raw:
            try:
                last_updated_str = db_data_raw.get('updated_at', '')
                if last_updated_str:
                    last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                    current_time = datetime.now()
                    time_diff = current_time - last_updated.replace(tzinfo=None)
                    
                    if time_diff.total_seconds() < 3600:  # Less than 1 hour
                        st.success(f"✅ Database data is fresh (updated {time_diff.total_seconds()/60:.0f} minutes ago)")
                    elif time_diff.total_seconds() < 86400:  # Less than 1 day
                        st.warning(f"⚠️ Database data is {time_diff.total_seconds()/3600:.1f} hours old")
                    else:
                        st.error(f"❌ Database data is {time_diff.days} days old - changes expected")
            except Exception as e:
                st.warning("Could not parse database timestamp")
        else:
            st.warning("⚠️ No database timestamp available - unable to assess data freshness")
        
        # Display delta report with clear header and enhanced diagnostics
        st.markdown("### 🔍 Changes Analysis")
        
        # Add toggle for debug mode
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("💡 **Tip:** Enable debug mode below to see detailed diagnostic information about data comparison.")
        with col2:
            debug_mode = st.toggle("Debug Mode", value=st.session_state.get('debug_mode', False), key="delta_debug_toggle")
            st.session_state['debug_mode'] = debug_mode
        
        # Enhanced delta reporting with better context
        st.markdown("#### Database vs API Data Comparison")
        st.caption(f"Comparing current database values with fresh API data retrieved at {st.session_state.get('last_api_call', 'Unknown time')}")
        
        from src.ui.data_collection.utils.delta_reporting import render_delta_report
        render_delta_report(db_data, api_data, data_type="channel")
        
        # --- Store raw data/delta in debug state ---
        if 'debug_raw_data' not in st.session_state:
            st.session_state['debug_raw_data'] = {}
        if 'debug_delta_data' not in st.session_state:
            st.session_state['debug_delta_data'] = {}
        st.session_state['debug_raw_data']['channel'] = {
            'db': db_data_raw,
            'api': api_data_raw
        }
        st.session_state['debug_delta_data']['channel'] = {
            'delta': api_data.get('delta')
        }
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Channel Data", key="refresh_save_channel_btn"):
                try:
                    # Normalize the channel data before saving to ensure consistent format
                    normalized_channel_data = normalize_channel_data_for_save(api_data, "refresh_channel")
                    
                    save_manager = SaveOperationManager()
                    success = save_manager.perform_save_operation(
                        youtube_service=self.youtube_service,
                        api_data=normalized_channel_data,
                        total_videos=0,
                        total_comments=0
                    )
                    debug_log_with_time(f"[PARITY] Save operation for channel_id={channel_id} success={success}")
                    if success:
                        st.session_state['channel_data_saved'] = True
                        from src.config import SQLITE_DB_PATH
                        from src.database.channel_repository import ChannelRepository
                        db_repo = ChannelRepository(SQLITE_DB_PATH)
                        db_record = db_repo.get_channel_data(normalized_channel_data.get('channel_id'))
                        db_api_format = convert_db_to_api_format(db_record) if db_record else {}
                        st.session_state['db_data'] = db_record
                        debug_log_with_time(f"[PARITY] Reloaded DB data after save for channel_id={channel_id}: {bool(db_record)}")
                        # Store post-save raw data in debug state
                        st.session_state['debug_raw_data']['channel_post_save'] = {
                            'db': db_record,
                            'api': normalized_channel_data.get('raw_channel_info')
                        }
                        st.session_state['debug_delta_data']['channel_post_save'] = {
                            'delta': normalized_channel_data.get('delta')
                        }
                        
                        # Display clear success confirmation with saved data details
                        st.success(f"Channel data for '{normalized_channel_data.get('channel_name')}' saved successfully!")
                        
                        # Show a summary of what was saved
                        st.info("**Data saved to database:**")
                        saved_summary = {
                            "Channel Name": normalized_channel_data.get('channel_name'),
                            "Channel ID": normalized_channel_data.get('channel_id'),
                            "Subscribers": format_number(normalized_channel_data.get('subscribers', 0)),
                            "Views": format_number(normalized_channel_data.get('views', 0)),
                            "Videos": format_number(normalized_channel_data.get('total_videos', 0)),
                            "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        for key, value in saved_summary.items():
                            st.write(f"**{key:}** {value}")
                        
                        if st.session_state.get('debug_mode', False):
                            st.markdown("---")
                            st.subheader(":inbox_tray: Database Record (Post-Save)")
                            st.json(db_api_format)
                            st.subheader(":satellite: API Response (Just Saved)")
                            st.json(normalized_channel_data.get('raw_channel_info'))
                            st.subheader(":mag: Delta Report (API vs DB, Raw)")
                            st.json(normalized_channel_data.get('delta'))
                except Exception as e:
                    st.error(f"Error saving data: {str(e)}")
                    debug_log_with_time(f"[PARITY] Error saving channel data: {str(e)}")
        with col2:
            if st.button("Continue to Playlist Review", key="refresh_continue_to_playlist_btn"):
                st.session_state['collection_step'] = 2
                st.session_state['refresh_workflow_step'] = 3
                debug_log_with_time("[PARITY] User continued to playlist review.")
                st.rerun()
    
    def render_step_2_playlist_review(self):
        """Render playlist review step in a user-friendly way, with full parity to new workflow."""
        st.subheader("Step 3: Review and Update Playlist Data")
        self.show_progress_indicator(3)
        channel_id = st.session_state.get('existing_channel_id')
        from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format
        db_data_raw = st.session_state.get('db_data', {})
        api_data_raw = st.session_state.get('api_data', {})
        api_data = self.convert_api_to_ui_format(self.extract_api_data_from_delta(api_data_raw))
        db_data = convert_db_to_api_format(db_data_raw) if db_data_raw else {}
        debug_log_with_time(f"[PARITY] Checking data for channel_id={channel_id}: {db_data}")
        
        # Get playlist data from API and DB
        playlist_api = api_data.get('uploads_playlist', {})
        if isinstance(playlist_api, str):
            import json
            try:
                playlist_api = json.loads(playlist_api)
            except:
                playlist_api = {}
        
        # Get playlist data from DB
        db_playlist = db_data.get('uploads_playlist', {})
        if isinstance(db_playlist, str):
            import json
            try:
                db_playlist = json.loads(db_playlist)
            except:
                db_playlist = {}
                
        # If we have playlist data, show summary
        if playlist_api and 'snippet' in playlist_api:
            snippet = playlist_api['snippet']
            st.success(f"✅ Playlist found: **{snippet.get('title', 'Untitled Playlist')}**")
            
            # Show basic playlist info
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📅 **Published:** {snippet.get('publishedAt', 'Unknown')[:10]}")
                st.write(f"📝 **Description:** {snippet.get('description', 'No description')[:100]}...")
            with col2:
                video_count = playlist_api.get('contentDetails', {}).get('itemCount', 'Unknown')
                st.write(f"🎬 **Videos in playlist:** {video_count}")
                privacy_status = playlist_api.get('status', {}).get('privacyStatus', 'Unknown')
                st.write(f"🔒 **Privacy:** {privacy_status.title()}")
        else:
            # Playlist data not found, create a basic playlist record
            playlist_id = api_data.get('playlist_id') or api_data.get('uploads_playlist_id')
            if playlist_id:
                st.warning(f"⚠️ No detailed playlist data found. Using basic information to create playlist record.")
                
                # Create basic playlist data
                playlist_api = {
                    'kind': 'youtube#playlist',
                    'etag': '',
                    'id': playlist_id,
                    'playlist_id': playlist_id,
                    'channel_id': channel_id,
                    'type': 'uploads',
                    'title': f"Uploads from {api_data.get('channel_name', 'Unknown Channel')}",
                    'description': f"Uploaded videos from {api_data.get('channel_name', 'Unknown Channel')}",
                    'snippet': {
                        'publishedAt': api_data.get('snippet_publishedAt', ''),
                        'channelId': channel_id,
                        'title': f"Uploads from {api_data.get('channel_name', 'Unknown Channel')}",
                        'description': f"Uploaded videos from {api_data.get('channel_name', 'Unknown Channel')}",
                        'channelTitle': api_data.get('channel_name', 'Unknown Channel'),
                    },
                    'status': {
                        'privacyStatus': 'public'
                    },
                    'contentDetails': {
                        'itemCount': api_data.get('total_videos', 0)
                    }
                }
                st.info("Basic playlist information created from channel data.")
            else:
                st.error("❌ No playlist ID found. Cannot create playlist record.")
        
        db_playlist_api = db_playlist if isinstance(db_playlist, dict) else {}
        debug_log_with_time(f"[PARITY] DB playlist data: {db_playlist_api}")
        
        # Store raw/delta in debug state
        if 'debug_raw_data' not in st.session_state:
            st.session_state['debug_raw_data'] = {}
        if 'debug_delta_data' not in st.session_state:
            st.session_state['debug_delta_data'] = {}
        st.session_state['debug_raw_data']['playlist'] = {
            'db': db_playlist_api,
            'api': playlist_api
        }
        st.session_state['debug_delta_data']['playlist'] = {
            'delta': None  # If you have a delta, store it here
        }
        
        # Display playlist comparison
        st.subheader("Playlist Comparison")
        
        # Only show raw/delta in UI if debug_mode is enabled
        if st.session_state.get('debug_mode', False):
            st.markdown("---")
            st.subheader("Playlist DB Record (Raw)")
            st.json(db_playlist_api)
            st.subheader("Playlist API Response (Raw)")
            st.json(playlist_api)
            st.subheader("Playlist Delta Report (Raw)")
            st.json(None)  # Replace with actual delta if available
        
        # Show user-friendly delta report
        st.subheader("Playlist Changes")
        render_delta_report(db_playlist_api, playlist_api, data_type="playlist")
        
        if 'playlist_saved' not in st.session_state:
            st.session_state['playlist_saved'] = False
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save Playlist Data", key="save_playlist_data_btn_refresh", disabled=st.session_state['playlist_saved']):
                try:
                    playlist_save_success = self.youtube_service.save_playlist_data(playlist_api)
                    if playlist_save_success:
                        st.session_state['playlist_saved'] = True
                        st.success("✅ Playlist data saved successfully!")
                    else:
                        st.error("❌ Failed to save playlist data.")
                except Exception as e:
                    st.error(f"❌ Error saving playlist: {str(e)}")
        with col3:
            if st.button("▶️ Continue to Videos", key="continue_to_videos_btn2_refresh", disabled=not st.session_state['playlist_saved']):
                st.session_state['collection_step'] = 3
                st.session_state['refresh_workflow_step'] = 4
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 2: Video collection (delegates to step 4 in refresh workflow)."""
        # In the refresh workflow, video collection is step 4, not step 2
        # This method exists to satisfy the abstract base class requirement
        return self.render_step_4_video_collection()
    
    def render_step_4_video_collection(self):
        """Render video collection step in a user-friendly way."""
        st.subheader("Step 4: Review and Update Video Data")
        self.show_progress_indicator(4)
        
        channel_id = st.session_state.get('existing_channel_id')
        
        # Get API and DB data
        from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format
        db_data_raw = st.session_state.get('db_data', {})
        api_data_raw = st.session_state.get('api_data', {})
        api_data = self.convert_api_to_ui_format(self.extract_api_data_from_delta(api_data_raw))
        db_data = convert_db_to_api_format(db_data_raw) if db_data_raw else {}
        
        # Extract video information
        db_videos_raw = db_data.get('video_id', []) if db_data else []
        db_videos = {v.get('video_id'): v for v in db_videos_raw if v.get('video_id')}
        logger.info(f"[WORKFLOW] DB videos found: {len(db_videos)}")
        
        # Make sure API data has a videos array
        if 'video_id' not in api_data or not api_data['video_id']:
            api_data['video_id'] = []
            logger.info(f"[WORKFLOW] No videos found in API data, created empty list")
            
        api_videos = api_data.get('video_id', [])
        api_video_count = len(api_videos)
        logger.info(f"[WORKFLOW] API videos found: {api_video_count}")
        
        # Display summary information
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Videos in Database", len(db_videos))
        with col2:
            st.metric("Videos from API", api_video_count)
            
        # Initialize session state for video actions
        if 'videos_saved' not in st.session_state:
            st.session_state['videos_saved'] = False
            
        # If we have API videos, show the option to save them
        if api_video_count > 0:
            # Show sample of videos
            st.write("**Sample Videos from API:**")
            max_display = min(5, api_video_count)
            for i in range(max_display):
                if i < len(api_videos):
                    video = api_videos[i]
                    st.write(f"- {video.get('title', 'Untitled')} ({video.get('views', 0)} views)")
                    
            # Action buttons for videos
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Save Video Data", key="save_videos_btn", 
                           disabled=st.session_state['videos_saved']):
                    try:
                        # Ensure we have all necessary fields for saving
                        api_data_with_videos = api_data.copy()
                        # Make sure channel_id is set in the data
                        if 'channel_id' not in api_data_with_videos:
                            api_data_with_videos['channel_id'] = channel_id
                        
                        # Normalize the data before saving to ensure consistent format
                        normalized_data = normalize_channel_data_for_save(api_data_with_videos, "refresh_channel_videos")
                            
                        save_success = self.youtube_service.save_channel_data(normalized_data, 'SQLite Database')
                        if save_success:
                            st.session_state['videos_saved'] = True
                            st.success(f"✅ Saved {api_video_count} videos successfully!")
                        else:
                            st.error("❌ Failed to save video data.")
                    except Exception as e:
                        st.error(f"❌ Error saving videos: {str(e)}")
            with col3:
                if st.button("▶️ Continue to Comments", key="continue_to_comments_btn", 
                           disabled=not st.session_state['videos_saved']):
                    st.session_state['collection_step'] = 3
                    st.session_state['refresh_workflow_step'] = 5
                    st.rerun()
        else:
            st.warning("⚠️ No videos found from the API.")
            # Allow continuing even without videos
            if st.button("▶️ Continue to Comments", key="continue_to_comments_btn_empty"):
                st.session_state['collection_step'] = 3
                st.session_state['refresh_workflow_step'] = 5
                st.rerun()
    
    def render_step_3_comment_collection(self):
        """Render step 3: Comment collection (delegates to step 5 in refresh workflow)."""
        # In the refresh workflow, comment collection is step 5, not step 3
        # This method exists to satisfy the abstract base class requirement
        return self.render_step_5_comment_collection()
    
    def render_step_5_comment_collection(self):
        """Render step 5 (in refresh workflow): Collect and display comment data."""
        st.subheader("Step 5: Comment Collection")
        self.show_progress_indicator(5)
        
        channel_id = st.session_state.get('existing_channel_id')
        
        # Get API and DB data
        from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format
        db_data_raw = st.session_state.get('db_data', {})
        api_data_raw = st.session_state.get('api_data', {})
        api_data = self.convert_api_to_ui_format(self.extract_api_data_from_delta(api_data_raw))
        db_data = convert_db_to_api_format(db_data_raw) if db_data_raw else {}
        
        # Check if we have videos to collect comments for
        api_videos = api_data.get('video_id', [])
        if not api_videos:
            st.warning("⚠️ No videos found to collect comments for.")
            if st.button("▶️ Continue to Summary", key="skip_to_summary_btn"):
                st.session_state['collection_step'] = 5
                st.session_state['refresh_workflow_step'] = 6
                st.rerun()
            return
            
        # Extract video information for display
        video_count = len(api_videos)
        videos_with_comments = 0
        total_comments = 0
        
        # Count videos with comments and total comments
        for video in api_videos:
            if 'comments' in video and video['comments']:
                videos_with_comments += 1
                total_comments += len(video['comments'])
                
        # Display summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Videos", video_count)
        with col2:
            st.metric("Videos with Comments", videos_with_comments)
        with col3:
            st.metric("Total Comments", total_comments)
            
        # Initialize session state for comment actions
        if 'comments_saved' not in st.session_state:
            st.session_state['comments_saved'] = False
            
        # Strategic Comment Collection Options
        st.markdown("### 🎯 Comment Collection Strategy")
        st.markdown("""
        **Choose your strategy based on your analysis goals:**
        - Each video costs 1 API unit regardless of comment count
        - Maximize value by choosing the right strategy for your needs
        """)
        
        # Strategy selection
        strategy_options = {
            "Speed Mode": {
                "description": "🚀 **Fast sampling** - Get quick insights from minimal comments",
                "comments": 5,
                "replies": 0,
                "benefits": "• Fastest collection (3-5x faster)\n• Minimal API usage\n• Good for sentiment overview",
                "best_for": "Quick content sampling, basic sentiment analysis"
            },
            "Balanced Mode": {
                "description": "⚖️ **Balanced approach** - Good mix of speed and data richness", 
                "comments": 20,
                "replies": 5,
                "benefits": "• Moderate collection time\n• Comprehensive conversation context\n• Good engagement insights",
                "best_for": "General analysis, audience engagement studies"
            },
            "Comprehensive Mode": {
                "description": "📊 **Maximum data** - Extract maximum value from each API call",
                "comments": 50,
                "replies": 10,
                "benefits": "• Complete conversation threads\n• Deep engagement analysis\n• Maximum ROI on API quota",
                "best_for": "In-depth research, complete conversation analysis"
            },
            "Custom": {
                "description": "⚙️ **Custom settings** - Fine-tune parameters for your specific needs",
                "comments": 20,
                "replies": 5,
                "benefits": "• Full control over parameters\n• Tailored to specific use cases\n• Flexible configuration",
                "best_for": "Specific research requirements, advanced users"
            }
        }
        
        # Strategy selection radio buttons
        selected_strategy = st.radio(
            "Select your comment collection strategy:",
            options=list(strategy_options.keys()),
            format_func=lambda x: strategy_options[x]["description"],
            help="Each strategy optimizes for different goals and API usage patterns"
        )
        
        # Show strategy details
        strategy = strategy_options[selected_strategy]
        
        # Display strategy information in columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**✅ Benefits:**\n{strategy['benefits']}")
        
        with col2:
            st.markdown(f"**🎯 Best for:** {strategy['best_for']}")
        
        # Strategy-specific controls
        if selected_strategy == "Custom":
            st.markdown("#### Custom Parameters")
            col1, col2 = st.columns(2)
            
            with col1:
                max_comments_per_video = st.slider(
                    "Maximum comments per video:", 
                    min_value=0, 
                    max_value=100, 
                    value=20,
                    step=5
                )
            
            with col2:
                max_replies_per_comment = st.slider(
                    "Replies per comment:",
                    min_value=0,
                    max_value=50,
                    value=5,
                    step=1
                )
        else:
            # Use predefined strategy values
            max_comments_per_video = strategy["comments"]
            max_replies_per_comment = strategy["replies"]
            
            # Show the selected values
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Comments per Video", max_comments_per_video)
            with col2:
                st.metric("Replies per Comment", max_replies_per_comment)
        
        # Additional options
        comment_sort_order = st.selectbox(
            "Comment sort order:",
            options=["relevance", "time"],
            index=0,
            help="Order in which comments are retrieved from YouTube"
        )
        
        include_replies = st.checkbox(
            "Include comment replies", 
            value=max_replies_per_comment > 0,
            disabled=max_replies_per_comment == 0,
            help="Automatically set based on your strategy selection"
        )
        
        # API efficiency information
        estimated_time = video_count * 0.3  # Optimized timing
        with st.expander("📊 Collection Efficiency Details"):
            st.markdown(f"""
            **API Constraints & Optimization:**
            - YouTube API requires 1 call per video (cannot be batched)
            - Total API calls needed: **{video_count}** (1 per video)
            - Estimated collection time: **~{estimated_time:.1f} seconds** (optimized)
            - Comments per video: **{max_comments_per_video}** (maximum value per API unit)
            - Replies per comment: **{max_replies_per_comment}**
            
            **Why we've optimized this:**
            - RAPID MODE processing with 0.3s delays (maximum safe speed)
            - Pre-filtering to skip videos with disabled comments
            - Exact fetch counts to eliminate over-fetching waste
            """)
        
        # Create options dictionary
        options = {
            'fetch_channel_data': False,
            'fetch_videos': False,
            'fetch_comments': True,
            'max_comments_per_video': max_comments_per_video,
            'max_top_level_comments': max_comments_per_video,
            'max_replies_per_comment': max_replies_per_comment,
            'comment_sort_order': comment_sort_order,
            'include_replies': include_replies
        }
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"🚀 Start Comment Collection ({selected_strategy})", key="collect_comments_btn", 
                       disabled=st.session_state['comments_saved']):
                try:
                    with st.spinner(f"Collecting comments using {selected_strategy}..."):
                        # Need to collect comments for each video
                        updated_api_data = api_data.copy()
                        
                        # For each video, fetch comments
                        for i, video in enumerate(updated_api_data.get('video_id', [])):
                            video_id = video.get('video_id')
                            if not video_id:
                                continue
                                
                            # Show progress
                            st.progress((i + 1) / video_count)
                            
                            # Fetch comments for this video
                            video_with_comments = self.youtube_service.collect_video_comments(
                                video_id, 
                                max_comments_per_video, 
                                comment_sort_order, 
                                include_replies
                            )
                            
                            if video_with_comments and 'comments' in video_with_comments:
                                video['comments'] = video_with_comments['comments']
                        
                        # Update the session state with new data
                        st.session_state['api_data'] = updated_api_data
                        
                        # Recount videos with comments and total comments
                        videos_with_comments = 0
                        total_comments = 0
                        for video in updated_api_data.get('video_id', []):
                            if 'comments' in video and video['comments']:
                                videos_with_comments += 1
                                total_comments += len(video['comments'])
                                
                        st.success(f"✅ Collected {total_comments} comments across {videos_with_comments} videos!")
                except Exception as e:
                    st.error(f"❌ Error collecting comments: {str(e)}")
                    
        with col2:
            if st.button("💾 Save Comments", key="save_comments_btn", 
                       disabled=st.session_state['comments_saved'] or videos_with_comments == 0):
                try:
                    # Save the updated video data with comments
                    api_data_to_save = api_data.copy()
                    if 'channel_id' not in api_data_to_save:
                        api_data_to_save['channel_id'] = channel_id
                        
                    save_success = self.youtube_service.save_channel_data(api_data_to_save, 'SQLite Database')
                    if save_success:
                        st.session_state['comments_saved'] = True
                        st.success(f"✅ Saved {total_comments} comments successfully!")
                    else:
                        st.error("❌ Failed to save comments.")
                except Exception as e:
                    st.error(f"❌ Error saving comments: {str(e)}")
                    
        with col3:
            if st.button("▶️ Continue to Summary", key="continue_to_summary_btn", 
                       disabled=total_comments > 0 and not st.session_state['comments_saved']):
                st.session_state['collection_step'] = 5
                st.session_state['refresh_workflow_step'] = 6
                st.rerun()
    
    def save_data(self):
        """Save collected data to the database."""
        # Get API data from session state
        api_data = st.session_state.get('api_data', {})
        
        if not api_data:
            st.error("No data to save.")
            return
            
        try:
            # Make sure we have a channel ID
            if not api_data.get('channel_id'):
                channel_id = st.session_state.get('existing_channel_id')
                if channel_id:
                    api_data['channel_id'] = channel_id
                else:
                    st.error("Missing channel ID.")
                    return
            
            # Update the video and comment data
            videos_data = st.session_state.get('videos_data', [])
            if videos_data:
                api_data['video_id'] = videos_data
            
            # Normalize the data before saving to ensure consistent format
            normalized_data = normalize_channel_data_for_save(api_data, "refresh_channel_final")
            
            # Check if youtube_service is properly initialized
            if not hasattr(self.youtube_service, 'save_channel_data'):
                st.error("YouTube service is not properly initialized.")
                logger.error(f"YouTube service missing save_channel_data method: {type(self.youtube_service)}")
                return
            
            # Calculate video and comment counts for the save operation manager
            total_videos = len(videos_data) if videos_data else 0
            total_comments = sum(len(video.get('comments', [])) for video in videos_data) if videos_data else 0
            
            # Use the SaveOperationManager to handle save operations with feedback
            save_manager = SaveOperationManager()
            success = save_manager.perform_save_operation(
                youtube_service=self.youtube_service,
                api_data=normalized_data,
                total_videos=total_videos,
                total_comments=total_comments
            )
            
            # Offer option to view in data storage tab after successful save
            if success and st.button("Go to Data Storage Tab", key="refresh_go_to_storage_btn"):
                st.session_state['main_tab'] = "data_storage"
                st.rerun()
                
        except Exception as e:
            handle_collection_error(e, "saving data")
    
    def store_video_data_in_session(self, video_response):
        """Store video data in session state for use in later steps."""
        if video_response and 'video_id' in video_response:
            st.session_state['videos_data'] = video_response['video_id']
    
    def render_current_step(self):
        """
        Render the current step of the workflow based on session state.
        
        Override the base class method to handle the additional step 1 (channel selection)
        that's specific to the refresh workflow.
        """
        # Get current refresh workflow step
        current_step = st.session_state.get('refresh_workflow_step', 1)
        
        if current_step == 1:
            self.render_step_1_select_channel()
        elif current_step == 2:
            self.render_step_1_channel_data()
        elif current_step == 3:
            self.render_step_2_playlist_review()
        elif current_step == 4:
            self.render_step_4_video_collection()
        elif current_step == 5:
            self.render_step_5_comment_collection()
        else:
            st.error(f"Unknown step: {current_step}")
        
        # Add debug mode toggle and panel at the bottom of all workflows
        self.render_debug_controls()
    
    def _handle_video_collection(self, channel_id, options):
        """
        Handle the process of collecting videos for a channel.
        
        Args:
            channel_id (str): The channel ID to collect videos for
            options (dict): Options for video collection including max_videos
            
        Returns:
            dict: The collected video data
        """
        try:
            # If options is a number, convert it to a proper options dict
            if isinstance(options, (int, str)):
                max_videos = int(options)
                options = {
                    'fetch_channel_data': False,
                    'fetch_videos': True,
                    'fetch_comments': False,
                    'max_videos': max_videos,
                    'comparison_level': 'comprehensive',
                    'track_keywords': ['copyright', 'disclaimer', 'new owner', 'policy', 'terms'],
                    'alert_on_significant_changes': True,
                    'persist_change_history': True,
                    'compare_all_fields': True
                }
            # Ensure required options are set
            if 'fetch_videos' not in options:
                options['fetch_videos'] = True
            if 'fetch_channel_data' not in options:
                options['fetch_channel_data'] = False
            if 'fetch_comments' not in options:
                options['fetch_comments'] = False
                
            debug_log_with_time(f"[WORKFLOW] Collecting videos for channel_id={channel_id} with options={options}")
            # Call update_channel_data to get videos with delta calculation
            response = self.youtube_service.update_channel_data(channel_id, options, interactive=False)
            if not response or not isinstance(response, dict):
                debug_log_with_time(f"[WORKFLOW][ERROR] Invalid response from update_channel_data: {response}")
                return None
            
            api_data = response.get('api_data', {})
            if not api_data:
                debug_log_with_time("[WORKFLOW][ERROR] No api_data in response")
                return None
                
            video_response = self.extract_api_data_from_delta(api_data)
            # Process the video data
            if video_response and 'video_id' in video_response:
                videos = video_response.get('video_id', [])
                debug_log_with_time(f"[WORKFLOW] Found {len(videos)} videos in response")
                
                # Process videos for display
                process_video_data(videos)
                # Fix missing fields in videos
                for video in videos:
                    fix_missing_views(video)
                # Update video data in session_state
                self.store_video_data_in_session(video_response)
                
                # Display success message with count (handled by calling function)
                return video_response
            else:
                debug_log_with_time("[WORKFLOW][ERROR] No videos found in response")
                return None
        except Exception as e:
            debug_log_with_time(f"[WORKFLOW][ERROR] Error collecting videos: {str(e)}")
            handle_collection_error(e, "collecting videos")
            return None

    def convert_api_to_ui_format(self, api_data):
        """
        Convert API-format channel data to a UI-friendly format for consistent display and comparison.
        Args:
            api_data (dict): Channel data from the API
        Returns:
            dict: Data converted to UI-compatible format
        """
        if not api_data:
            return {}
        # Start with a shallow copy
        ui_format = dict(api_data)
        # Map key fields for UI consistency
        if 'raw_channel_info' in api_data:
            info = api_data['raw_channel_info']
            ui_format['channel_id'] = info.get('id', ui_format.get('channel_id'))
            ui_format['channel_name'] = info.get('snippet', {}).get('title', ui_format.get('channel_name', 'Unknown Channel'))
            ui_format['playlist_id'] = info.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads', ui_format.get('playlist_id', ''))
            stats = info.get('statistics', {})
            if 'subscriberCount' in stats:
                try:
                    ui_format['subscribers'] = int(stats['subscriberCount'])
                except Exception:
                    ui_format['subscribers'] = stats['subscriberCount']
            if 'viewCount' in stats:
                try:
                    ui_format['views'] = int(stats['viewCount'])
                except Exception:
                    ui_format['views'] = stats['viewCount']
            if 'videoCount' in stats:
                try:
                    ui_format['total_videos'] = int(stats['videoCount'])
                except Exception:
                    ui_format['total_videos'] = stats['videoCount']
        # Ensure video_id is always a list
        if 'video_id' not in ui_format:
            ui_format['video_id'] = []
        # Ensure delta is present if available
        if 'delta' in api_data:
            ui_format['delta'] = api_data['delta']
        return ui_format

    def retry_api_fetch(self):
        """Retry fetching API data for the current channel and rerun the workflow."""
        import streamlit as st
        channel_id = st.session_state.get('existing_channel_id')
        if channel_id:
            st.session_state['api_data'] = {}
            st.session_state['api_last_error'] = None
            # Set a flag to trigger API fetch in the next run
            st.session_state['refresh_api_fetch'] = True
            st.rerun()

    def go_to_channel_selection(self):
        """Navigate back to the channel selection step and rerun the workflow."""
        import streamlit as st
        st.session_state['refresh_channel_step'] = 1
        st.rerun()

    def extract_api_data_from_delta(self, api_data):
        """
        Extract the canonical API data from delta structures if present.
        Args:
            api_data (dict): API data possibly containing delta
        Returns:
            dict: Flattened API data with raw_channel_info
        """
        if 'delta' in api_data and 'api_data_new' in api_data['delta']:
            value = api_data['delta']['api_data_new'].get('value')
            if value and isinstance(value, dict) and 'raw_channel_info' in value:
                return value
        if 'raw_channel_info' in api_data:
            return api_data
        return {}

    def safe_json_summary(self, obj):
        """Return a safe, serializable summary for debug display."""
        import json
        try:
            return json.dumps(obj, default=str, indent=2)[:2000]  # Truncate for safety
        except Exception:
            return str(obj)[:2000]

def debug_log_with_time(message: str):
    logger.info(f"{datetime.now().isoformat()} - {message}")
