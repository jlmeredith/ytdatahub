"""
Channel refresh workflow implementation for data collection.
"""
import streamlit as st
from src.utils.helpers import debug_log
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from .components.video_item import render_video_item
from .channel_refresh.comparison import display_comparison_results, compare_data
from .utils.data_conversion import format_number, convert_db_to_api_format
from .utils.error_handling import handle_collection_error
from src.utils.queue_tracker import render_queue_status_sidebar

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
        if st.button("Compare with YouTube API"):
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
                        options = {
                            'fetch_channel_data': True,
                            'fetch_videos': False,
                            'fetch_comments': False,
                            'max_videos': 0,
                            'max_comments_per_video': 0
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
        """Render step 2 (in refresh workflow): Review and update channel data."""
        st.subheader("Step 2: Review and Update Channel Data")
        channel_id = st.session_state.get('existing_channel_id')
        db_data = st.session_state.get('db_data', {})
        api_data = st.session_state.get('api_data', {})
        debug_logs = st.session_state.get('debug_logs', [])
        # Only fetch and compare channel info at this step
        if st.button("Refresh Channel Info from API"):
            with st.spinner("Fetching channel info from YouTube API..."):
                options = {
                    'fetch_channel_data': True,
                    'fetch_videos': False,
                    'fetch_comments': False,
                    'max_videos': 0,
                    'max_comments_per_video': 0
                }
                # Fetch channel info from API
                channel_info_response = self.youtube_service.update_channel_data(
                    channel_id,
                    options,
                    interactive=False
                )
                # Mark API as initialized and log the call
                st.session_state['api_initialized'] = True
                debug_logs.append(f"API call made to fetch channel info for {channel_id}")
                st.session_state['debug_logs'] = debug_logs
                st.session_state['last_api_call'] = channel_info_response.get('last_api_call')
                # Store API data and debug info for this step only
                if channel_info_response and isinstance(channel_info_response, dict):
                    st.session_state['api_data'] = channel_info_response.get('api_data', {})
                    st.session_state['response_data'] = channel_info_response.get('response_data', {})
                    # Compare and store channel-level delta
                    from src.ui.data_collection.channel_refresh.comparison import compare_data
                    delta = compare_data(db_data, st.session_state['api_data'])
                    st.session_state['delta'] = delta
                    # Store a summary delta for UI display
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

        # Display channel information in a modern, readable format
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Channel", api_data.get('channel_name', 'Unknown'))
            channel_url = f"https://www.youtube.com/channel/{api_data.get('channel_id')}"
            st.markdown(f"[View Channel on YouTube]({channel_url})")
        with col2:
            st.metric("Subscribers", format_number(int(api_data.get('subscribers', 0))))
        with col3:
            st.metric("Total Videos", format_number(int(api_data.get('total_videos', 0))))

        # Show additional channel details in an expander
        with st.expander("Channel Details"):
            st.write("**Description:**", api_data.get('channel_description', 'No description available'))
            st.write("**Total Views:**", format_number(int(api_data.get('views', 0))))
            st.write("**Channel ID:**", api_data.get('channel_id', 'Unknown'))

        # Buttons for save or continue
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Channel Data"):
                with st.spinner("Saving channel data..."):
                    try:
                        channel_data = st.session_state.get('api_data', {})
                        success = self.youtube_service.save_channel_data(channel_data, "sqlite")
                        if success:
                            st.session_state['channel_data_saved'] = True
                            st.success("Channel data saved successfully!")
                        else:
                            st.error("Failed to save data.")
                    except Exception as e:
                        st.error(f"Error saving data: {str(e)}")
                        debug_log(f"Error saving channel data: {str(e)}")
        with col2:
            if st.button("Continue to Videos Data"):
                st.session_state['refresh_workflow_step'] = 3
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 3 (in refresh workflow): Collect and display video data."""
        st.subheader("Step 3: Video Collection")
        render_queue_status_sidebar()  # Show queue in sidebar
        channel_id = st.session_state.get('existing_channel_id', '')
        db_data = st.session_state.get('db_data', {})
        videos_data = st.session_state.get('videos_data', [])
        debug_logs = st.session_state.get('debug_logs', [])
        # Only fetch and compare video data at this step
        if st.button("Fetch Videos from API"):
            with st.spinner("Fetching videos from YouTube API..."):
                max_videos = 50  # Or get from user input if available
                options = {
                    'fetch_channel_data': False,
                    'fetch_videos': True,
                    'fetch_comments': False,
                    'max_videos': max_videos
                }
                video_response = self.youtube_service.update_channel_data(
                    channel_id,
                    options,
                    interactive=False
                )
                st.session_state['api_initialized'] = True
                debug_logs.append(f"API call made to fetch videos for {channel_id}")
                st.session_state['debug_logs'] = debug_logs
                st.session_state['last_api_call'] = video_response.get('last_api_call')
                if video_response and isinstance(video_response, dict):
                    st.session_state['videos_data'] = video_response.get('video_id', [])
                    st.session_state['response_data'] = video_response.get('response_data', {})
                    # Compare and store video-level delta summary
                    db_videos = db_data.get('video_id', [])
                    api_videos = video_response.get('video_id', [])
                    video_delta = []
                    db_video_map = {v.get('video_id'): v for v in db_videos if 'video_id' in v}
                    summary = []
                    for video in api_videos:
                        vid = video.get('video_id')
                        if vid and vid in db_video_map:
                            old = db_video_map[vid]
                            view_diff = int(video.get('views', 0)) - int(old.get('views', 0))
                            like_diff = int(video.get('likes', 0)) - int(old.get('likes', 0))
                            comment_diff = int(video.get('comment_count', 0)) - int(old.get('comment_count', 0))
                            if view_diff != 0 or like_diff != 0 or comment_diff != 0:
                                video_delta.append({
                                    'video': video,
                                    'old_views': old.get('views', 0),
                                    'new_views': video.get('views', 0),
                                    'old_likes': old.get('likes', 0),
                                    'new_likes': video.get('likes', 0),
                                    'old_comments': old.get('comment_count', 0),
                                    'new_comments': video.get('comment_count', 0)
                                })
                    st.session_state['video_delta'] = video_delta
                    summary = [f"Videos with changes: {len(video_delta)}"]
                    st.session_state['delta_summary'] = summary
                    st.success(f"Successfully fetched {len(api_videos)} videos!")
                    st.rerun()
                else:
                    st.error("Failed to fetch videos. Please try again.")

        # Display video information
        if videos_data:
            st.write(f"Successfully fetched {len(videos_data)} videos.")
            for video in videos_data:
                with st.container():
                    cols = st.columns([1, 4, 2, 2, 2])
                    with cols[0]:
                        thumb = video.get('thumbnail_url') or video.get('thumbnail', '')
                        if thumb:
                            st.image(thumb, width=80)
                        else:
                            st.write(":movie_camera:")
                    with cols[1]:
                        st.markdown(f"**{video.get('title', 'Untitled')}**")
                        st.caption(f"ID: {video.get('video_id', 'N/A')}")
                    with cols[2]:
                        st.metric("Views", video.get('views', 0))
                    with cols[3]:
                        st.metric("Likes", video.get('likes', 0))
                    with cols[4]:
                        st.metric("Comments", video.get('comment_count', 0))

            # Buttons for save or continue
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Channel and Videos"):
                    with st.spinner("Saving channel and video data..."):
                        try:
                            channel_data = st.session_state.get('api_data', {})
                            success = self.youtube_service.save_channel_data(channel_data, "sqlite")
                            if success:
                                st.session_state['videos_data_saved'] = True
                                st.success("Channel and video data saved successfully!")
                            else:
                                st.error("Failed to save data.")
                        except Exception as e:
                            handle_collection_error(e, "saving channel and video data")
            with col2:
                if st.button("Continue to Comments Data"):
                    st.session_state['refresh_workflow_step'] = 4
                    st.rerun()
    
    def render_step_3_comment_collection(self):
        """Render step 4 (in refresh workflow): Collect and display comment data."""
        st.subheader("Step 4: Comment Collection")
        render_queue_status_sidebar()  # Show queue in sidebar
        channel_id = st.session_state.get('existing_channel_id', '')
        videos_data = st.session_state.get('videos_data', [])
        debug_logs = st.session_state.get('debug_logs', [])
        # Only fetch and compare comment data at this step
        if not st.session_state.get('comments_fetched', False):
            if not videos_data:
                st.warning("No videos available for comment collection. Please go back to the video collection step.")
                if st.button("Back to Video Collection"):
                    st.session_state['refresh_workflow_step'] = 3
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
            if st.button("Complete and Save Data"):
                self.save_data()
    
    def save_data(self):
        """Save collected data to the database."""
        # Get API data from session state
        api_data = st.session_state.get('api_data', {})
        
        if not api_data:
            st.error("No data to save.")
            return
            
        with st.spinner("Saving data to database..."):
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
                
                # Save to database
                success = self.youtube_service.save_channel_data(api_data, "sqlite")
                
                if success:
                    st.success("Data saved successfully!")
                    st.info("Comments saved successfully!")
                    # Offer option to view in data storage tab
                    if st.button("Go to Data Storage Tab"):
                        st.session_state['main_tab'] = "data_storage"
                        st.rerun()
                else:
                    st.error("Failed to save data.")
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
                # Store all data in session state
                st.session_state['videos_data'] = video_data.get('video_id', [])
                st.session_state['videos_fetched'] = True
                
                # Store delta information if present
                if 'delta' in video_data:
                    st.session_state['delta'] = video_data['delta']
                
                # Store debug logs and response data
                if 'debug_logs' in video_data:
                    st.session_state['debug_logs'] = video_data['debug_logs']
                if 'response_data' in video_data:
                    st.session_state['response_data'] = video_data['response_data']
                
                # Show success message with video count
                video_count = len(video_data.get('video_id', []))
                st.success(f"Successfully collected {video_count} videos!")
                st.rerun()
            else:
                st.error("Failed to fetch videos. Please try again.")
        except Exception as e:
            st.error(f"Error fetching videos: {str(e)}")
            debug_log(f"Error in video collection: {str(e)}")
