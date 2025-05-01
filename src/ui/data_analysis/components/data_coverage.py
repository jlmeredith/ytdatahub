"""
Data coverage dashboard component for analyzing data completeness and offering update options.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time

from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.helpers import debug_log, format_number
from src.utils.background_tasks import queue_data_collection_task, get_all_task_statuses

# Ensure all required session state variables are initialized
if 'background_tasks_status' not in st.session_state:
    st.session_state.background_tasks_status = {}

if 'performance_timers' not in st.session_state:
    st.session_state.performance_timers = {}

if 'performance_metrics' not in st.session_state:
    st.session_state.performance_metrics = {}

if 'use_data_cache' not in st.session_state:
    st.session_state.use_data_cache = True

# Add other required session state initializations
if 'active_analysis_section' not in st.session_state:
    st.session_state.active_analysis_section = None

if 'show_views_chart' not in st.session_state:
    st.session_state.show_views_chart = True
    
if 'show_likes_chart' not in st.session_state:
    st.session_state.show_likes_chart = True
    
if 'show_comments_chart' not in st.session_state:
    st.session_state.show_comments_chart = True
    
if 'show_duration_chart' not in st.session_state:
    st.session_state.show_duration_chart = False

def render_data_coverage_dashboard(channel_data, db=None):
    """
    Render the data coverage dashboard showing data completeness and update options.
    
    Args:
        channel_data: Dictionary containing channel data for one or more channels
        db: Database connection (optional)
    """
    # Start performance tracking for the entire dashboard rendering
    debug_log("Starting data coverage dashboard render", performance_tag="start_coverage_dashboard")
    
    # Initialize background_tasks variable with empty dictionary to prevent UnboundLocalError
    background_tasks = {}
    
    # Check if we're dealing with multiple channels
    if isinstance(channel_data, dict) and any(isinstance(v, dict) and 'channel_info' in v for v in channel_data.values()):
        # Multiple channels case
        channels_dict = channel_data
        is_multi_channel = True
        debug_log(f"Processing multiple channels dashboard: {len(channels_dict)} channels")
    else:
        # Single channel case (for backward compatibility)
        channels_dict = {'Single Channel': channel_data}
        is_multi_channel = False
        debug_log("Processing single channel dashboard")
    
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
    debug_log("Fetching background task status", performance_tag="start_background_tasks")
    
    try:
        background_tasks = get_all_task_statuses()
        running_tasks = {task_id: task for task_id, task in background_tasks.items() 
                        if task['status'] in ['queued', 'running']}
        debug_log(f"Found {len(running_tasks)} running tasks", performance_tag="end_background_tasks")
        
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
    except Exception as e:
        debug_log(f"Error fetching background tasks: {str(e)}")
        st.warning("Could not retrieve background task status. Some features may be limited.")
    
    # Process each channel and collect data coverage metrics
    debug_log("Starting coverage data processing", performance_tag="start_coverage_metrics")
    coverage_data = []
    
    # Check if there are channels to analyze
    if not channels_dict:
        st.warning("No channel data available for analysis. Please collect data first.")
        return
        
    for channel_name, channel_data in channels_dict.items():
        # Get data coverage information
        debug_log(f"Processing coverage for channel: {channel_name}", 
                  performance_tag=f"start_channel_coverage_{channel_name}")
        
        cache_key = f"data_coverage_{channel_name}"
        if use_cache and cache_key in st.session_state:
            debug_log(f"Using cached data coverage for: {channel_name}")
            coverage_info = st.session_state[cache_key]
        else:
            # Time the coverage analysis
            start_time = time.time()
            coverage_info = analysis.get_data_coverage(channel_data)
            elapsed = time.time() - start_time
            debug_log(f"Generated data coverage for {channel_name} in {elapsed:.2f}s")
            
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
            'Is Complete': coverage_info.get('is_complete', False),
            '_coverage_info': coverage_info  # Store full info for later use
        })
        
        debug_log(f"Completed coverage for channel: {channel_name}", 
                  performance_tag=f"end_channel_coverage_{channel_name}")
    
    # Convert to dataframe for display
    coverage_df = pd.DataFrame(coverage_data)
    debug_log("Completed coverage metrics processing", performance_tag="end_coverage_metrics")
    
    # If we have multiple channels, show a comparison table
    if is_multi_channel and len(coverage_df) > 1:
        debug_log("Rendering multi-channel comparison table", performance_tag="start_comparison_table")
        st.subheader("Channel Data Coverage Comparison")
        
        # Create display columns for the table (hiding internal fields)
        display_cols = [col for col in coverage_df.columns if not col.startswith('_') and col != 'Is Complete']
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
                "Channel": st.column_config.Column(
                    "Channel",
                    width="medium",
                    help="Click on a channel name to analyze it directly"
                ),
                "Total Videos (Reported)": st.column_config.TextColumn("Total Videos", width="small", help="Total videos available on YouTube"),
                "Videos Collected": st.column_config.TextColumn("Videos Collected", width="small", help="Number of videos in your database"),
                "Videos with Details": st.column_config.TextColumn("With Details", width="small", help="Videos with complete metadata"),
                "Videos with Comments": st.column_config.TextColumn("With Comments", width="small", help="Videos with comments collected"),
                "Video Coverage (%)": st.column_config.ProgressColumn("Video Coverage", width="small", help="Percentage of channel's videos in your database", format="%d%%", min_value=0, max_value=100),
                "Comment Coverage (%)": st.column_config.ProgressColumn("Comment Coverage", width="small", help="Percentage of collected videos that have comments", format="%d%%", min_value=0, max_value=100),
                "Latest Video": st.column_config.TextColumn("Latest Video", width="small", help="Date of most recent video in database"),
                "Oldest Video": st.column_config.TextColumn("Oldest Video", width="small", help="Date of oldest video in database"),
                "Actions": st.column_config.Column(
                    "Actions",
                    width="small",
                    help="Update or collect data for this channel"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Add clickable channel names with direct linking to channel analysis
        st.markdown("""
        <style>
        .channel-link {
            text-decoration: none;
            color: #1E88E5;
            font-weight: 500;
            cursor: pointer;
        }
        .channel-link:hover {
            text-decoration: underline;
            color: #0D47A1;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create links for each channel
        for i, row in display_df.iterrows():
            channel_name = row['Channel']
            st.markdown(f"""
            <p><a class="channel-link" href="javascript:void(0);" 
            onclick="document.dispatchEvent(new CustomEvent('streamlit:selectChannel', {{detail: '{channel_name}'}}))">
            {channel_name}</a></p>
            """, unsafe_allow_html=True)
            
        # JavaScript to handle the custom event
        st.markdown("""
        <script>
        document.addEventListener('streamlit:selectChannel', function(e) {
            const channelName = e.detail;
            window.parent.postMessage({
                type: 'streamlit:setSessionState', 
                session_state: {
                    selected_channel: channelName,
                    active_analysis_section: 'dashboard'
                }
            }, '*');
            // Force reload to apply the change
            setTimeout(() => window.parent.postMessage({type: 'streamlit:forceRerun'}, '*'), 100);
        });
        </script>
        """, unsafe_allow_html=True)

        # Add direct action buttons for each channel
        st.write("### Channel Actions")
        st.write("Select a channel to update or collect more data:")
        
        action_cols = st.columns(min(3, len(display_df)))
        for i, (_, row) in enumerate(display_df.iterrows()):
            col_idx = i % len(action_cols)
            with action_cols[col_idx]:
                channel_name = row['Channel']
                st.write(f"**{channel_name}**")
                
                # Get channel ID for actions
                channel_id = "unknown"
                channel_data = channels_dict.get(channel_name)
                if channel_data and 'channel_info' in channel_data and 'id' in channel_data['channel_info']:
                    channel_id = channel_data['channel_info']['id']
                
                # Add action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔄 Quick Update", key=f"quick_update_{i}", help="Run a quick background update"):
                        if channel_id != "unknown":
                            # Use stored API key
                            api_key = os.getenv('YOUTUBE_API_KEY', st.session_state.get('api_key', ''))
                            if api_key:
                                # Create options for update (videos + comments)
                                options = {
                                    'fetch_channel_data': True,
                                    'fetch_videos': True,
                                    'fetch_comments': True,
                                    'max_videos': 50,  # Fetch last 50 videos
                                    'max_comments_per_video': 20,  # 20 comments per video
                                    'save_to_storage': True,
                                    'storage_type': 'SQLite Database'
                                }
                                
                                # Queue the background task
                                task_id = queue_data_collection_task(channel_id, api_key, options)
                                st.success(f"✅ Quick update started for {channel_name}!")
                                st.rerun()  # Refresh UI
                            else:
                                st.error("No YouTube API key available. Please check your .env file.")
                        else:
                            st.error("Could not determine channel ID. Please try again.")
                
                with col2:
                    if st.button(f"📊 Full Collect", key=f"goto_collect_{i}", help="Go to data collection"):
                        # Set the channel in session state for data collection page
                        st.session_state.goto_collection_channel = channel_name
                        st.session_state.goto_collection_channel_id = channel_id
                        # Navigate to data collection tab
                        st.session_state.active_tab = "data_collection"
                        st.rerun()  # Trigger navigation
        
        debug_log("Completed rendering comparison table", performance_tag="end_comparison_table")
    
    # Now visualize the data coverage with charts
    st.subheader("Data Coverage Visualization")
    
    # Create a more informative combined coverage visualization
    debug_log("Generating enhanced coverage visualizations", performance_tag="start_coverage_visualization")
    try:
        # Extract coverage data for visualization and ensure proper numeric types
        coverage_metrics = pd.DataFrame([
            {
                'Channel': row['Channel'],
                'Total Videos': float(row['Total Videos (Reported)']),
                'Videos Collected': float(row['Videos Collected']),
                'Videos with Comments': float(row['Videos with Comments']),
                'Video Coverage (%)': float(row['Video Coverage (%)']),
                'Comment Coverage (%)': float(row['Comment Coverage (%)']),
                'Is Complete': row['Is Complete']
            }
            for _, row in coverage_df.iterrows()
        ])
        
        # Create column layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Create enhanced video coverage chart
            debug_log("Generating video coverage chart", performance_tag="start_video_coverage_chart")
            
            # Get coverage data for chart
            coverage_chart_data = coverage_metrics[['Channel', 'Video Coverage (%)', 'Comment Coverage (%)']].copy()
            
            # Sort by video coverage percentage for consistent display
            coverage_chart_data = coverage_chart_data.sort_values('Video Coverage (%)', ascending=False)
            
            # Melt the dataframe for easier plotting
            coverage_melted = pd.melt(
                coverage_chart_data, 
                id_vars=['Channel'], 
                value_vars=['Video Coverage (%)', 'Comment Coverage (%)'],
                var_name='Coverage Type', 
                value_name='Percentage'
            )
            
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
                barmode='group',
                color_discrete_sequence=["#2E86C1", "#F39C12"]  # Blue for videos, orange for comments
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
                ),
                margin=dict(l=10, r=10, t=50, b=40)
            )
            
            # Add percentage annotations on bars
            fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            debug_log("Video coverage chart rendered successfully", performance_tag="end_video_coverage_chart")
            
        with col2:
            # Create a stacked bar chart showing video counts and comment coverage
            debug_log("Generating video distribution chart", performance_tag="start_video_distribution_chart")
            
            # Calculate videos with and without comments
            distribution_data = []
            
            for _, row in coverage_metrics.iterrows():
                channel = row['Channel']
                videos_with_comments = int(row['Videos with Comments'])
                videos_collected = int(row['Videos Collected'])
                total_videos = int(row['Total Videos'])
                
                # Protect against negative numbers due to data inconsistencies
                videos_without_comments = max(0, videos_collected - videos_with_comments)
                videos_not_collected = max(0, total_videos - videos_collected)
                
                distribution_data.append({
                    'Channel': channel,
                    'Videos with Comments': videos_with_comments,
                    'Videos without Comments': videos_without_comments,
                    'Uncollected Videos': videos_not_collected
                })
            
            # Create dataframe for distribution
            distribution_df = pd.DataFrame(distribution_data)
            
            # Sort by the same order as the first chart
            channel_order = coverage_chart_data['Channel'].tolist()
            
            # Create a safe version of the categorical sorting
            try:
                # Try the categorical approach first
                distribution_df['Channel'] = pd.Categorical(distribution_df['Channel'], categories=channel_order, ordered=True)
                distribution_df = distribution_df.sort_values('Channel')
            except (ValueError, TypeError):
                # Fall back to manual sorting if categorical conversion fails
                sorter_index = {channel: i for i, channel in enumerate(channel_order)}
                distribution_df['Channel_Rank'] = distribution_df['Channel'].map(sorter_index)
                distribution_df = distribution_df.sort_values('Channel_Rank').drop('Channel_Rank', axis=1)
            
            # Melt for easier plotting
            distribution_melted = pd.melt(
                distribution_df,
                id_vars=['Channel'],
                value_vars=['Videos with Comments', 'Videos without Comments', 'Uncollected Videos'],
                var_name='Video Type',
                value_name='Count'
            )
            
            # Ensure Count is numeric
            distribution_melted['Count'] = pd.to_numeric(distribution_melted['Count'], errors='coerce').fillna(0).astype(int)
            
            # Create stacked bar chart
            fig = px.bar(
                distribution_melted,
                x='Channel',
                y='Count',
                color='Video Type',
                title="Video Collection Distribution",
                labels={'Count': 'Number of Videos', 'Channel': ''},
                barmode='stack',
                color_discrete_sequence=["#2ECC71", "#F39C12", "#E74C3C"]  # Green, orange, red
            )
            
            # Update layout
            fig.update_layout(
                yaxis=dict(title='Number of Videos'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=10, r=10, t=50, b=40)
            )
            
            # Add count annotations on bars (with safety checks)
            fig.update_traces(
                texttemplate="%{y}",  # Use fixed string template instead of lambda
                textposition="inside"
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            debug_log("Video distribution chart rendered successfully", performance_tag="end_video_distribution_chart")
    
        # Add a heatmap visualization for more detailed comparison
        if len(coverage_df) > 1:  # Only show heatmap for multiple channels
            st.subheader("Video and Comment Coverage Heatmap")
            
            # Create a heatmap showing various coverage metrics
            heatmap_data = coverage_df[['Channel', 'Video Coverage (%)', 'Comment Coverage (%)']].copy()
            
            # Ensure numeric data types
            for col in ['Video Coverage (%)', 'Comment Coverage (%)']:
                heatmap_data[col] = pd.to_numeric(heatmap_data[col], errors='coerce').fillna(0)
            
            # Sort by video coverage for consistent display
            heatmap_data = heatmap_data.sort_values('Video Coverage (%)', ascending=False)
            
            # Set the Channel as index for heatmap
            heatmap_data = heatmap_data.set_index('Channel')
            
            # Create heatmap figure
            fig = px.imshow(
                heatmap_data,
                labels=dict(x="Coverage Metric", y="Channel", color="Percentage"),
                x=['Video Coverage (%)', 'Comment Coverage (%)'],
                y=heatmap_data.index,
                color_continuous_scale='RdYlGn',  # Red to yellow to green
                range_color=[0, 100],  # 0-100%
                title="Coverage Comparison Heatmap",
                aspect="auto"
            )
            
            # Add percentage annotations with safety checks
            for i, channel in enumerate(heatmap_data.index):
                for j, metric in enumerate(['Video Coverage (%)', 'Comment Coverage (%)']):
                    # Make sure the value exists and is numeric
                    try:
                        value = float(heatmap_data.loc[channel, metric])
                        fig.add_annotation(
                            x=j,
                            y=i,
                            text=f"{value:.1f}%",
                            showarrow=False,
                            font=dict(color="black", size=14)
                        )
                    except (KeyError, ValueError, TypeError) as e:
                        debug_log(f"Error annotating heatmap: {str(e)}")
                        # Skip this annotation if there's an error
                        continue
            
            # Update layout
            fig.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                coloraxis_colorbar=dict(
                    title="Coverage (%)",
                    tickvals=[0, 25, 50, 75, 100],
                    ticktext=["0%", "25%", "50%", "75%", "100%"]
                )
            )
            
            # Display the heatmap
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        debug_log(f"Error generating coverage visualizations: {str(e)}")
        st.error(f"Error generating coverage visualizations: {str(e)}")
        
        # Fallback to simpler visualization with detailed error logging
        try:
            st.info("Displaying simplified coverage charts due to an error with the enhanced visualizations.")
            
            # Create simplified bar charts
            for channel_name, channel_data in channels_dict.items():
                try:
                    coverage_info = analysis.get_data_coverage(channel_data)
                    
                    # Create a simple bar chart for this channel
                    metrics = {
                        'Videos Collected': coverage_info['video_coverage_percent'],
                        'Videos with Comments': coverage_info['comment_coverage_percent'],
                    }
                    
                    # Plot as simple bar chart
                    st.write(f"#### {channel_name} Coverage")
                    chart_data = pd.DataFrame({
                        'Metric': list(metrics.keys()),
                        'Percentage': list(metrics.values())
                    })
                    
                    st.bar_chart(chart_data, x='Metric', y='Percentage', height=200)
                except Exception as channel_error:
                    debug_log(f"Error generating simplified chart for {channel_name}: {str(channel_error)}")
                    st.warning(f"Could not display data for {channel_name}")
        except Exception as e2:
            debug_log(f"Error in fallback visualization: {str(e2)}")
            st.error("Unable to generate visualizations. Please try with fewer channels or refresh the page.")
    
    # Create a channel selector for updating data
    debug_log("Rendering update section", performance_tag="start_update_section")
    st.subheader("Update Channel Data")
    st.markdown("""
    Select a channel to update its data. Updates will run in the background while you continue analyzing.
    """)
    
    # Get API key for data collection - First try .env, then session state
    api_key = os.getenv('YOUTUBE_API_KEY', '')
    
    # Add the key to session state if it exists in environment but not in session
    if api_key and 'api_key' not in st.session_state:
        st.session_state.api_key = api_key
        
    # Use API key from session state if available
    use_api_key = st.session_state.get('api_key', api_key)
    
    if not use_api_key:
        # If API key still not found, prompt as a last resort
        st.warning("⚠️ YouTube API key not found in environment or session state.")
        api_key_input = st.text_input(
            "Please enter your YouTube API Key for data collection:", 
            type="password",
            help="This key will be stored in session for this session only."
        )
        if api_key_input:
            st.session_state.api_key = api_key_input
            use_api_key = api_key_input
            st.success("API key saved for this session!")
    else:
        st.success("✅ Using YouTube API key from environment")
    
    if use_api_key:
        # Create two columns for layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Channel selector
            if 'auto_update_data' in st.session_state and st.session_state.auto_update_data:
                # Pre-select the first incomplete channel
                incomplete_channels = coverage_df[~coverage_df['Is Complete']]['Channel'].tolist()
                if incomplete_channels:
                    default_channel = incomplete_channels[0]
                else:
                    default_channel = coverage_df['Channel'].iloc[0]
                
                selected_channel = st.selectbox(
                    "Select channel to update",
                    options=coverage_df['Channel'].tolist(),
                    index=coverage_df['Channel'].tolist().index(default_channel),
                    key="update_channel_selector"
                )
                # Reset the auto update flag after using it
                st.session_state.auto_update_data = False
            else:
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
            is_complete = selected_data['Is Complete']
            
            # Display recommendations for the selected channel
            if recommendations:
                with col2:
                    if is_complete:
                        st.success(f"✅ {', '.join(recommendations)}")
                    else:
                        st.info(f"Recommendations: {', '.join(recommendations)}")
            
            # Create update options
            st.subheader(f"Update Options for {selected_channel}")
            
            # Get channel ID from the actual data - with enhanced extraction
            channel_id = "unknown"
            channel_data = channels_dict.get(selected_channel)
            
            # Debug the channel data structure
            debug_log(f"Channel data structure for {selected_channel}: {str(type(channel_data))}")
            
            if channel_data:
                # Try multiple ways to get the channel ID
                if 'channel_info' in channel_data:
                    # Method 1: Direct ID in channel_info
                    if 'id' in channel_data['channel_info']:
                        channel_id = channel_data['channel_info']['id']
                        debug_log(f"Found channel ID (method 1): {channel_id}")
                    # Method 2: ID in snippet
                    elif 'snippet' in channel_data['channel_info'] and 'channelId' in channel_data['channel_info']['snippet']:
                        channel_id = channel_data['channel_info']['snippet']['channelId']
                        debug_log(f"Found channel ID (method 2): {channel_id}")
                    # Method 3: ID in contentDetails
                    elif 'contentDetails' in channel_data['channel_info'] and 'relatedPlaylists' in channel_data['channel_info']['contentDetails']:
                        # Try to extract from uploads playlist
                        uploads = channel_data['channel_info']['contentDetails']['relatedPlaylists'].get('uploads', '')
                        if uploads and uploads.startswith('UU'):
                            # Convert uploads playlist ID back to channel ID format
                            channel_id = 'UC' + uploads[2:]
                            debug_log(f"Found channel ID (method 3): {channel_id}")
                
                # Method 4: Check if channel data is itself the ID string
                if channel_id == "unknown" and isinstance(channel_data, str) and (channel_data.startswith('UC') or channel_data.startswith('HC')):
                    channel_id = channel_data
                    debug_log(f"Found channel ID (method 4): {channel_id}")
                
                # Method 5: Look for channel ID in videos
                if channel_id == "unknown" and 'videos' in channel_data and channel_data['videos']:
                    for video in channel_data['videos']:
                        if 'snippet' in video and 'channelId' in video['snippet']:
                            channel_id = video['snippet']['channelId']
                            debug_log(f"Found channel ID (method 5): {channel_id}")
                            break
                
                # Method 6: Try to find it in channel title or name
                if channel_id == "unknown" and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
                    # If we have the DB connection, try to look up by title
                    if db:
                        try:
                            looked_up_id = db.get_channel_id_by_title(channel_data['channel_info']['title'])
                            if looked_up_id:
                                channel_id = looked_up_id
                                debug_log(f"Found channel ID (method 6): {channel_id}")
                        except Exception as e:
                            debug_log(f"Error looking up channel ID in DB: {str(e)}")
            
            debug_log(f"Final channel ID for {selected_channel}: {channel_id}")
            
            # Backup method: If we have an active DB connection, try to get channel ID directly
            if channel_id == "unknown" and db:
                try:
                    channel_id = db.get_channel_id_by_title(selected_channel)
                    if channel_id:
                        debug_log(f"Retrieved channel ID from database: {channel_id}")
                except Exception as e:
                    debug_log(f"Error retrieving channel ID from database: {str(e)}")
            
            # Create option sections using columns
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown("#### Content to Update")
                update_channel_info = st.checkbox("Update Channel Info", key="update_channel_info", value=True)
                update_videos = st.checkbox("Update Videos", key="update_videos", value=True)
                update_comments = st.checkbox("Update Comments", key="update_comments", value=not is_complete)
            
            with col2:
                st.markdown("#### Amount to Collect")
                # Determine max videos for slider based on total in API
                max_videos_api = coverage_info['total_videos_reported']
                current_videos = coverage_info['total_videos_collected']
                
                # Check if we need to auto-select "All available" when coming from quick update
                default_video_option = 0  # Default to "Only new videos"
                if 'auto_update_data' in st.session_state and st.session_state.get('auto_update_data_init', False):
                    default_video_option = 2  # "All available"
                    st.session_state.auto_update_data_init = False
                
                video_options = st.radio(
                    "Videos to collect:",
                    options=["Only new videos", "Custom number", "All available"],
                    index=default_video_option,
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
                    # Auto-set comment count to 100 for complete collection
                    default_comments = 100 if 'auto_update_data' in st.session_state and st.session_state.get('auto_update_data_init', False) else 20
                    
                    max_comments = st.slider(
                        "Comments per video",
                        min_value=0,
                        max_value=100,
                        value=default_comments,
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
                
                # Add one-click update button with auto triggers for quick updates
                if 'auto_update_data' in st.session_state and st.session_state.auto_update_data and not st.session_state.get('auto_update_triggered', False):
                    st.session_state.auto_update_data_init = True
                    st.session_state.auto_update_triggered = True
                    # Auto-trigger the update button via JavaScript
                    st.markdown("""
                    <script>
                        document.addEventListener("DOMContentLoaded", function() {
                            setTimeout(function() {
                                document.querySelector('button[kind="primary"]').click();
                            }, 500);
                        });
                    </script>
                    """, unsafe_allow_html=True)
                
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
                        
                        # Clear any auto-update flags
                        st.session_state.auto_update_data = False
                        st.session_state.auto_update_triggered = False
                        
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
    
    debug_log("Completed update section", performance_tag="end_update_section")
    debug_log("Completed data coverage dashboard render", performance_tag="end_coverage_dashboard")

def render_data_coverage_summary(channel_data, analysis):
    """
    Render a compact data coverage summary to be embedded in other analysis components.
    
    Args:
        channel_data: Dictionary containing channel data (single or multiple channels)
        analysis: YouTubeAnalysis instance
        
    Returns:
        None - renders directly to streamlit
    """
    # Initialize performance tracking variables in session state if they don't exist
    if 'performance_timers' not in st.session_state:
        st.session_state.performance_timers = {}
    
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {}
    
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
    
    # Temporarily disable coverage cache if requested
    if st.session_state.get('refresh_coverage_data', False):
        st.session_state['skip_coverage_cache'] = True
        st.session_state['refresh_coverage_data'] = False
    else:
        st.session_state['skip_coverage_cache'] = False
    
    # Create coverage summary container
    with st.container():
        st.markdown("### Data Coverage Summary")
        st.markdown("The analysis below is based on your local data collection. Here's how complete your data is:")
        
        # Create a table for coverage information
        coverage_rows = []
        all_complete = True
        
        # Add refresh button at the top
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 Refresh Coverage", key="refresh_coverage"):
                st.session_state['refresh_coverage_data'] = True
                st.rerun()
        
        # Process each channel and collect coverage metrics
        for channel_name, channel_data in channels_dict.items():
            # Get data coverage information
            cache_key = f"data_coverage_{channel_name}"
            if use_cache and not st.session_state.get('skip_coverage_cache', False) and cache_key in st.session_state:
                coverage_info = st.session_state[cache_key]
            else:
                coverage_info = analysis.get_data_coverage(channel_data)
                # Cache the result
                if use_cache:
                    st.session_state[cache_key] = coverage_info
            
            # Format date range with proper handling of None values
            oldest_date = "N/A"
            latest_date = "N/A"
            
            if coverage_info['oldest_video_date']:
                oldest_date = coverage_info['oldest_video_date'].strftime('%b %d, %Y')
            
            if coverage_info['latest_video_date']:
                latest_date = coverage_info['latest_video_date'].strftime('%b %d, %Y')
            
            # Get last updated time
            last_updated = "Unknown"
            if coverage_info.get('last_updated'):
                days_since_update = (datetime.now() - coverage_info['last_updated']).days
                if days_since_update == 0:
                    last_updated = "Today"
                elif days_since_update == 1:
                    last_updated = "Yesterday"
                else:
                    last_updated = f"{days_since_update} days ago"
            
            # Ensure we're using the current date values, not hardcoded ones
            time_range = f"{oldest_date} to {latest_date}"
            
            # Check if this channel has complete data
            is_complete = coverage_info.get('is_complete', False) and coverage_info.get('comment_coverage_percent', 0) >= 99.0
            all_complete = all_complete and is_complete
            
            # Format coverage status with clear visual indicator
            if is_complete:
                status = "✅ Complete"
            elif coverage_info['video_coverage_percent'] >= 75:
                status = "⚠️ Partial"
            else:
                status = "❌ Incomplete"
            
            # Add to the coverage data list for display with safe numeric handling
            coverage_rows.append({
                'Channel': channel_name,
                'Videos Collected': f"{int(coverage_info['total_videos_collected']):,} of {int(coverage_info['total_videos_reported']):,}",
                'Video Coverage': f"{coverage_info['video_coverage_percent']:.1f}%",
                'Comments Coverage': f"{coverage_info['comment_coverage_percent']:.1f}%",
                'Time Range': time_range,
                'Last Updated': last_updated,
                'Status': status,
                '_coverage_info': coverage_info  # Store full info for later use
            })
        
        # Create and display the coverage table
        coverage_df = pd.DataFrame(coverage_rows)
        display_cols = [col for col in coverage_df.columns if not col.startswith('_')]
        
        st.dataframe(
            coverage_df[display_cols],
            column_config={
                "Channel": st.column_config.TextColumn("Channel", width="medium"),
                "Videos Collected": st.column_config.TextColumn("Videos", width="small", help="Number of videos in your database out of total available"),
                "Video Coverage": st.column_config.TextColumn("Coverage", width="small", help="Percentage of channel's videos in your database"),
                "Comments Coverage": st.column_config.TextColumn("Comments", width="small", help="Percentage of videos that have comments"),
                "Time Range": st.column_config.TextColumn("Date Range", width="medium", help="Time range of videos in your database"),
                "Last Updated": st.column_config.TextColumn("Updated", width="small", help="When this data was last updated"),
                "Status": st.column_config.TextColumn("Status", width="small", help="Current data collection status")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Show coverage note and link to full coverage dashboard
        if not all_complete:
            st.warning("⚠️ Your analysis is based on incomplete data. Use the button below to update your data collection.")
            
            # Create column layout for update options
            update_col1, update_col2 = st.columns([1, 1])
            
            with update_col1:
                # Show one-click update button
                if st.button("📊 Update Data Collection", key="coverage_summary_update_btn", type="primary"):
                    # Set session state to navigate to coverage dashboard with update option preselected
                    st.session_state.active_analysis_section = "coverage"
                    st.session_state.auto_update_data = True
                    st.rerun()
            
            with update_col2:
                # Show go to dashboard button
                if st.button("🔍 View Coverage Details", key="coverage_summary_goto_btn"):
                    st.session_state.active_analysis_section = "coverage"
                    st.rerun()
        else:
            st.success("✅ Your data collection is complete! All videos and comments have been collected.")
            
            # Still offer the option to view coverage dashboard
            if st.button("🔍 View Coverage Details", key="coverage_summary_complete_goto_btn"):
                st.session_state.active_analysis_section = "coverage"
                st.rerun()
            
        # Add help text about data collection
        with st.expander("ℹ️ About Data Coverage"):
            st.markdown("""
            **What This Shows:**
            
            This section shows how complete your local data collection is for each YouTube channel. Complete
            data collection means you have all available videos and their comments locally stored.
            
            **Why This Matters:**
            
            - **Accuracy:** More complete data means more accurate analytics and insights
            - **History:** Complete historical data lets you analyze trends over time
            - **Comments:** Having comments collected enables sentiment and audience analysis
            
            **How to Update Your Data:**
            
            Click the "Update Data Collection" button to quickly fetch missing videos and comments.
            For more detailed options, use the "View Coverage Details" button.
            """)
            
        # Reset the skip cache flag after use
        st.session_state['skip_coverage_cache'] = False