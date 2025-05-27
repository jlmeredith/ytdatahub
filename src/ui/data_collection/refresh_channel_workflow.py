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
                        # Enhanced comparison options for comprehensive data tracking
                        options = {
                            'fetch_channel_data': True,
                            'fetch_videos': False,
                            'fetch_comments': False,
                            'max_videos': 0,
                            'max_comments_per_video': 0,
                            'comparison_level': 'comprehensive',  # Use comprehensive level by default
                            'track_keywords': ['copyright', 'disclaimer', 'new owner', 'ownership', 'management', 'rights'],
                            'alert_on_significant_changes': True,
                            'persist_change_history': True
                        }
                        comparison_data = self.youtube_service.update_channel_data(channel_id, options, interactive=False, existing_data=None)
                        st.session_state['last_api_call'] = datetime.datetime.now().isoformat()
                        if comparison_data and isinstance(comparison_data, dict):
                            st.session_state['db_data'] = comparison_data.get('db_data', {})
                            st.session_state['api_data'] = comparison_data.get('api_data', {})
                            if st.session_state['db_data'] is None:
                                st.session_state['db_data'] = {}
                            if st.session_state['api_data'] is None:
                                st.session_state['api_data'] = {}
                            # Promote delta info from api_data if present
                            if 'delta' in st.session_state['api_data']:
                                st.session_state['delta'] = st.session_state['api_data']['delta']
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
        """Render step 2 (in refresh workflow): Review and update channel data, and show all API fields."""
        st.subheader("Step 2: Review and Update Channel Data")
        channel_id = st.session_state.get('existing_channel_id')
        db_data = st.session_state.get('db_data', {})
        api_data = st.session_state.get('api_data', {})
        debug_logs = st.session_state.get('debug_logs', [])
        if st.button("Refresh Channel Info from API"):
            with st.spinner("Fetching channel info from YouTube API..."):
                options = {
                    'fetch_channel_data': True,
                    'fetch_videos': False,
                    'fetch_comments': False,
                    'max_videos': 0,
                    'max_comments_per_video': 0,
                    'comparison_level': 'comprehensive',
                    'track_keywords': ['copyright', 'disclaimer', 'new owner', 'ownership', 'management', 'rights'],
                    'alert_on_significant_changes': True,
                    'persist_change_history': True
                }
                channel_info_response = self.youtube_service.update_channel_data(
                    channel_id,
                    options,
                    interactive=False
                )
                st.session_state['api_initialized'] = True
                debug_logs.append(f"API call made to fetch channel info for {channel_id}")
                st.session_state['debug_logs'] = debug_logs
                st.session_state['last_api_call'] = channel_info_response.get('last_api_call')
                if channel_info_response and isinstance(channel_info_response, dict):
                    st.session_state['api_data'] = channel_info_response.get('api_data', {})
                    st.session_state['response_data'] = channel_info_response.get('response_data', {})
                    from src.ui.data_collection.channel_refresh.comparison import compare_data
                    delta = compare_data(db_data, st.session_state['api_data'])
                    st.session_state['delta'] = delta
                    summary = []
                    if 'subscribers' in delta:
                        diff = delta['subscribers']['new'] - delta['subscribers']['old']
                        arrow = '⬆️' if diff > 0 else ('⬇️' if diff < 0 else '')
                        summary.append(f"Subscribers: {delta['subscribers']['old']} → {delta['subscribers']['new']} {arrow}")
                    if 'views' in delta:
                        diff = delta['views']['new'] - delta['views']['old']
                        arrow = '⬆️' if diff > 0 else ('⬇️' if diff < 0 else '')
                        summary.append(f"Views: {delta['views']['old']} → {delta['views']['new']} {arrow}")
                    if 'videos' in delta:
                        diff = delta['videos']['new'] - delta['videos']['old']
                        arrow = '⬆️' if diff > 0 else ('⬇️' if diff < 0 else '')
                        summary.append(f"Videos: {delta['videos']['old']} → {delta['videos']['new']} {arrow}")
                    st.session_state['delta_summary'] = summary
                    st.success("Channel info refreshed from API.")
                else:
                    st.error("Failed to fetch channel info from API.")
                st.rerun()
        # Show summary card and collapsible explorer instead of raw st.json
        from src.ui.data_collection.components.comprehensive_display import render_channel_overview_card, render_collapsible_field_explorer
        st.write("### Channel Overview")
        render_channel_overview_card(api_data)
        render_collapsible_field_explorer(api_data, "All Channel Fields (Collapsible)")
        # Buttons for save, continue, and queue
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Channel Data", key="refresh_save_channel_btn"):
                try:
                    channel_data = st.session_state.get('api_data', {})
                    save_manager = SaveOperationManager()
                    success = save_manager.perform_save_operation(
                        youtube_service=self.youtube_service,
                        api_data=channel_data,
                        total_videos=0,
                        total_comments=0
                    )
                    if success:
                        st.session_state['channel_data_saved'] = True
                        db_repo = ChannelRepository(self.youtube_service.db_path)
                        db_record = db_repo.get_channel_data(channel_data.get('channel_id'))
                        st.markdown("---")
                        st.subheader(":inbox_tray: Database Record (Post-Save)")
                        st.json(db_record)
                        st.subheader(":satellite: API Response (Just Saved)")
                        st.json(channel_data.get('raw_channel_info'))
                        st.subheader(":mag: Delta Report (API vs DB)")
                        render_delta_report(channel_data.get('raw_channel_info'), db_record.get('raw_channel_info'), data_type="channel")
                except Exception as e:
                    st.error(f"Error saving data: {str(e)}")
                    debug_log(f"Error saving channel data: {str(e)}")
        with col2:
            if st.button("Continue to Videos Data", key="refresh_continue_to_videos_btn"):
                st.session_state['collection_step'] = 2
                st.session_state['refresh_workflow_step'] = 3
                st.rerun()
        with col3:
            if st.button("Save to Queue for Later", key="refresh_queue_channel_btn"):
                channel_data = st.session_state.get('api_data', {})
                add_to_queue('channels', channel_data.get('channel_id'), channel_data)
                st.success("Channel added to queue for later processing.")
    
    def render_step_2_playlist_review(self):
        """Render playlist review step: show API, DB, and delta for playlist, with explicit user control."""
        st.subheader("Step 2: Playlist Review (Refresh)")
        channel_info = st.session_state.get('api_data', {})
        playlist_id = channel_info.get('playlist_id')
        if not playlist_id:
            st.info("No playlist found for this channel.")
            return
        # Fetch playlist API response (from session or API)
        playlist_api = st.session_state.get('playlist_api_data')
        if not playlist_api:
            try:
                playlist_api = self.youtube_service.get_playlist_info(playlist_id)
                st.session_state['playlist_api_data'] = playlist_api
            except Exception as e:
                st.error(f"Error fetching playlist API data: {str(e)}")
                return
        # Flatten playlist_id and channel_id for DB save (but do not save yet)
        if playlist_api:
            if 'id' in playlist_api:
                playlist_api['playlist_id'] = playlist_api['id']
            if 'snippet' in playlist_api and 'channelId' in playlist_api['snippet']:
                playlist_api['channel_id'] = playlist_api['snippet']['channelId']
        # Fetch DB record
        from src.database.sqlite import SQLiteDatabase
        from src.config import SQLITE_DB_PATH
        db = SQLiteDatabase(SQLITE_DB_PATH)
        db_playlist = db.video_repository.get_playlist_data(playlist_id)
        # Fetch historical record (optional)
        try:
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM playlists_history WHERE playlist_id = ? ORDER BY fetched_at DESC LIMIT 1', (playlist_id,))
            row = cursor.fetchone()
            historical = row[-1] if row else None
            conn.close()
        except Exception:
            historical = None
        st.markdown("---")
        st.subheader(":satellite: Playlist API Response")
        st.json(playlist_api)
        st.subheader(":inbox_tray: Playlist DB Record")
        st.json(db_playlist)
        if historical:
            st.subheader(":clock1: Playlist Historical Record (Most Recent)")
            st.json(historical)
        st.subheader(":mag: Playlist Delta Report (API vs DB)")
        from src.ui.data_collection.utils.delta_reporting import render_delta_report
        render_delta_report(playlist_api, db_playlist, data_type="playlist")
        # --- User Controls ---
        if 'playlist_saved' not in st.session_state:
            st.session_state['playlist_saved'] = False
        if 'playlist_queued' not in st.session_state:
            st.session_state['playlist_queued'] = False
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Playlist Data", disabled=st.session_state['playlist_saved'] or st.session_state['playlist_queued']):
                playlist_save_success = self.youtube_service.save_playlist_data(playlist_api)
                if playlist_save_success:
                    st.session_state['playlist_saved'] = True
                    st.success("Playlist data saved to database.")
                else:
                    st.error("Failed to save playlist data to database.")
        with col2:
            if st.button("Queue Playlist for Later", disabled=st.session_state['playlist_saved'] or st.session_state['playlist_queued']):
                add_to_queue('playlists', playlist_id, playlist_api)
                st.session_state['playlist_queued'] = True
                st.success("Playlist added to queue for later processing.")
        with col3:
            if st.button("Continue to Videos Data", disabled=not (st.session_state['playlist_saved'] or st.session_state['playlist_queued'])):
                st.session_state['collection_step'] = 2
                st.session_state['refresh_workflow_step'] = 3
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 3 (in refresh workflow): Collect and display video data, with queue option."""
        st.subheader("Step 3: Video Collection")
        render_queue_status_sidebar()
        channel_id = st.session_state.get('existing_channel_id', '')
        db_data = st.session_state.get('db_data', {})
        if db_data and isinstance(db_data, dict):
            if 'videos' in db_data and 'video_id' not in db_data:
                db_data['video_id'] = db_data['videos']
            db_videos = extract_standardized_videos(db_data)
            st.session_state['db_data']['video_id'] = db_videos
            debug_log(f"Standardized DB videos count: {len(db_videos)}")
        videos_data = st.session_state.get('videos_data', [])
        debug_logs = st.session_state.get('debug_logs', [])

        # --- PAGINATION for videos ---
        videos_per_page = 10
        total_videos = len(videos_data)
        total_video_pages = max(1, math.ceil(total_videos / videos_per_page))
        if 'video_page' not in st.session_state:
            st.session_state['video_page'] = 0
        start_idx = st.session_state['video_page'] * videos_per_page
        end_idx = min(start_idx + videos_per_page, total_videos)
        paginated_videos = videos_data[start_idx:end_idx]
        st.write(f"Showing videos {start_idx+1}-{end_idx} of {total_videos}")
        col_v1, col_v2, col_v3 = st.columns([1, 2, 1])
        with col_v1:
            if st.button("← Previous Videos", disabled=st.session_state['video_page'] <= 0, key="refresh_video_prev_page_btn"):
                st.session_state['video_page'] -= 1
                st.rerun()
        with col_v2:
            st.write(f"Page {st.session_state['video_page']+1} of {total_video_pages}")
        with col_v3:
            if st.button("Next Videos →", disabled=st.session_state['video_page'] >= total_video_pages-1, key="refresh_video_next_page_btn"):
                st.session_state['video_page'] += 1
                st.rerun()

        # Direct video selection UI
        selected_video_ids = []
        for idx, video in enumerate(paginated_videos, start=start_idx+1):
            selected = render_video_item(video, index=idx, selectable=True)
            if selected:
                video_id = video.get('video_id')
                if video_id:
                    selected_video_ids.append(video_id)
        st.session_state['selected_video_ids'] = selected_video_ids

        # Action buttons for selected videos
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Selected Videos Data", key="refresh_save_selected_videos_btn"):
                if not selected_video_ids:
                    st.warning("Please select at least one video to save.")
                else:
                    try:
                        channel_data = st.session_state.get('api_data', {})
                        selected_videos = [v for v in videos_data if v.get('video_id') in selected_video_ids]
                        channel_data['video_id'] = selected_videos
                        save_manager = SaveOperationManager()
                        success = save_manager.perform_save_operation(
                            youtube_service=self.youtube_service,
                            api_data=channel_data,
                            total_videos=len(selected_videos),
                            total_comments=0
                        )
                        if success:
                            st.session_state['videos_data_saved'] = True
                            st.success("Selected video data saved successfully!")
                    except Exception as e:
                        handle_collection_error(e, "saving selected video data")
        with col2:
            if st.button("Continue to Comments Data", key="refresh_continue_to_comments_btn"):
                if not selected_video_ids:
                    st.warning("Please select at least one video to continue.")
                else:
                    # Only keep selected videos for next step
                    st.session_state['videos_data'] = [v for v in videos_data if v.get('video_id') in selected_video_ids]
                    st.session_state['collection_step'] = 3
                    st.session_state['refresh_workflow_step'] = 4
                    st.rerun()
        with col3:
            if st.button("Queue Selected Videos for Later", key="refresh_queue_selected_videos_btn"):
                if not selected_video_ids:
                    st.warning("Please select at least one video to queue.")
                else:
                    add_to_queue('videos', channel_id, [v for v in videos_data if v.get('video_id') in selected_video_ids])
                    st.success("Selected videos added to queue for later processing.")
    
    def render_step_3_comment_collection(self):
        """Render step 4 (in refresh workflow): Collect and display comment data, with queue option."""
        st.subheader("Step 4: Comment Collection")
        render_queue_status_sidebar()  # Show queue in sidebar (only once)
        channel_id = st.session_state.get('existing_channel_id', '')
        videos_data = st.session_state.get('videos_data', [])
        debug_logs = st.session_state.get('debug_logs', [])
        if not st.session_state.get('comments_fetched', False):
            if not videos_data:
                st.warning("No videos available for comment collection. Please go back to the video collection step.")
                if st.button("Back to Video Collection", key="refresh_back_to_videos_btn"):
                    st.session_state['collection_step'] = 2
                    st.session_state['refresh_workflow_step'] = 3
                    st.rerun()
                return
            # Create two columns for more intuitive UI layout
            col1, col2 = st.columns([1, 1])
            
            with col1:
                max_comments = st.slider(
                    "Top-Level Comments Per Video",
                    min_value=0,
                    max_value=100,
                    value=20,
                    help="Maximum number of top-level comments to import per video (0 to skip comments)",
                    key="refresh_max_comments_slider"
                )
                st.caption("Controls how many primary comments to collect for each video")
            
            with col2:
                max_replies = st.slider(
                    "Replies Per Top-Level Comment",
                    min_value=0,
                    max_value=50,
                    value=5,
                    help="Maximum number of replies to fetch for each top-level comment",
                    key="refresh_max_replies_slider"
                )
                st.caption("Controls how many replies to collect for each primary comment")
            
            # Add explanatory text about API quota impact
            st.info("💡 Higher values will provide more comprehensive data but may consume more API quota.")
            
            if st.button("Fetch Comments from API", key="refresh_fetch_comments_btn"):
                if max_comments == 0:
                    st.info("Comment collection skipped.")
                    st.session_state['comments_fetched'] = True
                    st.rerun()
                else:
                    with st.spinner(f"Fetching up to {max_comments} comments per video from YouTube API..."):
                        options = {
                            'fetch_channel_data': False,
                            'fetch_videos': False,
                            'fetch_comments': True,
                            'max_comments_per_video': max_comments,
                            'max_replies_per_comment': max_replies,
                            'comparison_level': 'comprehensive',
                            'track_keywords': ['copyright', 'disclaimer', 'new owner', 'ownership', 'management', 'rights'],
                            'alert_on_significant_changes': True,
                            'persist_change_history': True
                        }
                        comment_response = self.youtube_service.update_channel_data(
                            channel_id,
                            options,
                            interactive=False
                        )
                        st.session_state['api_initialized'] = True
                        debug_logs.append(f"API call made to fetch comments for {channel_id}")
                        st.session_state['debug_logs'] = debug_logs
                        st.session_state['last_api_call'] = comment_response.get('last_api_call')
                        if comment_response and isinstance(comment_response, dict):
                            st.session_state['videos_data'] = comment_response.get('video_id', [])
                            st.session_state['response_data'] = comment_response.get('response_data', {})
                            st.session_state['comments_fetched'] = True
                            total_comments = sum(len(video.get('comments', [])) for video in st.session_state['videos_data'])
                            summary = [f"Total comments fetched: {total_comments}"]
                            st.session_state['delta_summary'] = summary
                            st.success("Successfully fetched comments!")
                            # Add comments to queue for later
                            from src.utils.queue_tracker import add_to_queue
                            comments_data = [video.get('comments', []) for video in st.session_state['videos_data'] if video.get('comments')]
                            add_to_queue('comments', channel_id, comments_data)
                            st.success("Comments added to queue for later processing.")
                            st.rerun()
                        else:
                            st.error("Failed to fetch comments. Please try again.")
        else:
            total_comments = sum(len(video.get('comments', [])) for video in videos_data)
            videos_with_comments = sum(1 for video in videos_data if video.get('comments'))
            st.write(f"Successfully fetched {total_comments} comments from {videos_with_comments} videos.")
            videos_with_comments_list = [v for v in videos_data if v.get('comments')]
            if videos_with_comments_list:
                st.write("### Sample Video with Comments Data Structure")
                st.json(videos_with_comments_list[0])
            for video in videos_with_comments_list[:5]:
                st.subheader(f"Video: {video.get('title', 'Unknown Title')}")
                for comment in video.get('comments', [])[:3]:
                    st.write(f"**{comment.get('comment_author', 'Unknown')}**: {comment.get('comment_text', 'No text')}")
                if len(video.get('comments', [])) > 3:
                    st.write(f"... and {len(video.get('comments', [])) - 3} more comments")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Complete and Save Data", key="refresh_complete_save_btn"):
                    self.save_data()
                    # --- NEW: Comment Review Step ---
                    videos_data = st.session_state.get('videos_data', [])
                    from src.database.sqlite import SQLiteDatabase
                    from src.config import SQLITE_DB_PATH
                    db = SQLiteDatabase(SQLITE_DB_PATH)
                    st.markdown("---")
                    st.subheader(":speech_balloon: Comment Review (API, DB, History, Delta)")
                    comment_count = 0
                    for video in videos_data[:5]:  # Limit to first 5 videos for review
                        comments = video.get('comments', [])
                        for idx, comment in enumerate(comments[:5]):  # Limit to first 5 comments per video
                            comment_id = comment.get('comment_id')
                            st.markdown(f"#### Video: {video.get('title', 'Untitled')} — Comment {idx+1}")
                            st.write(":satellite: Comment API Response")
                            st.json(comment)
                            # Fetch DB record
                            db_comment = None
                            try:
                                conn = db.comment_repository
                                db_comment = conn.get_by_id(idx+1)  # This assumes sequential IDs; adjust as needed
                            except Exception:
                                db_comment = None
                            st.write(":inbox_tray: Comment DB Record")
                            st.json(db_comment)
                            # Fetch historical record
                            historical = None
                            try:
                                db_conn = db._get_connection()
                                cursor = db_conn.cursor()
                                cursor.execute('SELECT * FROM comments_history WHERE comment_id = ? ORDER BY fetched_at DESC LIMIT 1', (comment_id,))
                                row = cursor.fetchone()
                                historical = row[-1] if row else None
                                db_conn.close()
                            except Exception:
                                historical = None
                            if historical:
                                st.write(":clock1: Comment Historical Record (Most Recent)")
                                st.json(historical)
                            st.write(":mag: Comment Delta Report (API vs DB)")
                            from src.ui.data_collection.utils.delta_reporting import render_delta_report
                            render_delta_report(comment, db_comment, data_type="comment")
                            st.markdown("---")
                            comment_count += 1
                    if comment_count == 0:
                        st.info("No comments found for review.")
                    # --- NEW: Video Location Review Step ---
                    st.markdown("---")
                    st.subheader(":round_pushpin: Video Location Review (API, DB, History, Delta)")
                    location_count = 0
                    for video in videos_data[:5]:  # Limit to first 5 videos for review
                        locations = video.get('locations', [])
                        for idx, location in enumerate(locations[:5]):  # Limit to first 5 locations per video
                            st.markdown(f"#### Video: {video.get('title', 'Untitled')} — Location {idx+1}")
                            st.write(":satellite: Location API Response")
                            st.json(location)
                            # Fetch DB record
                            db_location = None
                            try:
                                conn = db.location_repository
                                db_location = conn.get_by_id(idx+1)  # This assumes sequential IDs; adjust as needed
                            except Exception:
                                db_location = None
                            st.write(":inbox_tray: Location DB Record")
                            st.json(db_location)
                            # Fetch historical record
                            historical = None
                            try:
                                db_conn = db._get_connection()
                                cursor = db_conn.cursor()
                                cursor.execute('SELECT * FROM video_locations_history WHERE video_id = ? ORDER BY fetched_at DESC LIMIT 1', (video.get('video_id'),))
                                row = cursor.fetchone()
                                historical = row[-1] if row else None
                                db_conn.close()
                            except Exception:
                                historical = None
                            if historical:
                                st.write(":clock1: Location Historical Record (Most Recent)")
                                st.json(historical)
                            st.write(":mag: Location Delta Report (API vs DB)")
                            from src.ui.data_collection.utils.delta_reporting import render_delta_report
                            render_delta_report(location, db_location, data_type="location")
                            st.markdown("---")
                            location_count += 1
                    if location_count == 0:
                        st.info("No video locations found for review.")
            with col2:
                if st.button("Back to Videos Data", key="refresh_back_to_videos_data_btn"):
                    st.session_state['collection_step'] = 2
                    st.session_state['refresh_workflow_step'] = 3
                    st.rerun()
            with col3:
                if st.button("Queue Comments for Later", key="refresh_queue_comments_btn"):
                    from src.utils.queue_tracker import add_to_queue
                    comments_data = [video.get('comments', []) for video in videos_data if video.get('comments')]
                    add_to_queue('comments', channel_id, comments_data)
                    st.success("Comments added to queue for later processing.")
    
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
            self.render_step_2_video_collection()
        elif current_step == 4:
            self.render_step_3_comment_collection()
        else:
            st.error(f"Unknown step: {current_step}")
    
    def _handle_video_collection(self, channel_id, max_videos):
        """
        Helper method to handle video collection process.
        Used for testing and to encapsulate video collection logic.
        
        Args:
            channel_id (str): Channel ID for which to collect videos
            max_videos (int): Maximum number of videos to collect
        """
        import datetime
        from src.utils.video_processor import process_video_data
        from src.utils.video_formatter import fix_missing_views
        
        try:
            # Create options for video collection only
            options = {
                'fetch_channel_data': False,
                'fetch_videos': True,
                'fetch_comments': False,
                'max_videos': max_videos,
                'include_details': True  # Make sure we get all video metrics
            }
            
            # Add API call logging
            debug_log(f"Calling update_channel_data for videos: channel={channel_id}, max_videos={max_videos}")
            
            # Make the API call to get videos
            video_data = self.youtube_service.update_channel_data(
                channel_id,
                options,
                interactive=False
            )
            
            # Add enhanced API status debug info
            debug_log(f"API response for videos: success={video_data is not None}, channel={channel_id}")
            
            # Always set last_api_call
            st.session_state['last_api_call'] = datetime.datetime.now().isoformat()
            
            if video_data and isinstance(video_data, dict):
                # Process the video data to ensure all needed fields are present
                raw_videos = video_data.get('video_id', [])
                debug_log(f"Raw video data count: {len(raw_videos)}")
                
                # Process and fix the video data
                processed_videos = process_video_data(raw_videos)
                debug_log(f"Processed video data count: {len(processed_videos)}")
                fixed_videos = fix_missing_views(processed_videos)
                debug_log(f"Fixed video data count: {len(fixed_videos)}")
                
                # Handle case where videos are stored in a different location
                if not fixed_videos:
                    debug_log("No videos found in video_id field, checking alternative locations")
                    if 'items' in video_data and isinstance(video_data['items'], list):
                        fixed_videos = fix_missing_views(process_video_data(video_data['items']))
                    elif 'videos' in video_data and isinstance(video_data['videos'], list):
                        fixed_videos = fix_missing_views(process_video_data(video_data['videos']))
                
                # Store the processed videos in session state
                st.session_state['videos_data'] = fixed_videos
                st.session_state['videos_fetched'] = True
                
                # Update the video_data with processed videos to ensure consistency
                video_data['video_id'] = fixed_videos
                
                # Store delta information if present
                if 'delta' in video_data:
                    st.session_state['delta'] = video_data['delta']
                
                # Store debug logs and response data
                if 'debug_logs' in video_data:
                    st.session_state['debug_logs'] = video_data['debug_logs']
                if 'response_data' in video_data:
                    st.session_state['response_data'] = video_data['response_data']
                
                # Show success message with video count
                video_count = len(fixed_videos)
                st.success(f"Successfully collected {video_count} videos!")
                
                # Debug log session state to verify data integrity
                debug_log(f"Session state videos_data count: {len(st.session_state['videos_data'])}")
                if len(st.session_state['videos_data']) > 0:
                    sample = st.session_state['videos_data'][0]
                    debug_log(f"Sample video keys: {list(sample.keys())}")
                    debug_log(f"Sample video values - title: {sample.get('title')}, views: {sample.get('views')}, likes: {sample.get('likes')}")
                
                st.rerun()
            else:
                st.error("Failed to fetch videos. Please try again.")
        except Exception as e:
            st.error(f"Error fetching videos: {str(e)}")
            debug_log(f"Error in video collection: {str(e)}")
