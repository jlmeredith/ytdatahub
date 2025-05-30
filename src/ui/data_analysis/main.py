"""
Main entry point for the Data Analysis tab UI.
"""
import streamlit as st
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.ui.data_analysis.components import (
    render_channel_selector,
    render_video_explorer,
    render_analytics_dashboard,
    render_comment_explorer,
    render_data_coverage_dashboard
)
from src.ui.data_analysis.utils.session_state import initialize_chart_toggles, initialize_analysis_section
from src.utils.debug_utils import debug_log
from src.utils.logging_utils import log_error

def render_data_analysis_tab():
    """Render the data analysis tab."""
    st.header("YouTube Channel Analytics")
    
    # Initialize session state for chart display toggles and active section
    initialize_chart_toggles()
    initialize_analysis_section()
    
    # Check if channel has changed since last render
    channel_changed = ('previous_channel' in st.session_state and 
                      'selected_channel' in st.session_state and 
                      st.session_state.previous_channel != st.session_state.selected_channel)
    
    if channel_changed:
        debug_log(f"Channel changed from {st.session_state.previous_channel} to {st.session_state.selected_channel}")
        # Clear all channel-specific caches when channel changes
        keys_to_delete = []
        for key in st.session_state.keys():
            if (key.startswith('analysis_') or 
                key.startswith('channel_data_') or 
                key.startswith('chart_') or 
                key.startswith('video_') or 
                key.startswith('comment_')):
                keys_to_delete.append(key)
        
        # Delete the keys in a separate loop to avoid modifying during iteration
        for key in keys_to_delete:
            del st.session_state[key]
        
        debug_log(f"Cleared {len(keys_to_delete)} cached items due to channel change")
    
    # Connect to database
    try:
        db = SQLiteDatabase(SQLITE_DB_PATH)
        channels = db.get_channels_list()
        
        # Add sidebar navigation and controls for the Data Analysis section
        with st.sidebar:
            st.subheader("Analytics Navigation")
            
            # Show data status
            if not channels:
                st.warning("⚠️ No channels found in database")
                st.info("💡 Go to 'Data Collection' tab to add channels first")
                st.divider()
            else:
                st.success(f"✅ {len(channels)} channel(s) available")
                st.divider()
            
            # Create section selector with buttons stacked vertically
            st.write("Select Analysis Section")
            
            if st.button("📊 Dashboard", 
                        key="dashboard_btn", 
                        use_container_width=True,
                        type="primary" if st.session_state.active_analysis_section == "dashboard" else "secondary"):
                st.session_state.active_analysis_section = "dashboard"
                st.rerun()
            
            if st.button("📈 Data Coverage", 
                        key="coverage_btn", 
                        use_container_width=True,
                        type="primary" if st.session_state.active_analysis_section == "coverage" else "secondary"):
                st.session_state.active_analysis_section = "coverage"
                st.rerun()
            
            if st.button("🎬 Videos", 
                        key="videos_btn", 
                        use_container_width=True,
                        type="primary" if st.session_state.active_analysis_section == "videos" else "secondary"):
                st.session_state.active_analysis_section = "videos"
                st.rerun()
            
            if st.button("💬 Comments", 
                        key="comments_btn", 
                        use_container_width=True,
                        type="primary" if st.session_state.active_analysis_section == "comments" else "secondary"):
                st.session_state.active_analysis_section = "comments"
                st.rerun()
            
            # Show different chart options based on selected section
            if st.session_state.active_analysis_section == "dashboard":
                st.subheader("Dashboard Display Options")
                
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
                
                # Add more dashboard options
                st.checkbox("Show Engagement Ratios", value=st.session_state.get("show_engagement_ratios", False), key="engagement_ratios_checkbox")
                st.checkbox("Show Performance Metrics", value=st.session_state.get("show_performance_metrics", False), key="performance_metrics_checkbox")
                
                # Add trendline options
                st.subheader("Trend Analysis")
                st.checkbox("Show Trend Lines", value=st.session_state.get("show_trend_lines", False), key="trend_lines_checkbox")
                if st.session_state.get("show_trend_lines", False):
                    st.select_slider("Trend Window", options=["Small", "Medium", "Large"], value=st.session_state.get("trend_window", "Medium"), key="trend_window_slider")
            
            elif st.session_state.active_analysis_section == "coverage":
                st.subheader("Coverage Display Options")
                st.checkbox("Show Data Recommendations", value=st.session_state.get("show_data_recommendations", True), key="data_recommendations_checkbox")
                st.checkbox("Auto-refresh Data", value=st.session_state.get("auto_refresh_data", True), key="auto_refresh_data_checkbox")
                
                # Add refresh interval control
                if st.session_state.get("auto_refresh_data", True):
                    st.select_slider("Refresh Interval", 
                                    options=["30 seconds", "1 minute", "5 minutes"], 
                                    value=st.session_state.get("refresh_interval", "1 minute"), 
                                    key="refresh_interval_slider")
            
            elif st.session_state.active_analysis_section == "videos":
                st.subheader("Video Explorer Options")
                st.slider("Results per page", min_value=5, max_value=50, value=st.session_state.get("video_page_size", 10), step=5, key="video_page_size_slider")
                st.checkbox("Show Video Thumbnails", value=st.session_state.get("show_video_thumbnails", False), key="video_thumbnails_checkbox")
                sort_options = ["Published (Newest)", "Published (Oldest)", "Views (Highest)", "Views (Lowest)", "Likes (Highest)", "Duration (Longest)"]
                st.selectbox("Sort Videos By", options=sort_options, index=sort_options.index(st.session_state.get("video_sort_by", "Published (Newest)")), key="video_sort_selector")
            
            elif st.session_state.active_analysis_section == "comments":
                st.subheader("Comment Analysis Options")
                st.slider("Comments per page", min_value=5, max_value=50, value=st.session_state.get("comment_page_size", 10), step=5, key="comment_page_size_slider")
                st.checkbox("Show Sentiment Analysis", value=st.session_state.get("show_comment_sentiment", False), key="comment_sentiment_checkbox")
                st.checkbox("Show Word Clouds", value=st.session_state.get("show_word_clouds", False), key="word_clouds_checkbox")
                
            # Add a cache control section
            st.subheader("Cache Controls")
            cache_enabled = st.toggle("Enable Data Caching", value=st.session_state.get('use_data_cache', True))
            if cache_enabled != st.session_state.get('use_data_cache', True):
                st.session_state.use_data_cache = cache_enabled
                # Clear all analysis caches if caching is disabled
                if not cache_enabled:
                    keys_to_delete = []
                    for key in st.session_state.keys():
                        if (key.startswith('channel_data_') or 
                            key.startswith('analysis_') or 
                            key.startswith('chart_')):
                            keys_to_delete.append(key)
                    
                    for key in keys_to_delete:
                        del st.session_state[key]
                        
                    st.success("Cache cleared. Data will be reloaded from the database.")
                    st.rerun()
            
            if st.button("Clear Cache and Reload Data"):
                # Clear all analysis and channel data caches
                keys_to_delete = []
                for key in st.session_state.keys():
                    if (key.startswith('channel_data_') or 
                        key.startswith('analysis_') or 
                        key.startswith('chart_')):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del st.session_state[key]
                    
                st.success("Cache cleared. Data will be reloaded from the database.")
                st.rerun()
        
        # The channel selector will always be visible at the top
        # Render channel selector component first to establish selected channel
        if channels:
            with st.spinner("Retrieving channel list..."):
                selected_channel, channel_data = render_channel_selector(channels, db)
            
            if not selected_channel or not channel_data:
                st.warning("No channel data found in database. Please collect data first.")
                return
        else:
            # No channels available - show helpful message
            st.warning("📊 No channels found in the database")
            st.info("""
            To get started with data analysis:
            1. Go to the **Data Collection** tab
            2. Add a YouTube channel by entering its URL or Channel ID
            3. Collect some data (videos, comments, etc.)
            4. Return here to analyze your data
            """)
            
            # Show the analysis section selector cards even without data
            st.subheader("Available Analysis Sections")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                ### 📊 Dashboard
                Get a comprehensive overview of your channel's performance metrics and trends.
                """)
                st.button("View Dashboard", key="dashboard_card_btn", disabled=True)
                    
                st.markdown("""
                ### 🎬 Videos
                Explore your videos and analyze their individual performance.
                """)
                st.button("Explore Videos", key="videos_card_btn", disabled=True)
            
            with col2:
                st.markdown("""
                ### 📈 Data Coverage
                Check the completeness of your data and update it as needed.
                """)
                st.button("Check Data Coverage", key="coverage_card_btn", disabled=True)
                    
                st.markdown("""
                ### 💬 Comments
                Analyze comments, sentiment, and audience engagement.
                """)
                st.button("Analyze Comments", key="comments_card_btn", disabled=True)
            
            return
        
        # Handle the case when no analysis section is selected
        if st.session_state.active_analysis_section is None:
            st.info("Select an analysis section from the sidebar to begin exploring your YouTube data.")
            
            # Display quick selection cards to choose an analysis section
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                ### 📊 Dashboard
                Get a comprehensive overview of your channel's performance metrics and trends.
                """)
                if st.button("View Dashboard", key="dashboard_card_btn"):
                    st.session_state.active_analysis_section = "dashboard"
                    st.rerun()
                    
                st.markdown("""
                ### 🎬 Videos
                Explore your videos and analyze their individual performance.
                """)
                if st.button("Explore Videos", key="videos_card_btn"):
                    st.session_state.active_analysis_section = "videos"
                    st.rerun()
            
            with col2:
                st.markdown("""
                ### 📈 Data Coverage
                Check the completeness of your data and update it as needed.
                """)
                if st.button("Check Data Coverage", key="coverage_card_btn"):
                    st.session_state.active_analysis_section = "coverage"
                    st.rerun()
                    
                st.markdown("""
                ### 💬 Comments
                Analyze comments, sentiment, and audience engagement.
                """)
                if st.button("Analyze Comments", key="comments_card_btn"):
                    st.session_state.active_analysis_section = "comments"
                    st.rerun()
            
            return
            
        # Handle channel data display based on active section
        try:
            # Display current section info
            component_name = {
                "dashboard": "Analytics Dashboard",
                "coverage": "Data Coverage",
                "videos": "Video Explorer",
                "comments": "Comment Analysis"
            }.get(st.session_state.active_analysis_section, "data")
            
            st.subheader(f"{component_name} for {selected_channel}")
            
            # Show a loading spinner while rendering the component
            with st.spinner(f"Loading {component_name.lower()} data..."):
                if st.session_state.active_analysis_section == "dashboard":
                    render_analytics_dashboard(channel_data)
                elif st.session_state.active_analysis_section == "coverage":
                    render_data_coverage_dashboard(channel_data, db)
                elif st.session_state.active_analysis_section == "videos":
                    render_video_explorer(channel_data)
                elif st.session_state.active_analysis_section == "comments":
                    render_comment_explorer(channel_data)
        except Exception as e:
            # Use the centralized error logging function
            error_message = log_error(e, f"rendering {component_name}", {
                "active_section": st.session_state.active_analysis_section,
                "selected_channel": selected_channel
            })
            
            # Show error in the UI
            st.error(f"Error rendering {component_name}: {str(e)}")
            st.info("Try clearing the cache and reloading the data using the button in the sidebar.")
            
    except Exception as e:
        # Use the centralized error logging function for main errors
        error_message = log_error(e, "data analysis tab", {
            "active_section": st.session_state.get('active_analysis_section', 'unknown')
        })
        
        # Show error in the UI
        st.error(f"Error analyzing YouTube data: {str(e)}")