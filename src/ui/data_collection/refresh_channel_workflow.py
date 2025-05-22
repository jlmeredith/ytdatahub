"""
Channel refresh workflow implementation for data collection.
"""
import streamlit as st
from src.utils.helpers import debug_log
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from .components.video_item import render_video_item
from .channel_refresh.comparison import display_comparison_results
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
                    
                    # Set flag to track comparison attempt
                    st.session_state['comparison_attempted'] = True
                    
                    try:
                        # Default options - channel data only
                        options = {
                            'fetch_channel_data': True,
                            'fetch_videos': False,
                            'fetch_comments': False,
                            'max_videos': 0,
                            'max_comments_per_video': 0
                        }
                        
                        comparison_data = self.youtube_service.update_channel_data(channel_id, options, interactive=False, existing_data=None)
                        
                        # Store data in session state for step 2
                        if comparison_data and isinstance(comparison_data, dict):
                            st.session_state['db_data'] = comparison_data.get('db_data', {})
                            st.session_state['api_data'] = comparison_data.get('api_data', {})
                            
                            # Ensure we have valid data dictionaries, not None
                            if st.session_state['db_data'] is None:
                                st.session_state['db_data'] = {}
                            if st.session_state['api_data'] is None:
                                st.session_state['api_data'] = {}
                            
                            # Promote delta info from api_data if present
                            if 'delta' in st.session_state['api_data']:
                                st.session_state['delta'] = st.session_state['api_data']['delta']
                            elif 'delta' in comparison_data:
                                st.session_state['delta'] = comparison_data['delta']
                            # Always ensure delta is present at the top level for test parity
                            if 'delta' not in st.session_state['api_data'] and 'delta' in st.session_state:
                                st.session_state['api_data']['delta'] = st.session_state['delta']
                            
                            # Ensure the returned channel data has delta at the top level
                            if 'channel' in st.session_state['api_data']:
                                if 'delta' in st.session_state['api_data']:
                                    st.session_state['api_data']['channel']['delta'] = st.session_state['api_data']['delta']
                                elif 'delta' in st.session_state:
                                    st.session_state['api_data']['channel']['delta'] = st.session_state['delta']
                            
                            # Check if we have actual data content in both objects
                            if (len(st.session_state['db_data']) == 0 and len(st.session_state['api_data']) == 0):
                                st.error("No data could be retrieved from either the database or YouTube API.")
                                return
                                
                            # Set the channel ID in session state
                            st.session_state['existing_channel_id'] = channel_id
                            
                            # Set the collection mode to refresh_channel
                            st.session_state['collection_mode'] = "refresh_channel"
                            
                            # Move to step 2 (review data)
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
        
        # Get data from session state
        channel_id = st.session_state.get('existing_channel_id')
        db_data = st.session_state.get('db_data', {})
        api_data = st.session_state.get('api_data', {})
        
        if not channel_id:
            st.warning("No channel selected. Please go back to Step 1.")
            if st.button("Go back to Step 1"):
                st.session_state['refresh_workflow_step'] = 1
                st.rerun()
            return
        
        # Handle completely missing data
        if db_data is None or api_data is None or (not db_data and not api_data):
            st.warning("Missing data for comparison. Please try the comparison again.")
            if st.button("Retry Comparison"):
                # Get fresh data for the channel
                with st.spinner("Retrying data comparison..."):
                    try:
                        # Fetch channel data again with same options
                        options = {
                            'fetch_channel_data': True,
                            'fetch_videos': False,
                            'fetch_comments': False,
                            'max_videos': 0,
                            'max_comments_per_video': 0
                        }
                        comparison_data = self.youtube_service.update_channel_data(channel_id, options, interactive=False, existing_data=None)
                        
                        # Update session state with new data
                        if comparison_data and isinstance(comparison_data, dict):
                            st.session_state['db_data'] = comparison_data.get('db_data', {})
                            st.session_state['api_data'] = comparison_data.get('api_data', {})
                            st.rerun()
                        else:
                            st.error("Failed to retrieve channel data. Please try again later.")
                    except Exception as e:
                        st.error(f"Error retrying comparison: {str(e)}")
            
            if st.button("Go Back"):
                st.session_state['refresh_workflow_step'] = 1
                st.rerun()
            return
            
        # Display data comparison
        display_comparison_results(db_data, api_data)
        
        # Define workflow steps to guide the user through data collection
        st.subheader("Action Steps")
        st.write("Please select your next action:")
        
        cols = st.columns(2)
        with cols[0]:
            # Button to update database with API data
            if st.button("Update Channel Data"):
                with st.spinner("Updating channel data..."):
                    # Save API data to the database only - this is a partial save
                    success = self.youtube_service.save_channel_data(api_data, "sqlite")
                    if success:
                        st.success("Channel data updated successfully!")
                        # Update session state to reflect that we saved this partial data
                        st.session_state['channel_data_saved'] = True
                    else:
                        st.error("Failed to update channel data.")
            
            # Button to proceed to video collection step
            if st.button("Proceed to Video Collection"):
                with st.spinner("Preparing video collection..."):
                    # Set up the session state for video collection
                    st.session_state['refresh_workflow_step'] = 3  # Move to step 3 in refresh workflow
                    
                    # Initialize video page number for pagination
                    st.session_state['video_page_number'] = 0
                    
                    # Create options for just videos - initial fetch with default settings
                    options = {
                        'fetch_channel_data': False,
                        'fetch_videos': True,
                        'fetch_comments': False,
                        'max_videos': 50  # Initial reasonable number of videos to fetch
                    }
                    
                    try:
                        # Update data with videos
                        video_data = self.youtube_service.update_channel_data(
                            channel_id,
                            options,
                            interactive=False,
                            existing_data=None
                        )
                        
                        if video_data and isinstance(video_data, dict):
                            # Store video data for next step
                            st.session_state['videos_data'] = video_data.get('api_data', {}).get('video_id', [])
                            st.session_state['videos_fetched'] = True
                            st.success(f"Successfully collected {len(st.session_state['videos_data'])} videos!")
                        else:
                            st.warning("No video data was retrieved. You can still continue.")
                    except Exception as e:
                        st.error(f"Error collecting video data: {str(e)}")
                        debug_log(f"Exception during video data collection: {str(e)}")
                    
                    st.rerun()
        
        with cols[1]:
            # Button to go back to channel selection
            if st.button("Back to Channel Selection"):
                st.session_state['refresh_workflow_step'] = 1
                
                # Clear data from session state
                if 'db_data' in st.session_state:
                    del st.session_state['db_data']
                if 'api_data' in st.session_state:
                    del st.session_state['api_data']
                if 'comparison_attempted' in st.session_state:
                    del st.session_state['comparison_attempted']
                
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 3 (in refresh workflow): Collect and display video data."""
        st.subheader("Step 3: Video Collection")
        render_queue_status_sidebar()  # Show queue in sidebar
        
        # Get channel info from session state
        channel_id = st.session_state.get('existing_channel_id', '')
        videos_data = st.session_state.get('videos_data', [])
        
        # Check if we have videos data
        if videos_data:
            # Ensure all metrics are present
            for video in videos_data:
                video.setdefault('views', 0)
                video.setdefault('likes', 0)
                video.setdefault('comment_count', 0)
            
            # Display videos count
            st.write(f"Collected {len(videos_data)} videos.")
            
            # Video sorting options
            sort_options = ["Most Recent", "Most Viewed", "Most Likes", "Most Comments"]
            sort_col1, sort_col2 = st.columns([2, 3])
            with sort_col1:
                selected_sort = st.selectbox("Sort videos by:", sort_options)
            
            # Sort the videos based on selection
            sorted_videos = videos_data.copy()
            if selected_sort == "Most Viewed":
                sorted_videos.sort(key=lambda v: int(v.get('views', 0)), reverse=True)
            elif selected_sort == "Most Likes":
                sorted_videos.sort(key=lambda v: int(v.get('likes', 0)), reverse=True)
            elif selected_sort == "Most Comments":
                sorted_videos.sort(key=lambda v: int(v.get('comment_count', 0)), reverse=True)
            # No sort for Most Recent as it's the default order
            
            # Display videos
            for idx, video in enumerate(sorted_videos):
                render_video_item(video, index=idx)
            
            # Buttons for save or continue
            col1, col2 = st.columns(2)
            with col1:
                # Save data at this step
                if st.button("Save Channel and Videos"):
                    # Save partial data
                    with st.spinner("Saving channel and video data..."):
                        try:
                            # Get the API data to save
                            api_data = st.session_state.get('api_data', {})
                            
                            # Update with the video data
                            api_data['video_id'] = sorted_videos
                            
                            # Save to database
                            success = self.youtube_service.save_channel_data(api_data, "sqlite")
                            
                            if success:
                                st.session_state['videos_data_saved'] = True
                                st.success("Channel and video data saved successfully!")
                            else:
                                st.error("Failed to save data.")
                        except Exception as e:
                            st.error(f"Error saving data: {str(e)}")
                            debug_log(f"Error saving channel and video data: {str(e)}")
                            
            with col2:
                # Continue to next step
                if st.button("Proceed to Comment Collection"):
                    st.session_state['refresh_workflow_step'] = 4  # Move to step 4 in refresh workflow
                    st.rerun()
        else:
            # Video collection options
            st.write("Configure video collection options:")
            
            # Get DB data for total videos count
            db_data = st.session_state.get('db_data', {})
            total_videos = db_data.get('total_videos', 100)
            
            # Video collection parameters
            fetch_all = st.checkbox("Fetch All Videos", value=False)
            
            if fetch_all:
                max_videos = total_videos
                st.write(f"Will fetch all {max_videos} videos")
            else:
                max_videos = st.slider(
                    "Maximum number of videos to fetch",
                    min_value=0,
                    max_value=min(500, total_videos),
                    value=min(50, total_videos)
                )
            
            # Button to fetch videos
            if st.button("Fetch Videos"):
                with st.spinner(f"Fetching up to {max_videos} videos..."):
                    try:
                        # Create options
                        options = {
                            'fetch_channel_data': False,
                            'fetch_videos': True,
                            'fetch_comments': False,
                            'max_videos': max_videos
                        }
                        
                        # Fetch videos using update_channel_data
                        video_data = self.youtube_service.update_channel_data(
                            channel_id,
                            options,
                            interactive=False
                        )
                        
                        # Add API status debug info
                        debug_log(f"API response for videos in refresh flow: success={video_data is not None}, channel={channel_id}")
                        
                        if video_data and isinstance(video_data, dict):
                            # Store video data for next step
                            videos_data = video_data.get('api_data', {}).get('video_id', [])
                            st.session_state['videos_data'] = videos_data
                            st.session_state['videos_fetched'] = True
                            
                            # Show more detailed success message with video metrics
                            video_count = len(videos_data)
                            video_with_metrics = sum(1 for v in videos_data if all(k in v for k in ['views', 'likes', 'comment_count']))
                            
                            st.success(f"Successfully collected {video_count} videos ({video_with_metrics} with complete metrics)!")
                            st.rerun()
                        else:
                            st.error("Failed to fetch videos. Please try again.")
                    except Exception as e:
                        st.error(f"Error fetching videos: {str(e)}")
                        debug_log(f"Error in video collection: {str(e)}")
    
    def render_step_3_comment_collection(self):
        """Render step 4 (in refresh workflow): Collect and display comment data."""
        st.subheader("Step 4: Comment Collection")
        render_queue_status_sidebar()  # Show queue in sidebar
        
        # Get channel info and videos from session state
        channel_id = st.session_state.get('existing_channel_id', '')
        videos_data = st.session_state.get('videos_data', [])
        comments_fetched = st.session_state.get('comments_fetched', False)
        
        if comments_fetched:
            # Calculate stats
            videos_with_comments = [v for v in videos_data if v.get('comments')]
            total_comments = sum(len(v.get('comments', [])) for v in videos_data)
            
            # Display summary
            st.write(f"Successfully fetched {total_comments} comments from {len(videos_with_comments)} videos.")
            
            # Button to save data
            if st.button("Complete and Save Data", key="save_data_button_comments"):
                self.save_data()
        else:
            # Comment collection options
            st.write("Configure comment collection options:")
            
            if not videos_data:
                st.warning("No videos available for comment collection. Please go back to the video collection step.")
                if st.button("Back to Video Collection"):
                    st.session_state['refresh_workflow_step'] = 3
                    st.rerun()
                return
            
            # Comment collection parameters
            max_comments = st.slider(
                "Maximum number of comments to fetch per video",
                min_value=0,
                max_value=100,
                value=20,
                help="Set to 0 to skip comment collection"
            )
            
            # Fetch comments button
            if st.button("Fetch Comments"):
                if max_comments == 0:
                    st.info("Comment collection skipped.")
                    st.session_state['comments_fetched'] = True
                    st.rerun()
                else:
                    with st.spinner(f"Fetching up to {max_comments} comments per video..."):
                        try:
                            # Create options for comment collection only
                            options = {
                                'fetch_channel_data': False,
                                'fetch_videos': False,
                                'fetch_comments': True,
                                'max_comments_per_video': max_comments
                            }
                            
                            # Get the API data to update with comments
                            api_data = st.session_state.get('api_data', {})
                            
                            # Add videos to API data for comment collection
                            api_data['video_id'] = videos_data
                            
                            # Fetch comments using update_channel_data - already has existing_data parameter
                            comment_data = self.youtube_service.update_channel_data(
                                channel_id,
                                options,
                                existing_data=api_data,
                                interactive=True
                            )
                            
                            # Add API status debug info
                            debug_log(f"API response for comments in refresh flow: success={comment_data is not None}, channel={channel_id}")
                            
                            if comment_data and isinstance(comment_data, dict):
                                # Update video data with comments
                                videos_with_comments = comment_data.get('video_id', [])
                                st.session_state['videos_data'] = videos_with_comments
                                st.session_state['comments_fetched'] = True
                                
                                # Calculate comment statistics
                                total_comments = sum(len(video.get('comments', [])) for video in videos_with_comments)
                                videos_with_comments_count = sum(1 for video in videos_with_comments if video.get('comments'))
                                
                                st.success(f"Successfully fetched {total_comments} comments from {videos_with_comments_count} videos!")
                                st.rerun()
                            else:
                                st.error("Failed to fetch comments. Please try again.")
                        except Exception as e:
                            st.error(f"Error fetching comments: {str(e)}")
                            debug_log(f"Error in comment collection: {str(e)}")
    
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
            
            if video_data and isinstance(video_data, dict):
                # Log detailed API response information
                api_data = video_data.get('api_data', {})
                api_quota_used = api_data.get('api_quota_used', 'Unknown')
                api_quota_remaining = api_data.get('api_quota_remaining', 'Unknown')
                debug_log(f"API quota used: {api_quota_used}, remaining: {api_quota_remaining}")
                
                # Show API details if debug mode is enabled
                if st.session_state.get('show_debug_info', False):
                    with st.expander("API Response Details"):
                        st.write("### API Response Information")
                        st.metric("API Quota Used", api_quota_used)
                        st.metric("API Quota Remaining", api_quota_remaining)
                        if 'api_response_time' in api_data:
                            st.metric("Response Time", f"{api_data['api_response_time']:.2f}s")
                
                # Store video data for next step
                videos = api_data.get('video_id', [])
                st.session_state['videos_data'] = videos
                st.session_state['videos_fetched'] = True
                
                # Log sample of video data
                if videos and len(videos) > 0:
                    first_video = videos[0]
                    debug_log(f"First video keys: {list(first_video.keys()) if isinstance(first_video, dict) else 'Not a dict'}")
                    debug_log(f"First video views: {first_video.get('views', 'Not found')}")
                    debug_log(f"First video likes: {first_video.get('likes', 'Not found')}")
                    debug_log(f"First video comment_count: {first_video.get('comment_count', 'Not found')}")
                
                # Count videos with complete metrics
                videos_with_metrics = sum(1 for v in videos if all(k in v for k in ['views', 'likes', 'comment_count']))
                st.success(f"Successfully collected {len(videos)} videos ({videos_with_metrics} with complete metrics)!")
                st.rerun()
            else:
                st.error("Failed to fetch videos. Please try again.")
        except Exception as e:
            st.error(f"Error fetching videos: {str(e)}")
            debug_log(f"Error in video collection: {str(e)}")
