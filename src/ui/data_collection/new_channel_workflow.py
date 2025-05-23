"""
New channel workflow implementation for data collection.
"""
import streamlit as st
from src.utils.helpers import debug_log
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from .components.video_item import render_video_item
from .utils.data_conversion import format_number
from .utils.error_handling import handle_collection_error
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
        """Render step 1: Display and collect channel data."""
        st.subheader("Step 1: Channel Data")
        render_queue_status_sidebar()  # Show queue in sidebar
        self.show_progress_indicator(1)
        
        channel_info = st.session_state.get('channel_info_temp', {})
        
        if not channel_info:
            st.error("No channel data available. Please go back and enter a channel URL or ID.")
            return
        
        # Display channel information in a modern, readable format
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Channel", channel_info.get('channel_name', 'Unknown'))
            channel_url = f"https://www.youtube.com/channel/{channel_info.get('channel_id')}"
            st.markdown(f"[View Channel on YouTube]({channel_url})")
        
        with col2:
            st.metric("Subscribers", self.format_number(int(channel_info.get('subscribers', 0))))
        
        with col3:
            st.metric("Total Videos", self.format_number(int(channel_info.get('total_videos', 0))))
        
        # Show additional channel details in an expander
        with st.expander("Channel Details"):
            st.write("**Description:**", channel_info.get('channel_description', 'No description available'))
            st.write("**Total Views:**", self.format_number(int(channel_info.get('views', 0))))
            st.write("**Channel ID:**", channel_info.get('channel_id', 'Unknown'))
        
        # Buttons for save or continue
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save Channel Data"):
                with st.spinner("Saving channel data..."):
                    try:
                        channel_data = st.session_state.get('channel_info_temp', {})
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
                st.session_state['collection_step'] = 2
                st.rerun()
    
    def render_step_2_video_collection(self):
        """Render step 2: Collect and display video data."""
        st.subheader("Step 2: Videos Data")
        render_queue_status_sidebar()  # Show queue in sidebar
        self.show_progress_indicator(2)
        channel_info = st.session_state.get('channel_info_temp', {})
        channel_id = channel_info.get('channel_id', '')
        videos = channel_info.get('video_id', []) if 'video_id' in channel_info else []
        debug_logs = st.session_state.get('debug_logs', [])
        if not videos:
            max_videos_available = int(channel_info.get('total_videos', 100))
            max_videos = st.slider(
                "Maximum number of videos to fetch",
                min_value=0,
                max_value=min(500, max_videos_available),
                value=min(50, max_videos_available)
            )
            if st.button("Fetch Videos from API"):
                with st.spinner(f"Fetching up to {max_videos} videos from YouTube API..."):
                    options = {
                        'fetch_channel_data': False,
                        'fetch_videos': True,
                        'fetch_comments': False,
                        'max_videos': max_videos
                    }
                    updated_data = self.youtube_service.collect_channel_data(
                        channel_id,
                        options,
                        existing_data=channel_info
                    )
                    st.session_state['api_initialized'] = True
                    debug_logs.append(f"API call made to fetch videos for {channel_id}")
                    st.session_state['debug_logs'] = debug_logs
                    st.session_state['last_api_call'] = updated_data.get('last_api_call') if updated_data else None
                    if updated_data and 'video_id' in updated_data:
                        st.session_state['channel_info_temp']['video_id'] = updated_data['video_id']
                        st.session_state['videos_fetched'] = True
                        summary = [f"Videos fetched: {len(updated_data['video_id'])}"]
                        st.session_state['delta_summary'] = summary
                        st.success(f"Successfully fetched {len(updated_data['video_id'])} videos!")
                        st.rerun()
                    else:
                        st.error("Failed to fetch videos. Please try again.")
        else:
            st.write(f"Successfully fetched {len(videos)} videos.")
            for video in videos:
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
            if videos:
                st.write("### Sample Video Data Structure")
                st.json(videos[0])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Channel and Videos"):
                    with st.spinner("Saving channel and video data..."):
                        try:
                            channel_data = st.session_state.get('channel_info_temp', {})
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
                    st.session_state['collection_step'] = 3
                    st.rerun()
    
    def render_step_3_comment_collection(self):
        """Render step 3: Collect and display comment data."""
        st.subheader("Step 3: Comments Data")
        render_queue_status_sidebar()  # Show queue in sidebar
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
            if st.button("Complete and Save Data"):
                self.save_data()
    
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
