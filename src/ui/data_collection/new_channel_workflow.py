"""
New channel workflow implementation for data collection.
"""
import streamlit as st
from src.utils.debug_utils import debug_log
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from .components.video_item import render_video_item, render_video_table_row
from .utils.data_conversion import format_number
from .utils.error_handling import handle_collection_error
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.utils.video_standardizer import extract_standardized_videos, standardize_video_data
from .components.comprehensive_display import render_collapsible_field_explorer, render_channel_overview_card
from src.database.channel_repository import ChannelRepository
from src.ui.data_collection.utils.delta_reporting import render_delta_report
import math
from src.ui.data_collection.components.save_operation_manager import SaveOperationManager
from src.ui.data_collection.components.video_selection_table import render_video_selection_table
from src.utils.data_collection.channel_normalizer import normalize_channel_data_for_save

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
            'new_channel_max_videos',
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
                        debug_log(f"[WORKFLOW] Channel data ready for channel_id={channel_id}")
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
        """Render channel data in a clean, user-friendly format."""
        st.subheader("Step 1: Channel Details")
        self.show_progress_indicator(1)
        
        channel_info = st.session_state.get('channel_info_temp', {})
        
        if not channel_info:
            st.warning("No channel data available. Please fetch channel data first.")
            return
            
        # Show channel overview in a clean format
        st.write("### Channel Overview")
        render_channel_overview_card(channel_info)
        
        # Get raw channel info
        raw_info = channel_info.get('raw_channel_info')
        if raw_info:
            import json
            if isinstance(raw_info, str):
                try:
                    raw_info = json.loads(raw_info)
                except Exception:
                    st.error("Error parsing channel data.")
                    return
            
            # Advanced field explorer - only visible if explicitly expanded by user
            with st.expander("Advanced: View All Channel Fields", expanded=False):
                if isinstance(raw_info, dict):
                    render_collapsible_field_explorer(raw_info, "Channel Fields", no_expander=True)
        
        # Store raw/delta in debug state
        if 'debug_raw_data' not in st.session_state:
            st.session_state['debug_raw_data'] = {}
        if 'debug_delta_data' not in st.session_state:
            st.session_state['debug_delta_data'] = {}
        st.session_state['debug_raw_data']['channel'] = {
            'api': raw_info,
            'db': None  # No DB in new channel step
        }
        st.session_state['debug_delta_data']['channel'] = {
            'delta': None  # If you have a delta, store it here
        }
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔙 Back", key="channel_data_back_btn"):
                # Clear temporary data
                if 'channel_info_temp' in st.session_state:
                    del st.session_state['channel_info_temp']
                # Go back to channel input
                st.session_state['collection_step'] = 1
                st.rerun()
        with col2:
            if st.button("📥 Save Channel", key="save_channel_btn"):
                # Save channel to database
                try:
                    # Normalize the channel data before saving to ensure consistent format
                    normalized_data = normalize_channel_data_for_save(channel_info, "new_channel")
                    
                    save_manager = SaveOperationManager()
                    success = save_manager.perform_save_operation(
                        youtube_service=self.youtube_service,
                        api_data=normalized_data,
                        total_videos=0,  # No videos yet
                        total_comments=0  # No comments yet
                    )
                    if success:
                        st.session_state['channel_data_saved'] = True
                        st.success("Channel data saved successfully!")
                        st.session_state['collection_step'] = 2
                        st.rerun()
                except Exception as e:
                    st.error(f"Error saving channel data: {str(e)}")
            if st.button("▶️ Continue to Videos", key="continue_to_videos_btn"):
                st.session_state['collection_step'] = 2
                st.rerun()
    
    def render_step_2_playlist_review(self):
        """Render playlist review step in a user-friendly way."""
        st.subheader("Step 2: Playlist Review")
        
        channel_info = st.session_state.get('channel_info_temp', {})
        playlist_id = channel_info.get('playlist_id')
        
        if not playlist_id:
            st.info("📋 No playlist found for this channel.")
            # Skip to videos step
            if st.button("Continue to Videos Data", key="skip_to_videos_btn"):
                st.session_state['collection_step'] = 2
                st.rerun()
            return
        
        # Fetch playlist API response (from session or API)
        playlist_api = st.session_state.get('playlist_api_data')
        if not playlist_api:
            try:
                with st.spinner("Fetching playlist information..."):
                    playlist_api = self.youtube_service.get_playlist_info(playlist_id)
                    st.session_state['playlist_api_data'] = playlist_api
            except Exception as e:
                st.error(f"❌ Error fetching playlist data: {str(e)}")
                return
        
        # Prepare playlist data for saving
        if playlist_api:
            if 'id' in playlist_api:
                playlist_api['playlist_id'] = playlist_api['id']
            if 'snippet' in playlist_api and 'channelId' in playlist_api['snippet']:
                playlist_api['channel_id'] = playlist_api['snippet']['channelId']
        
        # Show playlist summary (user-friendly)
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
        
        # Store raw/delta in debug state
        if 'debug_raw_data' not in st.session_state:
            st.session_state['debug_raw_data'] = {}
        if 'debug_delta_data' not in st.session_state:
            st.session_state['debug_delta_data'] = {}
        st.session_state['debug_raw_data']['playlist'] = {
            'db': None,  # No DB in new channel step
            'api': playlist_api
        }
        st.session_state['debug_delta_data']['playlist'] = {
            'delta': None
        }
        
        # Initialize session state for playlist actions
        if 'playlist_saved' not in st.session_state:
            st.session_state['playlist_saved'] = False
        if 'playlist_queued' not in st.session_state:
            st.session_state['playlist_queued'] = False
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Playlist Data", key="save_playlist_data_btn", 
                        disabled=st.session_state['playlist_saved'] or st.session_state['playlist_queued']):
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
            if st.button("📋 Save Playlist Data", key="save_playlist_btn", 
                        disabled=st.session_state['playlist_saved']):
                try:
                    debug_log(f"[WORKFLOW] Playlist data saved for playlist_id={playlist_id}")
                    st.session_state['playlist_saved'] = True
                    st.success("✅ Playlist data saved!")
                except Exception as e:
                    st.error(f"❌ Error saving playlist data: {str(e)}")
                    
        with col3:
            if st.button("▶️ Continue to Videos", key="continue_to_videos_btn2", 
                        disabled=not (st.session_state['playlist_saved'] or st.session_state['playlist_queued'])):
                st.session_state['collection_step'] = 3
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 2: Collect and display video data in a user-friendly way."""
        st.subheader("Step 2: Videos Data")
        self.show_progress_indicator(2)
        
        channel_info = st.session_state.get('channel_info_temp', {})
        channel_id = channel_info.get('channel_id', '')
        videos_data = channel_info.get('video_id', []) if 'video_id' in channel_info else []
        
        # Standardize video data if we have videos
        if videos_data:
            debug_log(f"[NEW CHANNEL] Before standardization: videos_data type={type(videos_data)}, length={len(videos_data) if isinstance(videos_data, list) else 'not a list'}")
            if videos_data and len(videos_data) > 0:
                first_video = videos_data[0]
                debug_log(f"[NEW CHANNEL] First video before standardization: type={type(first_video)}")
                if isinstance(first_video, dict):
                    debug_log(f"[NEW CHANNEL] First video keys: {list(first_video.keys())}")
                    debug_log(f"[NEW CHANNEL] First video sample: {str(first_video)[:300]}...")
                    # Check all possible video ID locations
                    debug_log(f"[NEW CHANNEL] video_id field: {first_video.get('video_id')}")
                    debug_log(f"[NEW CHANNEL] id field: {first_video.get('id')}")
                    debug_log(f"[NEW CHANNEL] youtube_id field: {first_video.get('youtube_id')}")
            
            videos_data = standardize_video_data(videos_data)
            debug_log(f"[NEW CHANNEL] After standardization: videos_data length={len(videos_data)}")
        
        # Store raw/delta in debug state
        if 'debug_raw_data' not in st.session_state:
            st.session_state['debug_raw_data'] = {}
        if 'debug_delta_data' not in st.session_state:
            st.session_state['debug_delta_data'] = {}
        st.session_state['debug_raw_data']['video'] = {
            'db': None,  # No DB in new channel step
            'api': videos_data
        }
        st.session_state['debug_delta_data']['video'] = {
            'delta': None
        }
        
        # Check if videos have been fetched
        if not st.session_state.get('videos_fetched', False):
            # Video collection configuration phase
            st.info("📹 Ready to collect videos from this channel")
            
            # Get total video count from multiple possible sources
            total_videos_in_channel = 'Unknown'
            
            # Method 1: From channel statistics (most reliable)
            if 'channel_info' in channel_info and 'statistics' in channel_info['channel_info']:
                stats = channel_info['channel_info']['statistics']
                if 'videoCount' in stats:
                    total_videos_in_channel = int(stats['videoCount'])
            
            # Method 2: From direct total_videos field (fallback)
            elif 'total_videos' in channel_info and channel_info['total_videos'] != 'Unknown':
                total_videos_in_channel = channel_info['total_videos']
            
            # Method 3: From any other statistics location
            elif 'statistics' in channel_info and 'videoCount' in channel_info['statistics']:
                total_videos_in_channel = int(channel_info['statistics']['videoCount'])
            
            # Display total video count with better formatting
            if total_videos_in_channel != 'Unknown':
                st.markdown(f"### 📊 Channel Video Information")
                st.success(f"This channel has **{total_videos_in_channel:,}** total videos available for import")
                
                # Add quota estimation for large channels
                if total_videos_in_channel > 1000:
                    st.warning(f"⚠️ Large channel detected! Importing all {total_videos_in_channel:,} videos will use significant API quota.")
                elif total_videos_in_channel > 100:
                    st.info(f"💡 Medium-sized channel. Consider if you need all {total_videos_in_channel:,} videos or just recent ones.")
            else:
                st.markdown(f"### 📊 Channel Video Information")
                st.info("📈 Total video count will be determined during import")
            
            # Import all videos checkbox
            import_all_videos = st.checkbox(
                "📥 Import All Available Videos", 
                value=False,
                help="Check this to import all videos from the channel. This will override the slider setting below."
            )
            
            # Video collection controls
            if import_all_videos:
                # When import all is selected, show the total and disable slider
                max_videos = 0  # 0 means fetch all videos
                if total_videos_in_channel != 'Unknown':
                    st.info(f"✅ **All {total_videos_in_channel:,} videos** will be imported from this channel")
                else:
                    st.info(f"✅ **All available videos** will be imported from this channel")
                
                # Show disabled slider for reference, matching the actual video count
                slider_max = total_videos_in_channel if isinstance(total_videos_in_channel, int) else 500
                st.slider(
                    "Number of videos to fetch",
                    min_value=0,
                    max_value=slider_max,
                    value=slider_max,
                    disabled=True,
                    help="Slider is disabled when 'Import All Available Videos' is checked"
                )
            else:
                # Normal slider mode
                session_key = 'new_channel_max_videos'
                # Determine slider max and default based on channel video count
                if isinstance(total_videos_in_channel, int):
                    slider_max = min(500, total_videos_in_channel)
                    slider_default = min(50, total_videos_in_channel)
                else:
                    slider_max = 500
                    slider_default = 50
                # Set default in session state if not already set
                if session_key not in st.session_state:
                    st.session_state[session_key] = slider_default
                # Add UI note if channel has fewer than 500 videos
                if isinstance(total_videos_in_channel, int) and total_videos_in_channel < 500:
                    st.info(f"This channel has only {total_videos_in_channel} videos. Slider is capped at this value.")
                # Use the slider with key parameter to automatically update session_state
                max_videos = st.slider(
                    "Number of videos to fetch",
                    min_value=0,
                    max_value=slider_max,
                    value=st.session_state[session_key],
                    key=session_key,
                    help="Set to 0 to skip video collection, or choose how many videos to fetch from the channel"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Dynamic button text based on import choice
                if import_all_videos:
                    if total_videos_in_channel != 'Unknown':
                        button_text = f"🚀 Import All {total_videos_in_channel:,} Videos"
                    else:
                        button_text = "🚀 Import All Available Videos"
                elif max_videos == 0:
                    button_text = "⏭️ Skip Video Collection"
                else:
                    button_text = f"🚀 Fetch {max_videos} Videos from API"
                
                if st.button(button_text, key="fetch_videos_btn", type="primary"):
                    if max_videos == 0 and not import_all_videos:
                        st.info("📹 Video collection skipped as requested.")
                        st.session_state['videos_fetched'] = True
                        st.rerun()
                    else:
                        # Determine actual max_videos for API call
                        actual_max_videos = 0 if import_all_videos else st.session_state.get('new_channel_max_videos', max_videos)
                        debug_log(f"[VIDEO FETCH] Using max_videos={actual_max_videos} (import_all={import_all_videos}, slider={max_videos})")
                        
                        # Show appropriate spinner message
                        if import_all_videos:
                            if total_videos_in_channel != 'Unknown':
                                spinner_msg = f"Importing all {total_videos_in_channel:,} videos from YouTube API... This may take a while."
                            else:
                                spinner_msg = "Importing all available videos from YouTube API... This may take a while."
                        else:
                            spinner_msg = f"Fetching {max_videos} videos from YouTube API..."
                        
                        with st.spinner(spinner_msg):
                            try:
                                options = {
                                    'fetch_channel_data': False,
                                    'fetch_videos': True,
                                    'fetch_comments': False,
                                    'max_videos': actual_max_videos
                                }
                                updated_data = self.youtube_service.collect_channel_data(
                                    channel_id,
                                    options,
                                    existing_data=channel_info
                                )
                                
                                # Debug logging to understand what's being returned
                                debug_log(f"[VIDEO FETCH DEBUG] updated_data type: {type(updated_data)}")
                                debug_log(f"[VIDEO FETCH DEBUG] updated_data is None: {updated_data is None}")
                                if updated_data:
                                    debug_log(f"[VIDEO FETCH DEBUG] updated_data keys: {list(updated_data.keys()) if isinstance(updated_data, dict) else 'Not a dict'}")
                                    if 'video_id' in updated_data:
                                        debug_log(f"[VIDEO FETCH DEBUG] video_id length: {len(updated_data['video_id'])}")
                                    else:
                                        debug_log(f"[VIDEO FETCH DEBUG] 'video_id' key not found in response")
                                    if 'error_videos' in updated_data:
                                        debug_log(f"[VIDEO FETCH DEBUG] error_videos: {updated_data['error_videos']}")
                                else:
                                    debug_log(f"[VIDEO FETCH DEBUG] updated_data is falsy: {updated_data}")
                                
                                if updated_data and 'video_id' in updated_data and updated_data['video_id']:
                                    st.session_state['channel_info_temp']['video_id'] = updated_data['video_id']
                                    st.session_state['videos_fetched'] = True
                                    
                                    total_videos = len(updated_data['video_id'])
                                    
                                    # Show success message with context
                                    if import_all_videos:
                                        if total_videos_in_channel != 'Unknown':
                                            st.success(f"✅ Successfully imported **{total_videos:,}** out of **{total_videos_in_channel:,}** available videos!")
                                            if total_videos < total_videos_in_channel:
                                                st.info(f"ℹ️ Some videos may be private, unlisted, or unavailable. Got {total_videos:,} of {total_videos_in_channel:,} total.")
                                        else:
                                            st.success(f"✅ Successfully imported **{total_videos:,}** videos (all available videos)!")
                                    else:
                                        st.success(f"✅ Successfully fetched **{total_videos:,}** videos!")
                                    st.rerun()
                                else:
                                    # More detailed error reporting
                                    error_msg = "❌ Failed to fetch videos."
                                    if updated_data:
                                        if 'error_videos' in updated_data:
                                            error_msg += f" Error: {updated_data['error_videos']}"
                                        elif 'video_id' not in updated_data:
                                            error_msg += " No video data returned from API."
                                        elif not updated_data['video_id']:
                                            error_msg += " No videos found for this channel."
                                        else:
                                            error_msg += " Unknown issue with API response."
                                    else:
                                        error_msg += " API returned no data."
                                    st.error(error_msg)
                            except Exception as e:
                                debug_log(f"[VIDEO FETCH EXCEPTION] {str(e)}")
                                st.error(f"❌ Error fetching videos: {str(e)}")
                                
            with col2:
                if st.button("⏭️ Skip Videos", key="skip_videos_btn"):
                    st.session_state['videos_fetched'] = True
                    st.info("📹 Video collection skipped.")
                    st.rerun()
                    
        else:
            # Videos have been fetched, show them in the new AgGrid table
            if not videos_data:
                st.info("📹 No videos were fetched for this channel.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Fetch Videos", key="refetch_videos_btn"):
                        st.session_state['videos_fetched'] = False
                        st.rerun()
                with col2:
                    if st.button("Continue to Comments", key="continue_to_comments_btn"):
                        st.session_state['collection_step'] = 4
                        st.rerun()
                return

            # Use the new AgGrid-based video selection table
            selection_result = render_video_selection_table(
                videos_data, 
                selected_ids=st.session_state.get('selected_video_ids', []),
                key="new_channel_video_selection"
            )
            selected_video_ids = selection_result.get("selected_ids", [])
            st.session_state['selected_video_ids'] = selected_video_ids

            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save Selected Videos Data", key="save_videos_btn"):
                    if not selected_video_ids:
                        st.warning("Please select at least one video to save.")
                    else:
                        try:
                            save_manager = SaveOperationManager()
                            # Only save selected videos
                            selected_videos = [v for v in videos_data if v.get('video_id') in selected_video_ids]
                            channel_info['video_id'] = selected_videos
                            success = save_manager.perform_save_operation(
                                youtube_service=self.youtube_service,
                                api_data=channel_info,
                                total_videos=len(selected_videos)
                            )
                            if success:
                                st.session_state['videos_data_saved'] = True
                                st.success("Selected video data saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving selected videos: {str(e)}")
            with col2:
                if st.button("Continue to Comments", key="continue_to_comments_btn"):
                    if not selected_video_ids:
                        st.warning("Please select at least one video to continue.")
                    else:
                        # Only keep selected videos for next step
                        channel_info['video_id'] = [v for v in videos_data if v.get('video_id') in selected_video_ids]
                        st.session_state['channel_info_temp'] = channel_info
                        st.session_state['collection_step'] = 4
                        st.rerun()
            with col3:
                if st.button("🔄 Refetch Videos", key="refetch_videos_btn"):
                    st.session_state['videos_fetched'] = False
                    st.rerun()
    
    def render_step_3_comment_collection(self):
        """Render step 3: Collect and display comment data in a user-friendly way."""
        st.subheader("Step 3: Comments Data")
        self.show_progress_indicator(3)
        
        channel_info = st.session_state.get('channel_info_temp', {})
        channel_id = channel_info.get('channel_id', '')
        videos = channel_info.get('video_id', [])
        
        if not videos:
            st.warning("⚠️ No videos available for comment collection. Please go back to the video collection step.")
            if st.button("Back to Video Collection"):
                st.session_state['collection_step'] = 3
                st.rerun()
            return
        
        # Check if comments are already fetched
        if not st.session_state.get('comments_fetched', False):
            st.info("💬 Ready to collect comments from YouTube videos")
            
            # Show video summary
            total_videos = len(videos)
            st.write(f"📹 Found **{total_videos}** videos to collect comments from")
            
            # Add comment import controls above the video table
            st.markdown("### Comment Import Controls")
            max_top_level_comments = st.slider(
                "Top-Level Comments Per Video",
                min_value=0,
                max_value=100,
                value=st.session_state.get('max_top_level_comments', 20),
                key='max_top_level_comments',
                help="Maximum number of top-level comments to import per video (0 to skip comments)"
            )
            max_replies_per_comment = st.slider(
                "Replies Per Top-Level Comment",
                min_value=0,
                max_value=50,
                value=st.session_state.get('max_replies_per_comment', 5),
                key='max_replies_per_comment',
                help="Maximum number of replies to fetch for each top-level comment"
            )
            st.caption("Adjust these to control comment import granularity before proceeding.")
            
            # Comment collection controls
            max_comments = st.slider(
                "Maximum number of comments to fetch per video",
                min_value=0,
                max_value=100,
                value=20,
                help="Set to 0 to skip comment collection entirely"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Fetch Comments from API", key="fetch_comments_btn", type="primary"):
                    if max_comments == 0:
                        st.info("💬 Comment collection skipped as requested.")
                        st.session_state['comments_fetched'] = True
                        st.rerun()
                    else:
                        with st.spinner(f"Fetching up to {max_comments} comments per video from YouTube API..."):
                            try:
                                options = {
                                    'fetch_channel_data': False,
                                    'fetch_videos': False,
                                    'fetch_comments': True,
                                    'max_comments_per_video': max_comments,
                                    'max_top_level_comments': max_top_level_comments,
                                    'max_replies_per_comment': max_replies_per_comment
                                }
                                updated_data = self.youtube_service.collect_channel_data(
                                    channel_id,
                                    options,
                                    existing_data=channel_info
                                )
                                
                                if updated_data and 'video_id' in updated_data:
                                    st.session_state['channel_info_temp']['video_id'] = updated_data['video_id']
                                    st.session_state['comments_fetched'] = True
                                    
                                    total_comments = sum(len(video.get('comments', [])) for video in updated_data['video_id'])
                                    videos_with_comments = sum(1 for video in updated_data['video_id'] if video.get('comments'))
                                    
                                    st.success(f"✅ Successfully fetched **{total_comments}** comments from **{videos_with_comments}** videos!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to fetch comments. Please try again.")
                            except Exception as e:
                                st.error(f"❌ Error fetching comments: {str(e)}")
                                
            with col2:
                if st.button("⏭️ Skip Comments", key="skip_comments_btn"):
                    st.session_state['comments_fetched'] = True
                    st.info("💬 Comment collection skipped.")
                    st.rerun()
        else:
            # Comments have been fetched, show summary
            total_comments = sum(len(video.get('comments', [])) for video in videos)
            videos_with_comments = sum(1 for video in videos if video.get('comments'))
            videos_without_comments = len(videos) - videos_with_comments
            
            # Display results summary
            if total_comments > 0:
                st.success(f"✅ Successfully collected **{total_comments}** comments from **{videos_with_comments}** videos")
                if videos_without_comments > 0:
                    st.info(f"ℹ️ **{videos_without_comments}** videos had no comments available")
                
                # Show sample comments (user-friendly preview)
                st.subheader("💬 Comment Overview")
                videos_with_comments_list = [v for v in videos if v.get('comments')]
                
                for idx, video in enumerate(videos_with_comments_list[:3]):  # Show first 3 videos with comments
                    with st.expander(f"📹 {video.get('title', 'Unknown Title')} ({len(video.get('comments', []))} comments)", expanded=False):
                        comments = video.get('comments', [])[:5]  # Show first 5 comments
                        for comment in comments:
                            author = comment.get('comment_author', 'Anonymous')
                            text = comment.get('comment_text', 'No text')[:200]  # Truncate long comments
                            if len(comment.get('comment_text', '')) > 200:
                                text += "..."
                            st.write(f"**{author}**: {text}")
                        
                        if len(video.get('comments', [])) > 5:
                            st.caption(f"... and {len(video.get('comments', [])) - 5} more comments")
                
                if len(videos_with_comments_list) > 3:
                    st.caption(f"... and {len(videos_with_comments_list) - 3} more videos with comments")
            else:
                st.info("💬 No comments were found for any videos in this channel")
            
            # Store raw/delta in debug state
            if 'debug_raw_data' not in st.session_state:
                st.session_state['debug_raw_data'] = {}
            if 'debug_delta_data' not in st.session_state:
                st.session_state['debug_delta_data'] = {}
            st.session_state['debug_raw_data']['comment'] = {
                'db': None,  # No DB in new channel step
                'api': videos
            }
            st.session_state['debug_delta_data']['comment'] = {
                'delta': None
            }
            
            # Action buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Complete and Save All Data", key="complete_save_btn", type="primary"):
                    self.save_data()
                        
            with col2:
                if st.button("🔙 Back to Videos", key="back_to_videos_final_btn"):
                    st.session_state['collection_step'] = 3
                    st.rerun()

    def save_data(self):
        """Save collected data to the database with user-friendly feedback."""
        channel_info = st.session_state.get('channel_info_temp')
        if not channel_info:
            st.error("❌ No data to save.")
            return
        
        with st.spinner("💾 Saving all collected data to database..."):
            try:
                save_manager = SaveOperationManager()
                
                # Calculate totals for user feedback
                total_videos = len(channel_info.get('video_id', [])) if 'video_id' in channel_info else 0
                total_comments = sum(len(video.get('comments', [])) for video in channel_info.get('video_id', [])) if 'video_id' in channel_info else 0
                
                success = save_manager.perform_save_operation(
                    youtube_service=self.youtube_service,
                    api_data=channel_info,
                    total_videos=total_videos,
                    total_comments=total_comments
                )
                
                if success:
                    # Show comprehensive success message
                    st.success("✅ **All data saved successfully!**")
                    
                    # Create summary info box
                    with st.container():
                        st.info(
                            f"📊 **Data Summary:**\n"
                            f"• Channel: {channel_info.get('channel_title', 'Unknown')}\n"
                            f"• Videos: {total_videos}\n"
                            f"• Comments: {total_comments}"
                        )
                    
                    # Navigation options
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📈 View Data Storage", key="view_storage_btn", type="primary"):
                            st.session_state['main_tab'] = "data_storage"
                            st.rerun()
                    with col2:
                        if st.button("🔄 Start New Collection", key="new_collection_btn"):
                            self.reset_workflow_state()
                            st.rerun()
                else:
                    st.error("❌ Failed to save data. Please try again or contact support.")
                
            except Exception as e:
                st.error(f"❌ Error during save operation: {str(e)}")
                st.info("💡 Try saving again or add the data to the processing queue for later.")

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
