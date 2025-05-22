"""
Base workflow for YouTube data collection.
This module defines a common interface for both new channel and refresh workflows.
"""
import streamlit as st
from abc import ABC, abstractmethod

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
    
    @abstractmethod
    def render_step_2_video_collection(self):
        """Render step 2: Collect and display video data."""
        pass
    
    @abstractmethod
    def render_step_3_comment_collection(self):
        """Render step 3: Collect and display comment data."""
        pass
    
    @abstractmethod
    def save_data(self):
        """Save collected data to the database."""
        pass
    
    def render_current_step(self):
        """
        Render the current step of the workflow based on the session state.
        """
        # Get the current step from session state
        current_step = self._get_current_step()
        
        # Render the appropriate step
        if current_step == 1:
            self.render_step_1_channel_data()
        elif current_step == 2:
            self.render_step_2_video_collection()
        elif current_step == 3:
            self.render_step_3_comment_collection()
        else:
            st.error(f"Unknown step: {current_step}")
    
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
