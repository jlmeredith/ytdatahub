"""
New channel workflow implementation for data collection.
"""
import streamlit as st
from src.utils.helpers import debug_log
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from .components.video_item import render_video_item
from .utils.data_conversion import format_number
from .utils.error_handling import handle_collection_error
from src.utils.queue_tracker import render_queue_status_sidebar, add_to_queue, get_queue_stats
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.utils.video_standardizer import extract_standardized_videos
from .components.comprehensive_display import render_collapsible_field_explorer, render_channel_overview_card
from src.database.channel_repository import ChannelRepository
from src.ui.data_collection.utils.delta_reporting import render_delta_report
import math
from src.ui.data_collection.components.save_operation_manager import SaveOperationManager

def flatten_dict(d, parent_key='', sep='.'):
    """Recursively flattens a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

class NewChannelWorkflow(BaseCollectionWorkflow):
    """
    Implementation of the workflow for collecting data from a new channel.
    This class follows the interface defined in BaseCollectionWorkflow.
    """
    
    def reset_workflow_state(self):
        """Reset all relevant session state keys for a new workflow."""
        keys_to_clear = [
            'channel_info_temp', 'channel_data_fetched', 'channel_fetch_failed',
            'collection_step', 'videos_fetched', 'comments_fetched',
            'api_data', 'delta_summary', 'debug_logs', 'last_api_call',
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state['collection_step'] = 1
        st.session_state['channel_data_fetched'] = False
        st.session_state['channel_fetch_failed'] = False
        st.session_state['videos_fetched'] = False
        st.session_state['comments_fetched'] = False

    def extract_and_validate_channel_fields(self, raw, channel_id):
        """Extract and validate all required fields from raw_channel_info. Return flat dict or None if invalid."""
        try:
            snippet = raw.get('snippet', {})
            statistics = raw.get('statistics', {})
            content_details = raw.get('contentDetails', {})
            related_playlists = content_details.get('relatedPlaylists', {})
            channel_title = snippet.get('title', '')
            description = snippet.get('description', '')
            published_at = snippet.get('publishedAt', '')
            country = snippet.get('country', '')
            custom_url = snippet.get('customUrl', '')
            default_language = snippet.get('defaultLanguage', '')
            thumbnail_default = snippet.get('thumbnails', {}).get('default', {}).get('url', '')
            thumbnail_medium = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
            thumbnail_high = snippet.get('thumbnails', {}).get('high', {}).get('url', '')
            subscriber_count = statistics.get('subscriberCount', 0)
            view_count = statistics.get('viewCount', 0)
            video_count = statistics.get('videoCount', 0)
            uploads_playlist_id = related_playlists.get('uploads', '')
            # Validate playlist_id
            valid_playlist_id = uploads_playlist_id and uploads_playlist_id.startswith('UU') and uploads_playlist_id != channel_id
            if not (channel_id and channel_title and valid_playlist_id):
                debug_log(f"[VALIDATION ERROR] channel_id={channel_id}, channel_title={channel_title}, uploads_playlist_id={uploads_playlist_id}")
                return None
            return {
                'raw_channel_info': raw,
                'channel_id': channel_id,
                'channel_name': channel_title,  # for summary card
                'channel_title': channel_title, # for DB
                'description': description,
                'published_at': published_at,
                'country': country,
                'custom_url': custom_url,
                'default_language': default_language,
                'thumbnail_default': thumbnail_default,
                'thumbnail_medium': thumbnail_medium,
                'thumbnail_high': thumbnail_high,
                'subscribers': int(subscriber_count) if subscriber_count else 0,
                'views': int(view_count) if view_count else 0,
                'total_videos': int(video_count) if video_count else 0,
                'video_count': int(video_count) if video_count else 0,
                'uploads_playlist_id': uploads_playlist_id,
                'playlist_id': uploads_playlist_id,
            }
        except Exception as e:
            debug_log(f"[EXTRACT ERROR] Exception extracting channel fields: {str(e)}")
            return None

    def initialize_workflow(self, channel_input):
        """
        Initialize the workflow with channel information.
        If the first API call returns None or incomplete data, retry once and log the error.
        """
        debug_log("[WORKFLOW] Entered initialize_workflow")
        if st.session_state.get('channel_input') != channel_input:
            self.reset_workflow_state()
            st.session_state['channel_input'] = channel_input
        db = SQLiteDatabase(SQLITE_DB_PATH)
        existing_data = db.get_channel_data(channel_input)
        debug_log(f"[WORKFLOW] DB check for channel_input={channel_input}: found={existing_data is not None}")
        if not existing_data:
            st.session_state['channel_fetch_failed'] = False
        if st.session_state.get('channel_fetch_failed', False):
            debug_log("[WORKFLOW][ERROR] Channel fetch previously failed. Not retrying.")
            try:
                st.error("Channel fetch previously failed. Please clear the form or enter a new channel.")
            except Exception as e:
                debug_log(f"[WORKFLOW][ERROR] st.error failed: {str(e)}")
            return
        info_temp = st.session_state.get('channel_info_temp')
        info_valid = info_temp and info_temp.get('channel_id') and info_temp.get('playlist_id')
        fetch_attempts = 0
        while not info_valid and channel_input and fetch_attempts < 2:
            with st.spinner("Fetching channel data..."):
                try:
                    channel_info = self.youtube_service.get_basic_channel_info(channel_input)
                    debug_log(f"[WORKFLOW] API fetch for channel_input={channel_input}: result={channel_info}")
                    if channel_info and 'raw_channel_info' in channel_info:
                        raw = channel_info['raw_channel_info']
                        channel_id = raw.get('id')
                        # --- Use robust extraction/validation ---
                        channel_info_temp = self.extract_and_validate_channel_fields(raw, channel_id)
                        if not channel_info_temp:
                            st.error("Could not extract all required channel fields. Please check the channel or try another.")
                            debug_log(f"[WORKFLOW][ERROR] Channel field extraction/validation failed for channel_id={channel_id}")
                            return
                        debug_log(f"[WORKFLOW] Extracted and validated channel_info_temp: {channel_info_temp}")
                        st.session_state['channel_info_temp'] = channel_info_temp
                        st.session_state['channel_data_fetched'] = True
                        st.session_state['api_data'] = channel_info_temp
                        add_to_queue('channels', channel_id, channel_info_temp)
                        debug_log(f"[WORKFLOW] Added channel_id={channel_id} to processing queue. Current queue stats: {get_queue_stats()}")
                        info_valid = True
                    else:
                        fetch_attempts += 1
                        if fetch_attempts == 1:
                            debug_log("[WORKFLOW][ERROR] First fetch failed, retrying once...")
                        else:
                            st.session_state['channel_fetch_failed'] = True
                            st.error("Failed to fetch channel data. Please check the channel ID or URL and try again.")
                            debug_log("[WORKFLOW][ERROR] Channel fetch failed after retry: No valid channel info or playlist_id.")
                            return
                except Exception as e:
                    fetch_attempts += 1
                    if fetch_attempts == 1:
                        debug_log(f"[WORKFLOW][ERROR] Exception fetching channel info: {str(e)}. Retrying once...")
                    else:
                        st.session_state['channel_fetch_failed'] = True
                        st.error(f"Error: {str(e)}")
                        debug_log(f"[WORKFLOW][ERROR] Exception fetching channel info after retry: {str(e)}")
                        return
        debug_log("[WORKFLOW] Exiting initialize_workflow")
    
    def render_step_1_channel_data(self):
        """Render all available channel fields from the DB and API (including all mapped columns and nested fields) in the UI."""
        st.subheader("Step 1: Channel Details")
        channel_info = st.session_state.get('channel_info_temp', {})
        import json
        from src.database.sqlite import SQLiteDatabase
        db = SQLiteDatabase(SQLITE_DB_PATH)

        # --- PATCH: Only use raw_channel_info for display ---
        raw_info = channel_info.get('raw_channel_info')
        if isinstance(raw_info, str):
            try:
                raw_info = json.loads(raw_info)
            except Exception:
                st.error("Failed to parse raw_channel_info as JSON.")
                return
        # Debug output: print type and keys of raw_channel_info
        st.write(f"**DEBUG:** type(raw_channel_info) = {type(raw_info)}")
        if isinstance(raw_info, dict):
            st.write(f"**DEBUG:** raw_channel_info keys = {list(raw_info.keys())}")
        else:
            st.write(f"**DEBUG:** raw_channel_info value = {raw_info}")
        if not isinstance(raw_info, dict):
            st.error("No valid raw_channel_info found. Cannot display full API response.")
            return
        full_api_response = raw_info

        # Flatten everything for table display
        flat = flatten_dict(full_api_response)
        # Show as table for exportability
        st.write("### All Channel Fields (Flat Table)")
        st.dataframe([{k: v for k, v in flat.items()}])
        # Show summary card and collapsible explorer instead of raw st.json
        st.write("### Channel Overview")
        render_channel_overview_card(channel_info)
        render_collapsible_field_explorer(full_api_response, "All Channel Fields (Collapsible)")
        # Buttons for save, continue, and queue
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Channel Data", key="save_channel_data_btn"):
                with st.spinner("Saving channel data..."):
                    try:
                        channel_data = st.session_state.get('channel_info_temp', {})
                        debug_log(f"[WORKFLOW] Saving new channel (validated fields): {channel_data}")
                        save_manager = SaveOperationManager()
                        success = save_manager.perform_save_operation(
                            youtube_service=self.youtube_service,
                            api_data=channel_data,
                            total_videos=0,
                            total_comments=0
                        )
                        debug_log(f"[WORKFLOW] Save result for channel_id={channel_data.get('channel_id')}: {success}")
                        if success:
                            st.session_state['channel_data_saved'] = True
                            db_repo = ChannelRepository(SQLITE_DB_PATH)
                            db_record = db_repo.get_channel_data(channel_data.get('channel_id'))
                            debug_log(f"[WORKFLOW] DB record after save: {db_record}")
                            st.markdown("---")
                            st.subheader(":inbox_tray: Database Record (Post-Save)")
                            st.json(db_record)
                            st.subheader(":satellite: API Response (Just Saved)")
                            st.json(channel_data.get('raw_channel_info'))
                            st.subheader(":mag: Delta Report (API vs DB)")
                            render_delta_report(channel_data.get('raw_channel_info'), db_record.get('raw_channel_info'), data_type="channel")
                            st.markdown("---")
                            st.info(":arrow_down: Proceeding to Playlist Review...")
                            debug_log("[WORKFLOW] Advancing to playlist review step after successful channel save.")
                            st.session_state['collection_step'] = 2
                            st.rerun()
                        else:
                            st.error("Failed to save data.")
                    except Exception as e:
                        st.error(f"Error saving data: {str(e)}")
                        debug_log(f"Error saving channel data: {str(e)}")
        with col2:
            if st.button("Continue to Videos Data", key="continue_to_videos_btn"):
                channel_info = st.session_state.get('channel_info_temp', {})
                playlist_id = channel_info.get('playlist_id')
                debug_log(f"[WORKFLOW] Continue to videos: using playlist_id={playlist_id} for channel_id={channel_info.get('channel_id')}")
                st.session_state['collection_step'] = 2
                st.rerun()
        with col3:
            if st.button("Save to Queue for Later", key="queue_channel_btn"):
                channel_data = st.session_state.get('channel_info_temp', {})
                add_to_queue('channels', channel_data.get('channel_id'), channel_data)
                st.success("Channel added to queue for later processing.")
    
    def render_step_2_playlist_review(self):
        """Render playlist review step: show API, DB, and delta for playlist, with explicit user control."""
        st.subheader("Step 2: Playlist Review")
        channel_info = st.session_state.get('channel_info_temp', {})
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
        render_delta_report(playlist_api, db_playlist, data_type="playlist")
        # --- User Controls ---
        if 'playlist_saved' not in st.session_state:
            st.session_state['playlist_saved'] = False
        if 'playlist_queued' not in st.session_state:
            st.session_state['playlist_queued'] = False
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Playlist Data", key="save_playlist_data_btn", disabled=st.session_state['playlist_saved'] or st.session_state['playlist_queued']):
                playlist_save_success = self.youtube_service.save_playlist_data(playlist_api)
                if playlist_save_success:
                    st.session_state['playlist_saved'] = True
                    st.success("Playlist data saved to database.")
                else:
                    st.error("Failed to save playlist data to database.")
        with col2:
            if st.button("Queue Playlist for Later", key="queue_playlist_btn", disabled=st.session_state['playlist_saved'] or st.session_state['playlist_queued']):
                add_to_queue('playlists', playlist_id, playlist_api)
                st.session_state['playlist_queued'] = True
                st.success("Playlist added to queue for later processing.")
        with col3:
            if st.button("Continue to Videos Data", key="continue_to_videos_btn2", disabled=not (st.session_state['playlist_saved'] or st.session_state['playlist_queued'])):
                st.session_state['collection_step'] = 2
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 2: Collect and display video data, with queue option."""
        st.subheader("Step 2: Videos Data")
        render_queue_status_sidebar()
        self.show_progress_indicator(2)
        channel_info = st.session_state.get('channel_info_temp', {})
        channel_id = channel_info.get('channel_id', '')
        videos_data = channel_info.get('video_id', []) if 'video_id' in channel_info else []
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
            if st.button("← Previous Videos", disabled=st.session_state['video_page'] <= 0, key="video_prev_page_btn"):
                st.session_state['video_page'] -= 1
                st.rerun()
        with col_v2:
            st.write(f"Page {st.session_state['video_page']+1} of {total_video_pages}")
        with col_v3:
            if st.button("Next Videos →", disabled=st.session_state['video_page'] >= total_video_pages-1, key="video_next_page_btn"):
                st.session_state['video_page'] += 1
                st.rerun()

        for idx, video in enumerate(paginated_videos):
            video_id = video.get('video_id')
            st.markdown(f"#### Video {start_idx+idx+1}: {video.get('title', 'Untitled')}")
            st.write(":satellite: Video API Response")
            st.json(video)
            # Fetch DB record
            db_video = None
            try:
                conn = db.video_repository
                db_video = conn.get_by_id(idx+1)  # This assumes sequential IDs; adjust as needed
            except Exception:
                db_video = None
            st.write(":inbox_tray: Video DB Record")
            st.json(db_video)
            # Fetch historical record
            historical = None
            try:
                db_conn = db._get_connection()
                cursor = db_conn.cursor()
                cursor.execute('SELECT * FROM videos_history WHERE video_id = ? ORDER BY fetched_at DESC LIMIT 1', (video_id,))
                row = cursor.fetchone()
                historical = row[-1] if row else None
                db_conn.close()
            except Exception:
                historical = None
            if historical:
                st.write(":clock1: Video Historical Record (Most Recent)")
                st.json(historical)
            st.write(":mag: Video Delta Report (API vs DB)")
            from src.ui.data_collection.utils.delta_reporting import render_delta_report
            render_delta_report(video, db_video, data_type="video")
            st.markdown("---")
        # --- PAGINATION for comments ---
        st.markdown("---")
        st.subheader(":speech_balloon: Comment Review (API, DB, History, Delta)")
        all_comments = []
        for video in videos_data:
            comments = video.get('comments', [])
            for comment in comments:
                all_comments.append((video, comment))
        total_comments = len(all_comments)
        comments_per_page = 10
        total_comment_pages = max(1, math.ceil(total_comments / comments_per_page))
        if 'comment_page' not in st.session_state:
            st.session_state['comment_page'] = 0
        c_start = st.session_state['comment_page'] * comments_per_page
        c_end = min(c_start + comments_per_page, total_comments)
        paginated_comments = all_comments[c_start:c_end]
        st.write(f"Showing comments {c_start+1}-{c_end} of {total_comments}")
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c1:
            if st.button("← Previous Comments", disabled=st.session_state['comment_page'] <= 0, key="comment_prev_page_btn"):
                st.session_state['comment_page'] -= 1
                st.rerun()
        with col_c2:
            st.write(f"Page {st.session_state['comment_page']+1} of {total_comment_pages}")
        with col_c3:
            if st.button("Next Comments →", disabled=st.session_state['comment_page'] >= total_comment_pages-1, key="comment_next_page_btn"):
                st.session_state['comment_page'] += 1
                st.rerun()
        comment_count = 0
        for video, comment in paginated_comments:
            comment_id = comment.get('comment_id')
            st.markdown(f"#### Video: {video.get('title', 'Untitled')} — Comment {comment_count+1}")
            st.write(":satellite: Comment API Response")
            st.json(comment)
            db_comment = None
            try:
                conn = db.comment_repository
                db_comment = conn.get_by_id(comment_count+1)
            except Exception:
                db_comment = None
            st.write(":inbox_tray: Comment DB Record")
            st.json(db_comment)
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
        for video in videos_data[:5]:
            locations = video.get('locations', [])
            for idx, location in enumerate(locations[:5]):
                st.markdown(f"#### Video: {video.get('title', 'Untitled')} — Location {idx+1}")
                st.write(":satellite: Location API Response")
                st.json(location)
                db_location = None
                try:
                    conn = db.location_repository
                    db_location = conn.get_by_id(idx+1)
                except Exception:
                    db_location = None
                st.write(":inbox_tray: Location DB Record")
                st.json(db_location)
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
    
    def render_step_3_comment_collection(self):
        """Render step 3: Collect and display comment data, with queue option."""
        st.subheader("Step 3: Comments Data")
        render_queue_status_sidebar()  # Show queue in sidebar (only once)
        self.show_progress_indicator(3)
        channel_info = st.session_state.get('channel_info_temp', {})
        channel_id = channel_info.get('channel_id', '')
        videos = channel_info.get('video_id', [])
        debug_logs = st.session_state.get('debug_logs', [])
        if not st.session_state.get('comments_fetched', False):
            if not videos:
                st.warning("No videos available for comment collection. Please go back to the video collection step.")
                if st.button("Back to Video Collection"):
                    st.session_state['collection_step'] = 2
                    st.rerun()
                return
            max_comments = st.slider(
                "Maximum number of comments to fetch per video",
                min_value=0,
                max_value=100,
                value=20,
                help="Set to 0 to skip comment collection"
            )
            if st.button("Fetch Comments from API"):
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
                            'max_comments_per_video': max_comments
                        }
                        updated_data = self.youtube_service.collect_channel_data(
                            channel_id,
                            options,
                            existing_data=channel_info
                        )
                        st.session_state['api_initialized'] = True
                        debug_logs.append(f"API call made to fetch comments for {channel_id}")
                        st.session_state['debug_logs'] = debug_logs
                        st.session_state['last_api_call'] = updated_data.get('last_api_call') if updated_data else None
                        if updated_data and 'video_id' in updated_data:
                            st.session_state['channel_info_temp']['video_id'] = updated_data['video_id']
                            st.session_state['comments_fetched'] = True
                            total_comments = sum(len(video.get('comments', [])) for video in updated_data['video_id'])
                            summary = [f"Total comments fetched: {total_comments}"]
                            st.session_state['delta_summary'] = summary
                            st.success("Successfully fetched comments!")
                            # Add comments to queue for later
                            comments_data = [video.get('comments', []) for video in updated_data['video_id'] if video.get('comments')]
                            add_to_queue('comments', channel_id, comments_data)
                            st.success("Comments added to queue for later processing.")
                            st.rerun()
                        else:
                            st.error("Failed to fetch comments. Please try again.")
        else:
            total_comments = sum(len(video.get('comments', [])) for video in videos)
            videos_with_comments = sum(1 for video in videos if video.get('comments'))
            st.write(f"Successfully fetched {total_comments} comments from {videos_with_comments} videos.")
            videos_with_comments_list = [v for v in videos if v.get('comments')]
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
                if st.button("Complete and Save Data", key="complete_and_save_data_btn"):
                    self.save_data()
            with col2:
                if st.button("Back to Videos Data", key="back_to_videos_btn"):
                    st.session_state['collection_step'] = 2
                    st.rerun()
            with col3:
                if st.button("Queue Comments for Later", key="queue_comments_btn"):
                    comments_data = [video.get('comments', []) for video in videos if video.get('comments')]
                    add_to_queue('comments', channel_id, comments_data)
                    st.success("Comments added to queue for later processing.")
    
    def save_data(self):
        """Save collected data to the database using SaveOperationManager for standardized feedback."""
        channel_info = st.session_state.get('channel_info_temp')
        if not channel_info:
            st.error("No data to save.")
            return
        with st.spinner("Saving data to database..."):
            try:
                save_manager = SaveOperationManager()
                success = save_manager.perform_save_operation(
                    youtube_service=self.youtube_service,
                    api_data=channel_info,
                    total_videos=len(channel_info.get('video_id', [])) if 'video_id' in channel_info else 0,
                    total_comments=sum(len(video.get('comments', [])) for video in channel_info.get('video_id', [])) if 'video_id' in channel_info else 0
                )
                if success:
                    st.info("Comments saved successfully!")
                    total_comments = sum(len(video.get('comments', [])) for video in channel_info.get('video_id', []))
                    videos_with_comments = sum(1 for video in channel_info.get('video_id', []) if video.get('comments'))
                    if total_comments > 0:
                        st.success(f"✅ Saved {total_comments} comments from {videos_with_comments} videos.")
                    else:
                        st.success("Channel and video data saved successfully!")
                    debug_log(f"Data save operation successful, saved channel: {channel_info.get('channel_id')} with {total_comments} comments")
                    if st.button("Go to Data Storage Tab"):
                        st.session_state['main_tab'] = "data_storage"
                        st.rerun()
                else:
                    st.error("Failed to save data.")
            except Exception as e:
                handle_collection_error(e, "saving data")

    def render_current_step(self):
        """
        Render only the current step as expanded, all others collapsed/hidden.
        """
        current_step = st.session_state.get('collection_step', 1)
        if current_step == 1:
            # Render directly to avoid nested expanders
            self.render_step_1_channel_data()
            with st.expander("Step 2: Playlist Review", expanded=False):
                pass
            with st.expander("Step 2: Videos Data", expanded=False):
                pass
            with st.expander("Step 3: Comments Data", expanded=False):
                pass
        elif current_step == 2:
            with st.expander("Step 1: Channel Details", expanded=False):
                pass
            self.render_step_2_playlist_review()
            with st.expander("Step 2: Videos Data", expanded=False):
                pass
            with st.expander("Step 3: Comments Data", expanded=False):
                pass
        elif current_step == 3:
            with st.expander("Step 1: Channel Details", expanded=False):
                pass
            with st.expander("Step 2: Playlist Review", expanded=False):
                pass
            self.render_step_2_video_collection()
            with st.expander("Step 3: Comments Data", expanded=False):
                pass
        elif current_step == 4:
            with st.expander("Step 1: Channel Details", expanded=False):
                pass
            with st.expander("Step 2: Playlist Review", expanded=False):
                pass
            with st.expander("Step 2: Videos Data", expanded=False):
                pass
            self.render_step_3_comment_collection()
