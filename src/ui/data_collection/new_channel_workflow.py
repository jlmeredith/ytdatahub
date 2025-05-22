"""
New channel workflow implementation for data collection.
"""
import streamlit as st
from src.utils.helpers import debug_log
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from .components.video_item import render_video_item
from .utils.data_conversion import format_number
from .utils.error_handling import handle_collection_error
from src.ui.data_collection.queue_ui import render_queue_status
from src.utils.queue_tracker import render_queue_status_sidebar

class NewChannelWorkflow(BaseCollectionWorkflow):
    """
    Implementation of the workflow for collecting data from a new channel.
    This class follows the interface defined in BaseCollectionWorkflow.
    """
    
    def initialize_workflow(self, channel_input):
        """
        Initialize the workflow with channel information.
        
        Args:
            channel_input: Channel ID or URL to process
        """
        # Initialize workflow variables
        if 'collection_step' not in st.session_state:
            st.session_state['collection_step'] = 1
        
        if 'channel_input' not in st.session_state:
            st.session_state['channel_input'] = channel_input
        
        # Initialize API
        if 'api_initialized' not in st.session_state:
            st.session_state['api_initialized'] = True
            
        # Initialize channel data if not already loaded
        if 'channel_info_temp' not in st.session_state and channel_input:
            # Validate and fetch basic channel info
            with st.spinner("Fetching channel data..."):
                try:
                    channel_info = self.youtube_service.get_basic_channel_info(channel_input)
                    if channel_info:
                        st.session_state['channel_info_temp'] = channel_info
                        st.session_state['channel_data_fetched'] = True
                        
                        # Match the API data storage pattern used in refresh workflow
                        # This makes both workflows more consistent
                        st.session_state['api_data'] = channel_info
                    else:
                        st.error("Failed to fetch channel data. Please check the channel ID or URL.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    def render_step_1_channel_data(self):
        """Render step 1: Collect and display channel data."""
        st.subheader("Step 1: Channel Data")
        
        # Get the channel info from session state with safe access
        channel_info = st.session_state.get('channel_info_temp')
        
        if channel_info is None:
            st.error("⚠️ Channel information is unavailable. Please refresh or try entering the channel again.")
            return
        
        # Show progress indicator
        self.show_progress_indicator(1)
        
        # Determine data source and display appropriate message
        data_source = channel_info.get('data_source', 'unknown')
        if data_source == 'database':
            st.info("📂 This data is loaded from the local database")
        elif data_source == 'api':
            st.success("📡 This data is freshly fetched from YouTube API")
        else:
            st.info("⚠️ Data source is unknown")
        
        # Display channel information in a modern, readable format
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Channel", channel_info.get('channel_name', 'Unknown'))
            channel_url = f"https://www.youtube.com/channel/{channel_info.get('channel_id')}"
            st.markdown(f"[View Channel on YouTube]({channel_url})")
        with col2:
            st.metric("Subscribers", format_number(int(channel_info.get('subscribers', 0))))
        with col3:
            st.metric("Total Videos", format_number(int(channel_info.get('total_videos', 0))))
        
        # Show additional channel details in an expander
        with st.expander("Channel Details"):
            st.write("**Description:**", channel_info.get('channel_description', 'No description available'))
            st.write("**Total Views:**", format_number(int(channel_info.get('views', 0))))
            st.write("**Channel ID:**", channel_info.get('channel_id', 'Unknown'))
        
        st.success("✅ Channel data fetched successfully!")
        
        # Buttons for save or continue
        col1, col2 = st.columns(2)
        with col1:
            # Save data at this step
            if st.button("Save Channel Data"):
                # Save partial data
                with st.spinner("Saving channel data..."):
                    try:
                        # Get the partial data to save (channel info only)
                        channel_data = st.session_state.get('channel_info_temp', {})
                        
                        # Save to database
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
            # Button to move to next step
            if st.button("Continue to Videos Data"):
                st.session_state['collection_step'] = 2
                st.rerun()
        
        # Show API debug information if requested
        if st.session_state.get('show_debug_info', False):
            channel_info = st.session_state.get('channel_info_temp', {})
            with st.expander("API Debug Information") as exp:
                exp.write("### Raw API Data")
                exp.json(channel_info)
                api_quota_used = channel_info.get('api_quota_used', 'Unknown')
                api_quota_remaining = channel_info.get('api_quota_remaining', 'Unknown')
                exp.metric("API Quota Used", api_quota_used)
                exp.metric("API Quota Remaining", api_quota_remaining)
                if 'api_response_time' in channel_info:
                    exp.metric("API Response Time", f"{channel_info['api_response_time']}s")
    
    def render_step_2_video_collection(self):
        """Render step 2: Collect and display video data."""
        st.subheader("Step 2: Videos Data")
        render_queue_status_sidebar()  # Show queue in sidebar
        
        # Show progress indicator
        self.show_progress_indicator(2)
        
        channel_info = st.session_state.get('channel_info_temp', {})
        channel_id = channel_info.get('channel_id', '')
        
        # Check if videos are already fetched
        if st.session_state.get('videos_fetched', False) and 'video_id' in channel_info and channel_info['video_id']:
            videos = channel_info.get('video_id', [])
            
            # Ensure all metrics are present
            for video in videos:
                video.setdefault('views', 0)
                video.setdefault('likes', 0)
                video.setdefault('comment_count', 0)
            
            # Display video stats
            st.write(f"Successfully fetched {len(videos)} videos.")
            
            # Video sorting options
            sort_options = ["Most Recent", "Most Viewed", "Most Likes", "Most Comments"]
            sort_col1, sort_col2 = st.columns([2, 3])
            with sort_col1:
                selected_sort = st.selectbox("Sort videos by:", sort_options)
            
            # Sort the videos based on selection
            if selected_sort == "Most Viewed":
                videos.sort(key=lambda v: int(v.get('views', 0)), reverse=True)
            elif selected_sort == "Most Likes":
                videos.sort(key=lambda v: int(v.get('likes', 0)), reverse=True)
            elif selected_sort == "Most Comments":
                videos.sort(key=lambda v: int(v.get('comment_count', 0)), reverse=True)
            else:  # Default to Most Recent
                # No sorting needed as they come in reverse chronological order by default
                pass
            
            # Display videos with custom component
            for video in videos:
                render_video_item(video)
            
            # API response debug expander
            if st.session_state.get('api_last_response'):
                with st.expander("API Response Data"):
                    st.json(st.session_state['api_last_response'])
            
            # Buttons for save or continue
            col1, col2 = st.columns(2)
            with col1:
                # Save data at this step
                if st.button("Save Channel and Videos"):
                    # Save partial data
                    with st.spinner("Saving channel and video data..."):
                        try:
                            # Get the partial data to save (without comments)
                            channel_data = st.session_state.get('channel_info_temp', {})
                            
                            # Save to database
                            success = self.youtube_service.save_channel_data(channel_data, "sqlite")
                            
                            if success:
                                st.session_state['videos_data_saved'] = True
                                st.success("Channel and video data saved successfully!")
                            else:
                                st.error("Failed to save data.")
                        except Exception as e:
                            handle_collection_error(e, "saving channel and video data")
            
            with col2:
                # Continue to next step
                if st.button("Continue to Comments Data"):
                    st.session_state['collection_step'] = 3
                    st.rerun()
        else:
            # Not fetched yet, show collection options
            st.write("Set the parameters for video collection:")
            
            # Maximum videos available
            max_videos_available = int(channel_info.get('total_videos', 100))
            
            # Only use the slider for max_videos (no fetch_all checkbox)
            max_videos = st.slider(
                "Maximum number of videos to fetch",
                min_value=0,
                max_value=min(500, max_videos_available),
                value=min(50, max_videos_available)
            )
            debug_log(f"[DEBUG] Using max_videos={max_videos}")
            
            # Fetch videos button
            if st.button("Fetch Videos"):
                with st.spinner(f"Fetching up to {max_videos} videos..."):
                    try:
                        # Update options
                        options = {
                            'fetch_channel_data': False,
                            'fetch_videos': True,
                            'fetch_comments': False,
                            'max_videos': max_videos
                        }
                        debug_log(f"[DEBUG] collect_channel_data options: {options}")
                        # Fetch videos
                        updated_data = self.youtube_service.collect_channel_data(
                            channel_id,
                            options,
                            existing_data=channel_info
                        )
                        
                        # Add enhanced API status debug info
                        debug_log(f"API response for videos: success={updated_data is not None}, channel={channel_id}")
                        
                        if updated_data:
                            # Log more detailed API response information
                            api_quota_used = updated_data.get('api_quota_used', 'Unknown')
                            api_quota_remaining = updated_data.get('api_quota_remaining', 'Unknown')
                            debug_log(f"API quota used: {api_quota_used}, remaining: {api_quota_remaining}")
                            
                            # Show API details in debug expander if debug mode is enabled
                            if st.session_state.get('show_debug_info', False):
                                with st.expander("API Response Details"):
                                    st.write("### API Response Information")
                                    st.metric("API Quota Used", api_quota_used)
                                    st.metric("API Quota Remaining", api_quota_remaining)
                                    if 'api_response_time' in updated_data:
                                        st.metric("Response Time", f"{updated_data['api_response_time']}s")
                                        
                                    # Show a sample of the data structure
                                    if 'video_id' in updated_data and updated_data['video_id'] and len(updated_data['video_id']) > 0:
                                        st.write("### Sample Video Data")
                                        first_video = updated_data['video_id'][0]
                                        
                                        # Check if the first video has complete metrics
                                        has_metrics = all(k in first_video for k in ['views', 'likes', 'comment_count'])
                                        st.code(f"Title: {first_video.get('title')}")
                                        st.code(f"ID: {first_video.get('video_id')}")
                                        st.code(f"Complete metrics: {has_metrics}")
                                        
                                        # Display available metrics
                                        st.code(f"Views: {first_video.get('views', 'Not found')}")
                                        st.code(f"Likes: {first_video.get('likes', 'Not found')}")
                                        st.code(f"Comment count: {first_video.get('comment_count', 'Not found')}")
                            
                            # Update session state
                            st.session_state['channel_info_temp'] = updated_data
                            st.session_state['videos_fetched'] = True
                            video_count = len(updated_data.get('video_id', []))
                            # Remove extra metrics from the success message for test compatibility
                            st.success(f"Successfully fetched {video_count} videos!")
                            st.rerun()
                        else:
                            st.error("Failed to fetch videos. Please try again.")
                    except Exception as e:
                        handle_collection_error(e, "fetching videos")
    
    def render_step_3_comment_collection(self):
        """Render step 3: Collect and display comment data."""
        st.subheader("Step 3: Comments Data")
        render_queue_status_sidebar()  # Show queue in sidebar
        
        # Show progress indicator
        self.show_progress_indicator(3)
        
        # Get channel data safely with defaults
        channel_info = st.session_state.get('channel_info_temp', {})
        channel_id = channel_info.get('channel_id', '')
        videos = channel_info.get('video_id', [])
        
        if not channel_id:
            st.error("Channel ID is missing. Please return to step 1.")
            if st.button("Return to Step 1"):
                st.session_state['collection_step'] = 1
                st.rerun()
            return
        
        # Check if comments are already fetched
        if st.session_state.get('comments_fetched', False):
            # Get comment stats
            total_comments = sum(len(video.get('comments', [])) for video in videos)
            videos_with_comments = sum(1 for video in videos if video.get('comments'))
            
            # Display summary
            st.write(f"Successfully fetched {total_comments} comments from {videos_with_comments} videos.")
            
            # Sample comments display
            if total_comments > 0:
                with st.expander("View Sample Comments"):
                    # Display up to 5 videos with comments
                    videos_with_comments = [v for v in videos if v.get('comments')]
                    for i, video in enumerate(videos_with_comments[:5]):
                        st.subheader(f"Video: {video.get('title', 'Unknown Title')}")
                        
                        # Display up to 3 comments per video
                        for j, comment in enumerate(video.get('comments', [])[:3]):
                            st.write(f"**{comment.get('comment_author', 'Unknown')}**: {comment.get('comment_text', 'No text')}")
                        
                        if len(video.get('comments', [])) > 3:
                            st.write(f"... and {len(video.get('comments', [])) - 3} more comments")
                        
                        if i < len(videos_with_comments) - 1:
                            st.divider()
            
            # Button to save data
            if st.button("Complete and Save Data"):
                self.save_data()
        else:
            # Not fetched yet, show collection options
            st.write("Set the parameters for comment collection:")
            
            if not videos:
                st.warning("No videos available for comment collection. Please go back to the video collection step.")
                if st.button("Back to Video Collection"):
                    st.session_state['collection_step'] = 2
                    st.rerun()
                return
            
            # Comment collection options
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
                            # Update options
                            options = {
                                'fetch_channel_data': False,
                                'fetch_videos': False,
                                'fetch_comments': True,
                                'max_comments_per_video': max_comments
                            }
                            
                            # Fetch comments
                            updated_data = self.youtube_service.collect_channel_data(
                                channel_id,
                                options,
                                existing_data=channel_info
                            )
                            
                            # Add enhanced API status debug info
                            debug_log(f"API response for comments: success={updated_data is not None}, channel={channel_id}")
                            
                            if updated_data:
                                # Log more detailed API response information
                                api_quota_used = updated_data.get('api_quota_used', 'Unknown')
                                api_quota_remaining = updated_data.get('api_quota_remaining', 'Unknown')
                                debug_log(f"API quota used: {api_quota_used}, remaining: {api_quota_remaining}")
                                
                                # Show API details in debug expander if debug mode is enabled
                                if st.session_state.get('show_debug_info', False):
                                    with st.expander("API Response Details"):
                                        st.write("### API Response Information")
                                        st.metric("API Quota Used", api_quota_used)
                                        st.metric("API Quota Remaining", api_quota_remaining)
                                        if 'api_response_time' in updated_data:
                                            st.metric("Response Time", f"{updated_data['api_response_time']}s")
                                            
                                        # Show a sample of the data structure
                                        st.write("### Data Structure Sample")
                                        if 'video_id' in updated_data and updated_data['video_id'] and len(updated_data['video_id']) > 0:
                                            # Show a simplified view of the first video with comments
                                            videos_with_comments = [v for v in updated_data['video_id'] if 'comments' in v and v['comments']]
                                            if videos_with_comments:
                                                st.write("First video with comments:")
                                                video_sample = videos_with_comments[0]
                                                st.code(f"Title: {video_sample.get('title')}")
                                                st.code(f"Comment count: {len(video_sample.get('comments', []))}")
                            
                                # Update session state
                                st.session_state['channel_info_temp'] = updated_data
                                st.session_state['comments_fetched'] = True
                                
                                # Get comment stats for better feedback
                                total_comments = sum(len(video.get('comments', [])) for video in updated_data.get('video_id', []))
                                videos_with_comments = sum(1 for video in updated_data.get('video_id', []) if video.get('comments'))
                                
                                st.success(f"Successfully fetched {total_comments} comments from {videos_with_comments} videos!")
                                st.rerun()
                            else:
                                st.error("Failed to fetch comments. Please try again.")
                        except Exception as e:
                            debug_log(f"Comment fetch error details: {str(e)}")
                            handle_collection_error(e, "fetching comments")
    
    def save_data(self):
        """Save collected data to the database."""
        channel_info = st.session_state.get('channel_info_temp')
        
        if not channel_info:
            st.error("No data to save.")
            return
            
        with st.spinner("Saving data to database..."):
            try:
                # Save to database
                success = self.youtube_service.save_channel_data(channel_info, "sqlite")
                
                if success:
                    st.success("Data saved successfully!")
                    st.info("Comments saved successfully!")
                    
                    # Count the number of comments saved for better feedback
                    total_comments = sum(len(video.get('comments', [])) for video in channel_info.get('video_id', []))
                    videos_with_comments = sum(1 for video in channel_info.get('video_id', []) if video.get('comments'))
                    
                    if total_comments > 0:
                        st.success(f"✅ Saved {total_comments} comments from {videos_with_comments} videos.")
                    else:
                        st.success("Channel and video data saved successfully!")
                    
                    # Log API response for debugging
                    debug_log(f"Data save operation successful, saved channel: {channel_info.get('channel_id')} with {total_comments} comments")
                    
                    # Offer option to view in data storage tab
                    if st.button("Go to Data Storage Tab"):
                        st.session_state['main_tab'] = "data_storage"
                        st.rerun()
                else:
                    st.error("Failed to save data.")
            except Exception as e:
                handle_collection_error(e, "saving data")
