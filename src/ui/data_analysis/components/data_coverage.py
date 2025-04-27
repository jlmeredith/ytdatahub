"""
Data coverage dashboard component for analyzing data completeness and offering update options.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.helpers import debug_log, format_number
from src.utils.background_tasks import queue_data_collection_task, get_all_task_statuses

def render_data_coverage_dashboard(channel_data, db=None):
    """
    Render the data coverage dashboard showing data completeness and update options.
    
    Args:
        channel_data: Dictionary containing channel data for one or more channels
        db: Database connection (optional)
    """
    # Check if we're dealing with multiple channels
    if isinstance(channel_data, dict) and any(isinstance(v, dict) and 'channel_info' in v for v in channel_data.values()):
        # Multiple channels case
        channels_dict = channel_data
        is_multi_channel = True
    else:
        # Single channel case (for backward compatibility)
        channels_dict = {'Single Channel': channel_data}
        is_multi_channel = False
    
    # Use caching for analysis results if enabled
    use_cache = st.session_state.get('use_data_cache', True)
    
    # Initialize analysis object
    analysis = YouTubeAnalysis()
    
    # Add introductory text about the dashboard
    st.markdown("""
    ### Data Coverage Analysis
    
    This dashboard shows how complete your YouTube data is for each channel and provides options to update it.
    """)
    
    # Show current background tasks if any are running
    background_tasks = get_all_task_statuses()
    running_tasks = {task_id: task for task_id, task in background_tasks.items() 
                    if task['status'] in ['queued', 'running']}
    
    if running_tasks:
        st.info(f"🔄 **{len(running_tasks)} background data collection tasks running.** These will update automatically when complete.")
        
        # Show progress of running tasks in an expander
        with st.expander("View Background Tasks"):
            for task_id, task in running_tasks.items():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                # Get channel name from the task if available
                channel_id = task.get('channel_id', 'Unknown')
                channel_name = channel_id
                if 'result' in task and task['result'] and 'channel_info' in task['result']:
                    channel_name = task['result']['channel_info'].get('title', channel_id)
                
                with col1:
                    st.write(f"**Channel:** {channel_name}")
                
                with col2:
                    status = task['status'].capitalize()
                    if status == 'Running':
                        # Add elapsed time if task is running
                        if task.get('started_at'):
                            started = datetime.fromisoformat(task['started_at'])
                            elapsed = datetime.now() - started
                            elapsed_mins = int(elapsed.total_seconds() / 60)
                            st.write(f"**Status:** {status} ({elapsed_mins} min)")
                        else:
                            st.write(f"**Status:** {status}")
                    else:
                        st.write(f"**Status:** {status}")
                
                with col3:
                    if task.get('queued_at'):
                        queued = datetime.fromisoformat(task['queued_at'])
                        queued_time = queued.strftime("%H:%M:%S")
                        st.write(f"**Queued at:** {queued_time}")
                        
                # Show task options in smaller text
                options = task.get('options', {})
                if options:
                    option_text = []
                    if options.get('fetch_channel_data', False):
                        option_text.append("Channel Info")
                    if options.get('fetch_videos', False):
                        video_count = options.get('max_videos', 0)
                        if video_count == 0:
                            option_text.append("All Videos")
                        else:
                            option_text.append(f"{video_count} Videos")
                    if options.get('fetch_comments', False):
                        comment_count = options.get('max_comments_per_video', 0)
                        if comment_count == 0:
                            option_text.append("No Comments")
                        else:
                            option_text.append(f"{comment_count} Comments/Video")
                    
                    st.caption(f"Collecting: {', '.join(option_text)}")
                
                # Add a separator
                st.divider()
    
    # Process each channel and collect data coverage metrics
    coverage_data = []
    
    for channel_name, channel_data in channels_dict.items():
        # Get data coverage information
        cache_key = f"data_coverage_{channel_name}"
        if use_cache and cache_key in st.session_state:
            debug_log(f"Using cached data coverage for: {channel_name}")
            coverage_info = st.session_state[cache_key]
        else:
            coverage_info = analysis.get_data_coverage(channel_data)
            
            # Cache the result
            if use_cache:
                st.session_state[cache_key] = coverage_info
                debug_log(f"Cached data coverage for: {channel_name}")
        
        # Add to the coverage data list for display
        coverage_data.append({
            'Channel': channel_name,
            'Total Videos (Reported)': coverage_info['total_videos_reported'],
            'Videos Collected': coverage_info['total_videos_collected'],
            'Videos with Details': coverage_info['videos_with_details'],
            'Videos with Comments': coverage_info['videos_with_comments'],
            'Video Coverage (%)': round(coverage_info['video_coverage_percent'], 1),
            'Comment Coverage (%)': round(coverage_info['comment_coverage_percent'], 1),
            'Latest Video': coverage_info['latest_video_date'].strftime('%b %d, %Y') if coverage_info['latest_video_date'] else 'N/A',
            'Oldest Video': coverage_info['oldest_video_date'].strftime('%b %d, %Y') if coverage_info['oldest_video_date'] else 'N/A',
            'Recommendations': coverage_info['update_recommendations'],
            '_coverage_info': coverage_info  # Store full info for later use
        })
    
    # Convert to dataframe for display
    coverage_df = pd.DataFrame(coverage_data)
    
    # If we have multiple channels, show a comparison table
    if is_multi_channel and len(coverage_df) > 1:
        st.subheader("Channel Data Coverage Comparison")
        
        # Create display columns for the table (hiding internal fields)
        display_cols = [col for col in coverage_df.columns if not col.startswith('_')]
        display_df = coverage_df[display_cols].copy()
        
        # Format percentages
        for col in ['Video Coverage (%)', 'Comment Coverage (%)']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else 'N/A')
        
        # Format counts with thousands separator
        for col in ['Total Videos (Reported)', 'Videos Collected', 'Videos with Details', 'Videos with Comments']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) and x > 0 else '0')
        
        # Hide recommendations in table
        if 'Recommendations' in display_df.columns:
            display_df = display_df.drop(columns=['Recommendations'])
        
        # Display the comparison table
        st.dataframe(
            display_df,
            column_config={
                "Channel": st.column_config.TextColumn("Channel", width="medium"),
                "Total Videos (Reported)": st.column_config.TextColumn("Total Videos", width="small", help="Total videos available on YouTube"),
                "Videos Collected": st.column_config.TextColumn("Videos Collected", width="small", help="Number of videos in your database"),
                "Videos with Details": st.column_config.TextColumn("With Details", width="small", help="Videos with complete metadata"),
                "Videos with Comments": st.column_config.TextColumn("With Comments", width="small", help="Videos with comments collected"),
                "Video Coverage (%)": st.column_config.TextColumn("Video Coverage", width="small", help="Percentage of channel's videos in your database"),
                "Comment Coverage (%)": st.column_config.TextColumn("Comment Coverage", width="small", help="Percentage of collected videos that have comments"),
                "Latest Video": st.column_config.TextColumn("Latest Video", width="small", help="Date of most recent video in database"),
                "Oldest Video": st.column_config.TextColumn("Oldest Video", width="small", help="Date of oldest video in database")
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Now visualize the data coverage with charts
    st.subheader("Data Coverage Visualization")
    
    # Create column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Create video coverage bar chart
        try:
            coverage_data = coverage_df[['Channel', 'Video Coverage (%)', 'Comment Coverage (%)']].copy()
            coverage_data = coverage_data.sort_values('Video Coverage (%)', ascending=False)
            
            # Melt the dataframe for easier plotting
            coverage_melted = pd.melt(coverage_data, 
                                    id_vars=['Channel'], 
                                    value_vars=['Video Coverage (%)', 'Comment Coverage (%)'],
                                    var_name='Coverage Type', 
                                    value_name='Percentage')
            
            # Map the coverage types to more readable labels
            coverage_melted['Coverage Type'] = coverage_melted['Coverage Type'].map({
                'Video Coverage (%)': 'Videos Collected',
                'Comment Coverage (%)': 'Videos with Comments'
            })
            
            # Create the bar chart
            fig = px.bar(
                coverage_melted,
                x='Channel',
                y='Percentage',
                color='Coverage Type',
                title="Video & Comment Coverage by Channel",
                labels={'Percentage': 'Coverage (%)', 'Channel': 'Channel Name'},
                barmode='group'
            )
            
            fig.update_layout(
                yaxis=dict(title='Coverage (%)', range=[0, 105]),  # Limit to 0-105% for better scale
                xaxis=dict(title=''),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Add percentage annotations on bars
            fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating coverage chart: {str(e)}")
    
    with col2:
        # Create a temporal coverage chart (how many videos from different time periods)
        try:
            # Prepare data for temporal coverage
            temporal_data = []
            
            for idx, row in coverage_df.iterrows():
                channel = row['Channel']
                coverage_info = row['_coverage_info']
                
                # Get temporal coverage data
                temporal = coverage_info['temporal_coverage']
                
                # Add to temporal data
                temporal_data.append({
                    'Channel': channel,
                    'Last Month': temporal['last_month'],
                    'Last 6 Months': temporal['last_6_months'],
                    'Last Year': temporal['last_year'],
                    'Older': temporal['older']
                })
            
            # Create dataframe
            temporal_df = pd.DataFrame(temporal_data)
            
            # Melt for easier plotting
            temporal_melted = pd.melt(
                temporal_df,
                id_vars=['Channel'],
                value_vars=['Last Month', 'Last 6 Months', 'Last Year', 'Older'],
                var_name='Time Period',
                value_name='Percentage'
            )
            
            # Create stacked bar chart
            fig = px.bar(
                temporal_melted,
                x='Channel',
                y='Percentage',
                color='Time Period',
                title="Temporal Coverage Distribution",
                labels={'Percentage': 'Percentage (%)', 'Channel': 'Channel Name'},
                barmode='stack'
            )
            
            # Update layout
            fig.update_layout(
                yaxis=dict(title='Percentage of Videos (%)', range=[0, 105]),
                xaxis=dict(title=''),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating temporal coverage chart: {str(e)}")
    
    # Create a channel selector for updating data
    st.subheader("Update Channel Data")
    st.markdown("""
    Select a channel to update its data. Updates will run in the background while you continue analyzing.
    """)
    
    # Get API key for data collection
    api_key = os.getenv('YOUTUBE_API_KEY', '')
    
    # First check if we have an API key in session state or in environment
    use_api_key = st.session_state.get('api_key', api_key)
    
    if not use_api_key:
        # No API key available, show input
        api_key_input = st.text_input("Enter YouTube API Key for data collection:", 
                                      type="password")
        st.session_state.api_key = api_key_input
        use_api_key = api_key_input
    
    if use_api_key:
        # Create two columns for layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Channel selector
            selected_channel = st.selectbox(
                "Select channel to update",
                options=coverage_df['Channel'].tolist(),
                key="update_channel_selector"
            )
        
        # Get selected channel's data
        if selected_channel:
            selected_data = coverage_df[coverage_df['Channel'] == selected_channel].iloc[0]
            coverage_info = selected_data['_coverage_info']
            recommendations = coverage_info['update_recommendations']
            
            # Display recommendations for the selected channel
            if recommendations:
                with col2:
                    st.info(f"Recommendations: {', '.join(recommendations)}")
            
            # Create update options
            st.subheader(f"Update Options for {selected_channel}")
            
            # Get channel ID from the actual data
            channel_id = "unknown"
            channel_data = channels_dict.get(selected_channel)
            if channel_data and 'channel_info' in channel_data and 'id' in channel_data['channel_info']:
                channel_id = channel_data['channel_info']['id']
            
            # Create option sections using columns
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown("#### Content to Update")
                update_channel_info = st.checkbox("Update Channel Info", key="update_channel_info", value=True)
                update_videos = st.checkbox("Update Videos", key="update_videos", value=True)
                update_comments = st.checkbox("Update Comments", key="update_comments", value=False)
            
            with col2:
                st.markdown("#### Amount to Collect")
                # Determine max videos for slider based on total in API
                max_videos_api = coverage_info['total_videos_reported']
                current_videos = coverage_info['total_videos_collected']
                
                video_options = st.radio(
                    "Videos to collect:",
                    options=["Only new videos", "Custom number", "All available"],
                    key="video_update_options"
                )
                
                if video_options == "Custom number":
                    # Custom number selected, show slider
                    max_videos = st.slider(
                        "Number of videos to collect",
                        min_value=5,
                        max_value=min(500, max(10, max_videos_api)),
                        value=min(50, max_videos_api),
                        step=5,
                        key="update_max_videos"
                    )
                elif video_options == "All available":
                    # All videos selected
                    max_videos = 0  # 0 means all
                    st.info(f"Will collect all available videos (up to {max_videos_api})")
                else:
                    # Only new videos selected
                    videos_to_collect = max(0, max_videos_api - current_videos)
                    max_videos = videos_to_collect
                    st.info(f"Will collect {videos_to_collect} new videos since last update")
                
                # Comment options
                if update_comments:
                    max_comments = st.slider(
                        "Comments per video",
                        min_value=0,
                        max_value=100,
                        value=20,
                        step=5,
                        key="update_max_comments"
                    )
                else:
                    max_comments = 0
            
            with col3:
                st.markdown("#### Update Settings")
                save_immediately = st.checkbox("Save to database immediately", value=True, key="save_immediately")
                
                # Calculate API usage estimate
                from src.utils.helpers import estimate_quota_usage
                quota = estimate_quota_usage(
                    fetch_channel=update_channel_info,
                    fetch_videos=update_videos,
                    fetch_comments=update_comments,
                    video_count=max_videos if max_videos > 0 else max_videos_api,
                    comments_count=max_comments
                )
                
                st.info(f"Estimated API quota usage: {quota} units")
                
                # Start update button
                if st.button("Start Background Update", key="start_update", type="primary"):
                    if channel_id != "unknown":
                        # Create options for collection
                        options = {
                            'fetch_channel_data': update_channel_info,
                            'fetch_videos': update_videos,
                            'fetch_comments': update_comments,
                            'max_videos': max_videos,
                            'max_comments_per_video': max_comments,
                            'save_to_storage': save_immediately,
                            'storage_type': 'SQLite Database'  # Default to SQLite
                        }
                        
                        # Queue the background task
                        task_id = queue_data_collection_task(channel_id, use_api_key, options)
                        
                        st.success(f"✅ Update task queued for {selected_channel}!")
                        st.markdown("""
                        The update is now running in the background. You can continue using the application.
                        This section will automatically refresh when the update is complete.
                        """)
                    else:
                        st.error("Could not determine channel ID. Please try again.")
    else:
        st.warning("No YouTube API key available. Please enter an API key to update channel data.")
    
    # Add a section for task history
    completed_tasks = {task_id: task for task_id, task in background_tasks.items() 
                     if task['status'] in ['completed', 'error']}
    
    if completed_tasks:
        st.subheader("Recently Completed Tasks")
        
        with st.expander("View Task History"):
            # Convert to dataframe for sorting
            tasks_df = pd.DataFrame([
                {
                    'Channel': task.get('channel_id', 'Unknown'),
                    'Status': task['status'].capitalize(),
                    'Started': datetime.fromisoformat(task['started_at']) if task.get('started_at') else None,
                    'Completed': datetime.fromisoformat(task['completed_at']) if task.get('completed_at') else None,
                    'Duration': (datetime.fromisoformat(task['completed_at']) - datetime.fromisoformat(task['started_at'])).total_seconds() / 60 if task.get('completed_at') and task.get('started_at') else None,
                    'Result': 'Success' if task.get('result') else ('Error: ' + task.get('error', 'Unknown error')),
                    'Saved': task.get('saved_to_storage', False)
                }
                for task_id, task in completed_tasks.items()
            ])
            
            # Sort by completion time
            if not tasks_df.empty and 'Completed' in tasks_df.columns:
                tasks_df = tasks_df.sort_values('Completed', ascending=False)
            
            # Format duration
            if 'Duration' in tasks_df.columns:
                tasks_df['Duration'] = tasks_df['Duration'].apply(lambda x: f"{x:.1f} min" if pd.notnull(x) else "Unknown")
            
            # Format timestamps
            for col in ['Started', 'Completed']:
                if col in tasks_df.columns:
                    tasks_df[col] = tasks_df[col].apply(lambda x: x.strftime("%Y-%m-%d %H:%M") if pd.notnull(x) else "Unknown")
            
            # Display dataframe
            st.dataframe(tasks_df, use_container_width=True)
            
            # Add clear history button
            if st.button("Clear Task History"):
                # Import here to avoid circular imports
                from src.utils.background_tasks import clear_completed_tasks
                clear_completed_tasks()
                st.success("Task history cleared")
                st.rerun()  # Force refresh of the UI