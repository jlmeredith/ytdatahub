"""
Collection steps UI components for data collection.
Provides functions to render the step-by-step data collection workflow.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.helpers import debug_log
from src.config import Settings
from .components.video_item import render_video_item
from .utils.data_conversion import format_number
from .utils.delta_reporting import render_delta_report

def render_collection_steps(channel_input, youtube_service):
    """
    Render the collection steps UI for both new and existing channel modes
    
    Args:
        channel_input: Channel ID/URL input
        youtube_service: Instance of the YouTubeService
    """
    # Get the channel info from session state
    channel_info = st.session_state.channel_info_temp
    # Get previous data if in existing channel mode
    previous_data = st.session_state.get('previous_channel_data')
    
    # STEP 1: CHANNEL DATA
    st.subheader("Step 1: Channel Data")
    
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
        
        # Add last refresh timestamp from the data if available
        if 'last_refresh' in channel_info and 'timestamp' in channel_info['last_refresh']:
            refresh_time = channel_info['last_refresh']['timestamp']
            # Format the timestamp for display if it's an ISO format string
            try:
                dt = datetime.fromisoformat(refresh_time)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                st.write("**Last refreshed:**", formatted_time)
            except (ValueError, TypeError):
                st.write("**Last refreshed:**", refresh_time)
    
    st.success("✅ Channel data fetched successfully!")
    
    # STEP 2: VIDEO DATA
    st.divider()
    st.subheader("Step 2: Videos Data")
    
    if st.session_state.videos_fetched and 'video_id' in channel_info and channel_info['video_id']:
        # Display video information
        videos = channel_info.get('video_id', [])
        videos_fetched = channel_info.get('videos_fetched', len(videos))
        videos_unavailable = channel_info.get('videos_unavailable', 0)
        
        # Refetch option
        with st.expander("Want to refetch with a different number of videos?"):
            st.write("If you'd like to try a different sample size, you can refetch videos:")
            max_videos_available = int(channel_info.get('total_videos', 0))
            
            refetch_col1, refetch_col2 = st.columns([3, 1])
            with refetch_col1:
                new_max_videos = st.slider(
                    "New number of videos to fetch", 
                    min_value=0, 
                    max_value=max_videos_available, 
                    value=max(videos_fetched, min(100, max_videos_available)),
                )
            with refetch_col2:
                refetch_all = st.checkbox("Fetch all videos")
            
            if refetch_all:
                st.session_state.max_videos = 0  # 0 means all videos
            else:
                st.session_state.max_videos = new_max_videos
            
            if st.button("Refetch Videos", key="refetch_videos_btn"):
                with st.spinner(f"Refetching videos from YouTube..."):
                    options = {
                        'fetch_channel_data': False,
                        'fetch_videos': True,
                        'fetch_comments': False,
                        'max_videos': st.session_state.max_videos,
                        'max_comments_per_video': 0
                    }
                    
                    updated_channel_info = youtube_service.collect_channel_data(
                        channel_input, options, existing_data=channel_info
                    )
                    
                    if updated_channel_info and 'video_id' in updated_channel_info:
                        st.session_state.channel_info_temp = updated_channel_info
                        st.session_state.current_channel_data = updated_channel_info
                        st.session_state.videos_fetched = True
                        st.session_state.show_all_videos = False
                        
                        videos = updated_channel_info.get('video_id', [])
                        videos_unavailable = updated_channel_info.get('videos_unavailable', 0)
                        
                        success_msg = f"✅ Successfully fetched {len(videos)} videos"
                        if videos_unavailable > 0:
                            success_msg += f" ({videos_unavailable} were unavailable)"
                        st.success(success_msg)
                        st.rerun()

        # Check for deltas if we're in existing channel mode (MOVED OUTSIDE EXPANDER)
        if previous_data and st.session_state.collection_mode == "existing_channel":
            st.subheader("Changes in Videos")
            prev_video_data = {'video_id': previous_data.get('video_id', [])}
            updated_video_data = {'video_id': channel_info.get('video_id', [])}
            render_delta_report(prev_video_data, updated_video_data, data_type="video")
        
        # Calculate total comments if available
        total_comments = 0
        videos_with_comments = 0
        total_comment_count = 0
        debug_log("Calculating comment counts...")
        
        # First check if we have comment_counts from video metadata (which doesn't require fetching comments)
        if 'comment_counts' in channel_info:
            debug_log("Using comment_counts from video metadata")
            comment_counts = channel_info['comment_counts']
            total_comment_count = comment_counts.get('total_comment_count', 0)
            videos_with_comments = comment_counts.get('videos_with_comments', 0)
            debug_log(f"From metadata: {total_comment_count} comments across {videos_with_comments} videos")
        
        # Then check actual comment content (if we've fetched them)
        has_comments = False
        for video in videos:
            if 'comments' in video and video['comments']:
                has_comments = True
                break
        
        # If no actual comments found, add debugging info
        if not has_comments:
            debug_log("No actual comment content found in any videos. Comments may not have been fetched yet.")
        
        # Even if we don't have actual comments, we should still show comment counts
        for video in videos:
            # Explicitly check if 'comments' exists and is a list
            if 'comments' not in video:
                debug_log(f"Video {video.get('title', 'Unknown')} has no comments field")
                video['comments'] = []
            
            # Count actual comments if available
            comments_count = len(video.get('comments', []))
            debug_log(f"Video '{video.get('title', 'Unknown')}' has {comments_count} comments fetched")
            total_comments += comments_count
        
        debug_log(f"Total actual comments fetched: {total_comments}, Metadata comment count: {total_comment_count}")
        
        # Display metrics in a row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Videos Downloaded", f"{videos_fetched} of {channel_info.get('total_videos', '0')}")
        with col2:
            # Always show comment metrics if we have comment_counts from metadata or actual comments
            if total_comment_count > 0:
                st.metric("Total Comments Available", total_comment_count, 
                        help="Based on YouTube statistics, not all comments may be downloaded")
            elif total_comments > 0:
                st.metric("Comments Downloaded", total_comments)
            else:
                if videos_unavailable > 0:
                    st.metric("Unavailable Videos", videos_unavailable, 
                            help="Some videos may be private, deleted, or restricted and cannot be accessed")
                else:
                    st.metric("Comments Status", "Unknown", 
                            help="Check Step 3 to fetch comments")
        with col3:
            if videos_fetched > 0:
                if total_comment_count > 0:
                    comment_ratio = total_comment_count / videos_fetched
                    st.metric("Comments per Video", f"{comment_ratio:.1f}", 
                            help="Average number of comments per video - higher numbers may indicate more engagement")
                elif total_comments > 0:
                    st.metric("Videos with Comments", videos_with_comments, 
                            help="Number of videos that have at least one comment")
                else:
                    st.metric("Videos with Comments", "Unknown", 
                            help="Use Step 3 to fetch actual comments")
        
        # Show video details in an expander with improved formatting
        with st.expander(f"View Downloaded Videos ({len(videos)})"):
            # Add sorting options for videos
            sort_option = st.selectbox(
                "Sort videos by:",
                ["Recent first", "Oldest first", "Most views", "Most likes", "Most comments"],
                index=0
            )
            
            # Sort videos based on user selection
            if sort_option == "Recent first":
                videos = sorted(videos, key=lambda x: x.get('published_at', ''), reverse=True)
            elif sort_option == "Oldest first":
                videos = sorted(videos, key=lambda x: x.get('published_at', ''))
            elif sort_option == "Most views":
                videos = sorted(videos, key=lambda x: int(x.get('views', 0)), reverse=True)
            elif sort_option == "Most likes":
                videos = sorted(videos, key=lambda x: int(x.get('likes', 0)), reverse=True)
            elif sort_option == "Most comments":
                videos = sorted(videos, key=lambda x: len(x.get('comments', [])), reverse=True)
            
            # Determine which videos to display based on show_all_videos state
            display_count = len(videos) if st.session_state.show_all_videos else min(15, len(videos))
            videos_to_display = videos[:display_count]
            
            # Display videos in a more user-friendly format
            for i, video in enumerate(videos_to_display):
                render_video_item(video, i)
                # Add a separator between videos
                st.divider()
            
            # Show all videos or show more button
            if not st.session_state.show_all_videos and len(videos) > 15:
                remaining = len(videos) - 15
                if st.button(f"Show All {len(videos)} Videos"):
                    st.session_state.show_all_videos = True
                    st.rerun()
            elif st.session_state.show_all_videos and len(videos) > 15:
                if st.button("Show Fewer Videos"):
                    st.session_state.show_all_videos = False
                    st.rerun()
        
        st.success("✅ Videos fetched successfully!")
        
        # STEP 3: COMMENTS DATA
        st.divider()
        st.subheader("Step 3: Comments Data")
        
        # Check if we've already fetched comments
        if st.session_state.comments_fetched:
            # Display summary of fetched data
            st.success("✅ Comments fetched successfully!")
            
            # Calculate summary statistics
            comment_stats = channel_info.get('comment_stats', {})
            total_comments = comment_stats.get('total_comments', 0)
            videos_with_comments = comment_stats.get('videos_with_comments', 0)
            
            # Create context for the data collection summary template
            channel_info_html = f"""
            <p><strong>Channel Name:</strong> {channel_info.get('channel_name', 'Unknown')}</p>
            <p><strong>Subscribers:</strong> {format_number(int(channel_info.get('subscribers', 0)))}</p>
            <p><strong>Total Channel Videos:</strong> {format_number(int(channel_info.get('total_videos', 0)))}</p>
            """
            
            collected_data_html = f"""
            <p><strong>Videos Downloaded:</strong> {videos_fetched} of {channel_info.get('total_videos', 0)}</p>
            """
            
            if 'videos_unavailable' in channel_info:
                collected_data_html += f"""
                <p><strong>Unavailable Videos:</strong> {channel_info.get('videos_unavailable', 0)}</p>
                """
                
            # Add storage options for saving the data
            st.divider()
            st.subheader("Step 4: Save Data")
            
            # Get the channel data to save - it's the current channel data in session state
            channel_data = st.session_state.current_channel_data
            
            if channel_data:
                from src.config import Settings
                app_settings = Settings()
                
                # Show storage options
                storage_option = st.selectbox(
                    "Select Storage Option:", 
                    app_settings.get_available_storage_options()
                )
                
                st.info(f"Selected storage type: **{storage_option}**. Data will be saved for later analysis.")
                
                # For existing channel mode, show special messaging
                if st.session_state.collection_mode == "existing_channel":
                    st.info("Since you are updating an existing channel, this will update the database record with the latest data.")
                
                if st.button("Save Channel Data", type="primary"):
                    with st.spinner("Saving data..."):
                        try:
                            # Use the YouTubeService to save the data
                            success = youtube_service.save_channel_data(channel_data, storage_option, app_settings)
                            
                            if success:
                                st.success(f"Data saved to {storage_option} successfully!")
                                
                                # Improved section with clearer options for what to do next
                                st.markdown("### What would you like to do next?")
                                st.info("You can analyze the data you just collected, or continue to iterate by collecting data for another channel.")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Analyze This Channel Data", key="goto_analysis"):
                                        st.session_state.active_tab = "Data Analysis"
                                        st.rerun()
                                with col2:
                                    if st.button("Collect Data for Another Channel", key="restart_collection"):
                                        # Reset collection state variables to start fresh
                                        st.session_state.channel_data_fetched = False
                                        st.session_state.videos_fetched = False
                                        st.session_state.comments_fetched = False
                                        st.session_state.show_all_videos = False
                                        st.session_state.collection_mode = "new_channel"
                                        if 'channel_info_temp' in st.session_state:
                                            del st.session_state.channel_info_temp
                                        if 'current_channel_data' in st.session_state:
                                            del st.session_state.current_channel_data
                                        if 'previous_channel_data' in st.session_state:
                                            del st.session_state.previous_channel_data
                                        if 'existing_channel_id' in st.session_state:
                                            del st.session_state.existing_channel_id
                                        st.rerun()
                            else:
                                st.error(f"Failed to save data to {storage_option}")
                        except Exception as e:
                            st.error(f"Error saving data: {str(e)}")
                
                # Add information about storage configuration
                with st.expander("About Data Storage Options"):
                    st.write("""
                    You can configure additional storage options in the **Utilities** tab.
                    
                    Available storage types:
                    - **SQLite Database**: Local database storage (default)
                    - **Local Storage (JSON)**: Simple file-based storage
                    """)
                    
                    # If we have MongoDB or PostgreSQL configured, mention them
                    if app_settings.mongodb_available:
                        st.write("- **MongoDB**: Document-based NoSQL database")
                    if app_settings.postgres_available:
                        st.write("- **PostgreSQL**: Relational database")
                    
                    st.info("💡 Tip: You can add and configure additional storage options in the Utilities section.")
            else:
                st.warning("No data available to save. Please complete the data collection steps first.")
        else:
            # Option to download comments
            st.write("Now you can fetch comments for the downloaded videos.")
            col1, col2 = st.columns([3, 1])
            with col1:
                max_comments = st.slider(
                    "Comments Per Video", 
                    min_value=0, 
                    max_value=100, 
                    value=st.session_state.get('max_comments_per_video', 10),
                    help="Maximum number of comments to import per video (0 to skip comments)"
                )
            with col2:
                fetch_all_comments = st.checkbox("Fetch All Available", help="Attempt to fetch all available comments (up to API limits)")
            
            if fetch_all_comments:
                st.session_state.max_comments_per_video = 100  # Set to max API limit
            else:
                st.session_state.max_comments_per_video = max_comments
            
            if st.button("Fetch Comments", type="primary"):
                # Only proceed if we have videos
                if videos:
                    with st.spinner("Fetching comments from YouTube..."):
                        # Create options with only comments retrieval enabled
                        options = {
                            'fetch_channel_data': False,
                            'fetch_videos': False,
                            'fetch_comments': True,
                            'max_videos': 0,
                            'max_comments_per_video': st.session_state.max_comments_per_video
                        }
                        
                        debug_log(f"COMMENT UI DEBUG: Starting comment fetch with max_comments_per_video={st.session_state.max_comments_per_video}")
                        
                        # Use existing channel_info but update with comments
                        updated_channel_info = youtube_service.collect_channel_data(channel_input, options, existing_data=channel_info)
                        
                        if updated_channel_info:
                            # Store the updated channel info with comments
                            st.session_state.channel_info_temp = updated_channel_info
                            st.session_state.current_channel_data = updated_channel_info
                            st.session_state.comments_fetched = True  # Mark comments as fetched
                            
                            # Force UI refresh to show the updated comment counts and summary view
                            st.rerun()
                        else:
                            st.error("Failed to fetch comment data from YouTube.")
                else:
                    st.error("No videos available to fetch comments for.")
    else:
        # Video fetching options
        st.write("You need to fetch videos for this channel.")
        col1, col2 = st.columns([3, 1])
        with col1:
            max_videos = st.slider(
                "Max Videos to Fetch", 
                min_value=1, 
                max_value=int(channel_info.get('total_videos', 50)),
                value=min(25, int(channel_info.get('total_videos', 25))),
                help="Maximum number of videos to fetch from the channel (larger numbers may take longer)"
            )
        with col2:
            fetch_all = st.checkbox("Fetch All Videos", 
                                help="Warning: Large channels may have hundreds or thousands of videos")
        
        if fetch_all:
            # Setting to 0 will fetch all videos in the backend
            st.session_state.max_videos = 0
        else:
            st.session_state.max_videos = max_videos
            
        if st.button("Fetch Videos", type="primary"):
            with st.spinner(f"Fetching videos from YouTube..."):
                # Create options with only video retrieval enabled
                options = {
                    'fetch_channel_data': False,
                    'fetch_videos': True,
                    'fetch_comments': False,
                    'max_videos': st.session_state.max_videos,  # 0 means fetch all
                    'max_comments_per_video': 0
                }
                
                # Use existing channel_info to avoid refetching channel data
                updated_channel_info = youtube_service.collect_channel_data(channel_input, options, existing_data=channel_info)
                
                if updated_channel_info and 'video_id' in updated_channel_info:
                    st.session_state.channel_info_temp = updated_channel_info
                    st.session_state.current_channel_data = updated_channel_info
                    st.session_state.videos_fetched = True
                    
                    videos = updated_channel_info.get('video_id', [])
                    videos_unavailable = updated_channel_info.get('videos_unavailable', 0)
                    
                    success_msg = f"✅ Successfully fetched {len(videos)} videos"
                    if videos_unavailable > 0:
                        success_msg += f" ({videos_unavailable} were unavailable)"
                    st.success(success_msg)
                    
                    # Check for deltas if we're in existing channel mode (MOVED OUTSIDE EXPANDER)
                    if previous_data and st.session_state.collection_mode == "existing_channel":
                        st.subheader("Changes in Videos")
                        # Create simple objects for video comparison
                        prev_video_ids = [v.get('video_id') for v in previous_data.get('video_id', [])]
                        new_video_ids = [v.get('video_id') for v in updated_channel_info.get('video_id', [])]
                        
                        # Find new videos
                        new_videos = [v for v in new_video_ids if v not in prev_video_ids]
                        if new_videos:
                            st.success(f"✅ {len(new_videos)} new videos found")
                            
                            # Show a bit more detail about the new videos
                            new_video_titles = []
                            for v in updated_channel_info.get('video_id', []):
                                if v.get('video_id') in new_videos:
                                    new_video_titles.append(v.get('title', 'Untitled'))
                            
                            if new_video_titles:
                                st.write("New videos:")
                                for i, title in enumerate(new_video_titles[:5]):
                                    st.write(f"- {title}")
                                if len(new_video_titles) > 5:
                                    st.write(f"...and {len(new_video_titles) - 5} more")
                        
                        # Compare video stats for existing videos
                        common_video_ids = [v for v in prev_video_ids if v in new_video_ids]
                        
                        changes = []
                        for vid_id in common_video_ids:
                            # Find the video in both old and new data
                            old_video = next((v for v in previous_data.get('video_id', []) if v.get('video_id') == vid_id), None)
                            new_video = next((v for v in updated_channel_info.get('video_id', []) if v.get('video_id') == vid_id), None)
                            
                            if old_video and new_video:
                                # Check for changes in key metrics
                                old_views = int(old_video.get('views', 0))
                                new_views = int(new_video.get('views', 0))
                                old_likes = int(old_video.get('likes', 0))
                                new_likes = int(new_video.get('likes', 0))
                                
                                if old_views != new_views or old_likes != new_likes:
                                    change = {
                                        "Title": new_video.get('title', 'Unknown'),
                                        "Views": f"{format_number(old_views)} → {format_number(new_views)}",
                                        "Likes": f"{format_number(old_likes)} → {format_number(new_likes)}"
                                    }
                                    changes.append(change)
                        
                        if changes:
                            st.write("#### Changes in existing videos")
                            changes_df = pd.DataFrame(changes)
                            st.dataframe(changes_df, use_container_width=True)
                        else:
                            st.info("No changes detected in existing videos")
                    
                    st.rerun()  # Rerun to update UI
                else:
                    st.error("This channel has no videos to fetch.")