"""
UI components for the Data Collection tab.
"""
import streamlit as st
import time
from datetime import datetime
import pandas as pd
import json
import os

from src.api.youtube_api import YouTubeAPI
from src.services.youtube_service import YouTubeService
from src.utils.helpers import debug_log, format_number, format_duration, get_thumbnail_url, estimate_quota_usage
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH

# Import DeepDiff for comparing data objects
try:
    from deepdiff import DeepDiff
except ImportError:
    # If not installed, we'll handle this later
    pass

def render_video_item(video, index):
    """Render a single video item in a consistent, readable format"""
    title = video.get('title', 'Untitled Video')
    video_id = video.get('video_id', '')
    thumbnail = video.get('thumbnails', '') or video.get('thumbnail_url', '')
    views = format_number(int(video.get('views', 0)))
    likes = format_number(int(video.get('likes', 0)))
    duration = format_duration(video.get('duration', ''))
    published_at = video.get('published_at', '')
    
    # Format the date
    try:
        date_obj = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
        published_date = date_obj.strftime('%b %d, %Y')
    except:
        published_date = published_at
    
    # Create a clean card layout for each video
    st.markdown(f"### {index+1}. {title}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display thumbnail with link
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Only add the image if we have a valid thumbnail URL
        if thumbnail and isinstance(thumbnail, str) and thumbnail.startswith('http'):
            st.markdown(f"[![Video Thumbnail]({thumbnail})]({video_url})")
        else:
            st.markdown(f"[Watch on YouTube]({video_url})")
    
    with col2:
        # Display video metadata in a clean format
        st.markdown(f"**Published:** {published_date}")
        
        # Create a metrics row
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        with metrics_col1:
            st.metric("Views", views)
        with metrics_col2:
            st.metric("Likes", likes)
        with metrics_col3:
            st.metric("Duration", duration)
        
        # Check if we have comments and show a count
        comments = video.get('comments', [])
        if comments:
            st.metric("Comments", len(comments))
            
            # Show sample comments in an expander
            with st.expander("View Comments"):
                for i, comment in enumerate(comments[:5]):  # Show first 5 comments
                    comment_text = comment.get('comment_text', '')
                    comment_author = comment.get('comment_author', 'Anonymous')
                    st.markdown(f"**{comment_author}:** {comment_text}")
                
                if len(comments) > 5:
                    st.markdown(f"*...and {len(comments) - 5} more comments*")

def render_delta_report(previous_data, updated_data, data_type="channel"):
    """
    Render a report showing the changes between previous and updated data
    
    Args:
        previous_data: The previous data before update
        updated_data: The newly fetched data
        data_type: Type of data being compared (channel, video, comment)
    """
    try:
        # Use DeepDiff to calculate differences
        diff = DeepDiff(previous_data, updated_data, ignore_order=True, verbose_level=2)
        
        if not diff:
            st.info(f"No changes detected in {data_type} data")
            return False
        
        # Show a summary of changes
        st.subheader(f"Changes in {data_type.title()} Data")
        
        # Count total changes
        total_changes = sum(len(changes) for changes in diff.values())
        st.write(f"Total changes detected: {total_changes}")
        
        # Process different types of changes
        if 'values_changed' in diff:
            st.write(f"#### Values Updated: {len(diff['values_changed'])}")
            
            # Create a table for the changes
            changes_data = []
            for path, change in diff['values_changed'].items():
                # Clean up the path for display
                clean_path = path.replace("root['", "").replace("']", "").replace(".", " > ")
                
                # Format the values for display
                old_value = change['old_value']
                new_value = change['new_value']
                
                # Special formatting for numbers
                if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                    if old_value > 1000 or new_value > 1000:
                        old_display = format_number(old_value)
                        new_display = format_number(new_value)
                        diff_value = new_value - old_value
                        diff_display = f"+{format_number(diff_value)}" if diff_value > 0 else format_number(diff_value)
                    else:
                        old_display = str(old_value)
                        new_display = str(new_value)
                        diff_value = new_value - old_value
                        diff_display = f"+{diff_value}" if diff_value > 0 else str(diff_value)
                else:
                    old_display = str(old_value)
                    new_display = str(new_value)
                
                # Adding a properly formatted change row
                change_str = f"{old_display} → {new_display}"
                if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)) and old_value != 0:
                    pct_change = ((new_value - old_value) / old_value) * 100
                    change_str += f" ({pct_change:+.1f}%)"
                
                changes_data.append({
                    "Field": clean_path,
                    "Change": change_str
                })
            
            # Display changes in a DataFrame
            if changes_data:
                changes_df = pd.DataFrame(changes_data)
                st.dataframe(changes_df, use_container_width=True)
        
        # Show newly added items
        if 'dictionary_item_added' in diff:
            added_items = [item.replace("root['", "").replace("']", "").replace(".", " > ") 
                          for item in diff['dictionary_item_added']]
            
            if data_type == "video":
                new_videos_count = len([item for item in added_items if "video_id" in item])
                if new_videos_count > 0:
                    st.success(f"✅ {new_videos_count} new videos found")
            elif data_type == "comment":
                new_comments_count = len([item for item in added_items if "comments" in item])
                if new_comments_count > 0:
                    st.success(f"✅ {new_comments_count} new comments found")
            else:
                if added_items:
                    st.success(f"✅ New data added: {', '.join(added_items[:5])}")
                    if len(added_items) > 5:
                        st.info(f"...and {len(added_items)-5} more items")
        
        # Show removed items
        if 'dictionary_item_removed' in diff:
            removed_items = [item.replace("root['", "").replace("']", "").replace(".", " > ") 
                            for item in diff['dictionary_item_removed']]
            
            if removed_items:
                st.warning(f"⚠️ Items no longer present: {', '.join(removed_items[:5])}")
                if len(removed_items) > 5:
                    st.info(f"...and {len(removed_items)-5} more items")
        
        return True
    except ImportError:
        st.warning("DeepDiff package not installed. Delta reporting disabled.")
        return False
    except Exception as e:
        st.error(f"Error generating delta report: {str(e)}")
        debug_log(f"Delta report error: {str(e)}", e)
        return False

def convert_db_to_api_format(db_data):
    """
    Convert database-structured channel data to YouTube API format
    for compatibility with the existing collection process
    
    Args:
        db_data: Channel data from database
        
    Returns:
        dict: Data in YouTube API format
    """
    try:
        # Create a new data structure in the API format
        api_data = {
            'channel_id': '',
            'channel_name': '',
            'subscribers': 0,
            'views': 0,
            'total_videos': 0,
            'channel_description': '',
            'video_id': []
        }
        
        # Debug logging to track the conversion process
        debug_log(f"Converting DB data to API format. Keys in db_data: {list(db_data.keys())}")
        
        # Map channel info fields
        if 'channel_info' in db_data:
            channel_info = db_data['channel_info']
            api_data['channel_name'] = channel_info.get('title', '')
            api_data['channel_description'] = channel_info.get('description', '')
            api_data['channel_id'] = channel_info.get('id', '')
            
            debug_log(f"Channel info found. ID: {api_data['channel_id']}, Name: {api_data['channel_name']}")
            
            if 'statistics' in channel_info:
                stats = channel_info['statistics']
                api_data['subscribers'] = int(stats.get('subscriberCount', 0))
                api_data['views'] = int(stats.get('viewCount', 0))
                
                # Get video count from statistics
                video_count_from_stats = int(stats.get('videoCount', 0))
                api_data['total_videos'] = video_count_from_stats
                
                debug_log(f"Channel statistics found. Subscribers: {api_data['subscribers']}, "
                          f"Views: {api_data['views']}, Total videos from stats: {video_count_from_stats}")
        
        # Convert videos
        if 'videos' in db_data:
            videos_count = len(db_data['videos'])
            
            # Only use the videos count as a fallback if stats didn't provide it or it's 0
            if api_data['total_videos'] == 0:
                api_data['total_videos'] = videos_count
                debug_log(f"Using video count from videos array: {videos_count}")
            
            # Always add the videos_fetched field for UI display
            api_data['videos_fetched'] = videos_count
            
            debug_log(f"Found {videos_count} videos to convert. Final total_videos value: {api_data['total_videos']}")
            
            # Convert each video
            for db_video in db_data['videos']:
                video_id = db_video.get('id', '')
                
                # Create API-format video object
                api_video = {
                    'video_id': video_id,
                    'title': db_video.get('snippet', {}).get('title', ''),
                    'video_description': db_video.get('snippet', {}).get('description', ''),
                    'published_at': db_video.get('snippet', {}).get('publishedAt', ''),
                    'published_date': db_video.get('snippet', {}).get('publishedAt', '')[:10] if db_video.get('snippet', {}).get('publishedAt', '') else '',
                    'views': int(db_video.get('statistics', {}).get('viewCount', 0)),
                    'likes': int(db_video.get('statistics', {}).get('likeCount', 0)),
                    'comment_count': int(db_video.get('statistics', {}).get('commentCount', 0)),
                    'duration': db_video.get('contentDetails', {}).get('duration', ''),
                    'comments': []
                }
                
                # Add comments if available for this video
                if 'comments' in db_data and video_id in db_data['comments']:
                    video_comments = db_data['comments'][video_id]
                    for db_comment in video_comments:
                        comment_data = {
                            'comment_id': db_comment.get('id', ''),
                            'comment_text': db_comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', ''),
                            'comment_author': db_comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('authorDisplayName', ''),
                            'comment_published_at': db_comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('publishedAt', '')
                        }
                        api_video['comments'].append(comment_data)
                
                # Add locations if available
                if 'locations' in db_video:
                    api_video['locations'] = db_video['locations']
                
                # Add this video to the channel data
                api_data['video_id'].append(api_video)
            
            # Final verification of video counts for debugging
            debug_log(f"Converted {len(api_data['video_id'])} videos to API format. "
                      f"total_videos: {api_data['total_videos']}, videos_fetched: {api_data['videos_fetched']}")
        else:
            debug_log("No videos found in database data")
        
        return api_data
    except Exception as e:
        debug_log(f"Error converting DB to API format: {str(e)}", e)
        return None

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
                        # Check for deltas if we're in existing channel mode
                        if previous_data and st.session_state.collection_mode == "existing_channel":
                            with st.expander("View Changes in Videos", expanded=True):
                                prev_video_data = {'video_id': previous_data.get('video_id', [])}
                                updated_video_data = {'video_id': updated_channel_info.get('video_id', [])}
                                render_delta_report(prev_video_data, updated_video_data, data_type="video")
                        
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
                collected_data_html += f"<p><strong>Unavailable Videos:</strong> {channel_info.get('videos_unavailable', 0)}</p>"
            
            if 'videos_with_comments_disabled' in channel_info:
                collected_data_html += f"<p><strong>Videos with Comments Disabled:</strong> {channel_info.get('videos_with_comments_disabled', 0)}</p>"
            
            # If we have actual comment stats from the API, show them
            if 'comment_stats' in channel_info:
                stats = channel_info['comment_stats']
                if 'videos_with_errors' in stats and stats['videos_with_errors'] > 0:
                    collected_data_html += f"<p><strong>Videos with Errors:</strong> {stats['videos_with_errors']}</p>"
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Videos", videos_fetched)
            with col2:
                st.metric("Videos With Comments", videos_with_comments)
            with col3:
                st.metric("Total Comments", total_comments)
            
            # Add more detailed summary in an expander
            with st.expander("View Collection Details"):
                # Use the template to render the collection summary
                render_template_as_markdown("data_collection_summary.html", {
                    "channel_info_html": channel_info_html,
                    "collected_data_html": collected_data_html
                })
            
            # Next steps guidance with a clear button
            st.markdown("### Next Steps")
            st.info("You've successfully collected data from YouTube. Now you can save this data for analysis.")
            
            # Storage options section (replacing the Go to Data Storage button)
            st.markdown("### Storage Options")
            
            # Initialize application settings to get available storage options
            from src.config import Settings
            app_settings = Settings()
            
            if 'current_channel_data' in st.session_state and st.session_state.current_channel_data:
                channel_data = st.session_state.current_channel_data
                
                # Display available storage options as a radio selection
                storage_option = st.radio(
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
                                
                                # Optional: Offer to view the data or continue to analysis
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Continue to Data Analysis", key="goto_analysis"):
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
                            
                            # Check for deltas if we're in existing channel mode
                            if previous_data and st.session_state.collection_mode == "existing_channel":
                                with st.expander("View Changes in Comments", expanded=True):
                                    # Extract only comment data for comparison
                                    prev_videos = previous_data.get('video_id', [])
                                    updated_videos = updated_channel_info.get('video_id', [])
                                    
                                    # Create simple objects for comment comparison
                                    prev_comment_data = {'comments': {}}
                                    updated_comment_data = {'comments': {}}
                                    
                                    # Extract comment counts for each video
                                    for video in prev_videos:
                                        vid_id = video.get('video_id', '')
                                        if vid_id:
                                            prev_comment_data['comments'][vid_id] = len(video.get('comments', []))
                                    
                                    for video in updated_videos:
                                        vid_id = video.get('video_id', '')
                                        if vid_id:
                                            updated_comment_data['comments'][vid_id] = len(video.get('comments', []))
                                    
                                    render_delta_report(prev_comment_data, updated_comment_data, data_type="comment")
                            
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
                        # If we're in existing channel mode, show delta report
                        if previous_data and st.session_state.collection_mode == "existing_channel":
                            with st.expander("View Changes in Videos", expanded=True):
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
    if 'collection_mode' not in st.session_state:
        st.session_state.collection_mode = "new_channel"  # "new_channel" or "existing_channel"
    if 'previous_channel_data' not in st.session_state:
        st.session_state.previous_channel_data = None
    
    # API Key input
    api_key = os.getenv('YOUTUBE_API_KEY', '')
    user_api_key = st.text_input("Enter YouTube API Key:", value=api_key, type="password")
    
    if user_api_key:
        # Initialize the YouTube service 
        youtube_service = YouTubeService(user_api_key)
        
        # Create tabs for new channel vs existing channel
        tab1, tab2 = st.tabs(["New Channel", "Update Existing Channel"])
        
        # New Channel tab
        with tab1:
            if st.session_state.collection_mode == "existing_channel":
                # Reset state if switching from existing to new channel mode
                reset_button = st.button("Start New Collection", type="primary")
                if reset_button:
                    # Reset collection state
                    st.session_state.collection_mode = "new_channel"
                    st.session_state.collection_step = 1
                    st.session_state.channel_data_fetched = False
                    st.session_state.videos_fetched = False
                    st.session_state.comments_fetched = False
                    st.session_state.previous_channel_data = None
                    if 'channel_info_temp' in st.session_state:
                        del st.session_state.channel_info_temp
                    st.rerun()
            else:
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
                
                # If we're in the New Channel tab, render the standard collection UI
                if st.session_state.channel_data_fetched and 'channel_info_temp' in st.session_state:
                    render_collection_steps(channel_input, youtube_service)
                else:
                    # First step - fetch channel data only
                    st.subheader("Step 1: Channel Data")
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
        
        # Existing Channel tab
        with tab2:
            if st.session_state.collection_mode == "new_channel":
                # Get available channels from SQLite database
                db = SQLiteDatabase(SQLITE_DB_PATH)
                channels_list = db.get_channels_list()
                
                if not channels_list:
                    st.info("No channels found in the database. Please collect data for a new channel first.")
                else:
                    st.write("Select an existing channel to update or refresh its data.")
                    selected_channel = st.selectbox("Select Channel:", channels_list)
                    
                    if st.button("Load Channel Data", type="primary"):
                        with st.spinner("Loading existing channel data..."):
                            # Get channel ID from title
                            channel_id = db.get_channel_id_by_title(selected_channel)
                            
                            if channel_id:
                                # Load existing channel data for comparison later
                                db_channel_data = db.get_channel_data(selected_channel)
                                if db_channel_data:
                                    # Convert database format to YouTube API format for compatibility
                                    existing_data = convert_db_to_api_format(db_channel_data)
                                    
                                    # Store the previous data for delta reporting
                                    st.session_state.previous_channel_data = existing_data
                                    
                                    # Set up session for existing channel update
                                    st.session_state.collection_mode = "existing_channel"
                                    
                                    # Critical fix: Set channel_data_fetched to True (was previously False)
                                    st.session_state.channel_data_fetched = True
                                    st.session_state.videos_fetched = False
                                    st.session_state.comments_fetched = False
                                    
                                    # Pass channel ID to the standard input flow
                                    st.session_state.existing_channel_id = channel_id
                                    
                                    # Store the channel info so render_collection_steps can use it
                                    st.session_state.channel_info_temp = existing_data
                                    
                                    st.success(f"Loaded channel: {selected_channel}")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to load data for channel: {selected_channel}")
                            else:
                                st.error(f"Could not find channel ID for: {selected_channel}")
            else:
                # We're in existing channel mode
                if 'existing_channel_id' in st.session_state:
                    channel_id = st.session_state.existing_channel_id
                    st.info(f"Updating channel with ID: {channel_id}")
                    
                    # Show step 1 for refreshing channel data
                    st.subheader("Step 1: Update Channel Data")
                    st.write("Fetch the latest channel data from YouTube.")
                    
                    if st.button("Refresh Channel Data", type="primary"):
                        with st.spinner("Fetching latest channel data from YouTube..."):
                            # Create options with only channel data retrieval enabled
                            options = {
                                'fetch_channel_data': True,
                                'fetch_videos': False,
                                'fetch_comments': False,
                                'max_videos': 0,
                                'max_comments_per_video': 0
                            }
                            
                            # Get previous data if available
                            previous_data = st.session_state.previous_channel_data
                            
                            # Fetch updated channel data
                            updated_channel_info = youtube_service.collect_channel_data(channel_id, options)
                            
                            if updated_channel_info:
                                # Store the updated data
                                st.session_state.channel_info_temp = updated_channel_info
                                st.session_state.channel_data_fetched = True
                                
                                # Show delta between previous and new data
                                st.success(f"Successfully fetched updated data for: {updated_channel_info.get('channel_name')}")
                                
                                # Only show delta if we have previous data
                                if previous_data:
                                    with st.expander("View Changes in Channel Data", expanded=True):
                                        render_delta_report(previous_data, updated_channel_info, data_type="channel")
                                
                                st.rerun()  # Rerun to update UI
                            else:
                                st.error("Failed to collect updated data for the channel.")
                    
                    # If channel data has been fetched, render the rest of the collection steps
                    if st.session_state.channel_data_fetched and 'channel_info_temp' in st.session_state:
                        render_collection_steps(channel_id, youtube_service)
                else:
                    st.error("No existing channel selected.")
        
        # Debug mode toggle at the bottom
        st.divider()
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.get('debug_mode', False))
    else:
        st.error("Please enter a YouTube API Key")