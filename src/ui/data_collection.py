"""
UI components for the Data Collection tab.
"""
import streamlit as st
import time
from datetime import datetime
import pandas as pd
import json
import os
import logging

from src.api.youtube_api import YouTubeAPI
from src.services.youtube_service import YouTubeService
from src.utils.helpers import debug_log, format_number, format_duration, get_thumbnail_url, estimate_quota_usage
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.utils.queue_manager import QueueManager
from src.utils.queue_tracker import QueueTracker, render_queue_status_sidebar, get_queue_stats

# Import DeepDiff for comparing data objects
try:
    from deepdiff import DeepDiff
except ImportError:
    # If not installed, we'll handle this later
    pass

# Initialize or get debug log capture handler
if 'debug_log_handler' not in st.session_state:
    # Create a StringIO handler to capture log messages
    import io
    from logging import StreamHandler
    
    class StringIOHandler(StreamHandler):
        def __init__(self):
            self.string_io = io.StringIO()
            StreamHandler.__init__(self, self.string_io)
            self.setLevel(logging.DEBUG)
            self.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%H:%M:%S'
            ))
        
        def get_logs(self):
            return self.string_io.getvalue()
            
        def clear(self):
            self.string_io.truncate(0)
            self.string_io.seek(0)
    
    # Create the handler and add it to the root logger
    st.session_state.debug_log_handler = StringIOHandler()
    logging.getLogger().addHandler(st.session_state.debug_log_handler)
    
# Function to update debug mode state
def toggle_debug_mode():
    """Update debug mode state and logging level"""
    if st.session_state.debug_mode:
        # Enable debug logging
        logging.getLogger().setLevel(logging.DEBUG)
        debug_log("Debug mode enabled")
        # When debug mode is turned on, update the session state log level
        st.session_state.log_level = logging.DEBUG
    else:
        # Disable debug logging
        logging.getLogger().setLevel(logging.WARNING)
        # When debug mode is turned off, update the session state log level
        st.session_state.log_level = logging.WARNING
        
# Function to display debug logs in the UI
def render_debug_logs():
    """Display debug logs in the UI when debug mode is enabled"""
    if st.session_state.debug_mode and 'debug_log_handler' in st.session_state:
        logs = st.session_state.debug_log_handler.get_logs()
        if logs:
            with st.expander("Debug Logs", expanded=True):
                st.text_area("Debug Information", logs, height=300)
                if st.button("Clear Logs"):
                    st.session_state.debug_log_handler.clear()
                    st.rerun()

def render_template_as_markdown(template_file, context):
    """
    Render a template file as markdown in Streamlit.
    
    Args:
        template_file (str): The filename of the template in the templates directory
        context (dict): A dictionary of variables to pass to the template
    """
    try:
        import os
        from jinja2 import Environment, FileSystemLoader
        
        # Get the path to the templates directory
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    "src", "static", "templates")
        
        # Set up Jinja2 environment with autoescape enabled for security
        env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
        template = env.get_template(template_file)
        
        # Render the template with the provided context
        rendered_html = template.render(**context)
        
        # Display as markdown in Streamlit
        st.markdown(rendered_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error rendering template: {str(e)}")
        debug_log(f"Template rendering error: {str(e)}", e)

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
            
            # Instead of using another expander which would cause nesting issues,
            # show a small sample of comments directly and add a "See more" tooltip
            st.markdown("**Sample Comments:**")
            for i, comment in enumerate(comments[:3]):  # Show first 3 comments
                comment_text = comment.get('comment_text', '')
                comment_author = comment.get('comment_author', 'Anonymous')
                st.markdown(f"- **{comment_author}**: {comment_text[:100]}{'...' if len(comment_text) > 100 else ''}")
            
            if len(comments) > 3:
                st.markdown(f"*...and {len(comments) - 3} more comments*")

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
        
        # Show a summary of changes
        st.subheader(f"Changes in {data_type.title()} Data")
        
        if not diff:
            # Show a more informative message and key metrics when no changes are detected
            st.info(f"No changes detected in {data_type} data")
            
            # For channel data, show the key metrics that were compared
            if data_type == "channel":
                st.write("The following metrics remain unchanged:")
                metrics_to_show = []
                
                # Extract key metrics to display from channel data
                if 'channel_name' in updated_data:
                    metrics_to_show.append(("Channel Name", updated_data.get('channel_name', 'Unknown')))
                if 'subscribers' in updated_data:
                    metrics_to_show.append(("Subscribers", format_number(int(updated_data.get('subscribers', 0)))))
                if 'views' in updated_data:
                    metrics_to_show.append(("Views", format_number(int(updated_data.get('views', 0)))))
                if 'total_videos' in updated_data:
                    metrics_to_show.append(("Videos", format_number(int(updated_data.get('total_videos', 0)))))
                
                # Display metrics in a clear format
                if metrics_to_show:
                    # Use columns to display metrics nicely
                    cols = st.columns(min(4, len(metrics_to_show)))
                    for i, (label, value) in enumerate(metrics_to_show):
                        with cols[i % len(cols)]:
                            st.metric(label, value)
                
                # Add timestamp info for last check
                st.caption(f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # For video data, show a summary of the videos that were checked
            elif data_type == "video":
                video_count = len(updated_data.get('video_id', []))
                if video_count > 0:
                    st.write(f"All {video_count} videos remain unchanged.")
                    
                    # Show a sample of video titles
                    sample_size = min(5, video_count)
                    if sample_size > 0:
                        st.write(f"Sample videos checked:")
                        for i in range(sample_size):
                            video = updated_data['video_id'][i]
                            st.write(f"- {video.get('title', 'Unknown')}")
                        
                        if video_count > sample_size:
                            st.write(f"...and {video_count - sample_size} more videos")
            
            # For comments data, show a summary of the comments that were checked
            elif data_type == "comment":
                if 'comments' in updated_data:
                    comment_data = updated_data['comments']
                    video_count = len(comment_data.keys())
                    comment_count = sum(comment_data.values())
                    
                    if video_count > 0:
                        st.write(f"All comments across {video_count} videos remain unchanged.")
                        st.write(f"Total comments checked: {comment_count}")
            
            return False
        
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
    # Always log some debug info to help with troubleshooting
    debug_log(f"Starting DB to API format conversion")
    
    # Create a new data structure in the API format with default values
    api_data = {
        'channel_id': '',
        'channel_name': '',
        'subscribers': 0,
        'views': 0,
        'total_videos': 0,
        'channel_description': '',
        'playlist_id': '',
        'video_id': []
    }
    
    try:
        # Validate input data
        if not db_data:
            debug_log(f"WARNING: Empty database data provided to convert_db_to_api_format")
            return api_data
        
        # Debug logging to track the conversion process
        debug_log(f"Converting DB data to API format. Keys in db_data: {list(db_data.keys())}")
        
        # Map channel info fields
        if 'channel_info' in db_data:
            channel_info = db_data['channel_info']
            debug_log(f"Found channel_info with keys: {list(channel_info.keys() if isinstance(channel_info, dict) else [])}")
            
            if isinstance(channel_info, dict):
                api_data['channel_name'] = channel_info.get('title', '')
                api_data['channel_description'] = channel_info.get('description', '')
                api_data['channel_id'] = channel_info.get('id', '')
                
                debug_log(f"Channel info found. ID: {api_data['channel_id']}, Name: {api_data['channel_name']}")
                
                # Check for uploads playlist ID in channel info
                if 'contentDetails' in channel_info and isinstance(channel_info['contentDetails'], dict):
                    if 'relatedPlaylists' in channel_info['contentDetails'] and isinstance(channel_info['contentDetails']['relatedPlaylists'], dict):
                        if 'uploads' in channel_info['contentDetails']['relatedPlaylists']:
                            api_data['playlist_id'] = channel_info['contentDetails']['relatedPlaylists']['uploads']
                            debug_log(f"Found uploads playlist ID in contentDetails: {api_data['playlist_id']}")
                
                if 'statistics' in channel_info and isinstance(channel_info['statistics'], dict):
                    stats = channel_info['statistics']
                    # Safely convert to integers with fallbacks
                    try:
                        api_data['subscribers'] = int(stats.get('subscriberCount', '0'))
                    except (ValueError, TypeError):
                        api_data['subscribers'] = 0
                        debug_log(f"Failed to convert subscriberCount to int: {stats.get('subscriberCount')}")
                    
                    try:
                        api_data['views'] = int(stats.get('viewCount', '0'))
                    except (ValueError, TypeError):
                        api_data['views'] = 0
                        debug_log(f"Failed to convert viewCount to int: {stats.get('viewCount')}")
                    
                    # Get video count from statistics
                    try:
                        video_count_from_stats = int(stats.get('videoCount', '0'))
                        api_data['total_videos'] = video_count_from_stats
                    except (ValueError, TypeError):
                        video_count_from_stats = 0
                        api_data['total_videos'] = 0
                        debug_log(f"Failed to convert videoCount to int: {stats.get('videoCount')}")
                    
                    debug_log(f"Channel statistics found. Subscribers: {api_data['subscribers']}, "
                              f"Views: {api_data['views']}, Total videos from stats: {video_count_from_stats}")
        else:
            debug_log(f"WARNING: No channel_info field found in database data")
        
        # Look for uploads_playlist_id in db_data (older databases might store it here)
        if 'uploads_playlist_id' in db_data and db_data['uploads_playlist_id']:
            api_data['playlist_id'] = db_data['uploads_playlist_id']
            debug_log(f"Found uploads playlist ID at root level: {api_data['playlist_id']}")
        
        # Convert videos
        if 'videos' in db_data and isinstance(db_data['videos'], list):
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
                if not isinstance(db_video, dict):
                    debug_log(f"Skipping non-dictionary video entry: {type(db_video)}")
                    continue
                    
                video_id = db_video.get('id', '')
                if not video_id:
                    debug_log(f"Skipping video missing ID")
                    continue
                
                # Create API-format video object with safe defaults
                api_video = {
                    'video_id': video_id,
                    'title': '',
                    'video_description': '',
                    'published_at': '',
                    'published_date': '',
                    'views': 0,
                    'likes': 0,
                    'comment_count': 0,
                    'duration': '',
                    'comments': []
                }
                
                # Safely extract nested properties with type checking
                if 'snippet' in db_video and isinstance(db_video['snippet'], dict):
                    snippet = db_video['snippet']
                    api_video['title'] = snippet.get('title', '')
                    api_video['video_description'] = snippet.get('description', '')
                    api_video['published_at'] = snippet.get('publishedAt', '')
                    # Extract date part of publishedAt if available
                    if api_video['published_at'] and len(api_video['published_at']) >= 10:
                        api_video['published_date'] = api_video['published_at'][:10]
                
                if 'statistics' in db_video and isinstance(db_video['statistics'], dict):
                    stats = db_video['statistics']
                    # Safely convert to integers
                    try:
                        api_video['views'] = int(stats.get('viewCount', '0'))
                    except (ValueError, TypeError):
                        api_video['views'] = 0
                    
                    try:
                        api_video['likes'] = int(stats.get('likeCount', '0'))
                    except (ValueError, TypeError):
                        api_video['likes'] = 0
                        
                    try:
                        api_video['comment_count'] = int(stats.get('commentCount', '0'))
                    except (ValueError, TypeError):
                        api_video['comment_count'] = 0
                
                if 'contentDetails' in db_video and isinstance(db_video['contentDetails'], dict):
                    api_video['duration'] = db_video['contentDetails'].get('duration', '')
                
                # Add comments if available for this video
                if 'comments' in db_data and isinstance(db_data['comments'], dict) and video_id in db_data['comments']:
                    video_comments = db_data['comments'][video_id]
                    if isinstance(video_comments, list):
                        for db_comment in video_comments:
                            if not isinstance(db_comment, dict):
                                continue
                            
                            # Carefully extract nested comment data
                            comment_data = {'comment_id': '', 'comment_text': '', 'comment_author': '', 'comment_published_at': ''}
                            
                            comment_data['comment_id'] = db_comment.get('id', '')
                            
                            # Navigate the nested structure carefully
                            if 'snippet' in db_comment and isinstance(db_comment['snippet'], dict):
                                if 'topLevelComment' in db_comment['snippet'] and isinstance(db_comment['snippet']['topLevelComment'], dict):
                                    if 'snippet' in db_comment['snippet']['topLevelComment'] and isinstance(db_comment['snippet']['topLevelComment']['snippet'], dict):
                                        comment_snippet = db_comment['snippet']['topLevelComment']['snippet']
                                        comment_data['comment_text'] = comment_snippet.get('textDisplay', '')
                                        comment_data['comment_author'] = comment_snippet.get('authorDisplayName', '')
                                        comment_data['comment_published_at'] = comment_snippet.get('publishedAt', '')
                            
                            api_video['comments'].append(comment_data)
                
                # Add locations if available
                if 'locations' in db_video and isinstance(db_video['locations'], list):
                    api_video['locations'] = db_video['locations']
                
                # Add this video to the channel data
                api_data['video_id'].append(api_video)
            
            # Final verification of video counts for debugging
            debug_log(f"Converted {len(api_data['video_id'])} videos to API format. "
                      f"total_videos: {api_data['total_videos']}, videos_fetched: {api_data['videos_fetched']}")
        else:
            debug_log("No videos found in database data or 'videos' is not a list")
        
        # Final check on uploads playlist ID
        if not api_data['playlist_id']:
            debug_log("WARNING: No uploads playlist ID found after conversion. Videos cannot be fetched without this.")
            # Try to extract it from another potential location
            if 'channel_info' in db_data and isinstance(db_data['channel_info'], dict):
                uploads_id = db_data['channel_info'].get('uploads_playlist_id', '')
                if uploads_id:
                    api_data['playlist_id'] = uploads_id
                    debug_log(f"Found uploads playlist ID in channel_info.uploads_playlist_id: {uploads_id}")
        
        debug_log(f"Final API data structure - has playlist_id: {'playlist_id' in api_data}, value: {api_data.get('playlist_id', 'NOT_FOUND')}")
        
        # Final validation - ensure channel_id exists
        if not api_data['channel_id']:
            debug_log("WARNING: No channel_id found in the converted data. This may cause issues downstream.")
            # Try to find channel_id in the database structure
            if 'channel_id' in db_data:
                api_data['channel_id'] = db_data['channel_id']
                debug_log(f"Found channel_id at root level: {api_data['channel_id']}")
        
        return api_data
    except Exception as e:
        # Catch all exceptions and log them, but return a valid data structure
        debug_log(f"ERROR in convert_db_to_api_format: {str(e)}", e)
        # Return the partially filled api_data, which should at least have default values
        return api_data

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
            
            # Check for deltas if we're in existing channel mode (MOVED OUTSIDE EXPANDER)
            if previous_data and st.session_state.collection_mode == "existing_channel":
                st.subheader("Changes in Comments")
                # Extract only comment data for comparison
                prev_videos = previous_data.get('video_id', [])
                updated_videos = channel_info.get('video_id', [])
                
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

def render_data_collection_tab():
    """
    Render the Data Collection tab UI.
    """
    st.header("YouTube Data Collection")

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
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
    if 'api_call_status' not in st.session_state:
        st.session_state.api_call_status = None
    
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
                    if st.button("Fetch Channel Data", type="primary"):
                        if channel_input:
                            with st.spinner("Fetching channel data from YouTube..."):
                                # Create options object with only channel data retrieval enabled
                                options = {
                                    'fetch_channel_data': True,
                                    'fetch_videos': False,
                                    'fetch_comments': False,
                                    'max_videos': 0,
                                    'max_comments_per_video': 0
                                }
                                
                                # Call the service to fetch channel data
                                channel_info = youtube_service.collect_channel_data(channel_input, options)
                                
                                if channel_info:
                                    st.session_state.channel_info_temp = channel_info
                                    st.session_state.channel_data_fetched = True
                                    st.success(f"Successfully fetched channel data for: {channel_info.get('channel_name')}")
                                    st.rerun()
                                else:
                                    st.error("Failed to fetch channel data. Please check your channel ID/URL and API key.")
                        else:
                            st.error("Please enter a Channel ID or URL")
        
        # Update Existing Channel tab
        with tab2:
            if st.session_state.collection_mode == "new_channel":
                # Initialize channel_id to None before it's potentially used
                channel_id = None
                
                # Here goes the code for selecting an existing channel
                db = SQLiteDatabase(SQLITE_DB_PATH)
                
                try:
                    channels = db.list_channels()
                    
                    if channels:
                        # Show dropdown with available channels
                        selected_channel = st.selectbox(
                            "Select a channel to update:",
                            options=channels,
                            format_func=lambda x: f"{x[1]} ({x[0]})"  # Show name (id)
                        )
                        
                        # Get channel ID from selection 
                        if selected_channel:
                            channel_id = selected_channel[0]  # First element is ID
                            debug_log(f"Channel selected from dropdown: {channel_id}")
                        
                        # Check if we have any error status to show from a previous attempt
                        if "api_call_error" in st.session_state:
                            st.error(st.session_state.api_call_error)
                            # Clear the error after showing it
                            del st.session_state.api_call_error
                        
                        if st.button("Load Channel Data", type="primary"):
                            with st.spinner("Loading existing channel data..."):
                                if channel_id:
                                    debug_log(f"Loading channel data for: {channel_id}")
                                    # Load existing channel data
                                    try:
                                        db_channel_data = db.get_channel_data(channel_id)
                                        
                                        if db_channel_data:
                                            debug_log(f"Channel data loaded successfully. Converting format...")
                                            # Convert DB format to API format for consistency
                                            api_format_data = convert_db_to_api_format(db_channel_data)
                                            debug_log(f"Data conversion completed. API format data keys: {list(api_format_data.keys())}")
                                            
                                            if api_format_data:
                                                # Store as previous data for delta comparison
                                                st.session_state.previous_channel_data = api_format_data
                                                
                                                # Setup for existing channel mode
                                                st.session_state.collection_mode = "existing_channel"
                                                st.session_state.existing_channel_id = channel_id
                                                st.session_state.api_call_status = "Success: Channel data loaded"
                                                
                                                # Notification of success
                                                st.success(f"Loaded channel: {selected_channel[1]}")
                                                st.rerun()
                                            else:
                                                error_msg = f"Failed to convert data format for channel: {selected_channel[1]}"
                                                debug_log(error_msg)
                                                st.session_state.api_call_status = f"Error: {error_msg}"
                                                st.error(error_msg)
                                        else:
                                            error_msg = f"Failed to load data for channel: {selected_channel[1]}"
                                            debug_log(error_msg)
                                            st.session_state.api_call_status = f"Error: {error_msg}"
                                            st.error(error_msg)
                                    except Exception as e:
                                        error_msg = f"Error loading channel data: {str(e)}"
                                        debug_log(error_msg, e)
                                        st.session_state.api_call_status = f"Error: {error_msg}"
                                        st.error(error_msg)
                                else:
                                    st.error("Please select a channel to load")
                    else:
                        st.warning("No channels found in database. Collect data for a channel first.")
                except Exception as e:
                    error_msg = f"Database error when listing channels: {str(e)}"
                    debug_log(error_msg, e)
                    st.session_state.api_call_status = f"Error: {error_msg}"
                    st.error(error_msg)
            else:
                # We're in existing channel mode
                if 'existing_channel_id' in st.session_state:
                    channel_id = st.session_state.existing_channel_id
                    st.info(f"Updating channel with ID: {channel_id}")
                    
                    # Show step 1 for refreshing channel data
                    st.subheader("Step 1: Update Channel Data")
                    st.write("Fetch the latest channel data from YouTube.")
                    
                    # Show current status if available
                    if 'api_call_status' in st.session_state and st.session_state.api_call_status:
                        if st.session_state.api_call_status.startswith("Success"):
                            st.success(st.session_state.api_call_status)
                        elif st.session_state.api_call_status.startswith("Error"):
                            st.error(st.session_state.api_call_status)
                        elif st.session_state.api_call_status.startswith("Warning"):
                            st.warning(st.session_state.api_call_status)
                        else:
                            st.info(st.session_state.api_call_status)
                    
                    if st.button("Refresh Channel Data", type="primary"):
                        debug_log(f"Refresh Channel Data button clicked for channel: {channel_id}")
                        with st.spinner("Fetching latest channel data from YouTube..."):
                            try:
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
                                debug_log(f"Previous data available: {previous_data is not None}")
                                
                                # Calculate and store last refresh time before refreshing
                                if 'channel_info_temp' in st.session_state:
                                    old_data = st.session_state.channel_info_temp
                                    if 'last_refresh' not in old_data:
                                        old_data['last_refresh'] = {}
                                    old_data['last_refresh']['timestamp'] = datetime.now().isoformat()
                                
                                debug_log(f"Calling YouTube API to fetch channel data for: {channel_id}")
                                # Fetch updated channel data
                                updated_channel_info = youtube_service.collect_channel_data(channel_id, options)
                                
                                if updated_channel_info:
                                    debug_log(f"API call successful. Received data with keys: {list(updated_channel_info.keys())}")
                                    
                                    # Add refresh timestamp to updated data
                                    if 'last_refresh' not in updated_channel_info:
                                        updated_channel_info['last_refresh'] = {}
                                    updated_channel_info['last_refresh']['timestamp'] = datetime.now().isoformat()
                                    
                                    # Store the updated data in multiple session state variables for consistency
                                    st.session_state.channel_info_temp = updated_channel_info
                                    st.session_state.current_channel_data = updated_channel_info  # Also set this for later storage
                                    
                                    # Important: Update ALL session state flags consistently
                                    st.session_state.channel_data_fetched = True
                                    st.session_state.api_call_status = "Success: Channel data loaded"
                                    
                                    # Update API debug information
                                    st.session_state.api_last_response = updated_channel_info
                                    st.session_state.api_client_initialized = True
                                    
                                    # Add a flag to indicate the channel data was successfully fetched
                                    if 'debug_state' not in st.session_state:
                                        st.session_state.debug_state = {}
                                    st.session_state.debug_state['channel_data_fetched'] = True
                                    
                                    # Calculate delta metrics and store them in the updated data
                                    if previous_data:
                                        delta = {}
                                        # Subscriber delta
                                        old_subs = int(previous_data.get('subscribers', 0))
                                        new_subs = int(updated_channel_info.get('subscribers', 0))
                                        delta['subscribers'] = new_subs - old_subs
                                        delta['subscribers_percent'] = (delta['subscribers'] / old_subs * 100) if old_subs > 0 else 0
                                        
                                        # Video count delta
                                        old_videos = int(previous_data.get('total_videos', 0))
                                        new_videos = int(updated_channel_info.get('total_videos', 0))
                                        delta['videos'] = new_videos - old_videos
                                        delta['videos_percent'] = (delta['videos'] / old_videos * 100) if old_videos > 0 else 0
                                        
                                        # Views delta
                                        old_views = int(previous_data.get('views', 0))
                                        new_views = int(updated_channel_info.get('views', 0))
                                        delta['views'] = new_views - old_views
                                        delta['views_percent'] = (delta['views'] / old_views * 100) if old_views > 0 else 0
                                        
                                        # Store delta in updated_channel_info
                                        updated_channel_info['last_refresh']['delta'] = delta
                                        # Also store previous metrics
                                        updated_channel_info['last_refresh']['previous'] = {
                                            'subscribers': old_subs,
                                            'videos': old_videos,
                                            'views': old_views
                                        }
                                        
                                        debug_log(f"Calculated deltas: {delta}")
                                    
                                    # Show success message
                                    st.success(f"Successfully fetched updated data for: {updated_channel_info.get('channel_name')}")
                                    
                                    # Display the delta information prominently
                                    if previous_data:
                                        debug_log("Displaying delta information")
                                        # Always show the delta metrics at the top
                                        st.subheader("Channel Update Delta")
                                        
                                        # Show delta summary with metrics
                                        if 'last_refresh' in updated_channel_info and 'delta' in updated_channel_info['last_refresh']:
                                            delta = updated_channel_info['last_refresh']['delta']
                                            
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                sub_delta = delta.get('subscribers', 0)
                                                sub_delta_str = f"+{format_number(sub_delta)}" if sub_delta >= 0 else f"{format_number(sub_delta)}"
                                                st.metric(
                                                    "Subscribers", 
                                                    format_number(int(updated_channel_info.get('subscribers', 0))),
                                                    sub_delta_str
                                                )
                                            with col2:
                                                vid_delta = delta.get('videos', 0)
                                                vid_delta_str = f"+{vid_delta}" if vid_delta >= 0 else f"{vid_delta}"
                                                st.metric(
                                                    "Videos", 
                                                    format_number(int(updated_channel_info.get('total_videos', 0))),
                                                    vid_delta_str
                                                )
                                            with col3:
                                                view_delta = delta.get('views', 0)
                                                view_delta_str = f"+{format_number(view_delta)}" if view_delta >= 0 else f"{format_number(view_delta)}"
                                                st.metric(
                                                    "Total Views",
                                                    format_number(int(updated_channel_info.get('views', 0))),
                                                    view_delta_str
                                                )
                                            
                                            # Calculate activity scores to help with refresh frequency decisions
                                            activity_score = 0
                                            if abs(delta.get('subscribers_percent', 0)) > 0.5:
                                                activity_score += 1
                                            if abs(delta.get('videos_percent', 0)) > 1:
                                                activity_score += 1
                                            if abs(delta.get('views_percent', 0)) > 1:
                                                activity_score += 1
                                                
                                            # Provide recommendation based on activity score
                                            activity_level = "Low"
                                            refresh_recommendation = "Monthly"
                                            if activity_score >= 2:
                                                activity_level = "High"
                                                refresh_recommendation = "Daily or Weekly"
                                            elif activity_score == 1:
                                                activity_level = "Medium"
                                                refresh_recommendation = "Weekly or Bi-weekly"
                                            
                                            # Show activity level and recommendation
                                            st.info(f"**Channel Activity Level: {activity_level}** - Recommended refresh frequency: {refresh_recommendation}")
                                        
                                        # Move delta reporting outside of the expander and make it more prominent
                                        st.subheader("Detailed Changes")
                                        # Explicitly call render_delta_report with the previous and updated data
                                        render_delta_report(previous_data, updated_channel_info, data_type="channel")
                                        
                                        # Still keep detailed view in an expander for reference
                                        with st.expander("View Detailed Channel Data"):
                                            # Display channel metrics in a clean format
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Subscribers", format_number(int(updated_channel_info.get('subscribers', 0))))
                                            with col2:
                                                st.metric("Total Videos", format_number(int(updated_channel_info.get('total_videos', 0))))
                                            with col3:
                                                st.metric("Total Views", format_number(int(updated_channel_info.get('views', 0))))
                                            
                                            # Show full channel details
                                            st.write("**Channel ID:**", updated_channel_info.get('channel_id', ''))
                                            st.write("**Description:**", updated_channel_info.get('channel_description', 'No description available'))
                                    
                                    # Update the previous_channel_data with the new data for future comparisons
                                    st.session_state.previous_channel_data = updated_channel_info
                                    
                                    # Rerun to update UI
                                    st.rerun()
                                else:
                                    error_msg = f"YouTube API returned no data for channel ID: {channel_id}"
                                    debug_log(error_msg)
                                    st.session_state.api_call_status = f"Error: {error_msg}"
                                    st.error(error_msg)
                            except Exception as e:
                                error_msg = f"Error refreshing channel data: {str(e)}"
                                debug_log(error_msg, e)
                                st.session_state.api_call_status = f"Error: {error_msg}"
                                st.error(error_msg)
                    
                    # If channel data has been fetched, render the rest of the collection steps
                    if st.session_state.channel_data_fetched and 'channel_info_temp' in st.session_state:
                        render_collection_steps(channel_id, youtube_service)
                else:
                    st.error("No existing channel selected.")
        
        # Debug mode toggle at the bottom
        st.divider()
        # Use on_change callback to properly update logging when checkbox changes
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.get('debug_mode', False), on_change=toggle_debug_mode)
        
        # When debug mode is enabled, show debug information
        if st.session_state.debug_mode:
            render_debug_panel()
    else:
        st.error("Please enter a YouTube API Key")

def render_queue_status():
    """
    Display the current queue status to help users understand the current working state
    of data fetching operations.
    """
    try:
        # Get queue stats directly from QueueTracker
        queue_stats = get_queue_stats()
        
        if not queue_stats or (queue_stats.get('total_items', 0) == 0 and 
                             queue_stats.get('channels_count', 0) == 0 and
                             queue_stats.get('videos_count', 0) == 0 and
                             queue_stats.get('comments_count', 0) == 0):
            st.info("No active queue tasks found. All data shown is from cached results.")
            return
        
        # Show a clear summary of what's happening
        st.subheader("Data Source Status")
        
        # Display metrics for each type of data
        col1, col2 = st.columns(2)
        
        with col1:
            if queue_stats.get('channels_count', 0) > 0:
                st.metric("Channels in Queue", queue_stats.get('channels_count', 0))
            if queue_stats.get('videos_count', 0) > 0:
                st.metric("Videos in Queue", queue_stats.get('videos_count', 0))
                
        with col2:
            if queue_stats.get('comments_count', 0) > 0:
                st.metric("Comments in Queue", queue_stats.get('comments_count', 0))
            if queue_stats.get('analytics_count', 0) > 0:
                st.metric("Analytics in Queue", queue_stats.get('analytics_count', 0))
        
        # Show overall status
        if queue_stats.get('total_items', 0) > 0:
            st.info(f"New data is being fetched via API calls - {queue_stats.get('total_items', 0)} items in queue")
        else:
            st.success("All data is being loaded from cache")
            
        # Show last updated time if available
        if queue_stats.get('last_updated'):
            st.caption(f"Last updated: {queue_stats.get('last_updated')}")
            
    except Exception as e:
        debug_log(f"Error displaying queue status: {str(e)}", e)
        st.warning("Could not retrieve queue status information")

def get_queue_stats():
    """
    Get current queue statistics from session state
    
    Returns:
        dict: Queue statistics including info about cached vs. API fetched data
    """
    # Initialize default stats
    if 'queue_stats' not in st.session_state:
        st.session_state.queue_stats = {
            'total_items': 0,
            'channels_count': 0,
            'videos_count': 0,
            'comments_count': 0,
            'analytics_count': 0,
            'last_updated': None
        }
    
    # Import QueueTracker to get latest queue status
    from src.utils.queue_tracker import get_queue_stats as get_tracker_stats
    
    # Get the stats from the QueueTracker
    tracker_stats = get_tracker_stats()
    
    # Combine local and tracker stats
    combined_stats = {**st.session_state.queue_stats}
    
    if tracker_stats:
        # Update with tracker data
        for key in tracker_stats:
            combined_stats[key] = tracker_stats[key]
    
    return combined_stats

def refresh_channel_data(channel_id, youtube_service, options):
    """
    Refresh channel data with a Streamlit UI for the 'Continue to iterate?' prompt
    
    Args:
        channel_id (str): The channel ID to refresh
        youtube_service (YouTubeService): The YouTube service instance
        options (dict): Dictionary containing collection options
        
    Returns:
        dict or None: The updated channel data or None if refresh failed
    """
    # Initialize state for iteration prompt if it doesn't exist
    if 'show_iteration_prompt' not in st.session_state:
        st.session_state.show_iteration_prompt = False
        st.session_state.iteration_choice = None
    
    # Define the callback function for the iteration prompt
    def iteration_prompt_callback():
        # Set flag to show the prompt
        st.session_state.show_iteration_prompt = True
        # We need to return something, but the actual decision will be made in the UI
        return None
    
    # Get the existing data from the database
    db = SQLiteDatabase(SQLITE_DB_PATH)
    existing_data = db.get_channel_data(channel_id)
    
    if not existing_data:
        debug_log(f"No existing data found for channel {channel_id}")
        return None
    
    # Convert DB format to API format
    api_format_data = convert_db_to_api_format(existing_data)
    
    # Update channel data with interactive mode enabled
    # We pass the callback to handle the "Continue to iterate?" prompt
    updated_data = youtube_service.update_channel_data(
        channel_id, 
        options, 
        existing_data=api_format_data,
        interactive=True,
        # Modified to use our callback for the prompt
        callback=iteration_prompt_callback
    )
    
    return updated_data

def render_debug_panel():
    """
    Render debug information panel when debug mode is enabled
    """
    with st.expander("Debug Information", expanded=True):
        # Create tabs for different debug info categories
        debug_tabs = st.tabs(["API Status", "Session State", "Logs", "Response Data"])
        
        # API Status Tab
        with debug_tabs[0]:
            st.subheader("YouTube API Status")
            
            # Display API initialization status
            api_initialized = st.session_state.get('api_client_initialized', False)
            st.metric(
                label="API Client Status", 
                value="Initialized" if api_initialized else "Not Initialized"
            )
            
            # Display last API call status
            api_call_status = st.session_state.get('api_call_status', 'No API calls made yet')
            st.info(f"Last API call: {api_call_status}")
            
            # Display any API errors
            if 'api_last_error' in st.session_state and st.session_state.api_last_error:
                st.error(f"Last API error: {st.session_state.api_last_error}")
        
        # Session State Tab
        with debug_tabs[1]:
            st.subheader("Session State Variables")
            
            # Display relevant session state variables in a table
            debug_vars = [
                {"Variable": "channel_input", "Value": str(st.session_state.get('channel_input', 'Not set'))},
                {"Variable": "channel_data_fetched", "Value": str(st.session_state.get('channel_data_fetched', False))},
                {"Variable": "api_initialized", "Value": str(st.session_state.get('api_initialized', False))},
                {"Variable": "api_client_initialized", "Value": str(st.session_state.get('api_client_initialized', False))}
            ]
            
            # Add channel data summary if available
            if 'channel_data' in st.session_state and st.session_state.channel_data:
                channel = st.session_state.channel_data
                debug_vars.append({"Variable": "channel_name", "Value": str(channel.get('channel_name', 'Unknown'))})
                debug_vars.append({"Variable": "channel_id", "Value": str(channel.get('channel_id', 'Unknown'))})
                debug_vars.append({"Variable": "total_videos", "Value": str(channel.get('total_videos', '0'))})
            
            # Display the debug variables table
            st.table(debug_vars)
        
        # Logs Tab
        with debug_tabs[2]:
            st.subheader("Debug Logs")
            
            # Display logs from string IO handler
            if 'debug_logs' in st.session_state:
                log_text = st.session_state.debug_logs.getvalue()
                st.text_area("Log Output", value=log_text, height=300)
                
                # Add button to clear logs
                if st.button("Clear Debug Logs"):
                    st.session_state.debug_logs.truncate(0)
                    st.session_state.debug_logs.seek(0)
                    st.rerun()
            else:
                st.info("No logs available. Enable debug mode to see logs.")
        
        # Response Data Tab
        with debug_tabs[3]:
            st.subheader("API Response Data")
            
            if 'api_last_response' in st.session_state and st.session_state.api_last_response:
                st.json(st.session_state.api_last_response)
            else:
                st.info("No API response data available yet.")

def channel_refresh_section(youtube_service):
    """Display the channel refresh section."""
    st.subheader("Refresh Channel Data")
    
    # Get the list of channels
    channels = youtube_service.get_channels_list("sqlite")
    
    if not channels:
        st.warning("No channels found in the database.")
        return

    # Display dropdown to select channel
    selected_channel = st.selectbox(
        "Select a channel to refresh", 
        options=channels,
        format_func=lambda x: x.get('channel_name', x.get('channel_id', 'Unknown'))
    )
    
    if not selected_channel:
        return
        
    channel_id = selected_channel.get('channel_id')
    channel_name = selected_channel.get('channel_name', 'Unknown')
    
    # Add a debug toggle specific to this operation
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Selected channel: **{channel_name}**")
    with col2:
        st.session_state.refresh_debug_mode = st.checkbox("Debug Mode", 
                                                          value=st.session_state.get('refresh_debug_mode', False),
                                                          key="refresh_debug_checkbox")
    
    # Collection options
    st.write("Refresh Options:")
    col1, col2 = st.columns(2)
    with col1:
        fetch_channel_data = st.checkbox("Channel Info", value=True, key="refresh_channel_info")
        fetch_videos = st.checkbox("Videos", value=True, key="refresh_videos")
    with col2:
        fetch_comments = st.checkbox("Comments", value=True, key="refresh_comments")
        analyze_sentiment = st.checkbox("Analyze Sentiment", value=False, key="refresh_sentiment")
    
    col1, col2 = st.columns(2)
    with col1:
        max_videos = st.number_input("Max Videos to Refresh", value=10, min_value=1, max_value=50, key="refresh_max_videos")
    with col2:
        max_comments = st.number_input("Max Comments per Video", value=20, min_value=0, max_value=100, key="refresh_max_comments")
    
    # Build options dict
    options = {
        'fetch_channel_data': fetch_channel_data,
        'fetch_videos': fetch_videos,
        'fetch_comments': fetch_comments,
        'analyze_sentiment': analyze_sentiment,
        'max_videos': max_videos,
        'max_comments_per_video': max_comments
    }
    
    # Initialize session state for iteration prompt if it doesn't exist
    if 'show_iteration_prompt' not in st.session_state:
        st.session_state.show_iteration_prompt = False
        st.session_state.iteration_response = None
    
    # Create a placeholder for debug output
    debug_output = st.empty()
    
    # Refresh button
    if st.button("Refresh Channel Data", key="refresh_button"):
        with st.spinner("Refreshing channel data..."):
            # Setup debug capture
            debug_io = None
            if st.session_state.refresh_debug_mode:
                debug_io = StringIOHandler()
                debug_io.activate()
            
            # Define the iteration prompt callback
            def iteration_callback():
                st.session_state.show_iteration_prompt = True
                # Return None initially - the actual response will be handled by the UI
                return False
            
            try:
                # Call the update_channel_data method with the interactive callback
                updated_data = youtube_service.update_channel_data(
                    channel_id,
                    options,
                    interactive=True,
                    callback=iteration_callback  # Pass the callback function
                )
                
                if updated_data:
                    # Save the updated data
                    if youtube_service.save_channel_data(updated_data, "sqlite"):
                        st.success(f"Successfully refreshed and saved data for {channel_name}")
                    else:
                        st.error("Failed to save the refreshed data")
                else:
                    st.error("Failed to refresh channel data")
            
            except Exception as e:
                st.error(f"Error refreshing channel data: {str(e)}")
                
            finally:
                # Capture and display debug output
                if st.session_state.refresh_debug_mode and debug_io:
                    debug_io.deactivate()
                    debug_text = debug_io.getvalue()
                    if debug_text:
                        debug_output.text_area("Debug Output", debug_text, height=400)
    
    # Display the iteration prompt if needed
    if st.session_state.show_iteration_prompt:
        st.subheader("Continue Iteration?")
        st.write("Additional data is available. Would you like to continue iterating to fetch more?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, continue", key="continue_yes"):
                st.session_state.iteration_response = True
                st.session_state.show_iteration_prompt = False
                # Simulate clicking the refresh button again with the same options
                st.experimental_rerun()
        with col2:
            if st.button("No, stop", key="continue_no"):
                st.session_state.iteration_response = False
                st.session_state.show_iteration_prompt = False
                st.success("Data refresh completed")