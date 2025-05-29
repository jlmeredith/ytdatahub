"""
Component for rendering video items in the data collection UI.
"""
import streamlit as st
from datetime import datetime
import re
from ...data_collection.utils.data_conversion import format_number

def render_video_item(video, index=0, selectable=False):
    """
    Render a single video item in a consistent, readable format, with optional selection checkbox.
    
    Args:
        video (dict): Video data to render
        index (int): Index of the video in the list (for unique keys)
        selectable (bool): If True, show a checkbox for selecting this video
    Returns:
        bool or None: If selectable, returns whether the video is selected; else None
    """
    if not video:
        return
    
    # Import debug logging function at the top level if not already imported
    from src.utils.debug_utils import debug_log
    
    # Use our standardizer to ensure consistent video structure
    from src.utils.video_standardizer import standardize_video_data
    
    # Standardize this single video (wrap in list and extract first item)
    debug_log(f"VIDEO_ITEM: Before standardization, video data: {str(video)[:200]}...")
    debug_log(f"VIDEO_ITEM: Before standardization, video type: {type(video)}")
    debug_log(f"VIDEO_ITEM: Before standardization, has key 'video_id': {'video_id' in video if isinstance(video, dict) else 'not a dict'}")
    video = standardize_video_data([video])[0] if video else {}
    debug_log(f"VIDEO_ITEM: After standardization, video data: {str(video)[:200]}...")
    
    # Extract video information (should now be standardized)
    title = video.get('title', 'No Title')
    video_id = video.get('video_id', '')
    published_at = video.get('published_at', '')
    debug_log(f"VIDEO_ITEM: Extracted key fields - title: {title}, video_id: {video_id}")
    
    # Log diagnostic info 
    debug_log(f"Processing video item for video_id: {video_id}")
    debug_log(f"Video keys: {list(video.keys())}")
    
    # VIEWS - Convert to integers safely with more robust extraction logic
    views = 0
    try:
        # Explicit debug log to track the paths
        debug_log(f"Looking for views data in video {video_id}")
        
        # Try all possible locations for views data
        if 'views' in video and video['views']:
            try:
                views_str = str(video['views']).strip()
                views = int(views_str) if views_str.isdigit() else 0
                debug_log(f"Found views in direct field: {views}")
            except (ValueError, TypeError):
                debug_log(f"Invalid direct views format: {video.get('views')}")
        elif 'statistics' in video and isinstance(video['statistics'], dict):
            if 'viewCount' in video['statistics']:
                try:
                    views = int(video['statistics']['viewCount'])
                    debug_log(f"Found views in statistics.viewCount: {views}")
                except (ValueError, TypeError):
                    debug_log(f"Invalid statistics.viewCount format: {video['statistics'].get('viewCount')}")
        
        # If views is still 0, check other possible paths
        if views == 0:
            # Check contentDetails.statistics path
            if 'contentDetails' in video and 'statistics' in video['contentDetails']:
                stats = video['contentDetails']['statistics']
                if 'viewCount' in stats:
                    try:
                        views = int(stats['viewCount'])
                        debug_log(f"Found views in contentDetails.statistics.viewCount: {views}")
                    except (ValueError, TypeError):
                        pass
    except (ValueError, TypeError) as e:
        debug_log(f"Error extracting views for video {video_id}: {str(e)}")
        views = 0
        
    # LIKES - Extract with similar robust approach
    likes = 0
    try:
        if 'likes' in video and video['likes']:
            try:
                likes_str = str(video['likes']).strip()
                likes = int(likes_str) if likes_str.isdigit() else 0
                debug_log(f"Found likes in direct field: {likes}")
            except (ValueError, TypeError):
                debug_log(f"Invalid direct likes format: {video.get('likes')}")
        elif 'statistics' in video and isinstance(video['statistics'], dict):
            if 'likeCount' in video['statistics']:
                try:
                    likes = int(video['statistics']['likeCount'])
                    debug_log(f"Found likes in statistics.likeCount: {likes}")
                except (ValueError, TypeError):
                    debug_log(f"Invalid statistics.likeCount format: {video['statistics'].get('likeCount')}")
    except (ValueError, TypeError):
        debug_log(f"Error extracting likes for video {video_id}")
        likes = 0
        
    # COMMENTS - Extract with similar robust approach
    comment_count = 0
    try:
        if 'comment_count' in video and video['comment_count']:
            try:
                comment_str = str(video['comment_count']).strip()
                comment_count = int(comment_str) if comment_str.isdigit() else 0
                debug_log(f"Found comments in comment_count field: {comment_count}")
            except (ValueError, TypeError):
                debug_log(f"Invalid comment_count format: {video.get('comment_count')}")
        elif 'comments' in video and isinstance(video['comments'], list):
            comment_count = len(video['comments'])
            debug_log(f"Found {comment_count} comments in comments list")
        elif 'statistics' in video and isinstance(video['statistics'], dict):
            if 'commentCount' in video['statistics']:
                try:
                    comment_count = int(video['statistics']['commentCount'])
                    debug_log(f"Found comments in statistics.commentCount: {comment_count}")
                except (ValueError, TypeError):
                    debug_log(f"Invalid statistics.commentCount format: {video['statistics'].get('commentCount')}")
    except (ValueError, TypeError):
        debug_log(f"Error extracting comment count for video {video_id}")
        comment_count = 0
        
    # Final diagnostic log
    debug_log(f"Video {video_id} final metrics: views={views}, likes={likes}, comments={comment_count}")
        
    # Always log metric values for debugging
    debug_log(f"Video {video_id} metrics: views={views}, likes={likes}, comments={comment_count}")
    
    # Format the date
    formatted_date = "Unknown"
    if published_at:
        try:
            # Handle different date formats
            if 'T' in published_at and ('Z' in published_at or '+' in published_at):
                # ISO format: 2025-04-01T12:00:00Z or 2025-04-01T12:00:00+00:00
                # Convert to just date component for display
                date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%b %d, %Y')
            else:
                # Simple date format: 2025-04-01
                formatted_date = datetime.strptime(published_at, '%Y-%m-%d').strftime('%b %d, %Y')
        except (ValueError, TypeError) as e:
            # If there's an error, just use the raw string
            formatted_date = published_at
    
    # YouTube URL for preview
    video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else "#"
    
    # Get thumbnail URL from standardized field or try multiple fallback sources
    thumbnail_url = video.get('thumbnail_url', '')
    
    # If not in standard field, try other possible locations
    if not thumbnail_url:
        debug_log(f"No thumbnail_url found for video {video_id}, trying alternative sources")
        
        # Try thumbnails nested object - API standard format
        if isinstance(video.get('thumbnails'), dict):
            thumbnails = video['thumbnails']
            debug_log(f"Found thumbnails object with keys: {list(thumbnails.keys())}")
            
            # Try medium, then default, then high resolution
            if 'medium' in thumbnails and isinstance(thumbnails['medium'], dict) and 'url' in thumbnails['medium']:
                thumbnail_url = thumbnails['medium'].get('url', '')
                debug_log(f"Using thumbnails.medium.url: {thumbnail_url[:60]}...")
            elif 'default' in thumbnails and isinstance(thumbnails['default'], dict) and 'url' in thumbnails['default']:
                thumbnail_url = thumbnails['default'].get('url', '')
                debug_log(f"Using thumbnails.default.url: {thumbnail_url[:60]}...")
            elif 'high' in thumbnails and isinstance(thumbnails['high'], dict) and 'url' in thumbnails['high']:
                thumbnail_url = thumbnails['high'].get('url', '')
                debug_log(f"Using thumbnails.high.url: {thumbnail_url[:60]}...")
        
        # Try snippet.thumbnails path - another common format
        elif isinstance(video.get('snippet'), dict) and isinstance(video['snippet'].get('thumbnails'), dict):
            thumbnails = video['snippet']['thumbnails']
            debug_log(f"Found snippet.thumbnails object with keys: {list(thumbnails.keys())}")
            
            if 'medium' in thumbnails and isinstance(thumbnails['medium'], dict) and 'url' in thumbnails['medium']:
                thumbnail_url = thumbnails['medium'].get('url', '')
                debug_log(f"Using snippet.thumbnails.medium.url: {thumbnail_url[:60]}...")
            elif 'default' in thumbnails and isinstance(thumbnails['default'], dict) and 'url' in thumbnails['default']:
                thumbnail_url = thumbnails['default'].get('url', '')
                debug_log(f"Using snippet.thumbnails.default.url: {thumbnail_url[:60]}...")
    
    # If still no thumbnail, use video ID to construct URL, or fall back to placeholder
    if not thumbnail_url or not isinstance(thumbnail_url, str):
        if video_id:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            debug_log(f"Generated thumbnail URL from video_id: {thumbnail_url}")
        else:
            thumbnail_url = "https://via.placeholder.com/320x180?text=No+Thumbnail"
            debug_log("Using placeholder thumbnail image")
    
    # Create a card-like display
    col1, col2 = st.columns([1, 3])
    selection = None
    with col1:
        # Make the thumbnail clickable
        st.markdown(f"[![Thumbnail]({thumbnail_url})]({video_url})")
        st.caption(f"Published: {formatted_date}")
        if selectable:
            selection = st.checkbox(
                "Select this video",
                key=f"select_video_{video_id}_{index}",
                value=False
            )

    # Right column for title and details
    with col2:
        col2.markdown(f"### [{title}]({video_url})")
        
        # Display metrics in columns (use col2.columns for test compatibility)
        metric_cols = col2.columns(3)
        metric_cols[0].metric("Views", format_number(views, short=True))
        metric_cols[1].metric("Likes", format_number(likes, short=True))
        # Defensive: Only use metric_cols[2] if it exists, else fallback to col2
        if len(metric_cols) > 2:
            metric_cols[2].metric("Comments", format_number(comment_count, short=True))
        else:
            st.metric("Comments", format_number(comment_count, short=True))
    
    # Display comments if available
    if 'comments' in video and video['comments']:
        comments = video['comments']
        
        if st.checkbox(f"Show {len(comments)} Comments", key=f"show_comments_{video_id}_{index}"):
            st.write("Top Comments:")
            
            for i, comment in enumerate(comments[:5]):  # Show only first 5 comments
                comment_text = comment.get('comment_text', 'No comment text')
                comment_author = comment.get('comment_author', 'Anonymous')
                
                # Limit comment length for display
                if len(comment_text) > 300:
                    comment_text = comment_text[:297] + "..."
                
                st.markdown(f"> {comment_text}")
                st.caption(f"— {comment_author}")
                
                # Add separator between comments
                if i < len(comments[:5]) - 1:
                    st.markdown("---")
            
            # Indicate if there are more comments
            if len(comments) > 5:
                st.caption(f"...and {len(comments) - 5} more comments")
    
    # Extract and display video duration if available
    if 'duration' in video:
        duration = video['duration']
        
        # Try to extract duration from PT format (ISO 8601 duration)
        if duration and duration.startswith('PT'):
            duration_pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(duration_pattern, duration)
            
            if match:
                hours, minutes, seconds = match.groups()
                formatted_duration = ""
                
                if hours:
                    formatted_duration += f"{int(hours)}h "
                if minutes:
                    formatted_duration += f"{int(minutes)}m "
                if seconds:
                    formatted_duration += f"{int(seconds)}s"
                
                if formatted_duration:
                    st.caption(f"Duration: {formatted_duration.strip()}")
        else:
            st.caption(f"Duration: {duration}")
            
    # Show video description if available (in an expander)
    if 'description' in video or 'video_description' in video:
        description = video.get('description', video.get('video_description', ''))
        if description:
            with st.expander("Video Description"):
                # Limit description length for very long descriptions
                if len(description) > 1000:
                    st.write(f"{description[:1000]}...")
                    st.caption("(Description truncated)")
                else:
                    st.write(description)
    return selection

def render_video_table_row(video, index=0, selected=False, on_select=None):
    """
    Render a single video as a row in a compact table for selection.
    Args:
        video (dict): Video data
        index (int): Row index
        selected (bool): Whether this video is selected
        on_select (callable): Optional callback for selection change
    Returns:
        bool: Whether the video is selected
    """
    import streamlit as st
    from ...data_collection.utils.data_conversion import format_number
    from datetime import datetime
    video_id = video.get('video_id', '')
    title = video.get('title', 'No Title')
    views = video.get('views', 0)
    comment_count = video.get('comment_count', 0)
    if not comment_count and 'statistics' in video and 'commentCount' in video['statistics']:
        try:
            comment_count = int(video['statistics']['commentCount'])
        except Exception:
            comment_count = 0
    published_at = video.get('published_at', '')
    try:
        if published_at and 'T' in published_at:
            published_at = published_at.split('T')[0]
    except Exception:
        pass
    col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 2, 2])
    with col1:
        checked = st.checkbox("", value=selected, key=f"table_select_{video_id}_{index}")
    with col2:
        st.markdown(f"[{title}](https://www.youtube.com/watch?v={video_id})")
    with col3:
        st.write(format_number(views, short=True))
    with col4:
        st.write(format_number(comment_count, short=True))
    with col5:
        st.write(published_at)
    return checked