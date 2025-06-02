"""
Main entry point for data collection UI.
Renders the data collection tab and orchestrates the UI components.
"""
import streamlit as st
import os
from src.utils.debug_utils import debug_log, ensure_debug_panel_state
from src.services.youtube_service import YouTubeService
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH

from .state_management import initialize_session_state, toggle_debug_mode
from .steps_ui import render_collection_steps
from .comparison_ui import render_comparison_view
from .debug_ui import render_debug_panel
from .utils.delta_reporting import render_delta_report

# Import workflow components (these will replace channel_refresh_section)
from .workflow_base import BaseCollectionWorkflow
from .workflow_factory import create_workflow

def render_data_collection_tab():
    """
    Render the Data Collection tab UI.
    """
    st.header("📥 Data Collection")
    st.markdown("*Collect YouTube data to power your analytics insights*")

    # Check if analytics data exists
    from src.config import Settings
    from src.storage.factory import StorageFactory
    settings = Settings()
    sqlite_db = StorageFactory.get_storage_provider("SQLite Database", settings)
    existing_channels = sqlite_db.get_channels_list()
    
    if existing_channels:
        st.info(f"📊 **Good news!** You already have data from {len(existing_channels)} channel{'s' if len(existing_channels) != 1 else ''}. You can collect more data or update existing channels below.")
    else:
        st.markdown("### 🚀 Start Your Analytics Journey")
        st.markdown("Collect your first YouTube channel data to unlock powerful analytics features.")
    
    # Emphasize analytics purpose
    with st.expander("💡 Why Collect Data?", expanded=not existing_channels):
        st.markdown("""
        **Data collection enables powerful analytics:**
        
        📈 **Performance Tracking**: Monitor views, likes, and engagement trends over time  
        📹 **Content Analysis**: Identify your best-performing videos and content patterns  
        💬 **Audience Insights**: Understand what your viewers are saying in comments  
        📊 **Growth Analytics**: Track channel growth and subscriber engagement
        
        *The more data you collect, the richer your analytics insights become.*
        """)

    # Add custom CSS to improve tab visibility and styling
    st.markdown("""
    <style>
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 5px 10px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        font-weight: 600;
        margin: 5px 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 99, 132, 0.7) !important;
        color: white !important.
    }
    
    /* Add styling for comparison tables */
    .comparison-table th {
        background-color: rgba(255, 255, 255, 0.1);
        font-weight: 600;
    }
    
    .comparison-table td.changed {
        background-color: rgba(255, 255, 0, 0.2);
        font-weight: 600;
    }

    /* Add styling for debug panel */
    .debug-container {
        margin-top: 30px;
        padding-top: 10px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state variables if they don't exist
    initialize_session_state()
    
    # Ensure debug_mode is initialized
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    # API Key input
    api_key = os.getenv('YOUTUBE_API_KEY', '')
    user_api_key = st.text_input("Enter YouTube API Key:", value=api_key, type="password")
    
    if user_api_key:
        # Initialize YouTube service
        youtube_service = YouTubeService(user_api_key)
        st.session_state.api_key = user_api_key
        
        # Store service initialization status for debug purposes
        st.session_state.api_initialized = True
        
        # Ensure debug panel state
        ensure_debug_panel_state()
        
        # MAIN UI RENDERING BASED ON VIEW STATE
        
        # Check if we're in comparison view mode
        if st.session_state.get('compare_data_view', False):
            # Render comparison view
            render_comparison_view(youtube_service)
            
            # Add a button to go back to the update channel tab
            if st.button("Back to Update Channel", key="back_to_update_from_comparison"):
                st.session_state.compare_data_view = False
                # Reset workflow step to start fresh next time
                if 'refresh_workflow_step' in st.session_state:
                    st.session_state.refresh_workflow_step = 1
                st.rerun()
        else:
            # Use unified workflow instead of separate tabs
            st.subheader("YouTube Data Collection")
            st.markdown("*Streamlined workflow for both new and existing channels*")
            
            # Create and render unified workflow
            from .workflow_factory import create_workflow
            workflow = create_workflow(youtube_service, "unified")
            workflow.initialize_workflow()
            workflow.render_current_step()
        
        # Debug panel toggle and rendering
        st.divider()
        show_debug_panel = st.checkbox(
            "Show Debug Panel", 
            value=st.session_state.get('show_debug_panel', False),
            key="show_debug_panel_checkbox_collection",
            help="Enable to display the debug panel for troubleshooting."
        )
        if show_debug_panel != st.session_state.get('show_debug_panel', False):
            st.session_state.show_debug_panel = show_debug_panel
            st.rerun()
        if st.session_state.get('show_debug_panel', False):
            from .debug_ui import render_debug_panel
            render_debug_panel()
    else:
        st.error("Please enter a YouTube API Key")