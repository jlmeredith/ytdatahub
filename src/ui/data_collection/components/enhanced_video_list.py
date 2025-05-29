"""
Enhanced video render component that provides more robust video display.
This version addresses the issues with missing videos in the UI.
"""
import streamlit as st
from src.utils.debug_utils import debug_log
from src.utils.video_standardizer import standardize_video_data

def render_enhanced_video_list(videos_data):
    """
    Renders a list of videos with enhanced error handling and diagnostics.
    
    Args:
        videos_data: List of video dictionaries to render
    """
    if not videos_data:
        st.warning("No videos to display.")
        return
    
    # Standardize all video data for consistent rendering
    videos_data = standardize_video_data(videos_data)
        
    # Log diagnostic information
    debug_log(f"render_enhanced_video_list: Rendering {len(videos_data)} videos")
    
    # Example of first video for debugging
    if videos_data and len(videos_data) > 0:
        first_video = videos_data[0]
        debug_log(f"Sample video keys: {list(first_video.keys())}")
        debug_log(f"Sample video ID: {first_video.get('video_id', 'Unknown')}")
        debug_log(f"Sample video title: {first_video.get('title', 'Unknown')}")
        debug_log(f"Sample video views: {first_video.get('views', 'Unknown')}")
        debug_log(f"Sample video statistics: {first_video.get('statistics', 'Not present')}")
        
        # Count videos with valid views
        videos_with_views = sum(1 for v in videos_data if v.get('views') and str(v.get('views')) != '0')
        debug_log(f"Videos with valid view counts: {videos_with_views}/{len(videos_data)}")
    
    # Create a tabbed interface with different view options
    tab1, tab2 = st.tabs(["Simple View", "Detailed View"])
    
    # Simple view tab
    with tab1:
        for i, video in enumerate(videos_data):
            try:
                # Extract basic video information with defensive programming
                video_id = video.get('video_id', f'unknown_{i}')
                title = video.get('title', 'Untitled Video')
                
                # Try to get views/likes/comments with fallbacks to statistics if needed
                views = None
                likes = None
                comments = None
                
                # First try direct fields
                if 'views' in video and video['views'] and str(video['views']) != '0':
                    views = str(video['views'])
                if 'likes' in video and video['likes']:
                    likes = str(video['likes'])
                if 'comment_count' in video and video['comment_count']:
                    comments = str(video['comment_count'])
                
                # If not found, try statistics object
                if (not views or not likes or not comments) and 'statistics' in video and isinstance(video['statistics'], dict):
                    if not views and 'viewCount' in video['statistics']:
                        views = str(video['statistics']['viewCount'])
                    if not likes and 'likeCount' in video['statistics']:
                        likes = str(video['statistics']['likeCount'])
                    if not comments and 'commentCount' in video['statistics']:
                        comments = str(video['statistics']['commentCount'])
                
                # Final fallbacks
                if not views: views = '0'
                if not likes: likes = '0'
                if not comments: comments = '0'
                
                debug_log(f"Rendering video {video_id}: views={views}, likes={likes}, comments={comments}")
                
                # Format numeric values
                try:
                    views_formatted = f"{int(views):,}" if views and views.isdigit() else views
                    likes_formatted = f"{int(likes):,}" if likes and likes.isdigit() else likes
                    comments_formatted = f"{int(comments):,}" if comments and comments.isdigit() else comments
                except Exception as e:
                    debug_log(f"Error formatting metrics for {video_id}: {str(e)}")
                    views_formatted = views
                    likes_formatted = likes
                    comments_formatted = comments
                
                # Get thumbnail URL with structured fallback approach
                debug_log(f"Looking for thumbnail for video {video_id}")
                
                thumbnail = None
                
                # Option 1: Direct thumbnail_url field
                if 'thumbnail_url' in video and video['thumbnail_url']:
                    thumbnail = video['thumbnail_url']
                    debug_log(f"Using thumbnail_url for {video_id}: {thumbnail[:50]}...")
                
                # Option 2: 'thumbnail' field
                elif 'thumbnail' in video and video['thumbnail']:
                    thumbnail = video['thumbnail']
                    debug_log(f"Using thumbnail field for {video_id}: {thumbnail[:50]}...")
                
                # Option 3: From snippet.thumbnails
                elif 'snippet' in video and isinstance(video['snippet'], dict) and 'thumbnails' in video['snippet']:
                    thumbnails = video['snippet']['thumbnails']
                    if 'medium' in thumbnails:
                        thumbnail = thumbnails['medium'].get('url', '')
                        debug_log(f"Using snippet.thumbnails.medium for {video_id}")
                    elif 'default' in thumbnails:
                        thumbnail = thumbnails['default'].get('url', '')
                        debug_log(f"Using snippet.thumbnails.default for {video_id}")
                
                # Option 4: From direct thumbnails field
                elif 'thumbnails' in video:
                    thumbnails = video['thumbnails']
                    if isinstance(thumbnails, dict):
                        if 'medium' in thumbnails:
                            thumbnail = thumbnails['medium'].get('url', '')
                            debug_log(f"Using thumbnails.medium for {video_id}")
                        elif 'default' in thumbnails:
                            thumbnail = thumbnails['default'].get('url', '')
                            debug_log(f"Using thumbnails.default for {video_id}")
                
                # Option 5: Construct from video ID (most reliable fallback)
                if not thumbnail and video_id and video_id != f'unknown_{i}':
                    thumbnail = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                    debug_log(f"Constructed thumbnail URL for {video_id}: {thumbnail}")
                
                # Create columns for layout
                cols = st.columns([1, 3, 1, 1, 1])
                
                # Thumbnail
                with cols[0]:
                    if thumbnail:
                        st.image(thumbnail, width=80)
                    else:
                        st.write("🎬")
                
                # Title and info
                with cols[1]:
                    st.markdown(f"**{title}**")
                    if video_id and video_id != f'unknown_{i}':
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        st.caption(f"[View on YouTube]({video_url})")
                
                # Stats
                with cols[2]:
                    st.metric("Views", views_formatted)
                
                with cols[3]:
                    st.metric("Likes", likes_formatted)
                
                with cols[4]:
                    st.metric("Comments", comments_formatted)
                
                # Separator
                st.markdown("---")
            except Exception as e:
                st.error(f"Error displaying video {i}: {str(e)}")
                debug_log(f"Error rendering video {i}: {str(e)}")
    
    # Detailed view tab
    with tab2:
        from .components.video_item import render_video_item
        
        for i, video in enumerate(videos_data):
            try:
                render_video_item(video, index=i)
                st.markdown("---")
            except Exception as e:
                st.error(f"Error displaying detailed view for video {i}: {str(e)}")
                debug_log(f"Error rendering detailed view for video {i}: {str(e)}")
