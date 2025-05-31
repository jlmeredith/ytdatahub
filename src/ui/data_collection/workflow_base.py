"""
Base workflow for YouTube data collection.
This module defines a common interface for both new channel and refresh workflows.
"""
import streamlit as st
from abc import ABC, abstractmethod
from src.utils.debug_utils import debug_log
from .utils.delta_reporting import render_delta_report
from .state_management import toggle_debug_mode
from .debug_ui import render_debug_panel, generate_unique_key

class BaseCollectionWorkflow(ABC):
    """
    Abstract base class defining the interface for YouTube data collection workflows.
    
    This ensures both the new channel and existing channel refresh workflows
    follow the same pattern and steps, with appropriate customization where needed.
    """
    
    def __init__(self, youtube_service):
        """
        Initialize the workflow with a YouTube service.
        
        Args:
            youtube_service: The YouTube service instance for API operations
        """
        self.youtube_service = youtube_service
    
    @abstractmethod
    def initialize_workflow(self, channel_input):
        """
        Initialize the workflow with channel information.
        
        Args:
            channel_input: Channel ID or URL to process
        """
        pass
    
    @abstractmethod
    def render_step_1_channel_data(self):
        """Render step 1: Collect and display channel data."""
        pass
    
    def render_step_2_video_collection(self):
        """Render step 2: Collect and display video data. Optional - implement in subclass if needed."""
        pass
    
    def render_step_3_comment_collection(self):
        """Render step 3: Collect and display comment data. Optional - implement in subclass if needed."""
        pass
    
    @abstractmethod
    def save_data(self):
        """Save collected data to the database."""
        pass
    
    @abstractmethod
    def render_current_step(self):
        """
        Render the current step of the workflow based on the session state.
        Each workflow implements its own step structure.
        """
        pass
    
    def _get_current_step(self):
        """
        Get the current workflow step from session state.
        This method standardizes step tracking between both workflows.
        """
        # For new channel workflow
        if 'collection_step' in st.session_state:
            return st.session_state['collection_step']
        # For refresh workflow
        elif 'refresh_workflow_step' in st.session_state:
            # Convert refresh workflow steps to align with new channel steps
            refresh_step = st.session_state['refresh_workflow_step']
            # Map refresh steps to collection steps:
            # 1 (Select Channel) -> skipped in this workflow
            # 2 (Review Data) -> 1 (Channel Data)
            # 3 (Video Collection) -> 2 (Video Collection)
            # 4 (Comment Collection) -> 3 (Comment Collection)
            if refresh_step == 2:
                return 1
            elif refresh_step == 3:
                return 2
            elif refresh_step == 4:
                return 3
            else:
                return refresh_step
        # Default to step 1
        return 1

    def show_progress_indicator(self, step):
        """
        Show a progress indicator for the current step.
        
        This method displays a consistent progress bar and step label
        for both workflows, accounting for the different step numbering.
        
        Args:
            step (int): The normalized step number (1-3)
        """
        # Check if this is the refresh workflow
        is_refresh = 'refresh_workflow_step' in st.session_state
        
        # For refresh workflow, adjust step display to show steps 2-4 
        # (since step 1 is selection)
        refresh_offset = 1 if is_refresh else 0
        total_steps = 4 if is_refresh else 3
        display_step = step + refresh_offset
        
        if step == 1:
            st.progress(step / 3)
            st.write(f"Step {display_step} of {total_steps}: Channel Data")
        elif step == 2:
            st.progress(step / 3)
            st.write(f"Step {display_step} of {total_steps}: Video Collection")
        elif step == 3:
            st.progress(1.0)
            st.write(f"Step {display_step} of {total_steps}: Comment Collection")
            
    def handle_iteration_prompt(self, message="Continue to iterate?", key_prefix="iter"):
        """
        Handle the 'Continue to iterate?' prompt.
        This is a standardized implementation that works for both workflows.
        
        Args:
            message (str): Message to display in the prompt
            key_prefix (str): Prefix for the session state keys
            
        Returns:
            bool or None: True to continue, False to stop, None if waiting for input
        """
        # Initialize state variables if not present
        iteration_key = f"{key_prefix}_choice"
        prompt_key = f"{key_prefix}_show_prompt"
        
        if iteration_key not in st.session_state:
            st.session_state[iteration_key] = None
        
        if prompt_key not in st.session_state:
            st.session_state[prompt_key] = False
            
        # If we're showing the prompt and no choice has been made
        if st.session_state[prompt_key] and st.session_state[iteration_key] is None:
            st.subheader("Data Collection Progress")
            st.write(message)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes", key=f"{key_prefix}_yes"):
                    st.session_state[iteration_key] = True
                    st.session_state[prompt_key] = False
                    st.rerun()
            with col2:
                if st.button("No", key=f"{key_prefix}_no"):
                    st.session_state[iteration_key] = False
                    st.session_state[prompt_key] = False
                    st.rerun()
            
            # Show progress message while waiting for user input
            st.info("Waiting for your decision to continue data collection...")
            return None
        
        # If choice has already been made, return it and reset for next iteration
        if st.session_state[iteration_key] is not None:
            choice = st.session_state[iteration_key]
            st.session_state[iteration_key] = None
            return choice
            
        # Set flag to show the prompt
        st.session_state[prompt_key] = True
        return None
    
    def debug_video_data_flow(self, video_data, title="Video Data Diagnostic"):
        """
        Debug tool to diagnose issues in the video data flow pipeline.
        This helps identify where video data might be getting lost or corrupted.
        
        Args:
            video_data: The video data to diagnose
            title: Title for the diagnostic section
        """
        from src.utils.debug_utils import debug_log
        
        # Create an expandable section for the diagnostics
        with st.expander(f"🔍 {title}", expanded=False):
            st.write("### Video Data Structure Analysis")
            
            # Check if video_data exists
            if video_data is None:
                st.error("❌ Video data is None")
                debug_log("Video data is None")
                return
                
            # Check data type
            data_type = type(video_data).__name__
            if isinstance(video_data, dict):
                st.info(f"📊 Data type: Dictionary with {len(video_data)} keys")
                st.write("Top-level keys:")
                st.code(list(video_data.keys()))
                
                # Look for video data in common locations
                locations = ['video_id', 'videos', 'items']
                found = False
                
                for loc in locations:
                    if loc in video_data:
                        videos = video_data[loc]
                        if isinstance(videos, list):
                            st.success(f"✅ Found {len(videos)} videos in '{loc}' field")
                            found = True
                            # Show sample of first video
                            if videos:
                                with st.expander("First Video Sample"):
                                    st.json(videos[0])
                                    
                                # Check for critical fields
                                has_video_id = all('video_id' in v for v in videos if isinstance(v, dict))
                                has_views = all('views' in v for v in videos if isinstance(v, dict)) 
                                
                                if has_video_id:
                                    st.success("✅ All videos have video_id field")
                                else:
                                    st.error("❌ Some videos missing video_id field")
                                    
                                if has_views:
                                    st.success("✅ All videos have views field")
                                    # Check for zero views
                                    zero_views = sum(1 for v in videos if isinstance(v, dict) and v.get('views') == '0')
                                    if zero_views:
                                        st.warning(f"⚠️ {zero_views} videos have '0' views")
                                else:
                                    st.error("❌ Some videos missing views field")
                        else:
                            st.warning(f"⚠️ '{loc}' field exists but is not a list: {type(videos).__name__}")
                            
                if not found:
                    st.error("❌ No video data found in standard locations")
                    
            elif isinstance(video_data, list):
                st.info(f"📊 Data type: List with {len(video_data)} items")
                
                # Check if items are video objects
                if video_data and isinstance(video_data[0], dict):
                    video_fields = ['video_id', 'id', 'title']
                    is_video_list = any(field in video_data[0] for field in video_fields)
                    
                    if is_video_list:
                        st.success(f"✅ Found list of {len(video_data)} videos")
                        # Show sample of first video
                        with st.expander("First Video Sample"):
                            st.json(video_data[0])
                            
                        # Check for critical fields
                        has_video_id = all('video_id' in v for v in video_data if isinstance(v, dict))
                        has_views = all('views' in v for v in video_data if isinstance(v, dict)) 
                        
                        if has_video_id:
                            st.success("✅ All videos have video_id field")
                        else:
                            st.error("❌ Some videos missing video_id field")
                            
                        if has_views:
                            st.success("✅ All videos have views field")
                            # Check for zero views
                            zero_views = sum(1 for v in video_data if isinstance(v, dict) and v.get('views') == '0')
                            if zero_views:
                                st.warning(f"⚠️ {zero_views} videos have '0' views")
                        else:
                            st.error("❌ Some videos missing views field")
                    else:
                        st.warning("⚠️ List does not appear to contain video objects")
            else:
                st.error(f"❌ Unexpected data type: {data_type}")
                debug_log(f"Unexpected video data type: {data_type}")
                
            # Add a 'Copy Raw Data' button for further analysis
            st.subheader("Raw Data")
            if st.button("Copy Raw Data to Clipboard"):
                import json
                try:
                    st.session_state['_debug_clipboard'] = json.dumps(video_data, indent=2)
                    st.success("Data copied to clipboard! (Available in session state)")
                except Exception as e:
                    st.error(f"Error copying data: {str(e)}")
                    
            # Show raw data in an expandable section
            with st.expander("View Raw Data"):
                st.json(video_data)

    def render_debug_controls(self):
        """Render debug mode toggle and debug panel if enabled."""
        # Make sure debug module imports are at function level to avoid circular imports
        from .debug_ui import generate_unique_key, render_debug_panel
        from .state_management import toggle_debug_mode
        
        # Add divider to separate workflow content from debug controls
        st.divider()
        
        # Initialize debug_mode in session state if not present
        if 'debug_mode' not in st.session_state:
            st.session_state.debug_mode = False
        
        # Create a container for debug controls
        debug_container = st.container()
        
        with debug_container:
            # Use a unique key for the debug mode toggle to prevent duplicate ID errors
            toggle_key = generate_unique_key("debug_mode_toggle")
            
            # Add debug mode toggle with on_change callback
            debug_enabled = st.checkbox(
                "Debug Mode", 
                value=st.session_state.debug_mode,
                key=toggle_key
            )
            
            # Check if debug mode changed and update session state
            if debug_enabled != st.session_state.debug_mode:
                st.session_state.debug_mode = debug_enabled
                toggle_debug_mode()  # Call this to handle side effects
            
            # Show debug panel when debug mode is enabled
            if st.session_state.debug_mode:
                render_debug_panel()
