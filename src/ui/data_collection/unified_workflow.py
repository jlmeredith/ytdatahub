"""
Unified workflow implementation that combines new channel and refresh channel workflows.
This replaces the separate NewChannelWorkflow and RefreshChannelWorkflow classes.
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

# Import specific methods from the original workflows
from .new_channel_workflow import NewChannelWorkflow
from .refresh_channel_workflow import RefreshChannelWorkflow

class UnifiedWorkflow(BaseCollectionWorkflow):
    """
    Unified workflow that combines both new channel and refresh channel functionalities.
    
    Steps:
    1. Mode Selection - Choose between New Collection or Update Existing
    2. Channel Input/Selection - Enter URL/ID for new, or select from database for refresh
    3. Channel Data Review - Review and process channel information  
    4. Video Collection - Collect video data
    5. Comment Collection - Collect comment data
    """
    
    def __init__(self, youtube_service):
        """Initialize the unified workflow."""
        super().__init__(youtube_service)
        self.mode = None  # Will be set to 'new' or 'refresh'
        
        # Initialize step counter for unified workflow
        if 'unified_workflow_step' not in st.session_state:
            st.session_state['unified_workflow_step'] = 1
    
    def initialize_workflow(self, channel_input=None):
        """
        Initialize the unified workflow.
        
        Args:
            channel_input: Optional channel ID or URL (for direct initialization)
        """
        # Set initial step if not already set
        if 'unified_workflow_step' not in st.session_state:
            st.session_state['unified_workflow_step'] = 1
        
        # Store channel input if provided
        if channel_input:
            st.session_state['channel_input'] = channel_input
    
    def render_current_step(self):
        """Render the current step of the unified workflow."""
        current_step = st.session_state.get('unified_workflow_step', 1)
        
        # Set mode based on session state
        self.mode = st.session_state.get('workflow_mode', None)
        
        # Create progress indicator
        self.render_progress_indicator(current_step)
        
        # Render the appropriate step
        if current_step == 1:
            self.render_step_1_mode_selection()
        elif current_step == 2:
            if self.mode == 'new':
                self.render_step_2_new_channel_input()
            else:  # refresh mode
                self.render_step_2_channel_selection()
        elif current_step == 3:
            self.render_step_3_channel_data_review()
        elif current_step == 4:
            self.render_step_4_video_collection()
        elif current_step == 5:
            self.render_step_5_comment_collection()
        else:
            st.error("Invalid workflow step")
    
    def render_progress_indicator(self, current_step):
        """Render a progress indicator for the unified workflow."""
        steps = [
            "Mode Selection",
            "Channel Input" if self.mode == 'new' else "Channel Selection" if self.mode == 'refresh' else "Channel Setup",
            "Channel Data Review", 
            "Video Collection",
            "Comment Collection"
        ]
        
        # Create progress bar
        progress = (current_step - 1) / (len(steps) - 1) if len(steps) > 1 else 1.0
        st.progress(progress)
        
        # Create step indicators
        cols = st.columns(len(steps))
        for i, (col, step_name) in enumerate(zip(cols, steps)):
            with col:
                if i + 1 == current_step:
                    st.markdown(f"**🔵 {i+1}. {step_name}**")
                elif i + 1 < current_step:
                    st.markdown(f"✅ {i+1}. {step_name}")
                else:
                    st.markdown(f"⚪ {i+1}. {step_name}")
        
        st.divider()
    
    def render_step_1_mode_selection(self):
        """Step 1: Select workflow mode (New Collection or Update Existing)."""
        st.subheader("Step 1: Choose Collection Mode")
        
        # Check if we have existing channels to show the update option
        from src.config import Settings
        from src.storage.factory import StorageFactory
        settings = Settings()
        sqlite_db = StorageFactory.get_storage_provider("SQLite Database", settings)
        existing_channels = sqlite_db.get_channels_list()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🆕 New Collection")
            st.markdown("""
            Start fresh with a new YouTube channel:
            - Enter channel URL or ID
            - Collect complete channel data
            - Perfect for first-time data collection
            """)
            
            if st.button("Start New Collection", key="select_new_mode", type="primary"):
                self.mode = 'new'
                st.session_state['workflow_mode'] = 'new'
                st.session_state['unified_workflow_step'] = 2
                st.rerun()
        
        with col2:
            st.markdown("### 🔄 Update Existing")
            if existing_channels:
                st.markdown(f"""
                Update data for existing channels:
                - Choose from {len(existing_channels)} existing channel{'s' if len(existing_channels) != 1 else ''}
                - Compare with latest YouTube data
                - Efficient incremental updates
                """)
                
                if st.button("Update Existing Channel", key="select_refresh_mode", type="primary"):
                    self.mode = 'refresh'
                    st.session_state['workflow_mode'] = 'refresh'
                    st.session_state['unified_workflow_step'] = 2
                    st.rerun()
            else:
                st.markdown("""
                No existing channels found.
                
                *You'll need to collect data from at least one channel before you can use the update feature.*
                """)
                st.button("Update Existing Channel", key="select_refresh_mode_disabled", type="secondary", disabled=True)
        
        # Add informational section
        with st.expander("💡 Which mode should I choose?"):
            st.markdown("""
            **Choose New Collection when:**
            - This is your first time using the system
            - You want to analyze a channel you haven't collected before
            - You're starting a fresh analysis project
            
            **Choose Update Existing when:**
            - You want to refresh data for channels you've already collected
            - You need the latest metrics for ongoing analysis
            - You want to track changes over time
            """)
    
    def render_step_2_new_channel_input(self):
        """Step 2 for new mode: Channel URL/ID input."""
        st.subheader("Step 2: Enter Channel Information")
        
        # Back button
        if st.button("← Back to Mode Selection", key="back_to_mode_from_input"):
            st.session_state['unified_workflow_step'] = 1
            st.rerun()
        
        st.write("Enter a YouTube Channel URL or ID to start collecting data.")
        
        with st.form("unified_channel_form", clear_on_submit=False):
            channel_input = st.text_input(
                "Enter a YouTube Channel URL or ID:", 
                value=st.session_state.get('channel_input', ''),
                help="For example: https://www.youtube.com/c/ChannelName or UCxxxxx"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Fetch Channel Data", type="primary"):
                    if channel_input.strip():
                        st.session_state['channel_input'] = channel_input.strip()
                        st.session_state['unified_workflow_step'] = 3
                        st.rerun()
                    else:
                        st.error("Please enter a channel URL or ID")
            
            with col2:
                if st.form_submit_button("Clear Form", type="secondary"):
                    # Clear form data
                    if 'channel_input' in st.session_state:
                        del st.session_state['channel_input']
                    self.reset_workflow_state()
                    st.rerun()
        
        # Display helpful information
        with st.expander("How Data Collection Works"):
            st.write("""
            ### Collection Process
            
            1. **Channel Data**: Basic channel information like name, description, and subscriber count.
            2. **Videos**: Metadata for the channel's videos (titles, views, likes).
            3. **Comments**: Comments on the videos (optional).
            4. **Save Data**: Store collected data for analysis.
            
            ### YouTube API Quota
            
            Data collection uses YouTube API quota. Each day you have a limited number of requests.
            - Channel data: 1 unit
            - Videos list: 1 unit per 50 videos
            - Comments: 1 unit per 100 comments
            
            Tip: Start with a small number of videos and comments to save quota.
            """)
    
    def render_step_2_channel_selection(self):
        """Step 2 for refresh mode: Channel selection from database."""
        st.subheader("Step 2: Select Channel to Update")
        
        # Back button
        if st.button("← Back to Mode Selection", key="back_to_mode_from_selection"):
            st.session_state['unified_workflow_step'] = 1
            st.rerun()
        
        # Get list of channels from database
        channels = self.youtube_service.get_channels_list("sqlite")
        
        if not channels:
            st.warning("No channels found in the database.")
            st.info("You'll need to collect data from at least one channel using 'New Collection' before you can update existing channels.")
            return
        
        # Create channel selection interface
        st.write(f"Choose from {len(channels)} existing channel{'s' if len(channels) != 1 else ''} to update:")
        
        # Display channels in a more user-friendly format
        for i, channel in enumerate(channels):
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{channel['channel_name']}**")
                    st.caption(f"ID: {channel['channel_id']}")
                
                with col2:
                    # Show last updated info if available
                    if 'last_updated' in channel:
                        st.caption(f"Last updated: {channel['last_updated']}")
                    else:
                        st.caption("Last updated: Unknown")
                
                with col3:
                    if st.button("Select", key=f"select_channel_{i}", type="primary"):
                        st.session_state['channel_input'] = channel['channel_id']
                        st.session_state['selected_channel_name'] = channel['channel_name']
                        st.session_state['unified_workflow_step'] = 3
                        st.rerun()
                
                st.divider()
    
    def render_step_3_channel_data_review(self):
        """Step 3: Channel data review (shared between both modes)."""
        mode = st.session_state.get('workflow_mode', 'new')
        
        # Add navigation buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", key="back_from_channel_data"):
                st.session_state['unified_workflow_step'] = 2
                st.rerun()
        
        if mode == 'new':
            # Use NewChannelWorkflow for the channel data step
            new_workflow = NewChannelWorkflow(self.youtube_service)
            new_workflow.initialize_workflow(st.session_state.get('channel_input'))
            
            # Render the channel data step from new workflow
            new_workflow.render_step_1_channel_data()
            
            # Check if user wants to continue to next step
            # The new workflow has its own navigation, but we need to sync states
            if st.session_state.get('collection_step', 1) == 2:
                st.session_state['unified_workflow_step'] = 4
                st.session_state['collection_step'] = 1  # Reset for next workflow
                st.rerun()
            
        else:  # refresh mode
            # Use RefreshChannelWorkflow for the channel data comparison
            refresh_workflow = RefreshChannelWorkflow(self.youtube_service)
            refresh_workflow.initialize_workflow(st.session_state.get('channel_input'))
            
            # Render the channel data review from refresh workflow
            refresh_workflow.render_step_1_channel_data()
            
            # Check if user wants to continue to next step
            if st.session_state.get('refresh_workflow_step', 2) == 3:
                st.session_state['unified_workflow_step'] = 4
                st.session_state['refresh_workflow_step'] = 2  # Reset for next workflow
                st.rerun()
    
    def render_step_4_video_collection(self):
        """Step 4: Video collection (shared between both modes)."""
        mode = st.session_state.get('workflow_mode', 'new')
        
        # Navigation
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", key="back_from_video_collection"):
                st.session_state['unified_workflow_step'] = 3
                st.rerun()
        
        if mode == 'new':
            # Use NewChannelWorkflow for video collection
            new_workflow = NewChannelWorkflow(self.youtube_service)
            new_workflow.initialize_workflow(st.session_state.get('channel_input'))
            new_workflow.render_step_2_video_collection()
            
            # Check if user wants to continue to next step
            if st.session_state.get('collection_step', 1) == 4:
                st.session_state['unified_workflow_step'] = 5
                st.session_state['collection_step'] = 1  # Reset
                st.rerun()
        else:  # refresh mode
            # Use RefreshChannelWorkflow for video collection
            refresh_workflow = RefreshChannelWorkflow(self.youtube_service)
            refresh_workflow.initialize_workflow(st.session_state.get('channel_input'))
            refresh_workflow.render_step_4_video_collection()
            
            # Check if user wants to continue to next step
            if st.session_state.get('refresh_workflow_step', 2) == 5:
                st.session_state['unified_workflow_step'] = 5
                st.session_state['refresh_workflow_step'] = 2  # Reset
                st.rerun()
    
    def render_step_5_comment_collection(self):
        """Step 5: Comment collection (shared between both modes)."""
        mode = st.session_state.get('workflow_mode', 'new')
        
        # Navigation
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", key="back_from_comment_collection"):
                st.session_state['unified_workflow_step'] = 4
                st.rerun()
        
        if mode == 'new':
            # Use NewChannelWorkflow for comment collection
            new_workflow = NewChannelWorkflow(self.youtube_service)
            new_workflow.initialize_workflow(st.session_state.get('channel_input'))
            new_workflow.render_step_3_comment_collection()
        else:  # refresh mode
            # Use RefreshChannelWorkflow for comment collection
            refresh_workflow = RefreshChannelWorkflow(self.youtube_service)
            refresh_workflow.initialize_workflow(st.session_state.get('channel_input'))
            refresh_workflow.render_step_5_comment_collection()
    
    def reset_workflow_state(self):
        """Reset workflow state for a fresh start."""
        keys_to_clear = [
            'unified_workflow_step', 'workflow_mode', 'channel_input',
            'channel_info_temp', 'channel_data_fetched', 'channel_fetch_failed',
            'collection_step', 'videos_fetched', 'comments_fetched',
            'api_data', 'delta_summary', 'debug_logs', 'last_api_call',
            'new_channel_max_videos', 'selected_channel_name',
            'refresh_workflow_step'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Reset to initial state
        st.session_state['unified_workflow_step'] = 1
    
    # Delegate abstract methods to be implemented by the workflow classes
    def render_step_1_channel_data(self):
        """This is replaced by the unified workflow steps."""
        pass
    
    def save_data(self):
        """Save collected data to the database by delegating to the appropriate workflow."""
        workflow_mode = st.session_state.get('unified_workflow_mode', 'new_collection')
        
        if workflow_mode == 'new_collection' and self.new_channel_workflow:
            return self.new_channel_workflow.save_data()
        elif workflow_mode == 'update_existing' and self.refresh_channel_workflow:
            return self.refresh_channel_workflow.save_data()
        else:
            st.error("❌ No active workflow to save data. Please complete the previous steps.")
            return False
