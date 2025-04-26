"""
UI components for the Data Collection tab.
"""
import streamlit as st
import os
from src.services.youtube_service import YouTubeService
from src.utils.helpers import estimate_quota_usage, debug_log, format_number

def render_data_collection_tab():
    """
    Render the Data Collection tab UI.
    """
    st.header("YouTube Data Collection")
    
    # Initialize session state variables if they don't exist
    if 'collection_step' not in st.session_state:
        st.session_state.collection_step = 1  # Step 1: Channel, Step 2: Videos, Step 3: Comments
    if 'channel_data_fetched' not in st.session_state:
        st.session_state.channel_data_fetched = False
    if 'videos_fetched' not in st.session_state:
        st.session_state.videos_fetched = False
    if 'comments_fetched' not in st.session_state:
        st.session_state.comments_fetched = False
    if 'show_all_videos' not in st.session_state:
        st.session_state.show_all_videos = False
    
    # API Key input
    api_key = os.getenv('YOUTUBE_API_KEY', '')
    user_api_key = st.text_input("Enter YouTube API Key:", value=api_key, type="password")
    
    if user_api_key:
        # Initialize the YouTube service 
        youtube_service = YouTubeService(user_api_key)
        
        # Channel ID/URL input with improved help text
        st.write("Enter a YouTube Channel ID or URL to begin gathering data.")
        channel_input = st.text_input(
            "Enter YouTube Channel ID or URL:",
            help="You can enter any of the following formats:\n"
                 "• Channel ID (starts with UC...)\n"
                 "• Channel URL (https://www.youtube.com/channel/UC...)\n"
                 "• Custom URL (https://www.youtube.com/c/ChannelName)\n"
                 "• Handle URL (https://www.youtube.com/@username)"
        )
        
        # STEP 1: CHANNEL DATA
        st.subheader("Step 1: Channel Data")
        
        # If channel data has been fetched, display it
        if st.session_state.channel_data_fetched and 'channel_info_temp' in st.session_state:
            channel_info = st.session_state.channel_info_temp
            
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
            
            st.success("✅ Channel data fetched successfully!")
            
            # STEP 2: VIDEO DATA
            st.divider()
            st.subheader("Step 2: Videos Data")
            
            if st.session_state.videos_fetched and 'video_id' in channel_info and channel_info['video_id']:
                # Display video information in a modern, readable format
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
                
                # Calculate total comments if available
                total_comments = 0
                videos_with_comments = 0
                total_comment_count = 0
                debug_log("Calculating comment counts...")  # Debug log to help trace the issue
                
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
                
                # Show video details in an expander with improved formatting for wide mode
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
                        # Create a card-like layout for each video
                        st.markdown(f"### {i+1}. {video.get('title', 'Untitled')}")
                        
                        # Video URL for linking out
                        video_url = f"https://www.youtube.com/watch?v={video.get('video_id')}"
                        st.markdown(f"[Watch on YouTube]({video_url})")
                        
                        # Use 4 columns for better layout in wide mode
                        cols = st.columns([2, 1, 1, 1])
                        
                        # Column 1: Description/thumbnail
                        with cols[0]:
                            if 'thumbnails' in video:
                                st.image(video.get('thumbnails', ''), width=240)
                            else:
                                st.write("Video description:", video.get('video_description', '')[:100] + "..." if video.get('video_description', '') else "No description")
                        
                        # Column 2: View stats
                        with cols[1]:
                            st.metric("Views", format_number(int(video.get('views', 0))))
                            st.write(f"Published: {video.get('published_date', 'Unknown')}")
                        
                        # Column 3: Like stats
                        with cols[2]:
                            st.metric("Likes", format_number(int(video.get('likes', 0))))
                            if 'duration' in video:
                                # Format duration if possible
                                duration = video.get('duration', 'Unknown')
                                st.write(f"Duration: {duration}")
                        
                        # Column 4: Comment stats
                        with cols[3]:
                            # Use comment_count from the video metadata if available, otherwise use actual comments
                            if 'comment_count' in video:
                                comment_count = int(video.get('comment_count', 0))
                                actual_comments = len(video.get('comments', []))
                                
                                # Always show the comment count from metadata
                                debug_log(f"Video '{video.get('title', 'Unknown')}' has metadata comment_count: {comment_count}")
                                
                                # Indicate if actual comments are available
                                if comment_count > 0:
                                    if actual_comments > 0:
                                        # We have both metadata count and actual comments
                                        st.metric("Comments", f"{actual_comments}/{comment_count}")
                                    else:
                                        # We have only metadata count
                                        st.metric("Comments", comment_count)
                                        
                                        # Check if comments are disabled
                                        if video.get('comments_disabled', False):
                                            st.info("Comments disabled by owner")
                                else:
                                    st.metric("Comments", "0")
                            else:
                                # Fall back to counting comments array
                                comment_count = len(video.get('comments', []))
                                st.metric("Comments", comment_count)
                                debug_log(f"Video '{video.get('title', 'Unknown')}' has no comment_count field, using array length: {comment_count}")
                            
                            # Show sample comment if available
                            if len(video.get('comments', [])) > 0:
                                # Use a button that toggles the comments display in session state
                                comment_id = f"show_comments_{video.get('video_id')}"
                                if comment_id not in st.session_state:
                                    st.session_state[comment_id] = False
                                
                                if st.button(f"{'Hide' if st.session_state[comment_id] else 'Show'} Comments", key=f"btn_{video.get('video_id')}"):
                                    st.session_state[comment_id] = not st.session_state[comment_id]
                                
                                # Display comments if the button state is True
                                if st.session_state[comment_id]:
                                    for j, comment in enumerate(video.get('comments', [])[:3]):
                                        author = comment.get('comment_author', 'Anonymous')
                                        text = comment.get('comment_text', '')
                                        # Truncate long comments
                                        display_text = text[:100] + '...' if len(text) > 100 else text
                                        st.write(f"**{author}:** {display_text}")
                                    
                                    # Link to see all comments on YouTube
                                    st.markdown(f"[View all comments on YouTube]({video_url})")
                        
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
                    
                    # Display detailed summary
                    st.markdown("### Data Collection Summary")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Videos", videos_fetched)
                    with col2:
                        st.metric("Videos With Comments", videos_with_comments)
                    with col3:
                        st.metric("Total Comments", total_comments)
                    
                    # Add more detailed summary in an expander
                    with st.expander("View Collection Details"):
                        st.markdown("#### Channel Information")
                        st.write(f"**Channel Name:** {channel_info.get('channel_name', 'Unknown')}")
                        st.write(f"**Subscribers:** {format_number(int(channel_info.get('subscribers', 0)))}")
                        st.write(f"**Total Channel Videos:** {format_number(int(channel_info.get('total_videos', 0)))}")
                        
                        st.markdown("#### Collected Data")
                        st.write(f"**Videos Downloaded:** {videos_fetched} of {channel_info.get('total_videos', 0)}")
                        if 'videos_unavailable' in channel_info:
                            st.write(f"**Unavailable Videos:** {channel_info.get('videos_unavailable', 0)}")
                        if 'videos_with_comments_disabled' in channel_info:
                            st.write(f"**Videos with Comments Disabled:** {channel_info.get('videos_with_comments_disabled', 0)}")
                        
                        # If we have actual comment stats from the API, show them
                        if 'comment_stats' in channel_info:
                            stats = channel_info['comment_stats']
                            if 'videos_with_errors' in stats and stats['videos_with_errors'] > 0:
                                st.write(f"**Videos with Errors:** {stats['videos_with_errors']}")
                    
                    # Next steps guidance with a clear button
                    st.markdown("### Next Steps")
                    st.info("You've successfully collected data from YouTube. Now you can save this data for analysis.")
                    
                    # Add a prominent "Go to Data Storage" button
                    if st.button("Go to Data Storage Tab", type="primary"):
                        # Set the Streamlit session state to switch to the Storage tab
                        st.session_state.active_tab = "Data Storage"
                        st.rerun()
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
                                    
                                    # Count total comments retrieved for display
                                    total_comments = 0
                                    videos_with_comments = 0
                                    
                                    debug_log("COMMENT UI DEBUG: Scanning returned videos to count comments...")
                                    for video in updated_channel_info.get('video_id', []):
                                        comments_count = len(video.get('comments', []))
                                        
                                        # Add debugging for first video with comments
                                        if comments_count > 0 and videos_with_comments == 0:
                                            debug_log(f"COMMENT UI DEBUG: First video with comments: '{video.get('title')}' has {comments_count} comments")
                                            if comments_count > 0:
                                                sample_comment = video['comments'][0]
                                                debug_log(f"COMMENT UI DEBUG: Sample comment: {sample_comment}")
                                        
                                        total_comments += comments_count
                                        if comments_count > 0:
                                            videos_with_comments += 1
                                    
                                    # Check if we have comment stats from the API
                                    if 'comment_stats' in updated_channel_info:
                                        stats = updated_channel_info['comment_stats']
                                        debug_log(f"COMMENT UI DEBUG: Comment stats from API: {stats}")
                                    else:
                                        debug_log("COMMENT UI DEBUG: No comment_stats found in returned channel_info")
                                    
                                    if total_comments == 0:
                                        debug_log("COMMENT UI DEBUG: No comments were found after fetch operation")
                                        
                                        # Check if any videos might have disabled comments
                                        videos_with_disabled_comments = 0
                                        for video in updated_channel_info.get('video_id', []):
                                            if video.get('comments_disabled', False):
                                                videos_with_disabled_comments += 1
                                        
                                        if videos_with_disabled_comments > 0:
                                            st.warning(f"⚠️ {videos_with_disabled_comments} videos have comments disabled by the channel owner")
                                    
                                    # Force UI refresh to show the updated comment counts and summary view
                                    st.rerun()
                        else:
                            st.error("No videos available to fetch comments for.")
            else:
                # Video fetching options
                st.write("Now you can fetch videos for this channel.")
                max_videos_available = int(channel_info.get('total_videos', 0))
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if max_videos_available > 0:
                        video_slider_help = (f"Select how many videos to import (from 0 to {max_videos_available}). "
                                            f"Note: Some videos may be private or unavailable.")
                        max_videos = st.slider(
                            "Number of Videos to Fetch", 
                            min_value=0, 
                            max_value=max_videos_available, 
                            value=min(25, max_videos_available),
                            help=video_slider_help
                        )
                    else:
                        st.warning("No videos found for this channel.")
                        max_videos = 0
                
                with col2:
                    fetch_all_videos = st.checkbox(
                        "Fetch All Videos", 
                        help=f"Attempt to fetch all {max_videos_available} videos from this channel"
                    )
                
                if fetch_all_videos:
                    st.session_state.max_videos = 0  # 0 means fetch all available videos
                    st.info(f"Will attempt to fetch all {max_videos_available} videos (may take time for channels with many videos)")
                else:
                    st.session_state.max_videos = max_videos
                
                # Calculate quota estimate and show API usage warning for large channels
                if max_videos_available > 500 and fetch_all_videos:
                    st.warning("⚠️ Warning: Fetching all videos from a large channel may consume significant API quota and take time.")
                
                video_quota = estimate_quota_usage(
                    fetch_channel=False,
                    fetch_videos=True,
                    fetch_comments=False,
                    video_count=max_videos_available if fetch_all_videos else max_videos,
                    comments_count=0
                )
                st.info(f"Estimated API quota cost for videos: {video_quota} units")
                
                # Button to fetch videos
                if st.button("Fetch Videos", type="primary"):
                    if max_videos_available > 0:
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
                                st.rerun()  # Rerun to update UI
                    else:
                        st.error("This channel has no videos to fetch.")
        
        else:
            # First step - fetch channel data only
            st.write("First, fetch the channel data to get basic information.")
            
            # Calculate quota for just channel data
            channel_quota = estimate_quota_usage(
                fetch_channel=True,
                fetch_videos=False,
                fetch_comments=False,
                video_count=0,
                comments_count=0
            )
            st.info(f"Estimated API quota cost for channel data: {channel_quota} units")
            
            # Button to fetch channel data
            if st.button("Fetch Channel Data", type="primary"):
                if channel_input:
                    with st.spinner("Fetching channel data from YouTube..."):
                        # Create options with only channel data retrieval enabled
                        options = {
                            'fetch_channel_data': True,
                            'fetch_videos': False,
                            'fetch_comments': False,
                            'max_videos': 0,
                            'max_comments_per_video': 0
                        }
                        
                        channel_info = youtube_service.collect_channel_data(channel_input, options)
                        
                        if channel_info:
                            st.session_state.channel_info_temp = channel_info
                            st.session_state.channel_data_fetched = True
                            st.success(f"Successfully fetched channel data for: {channel_info.get('channel_name')}")
                            st.rerun()  # Rerun to update UI
                        else:
                            st.error("Failed to collect data for the channel. Please check the channel ID and API key.")
                else:
                    st.error("Please enter a YouTube Channel ID or URL")
        
        # Debug mode toggle at the bottom
        st.divider()
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
    else:
        st.error("Please enter a YouTube API Key")