"""
Channel refresh workflow implementation for data collection.
"""
import streamlit as st
import pandas as pd
import datetime
import json
import sys
from src.utils.helpers import debug_log
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from .components.video_item import render_video_item
from .components.comprehensive_display import render_collapsible_field_explorer, render_channel_overview_card, render_detailed_change_dashboard
from .components.save_operation_manager import SaveOperationManager
from .channel_refresh.comparison import display_comparison_results, compare_data
from .utils.data_conversion import format_number, convert_db_to_api_format
from .utils.error_handling import handle_collection_error
from src.utils.queue_tracker import render_queue_status_sidebar, add_to_queue
from src.utils.video_processor import process_video_data
from src.utils.video_formatter import fix_missing_views
from src.utils.video_standardizer import extract_standardized_videos, standardize_video_data
from src.database.channel_repository import ChannelRepository
from src.ui.data_collection.utils.delta_reporting import render_delta_report
import math
from datetime import datetime
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
                    debug_log(f"Getting comparison data for channel: {channel_id}")
                    st.session_state['comparison_attempted'] = True
                    import datetime
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
                        st.session_state['last_api_call'] = datetime.datetime.now().isoformat()
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
        from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format
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
        
        # Show comparison table with clear headers
        st.markdown("### Database vs API Comparison")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Current Database Values**")
            render_channel_overview_card(db_data)
        with col2:
            st.markdown("**Latest API Values**") 
            render_channel_overview_card(api_data)
        
        # Display delta report with clear header
        st.markdown("### Changes Detected")
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
                    channel_data = api_data
                    save_manager = SaveOperationManager()
                    success = save_manager.perform_save_operation(
                        youtube_service=self.youtube_service,
                        api_data=channel_data,
                        total_videos=0,
                        total_comments=0
                    )
                    debug_log_with_time(f"[PARITY] Save operation for channel_id={channel_id} success={success}")
                    if success:
                        st.session_state['channel_data_saved'] = True
                        from src.config import SQLITE_DB_PATH
                        from src.database.channel_repository import ChannelRepository
                        db_repo = ChannelRepository(SQLITE_DB_PATH)
                        db_record = db_repo.get_channel_data(channel_data.get('channel_id'))
                        db_api_format = convert_db_to_api_format(db_record) if db_record else {}
                        st.session_state['db_data'] = db_record
                        debug_log_with_time(f"[PARITY] Reloaded DB data after save for channel_id={channel_id}: {bool(db_record)}")
                        # Store post-save raw data in debug state
                        st.session_state['debug_raw_data']['channel_post_save'] = {
                            'db': db_record,
                            'api': channel_data.get('raw_channel_info')
                        }
                        st.session_state['debug_delta_data']['channel_post_save'] = {
                            'delta': channel_data.get('delta')
                        }
                        
                        # Display clear success confirmation with saved data details
                        st.success(f"Channel data for '{channel_data.get('channel_name')}' saved successfully!")
                        
                        # Show a summary of what was saved
                        st.info("**Data saved to database:**")
                        saved_summary = {
                            "Channel Name": channel_data.get('channel_name'),
                            "Channel ID": channel_data.get('channel_id'),
                            "Subscribers": format_number(channel_data.get('subscribers', 0)),
                            "Views": format_number(channel_data.get('views', 0)),
                            "Videos": format_number(channel_data.get('total_videos', 0)),
                            "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        for key, value in saved_summary.items():
                            st.write(f"**{key}:** {value}")
                        
                        if st.session_state.get('debug_mode', False):
                            st.markdown("---")
                            st.subheader(":inbox_tray: Database Record (Post-Save)")
                            st.json(db_api_format)
                            st.subheader(":satellite: API Response (Just Saved)")
                            st.json(channel_data.get('raw_channel_info'))
                            st.subheader(":mag: Delta Report (API vs DB, Raw)")
                            st.json(channel_data.get('delta'))
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
        if 'playlist_queued' not in st.session_state:
            st.session_state['playlist_queued'] = False
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save Playlist Data", key="save_playlist_data_btn_refresh", disabled=st.session_state['playlist_saved'] or st.session_state['playlist_queued']):
                try:
                    playlist_save_success = self.youtube_service.save_playlist_data(playlist_api)
                    if playlist_save_success:
                        st.session_state['playlist_saved'] = True
                        st.success("✅ Playlist data saved successfully!")
                    else:
                        st.error("❌ Failed to save playlist data.")
                except Exception as e:
                    st.error(f"❌ Error saving playlist: {str(e)}")
        with col2:
            if st.button("📋 Add to Queue", key="queue_playlist_btn_refresh", disabled=st.session_state['playlist_saved'] or st.session_state['playlist_queued']):
                try:
                    add_to_queue('playlists', channel_id, playlist_api)
                    st.session_state['playlist_queued'] = True
                    st.success("✅ Playlist added to processing queue!")
                except Exception as e:
                    st.error(f"❌ Error adding to queue: {str(e)}")
        with col3:
            if st.button("▶️ Continue to Videos", key="continue_to_videos_btn2_refresh", disabled=not (st.session_state['playlist_saved'] or st.session_state['playlist_queued'])):
                st.session_state['collection_step'] = 3
                st.session_state['refresh_workflow_step'] = 4
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 4 (in refresh workflow): Collect and display video data, with delta and queue option."""
        st.subheader("Step 4: Video Collection (Refresh)")
        self.show_progress_indicator(4)
        render_queue_status_sidebar()
        channel_id = st.session_state.get('existing_channel_id', '')
        from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format
        db_data_raw = st.session_state.get('db_data', {})
        db_data = convert_db_to_api_format(db_data_raw) if db_data_raw else {}
        db_videos = db_data.get('video_id', [])
        api_data_raw = st.session_state.get('api_data', {})
        api_data = self.convert_api_to_ui_format(self.extract_api_data_from_delta(api_data_raw))
        
        # Get the channel name for context
        channel_name = api_data.get('channel_name', db_data.get('channel_name', 'Unknown Channel'))
        st.write(f"Collecting videos for: **{channel_name}** ({channel_id})")
        
        show_api_error = not api_data or api_data.get('raw_channel_info') is None
        # Store raw/delta in debug state
        if 'debug_raw_data' not in st.session_state:
            st.session_state['debug_raw_data'] = {}
        if 'debug_delta_data' not in st.session_state:
            st.session_state['debug_delta_data'] = {}
        st.session_state['debug_raw_data']['video'] = {
            'db': db_videos,
            'api': api_data.get('video_id', [])
        }
        st.session_state['debug_delta_data']['video'] = {
            'delta': None  # If you have a delta, store it here
        }
        if st.session_state.get('debug_mode', False):
            st.markdown("---")
            st.subheader("Videos in Database (Raw)")
            st.json(db_videos)
            st.subheader("Videos from API (Raw)")
            st.json(api_data.get('video_id', []))
            st.subheader("Video Delta Report (Raw)")
            st.json(None)  # Replace with actual delta if available
        
        # Display video collection controls
        st.markdown("### Video Collection Options")
        max_video_default = min(50, api_data.get('total_videos', 50))
        # Get actual count from API if available
        actual_video_count = api_data.get('total_videos', 0)
        
        # Use a slider that allows selecting up to the actual video count
        max_videos = st.slider(
            "Maximum number of videos to collect:",
            min_value=0,
            max_value=max(actual_video_count, 100),  # Allow at least 100 as max
            value=max_video_default,
            step=5
        )
        
        # Add comparison options just like in channel update
        st.markdown("### Video Comparison Options")
        comparison_level = st.selectbox(
            "Comparison Detail Level:",
            options=["basic", "standard", "comprehensive"],
            index=2,  # Default to comprehensive
            help="Choose how detailed the comparison should be between existing and new video data"
        )
        
        track_keywords = st.text_input(
            "Keywords to Track (comma-separated):",
            value="copyright,disclaimer,new owner,ownership,policy,terms",
            help="Enter keywords to track in video titles and descriptions"
        ).split(",")
        
        alert_on_changes = st.checkbox(
            "Alert on Significant Changes",
            value=True,
            help="Highlight videos with significant metric changes"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Collect Videos", key="refresh_collect_videos_btn"):
                if channel_id:
                    with st.spinner(f"Collecting up to {max_videos} videos..."):
                        # Create options with enhanced comparison settings
                        options = {
                            'fetch_channel_data': False,
                            'fetch_videos': True,
                            'fetch_comments': False,
                            'max_videos': max_videos,
                            'comparison_level': comparison_level,
                            'track_keywords': track_keywords,
                            'alert_on_significant_changes': alert_on_changes,
                            'persist_change_history': True,
                            'compare_all_fields': True  # Ensure all fields are compared
                        }
                        video_response = self._handle_video_collection(channel_id, options)
                        if video_response:
                            st.session_state['videos_fetched'] = True
                            st.session_state['video_response'] = video_response
                            st.success(f"Successfully collected {len(video_response.get('video_id', []))} videos!")
                            
                            # Show summary of collected videos
                            video_count = len(video_response.get('video_id', []))
                            st.info(f"**Videos collected:** {video_count}")
                            
                            # Display some basic stats about the collected videos
                            if video_count > 0:
                                videos = video_response.get('video_id', [])
                                total_views = sum(int(v.get('views', 0)) for v in videos)
                                total_likes = sum(int(v.get('likes', 0)) for v in videos)
                                total_comments = sum(int(v.get('comment_count', 0)) for v in videos)
                                
                                st.write(f"**Total Views:** {format_number(total_views)}")
                                st.write(f"**Total Likes:** {format_number(total_likes)}")
                                st.write(f"**Total Comments:** {format_number(total_comments)}")
                                
                            # Auto-rerun to refresh the UI with the new data
                            st.rerun()
                        else:
                            st.error("Failed to collect videos. Check logs for details.")
        with col2:
            if st.button("Continue to Comments Data", key="refresh_continue_to_comments_btn"):
                st.session_state['collection_step'] = 4
                st.session_state['refresh_workflow_step'] = 5
                st.rerun()
    
    def render_step_3_comment_collection(self):
        """Render step 5 (in refresh workflow): Collect and display comment data, with delta and queue option."""
        st.subheader("Step 5: Comment Collection (Refresh)")
        self.show_progress_indicator(5)
        render_queue_status_sidebar()
        channel_id = st.session_state.get('existing_channel_id', '')
        from src.ui.data_collection.utils.data_conversion import convert_db_to_api_format
        db_data_raw = st.session_state.get('db_data', {})
        db_data = convert_db_to_api_format(db_data_raw) if db_data_raw else {}
        db_videos = db_data.get('video_id', [])
        api_data_raw = st.session_state.get('api_data', {})
        api_data = self.convert_api_to_ui_format(self.extract_api_data_from_delta(api_data_raw))
        show_api_error = not api_data or api_data.get('raw_channel_info') is None
        
        # Store raw/delta in debug state
        if 'debug_raw_data' not in st.session_state:
            st.session_state['debug_raw_data'] = {}
        if 'debug_delta_data' not in st.session_state:
            st.session_state['debug_delta_data'] = {}
        st.session_state['debug_raw_data']['comment'] = {
            'db': db_videos,
            'api': api_data.get('video_id', [])
        }
        st.session_state['debug_delta_data']['comment'] = {
            'delta': None  # If you have a delta, store it here
        }
        
        # Only show raw/delta in UI if debug_mode is enabled
        if st.session_state.get('debug_mode', False):
            st.markdown("---")
            st.subheader("Videos in Database (Raw)")
            st.json(db_videos)
            st.subheader("Videos from API (Raw)")
            st.json(api_data.get('video_id', []))
            st.subheader("Comment Delta Report (Raw)")
            st.json(None)  # Replace with actual delta if available
        
        # Show user-friendly summary of videos
        st.subheader("Video Summary")
        api_videos = api_data.get('video_id', [])
        
        # Create a user-friendly summary table
        if db_videos or api_videos:
            video_summary = []
            
            if db_videos and len(db_videos) > 0:
                st.write(f"Found **{len(db_videos)}** videos in database")
                
                # Show sample of videos from DB
                st.write("Sample of videos in database:")
                for i, video in enumerate(db_videos[:5]):
                    if isinstance(video, dict):
                        title = video.get('title', 'Unknown')
                        video_id = video.get('video_id', 'Unknown')
                        st.write(f"{i+1}. **{title}** ({video_id})")
                
                if len(db_videos) > 5:
                    st.caption(f"... and {len(db_videos) - 5} more videos in DB.")
            else:
                st.warning("No videos found in database.")
            
            if api_videos and len(api_videos) > 0:
                st.write(f"Found **{len(api_videos)}** videos from API")
                
                # Count new videos (in API but not in DB)
                db_video_ids = {v.get('video_id') for v in db_videos if isinstance(v, dict) and 'video_id' in v}
                new_videos = [v for v in api_videos if isinstance(v, dict) and 'video_id' in v and v.get('video_id') not in db_video_ids]
                
                if new_videos:
                    st.success(f"Found {len(new_videos)} new videos that are not in the database.")
            else:
                st.warning("No videos found from API.")
        else:
            st.warning("No videos found in either database or API.")
        
        st.markdown("---")
        st.write("### Comment Collection Options")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Collect Comments", key="refresh_collect_comments_btn"):
                if channel_id:
                    with st.spinner("Collecting comments..."):
                        # Create options for comment collection
                        options = {
                            'fetch_channel_data': False,
                            'fetch_videos': False,
                            'fetch_comments': True,
                            'max_videos': 0,
                            'max_comments_per_video': 10,
                            'comparison_level': 'comprehensive',
                            'track_keywords': ['copyright', 'disclaimer', 'new owner', 'policy', 'terms'],
                            'alert_on_significant_changes': True,
                            'persist_change_history': True,
                            'compare_all_fields': True
                        }
                        comment_response = self._handle_video_collection(channel_id, options)
                        if comment_response:
                            st.session_state['comments_fetched'] = True
                            st.session_state['comment_response'] = comment_response
                            st.success(f"Successfully collected {len(comment_response.get('comments', []))} comments!")
                            
                            # Show summary of collected comments
                            comment_count = len(comment_response.get('comments', []))
                            st.info(f"**Comments collected:** {comment_count}")
                            
                            # Auto-rerun to refresh the UI with the new data
                            st.rerun()
                        else:
                            st.error("Failed to collect comments. Check logs for details.")
        with col2:
            if st.button("Back to Videos Data", key="refresh_back_to_videos_data_btn"):
                st.session_state['collection_step'] = 3
                st.session_state['refresh_workflow_step'] = 4
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
            
            # Check if youtube_service is properly initialized
            if not hasattr(self.youtube_service, 'save_channel_data'):
                st.error("YouTube service is not properly initialized.")
                from src.utils.helpers import debug_log
                debug_log(f"YouTube service missing save_channel_data method: {type(self.youtube_service)}")
                return
            
            # Calculate video and comment counts for the save operation manager
            total_videos = len(videos_data) if videos_data else 0
            total_comments = sum(len(video.get('comments', [])) for video in videos_data) if videos_data else 0
            
            # Use the SaveOperationManager to handle save operations with feedback
            save_manager = SaveOperationManager()
            success = save_manager.perform_save_operation(
                youtube_service=self.youtube_service,
                api_data=api_data,
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
            self.render_step_2_video_collection()
        elif current_step == 5:
            self.render_step_3_comment_collection()
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
    debug_log(f"{datetime.now().isoformat()} - {message}")
