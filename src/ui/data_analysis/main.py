"""
Main entry point for the Data Analysis tab UI.
"""
import streamlit as st
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.ui.data_analysis.components.channel_selector import render_channel_selector
from src.ui.data_analysis.components.video_explorer import render_video_explorer
from src.ui.data_analysis.components.analytics_dashboard import render_analytics_dashboard
from src.ui.data_analysis.components.comment_explorer import render_comment_explorer
from src.ui.data_analysis.utils.session_state import initialize_chart_toggles

def render_data_analysis_tab():
    """Render the data analysis tab."""
    st.header("YouTube Channel Analytics")
    
    # Warn if no API key is set (needed for charts)
    if 'api_key' not in st.session_state or not st.session_state.api_key:
        st.warning("No YouTube API key set. Some functionality may be limited.")
    
    # Connect to database
    try:
        db = SQLiteDatabase(SQLITE_DB_PATH)
        channels = db.get_channels_list()
        
        if not channels:
            st.warning("No channels found in the database. Please collect data first.")
            return
        
        # Initialize session state for chart display toggles
        initialize_chart_toggles()
        
        # Add sidebar controls for chart display
        with st.sidebar:
            st.subheader("Chart Display Options")
            
            # Use session state values as defaults and update session state on change
            views_chart = st.checkbox("Show Views Chart", value=st.session_state.show_views_chart, key="views_checkbox")
            likes_chart = st.checkbox("Show Likes Chart", value=st.session_state.show_likes_chart, key="likes_checkbox")
            comments_chart = st.checkbox("Show Comments Chart", value=st.session_state.show_comments_chart, key="comments_checkbox")
            duration_chart = st.checkbox("Show Duration Chart", value=st.session_state.show_duration_chart, key="duration_checkbox")
            
            # Update session state if checkboxes changed
            if views_chart != st.session_state.show_views_chart:
                st.session_state.show_views_chart = views_chart
                st.rerun()
            if likes_chart != st.session_state.show_likes_chart:
                st.session_state.show_likes_chart = likes_chart
                st.rerun()
            if comments_chart != st.session_state.show_comments_chart:
                st.session_state.show_comments_chart = comments_chart
                st.rerun()
            if duration_chart != st.session_state.show_duration_chart:
                st.session_state.show_duration_chart = duration_chart
                st.rerun()
        
        # Render channel selector component
        selected_channel, channel_data = render_channel_selector(channels, db)
        
        if selected_channel and channel_data:
            # Render the UI components
            with st.expander("Video Data Explorer", expanded=True):
                render_video_explorer(channel_data)
            
            with st.expander("Analytics Dashboard", expanded=True):
                render_analytics_dashboard(channel_data)
                
            with st.expander("Comment Analysis", expanded=True):
                render_comment_explorer(channel_data)
        else:
            st.warning("No channel data found in database. Please collect data first.")
            
    except Exception as e:
        st.error(f"Error analyzing YouTube data: {str(e)}")