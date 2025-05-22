"""
Component for rendering video items in the data collection UI.
"""
import streamlit as st
from datetime import datetime
import re
from ...data_collection.utils.data_conversion import format_number

def render_video_item(video, index=0):
    """
    Render a single video item in a consistent, readable format
    
    Args:
        video (dict): Video data to render
        index (int): Index of the video in the list (for unique keys)
    """
    if not video:
        return
    
    # Import debug logging function at the top level if not already imported
    from src.utils.helpers import debug_log
    
    # Log video structure for debugging if missing crucial fields
    if not all(k in video for k in ['title', 'video_id', 'views', 'likes', 'comment_count']):
        debug_log(f"Video data missing fields: {', '.join(k for k in ['title', 'video_id', 'views', 'likes', 'comment_count'] if k not in video)}")
        debug_log(f"Available keys: {', '.join(video.keys())}")
    
    # Extract video information
    title = video.get('title', 'No Title')
    video_id = video.get('video_id', '')
    published_at = video.get('published_at', '')
    
    # Ensure metrics are always present
    video.setdefault('views', 0)
    video.setdefault('likes', 0)
    video.setdefault('comment_count', 0)
    
    # Convert to integers safely - protect against invalid values
    try:
        # Try to extract views from different possible locations in the structure
        if 'views' in video:
            views = int(video.get('views', 0))
        elif 'statistics' in video and 'viewCount' in video['statistics']:
            views = int(video['statistics']['viewCount'])
        else:
            views = 0
    except (ValueError, TypeError):
        debug_log(f"Invalid views format: {video.get('views')}")
        views = 0
        
    try:
        # Try to extract likes from different possible locations in the structure
        if 'likes' in video:
            likes = int(video.get('likes', 0))
        elif 'statistics' in video and 'likeCount' in video['statistics']:
            likes = int(video['statistics']['likeCount'])
        else:
            likes = 0
    except (ValueError, TypeError):
        debug_log(f"Invalid likes format: {video.get('likes')}")
        likes = 0
        
    try:
        # Try to extract comment count from different possible locations in the structure
        if 'comment_count' in video:
            comment_count = int(video.get('comment_count', 0))
        elif 'comments' in video and isinstance(video['comments'], list):
            comment_count = len(video['comments'])
        elif 'statistics' in video and 'commentCount' in video['statistics']:
            comment_count = int(video['statistics']['commentCount'])
        else:
            comment_count = 0
    except (ValueError, TypeError):
        debug_log(f"Invalid comment_count format: {video.get('comment_count')}")
        comment_count = 0
        
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
    
    # Get thumbnail URL or use default
    thumbnail_url = video.get('thumbnails', '')
    if isinstance(thumbnail_url, dict) and 'medium' in thumbnail_url:
        thumbnail_url = thumbnail_url['medium'].get('url', '')
    elif isinstance(thumbnail_url, dict) and 'default' in thumbnail_url:
        thumbnail_url = thumbnail_url['default'].get('url', '')
    
    if not thumbnail_url or not isinstance(thumbnail_url, str):
        # Use video ID to construct thumbnail URL if not provided
        if video_id:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
        else:
            thumbnail_url = "https://via.placeholder.com/320x180?text=No+Thumbnail"
    
    # Create a card-like display
    col1, col2 = st.columns([1, 3])
    
    # Left column for thumbnail and primary stats
    with col1:
        # Make the thumbnail clickable
        st.markdown(f"[![Thumbnail]({thumbnail_url})]({video_url})")
        st.caption(f"Published: {formatted_date}")

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