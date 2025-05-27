"""
This module handles the video section of the channel refresh UI.
"""
import streamlit as st
import pandas as pd
from src.utils.helpers import debug_log
from src.utils.video_standardizer import standardize_video_data, extract_standardized_videos
from src.utils.video_formatter import extract_video_views, extract_video_comments
from ..utils.data_conversion import format_number

def render_video_section(videos_data, youtube_service, channel_id):
    """
    Render the video section of the channel refresh UI.
    
    Args:
        videos_data: List of video data from the API
        youtube_service: YouTube service instance
        channel_id: Channel ID
    """
    if not videos_data:
        st.info("No videos found or videos have not been loaded yet.")
        return
    
    debug_log(f"render_video_section: Raw input data type: {type(videos_data)}")
    
    # Handle different input formats
    if isinstance(videos_data, dict):
        # If videos_data is a dict (e.g., API response), extract videos
        debug_log("render_video_section: Input is a dictionary, extracting videos")
        videos_data = extract_standardized_videos(videos_data)
    else:
        # Otherwise standardize as is
        debug_log(f"render_video_section: Input appears to be a list of {len(videos_data) if isinstance(videos_data, list) else 'non-list'} videos")
        videos_data = standardize_video_data(videos_data)
    
    st.write(f"Found {len(videos_data)} videos for this channel")
    
    # Add button to save all fetched videos to database
    if st.button("Save Videos to Database", type="primary", key="video_section_save_videos_btn"):  # Make this a primary button for visibility
        with st.spinner("Saving videos to database..."):
            try:
                # Structure data properly for saving
                # We need to include the channel_id and videos in a format expected by save_channel_data
                data_to_save = {
                    'channel_id': channel_id,
                    'video_id': videos_data  # The API returns videos in the video_id key
                }
                
                # Save to database using the youtube_service
                success = youtube_service.save_channel_data(data_to_save, "sqlite")
                
                if success:
                    st.success(f"Successfully saved {len(videos_data)} videos to database!")
                else:
                    st.error("Failed to save videos to database.")
            except Exception as e:
                st.error(f"Error saving videos: {str(e)}")
                debug_log(f"Exception during video save: {str(e)}")
    
    # Option to view raw API data (like in channel comparison)
    show_raw_data = st.checkbox("Show Raw API Data", value=False, key="video_section_show_raw_data")
    if show_raw_data:
        st.subheader("Raw API Video Data")
        
        # Log the structure of the first video for debugging
        if videos_data and len(videos_data) > 0:
            first_video = videos_data[0]
            debug_log(f"First video structure: {first_video}")
            debug_log(f"First video keys: {first_video.keys() if isinstance(first_video, dict) else 'Not a dictionary'}")
            
            # Use the utility function to ensure views data is properly set
            if isinstance(first_video, dict):
                # Fix views in place
                raw_views = extract_video_views(first_video)
                first_video['views'] = raw_views
                debug_log(f"Fixed views for first video using utility: {raw_views}")
            
            debug_log(f"Views in first video: {first_video.get('views', 'Not found')}")
            
            # Create an enhanced expandable display for the first video to help debugging
            # Adding unique key to prevent StreamlitDuplicateElementId errors
            with st.expander("Sample Video Data (First Video)", expanded=True, key="video_section_first_video_expander"):
                st.write("### Basic Information")
                st.code(f"Video ID: {first_video.get('video_id', 'Unknown')}")
                st.code(f"Title: {first_video.get('title', 'Unknown')}")
                
                # Enhanced views information with all possible sources
                st.write("### Views Information (All Possible Sources)")
                
                # Store original views value
                original_views = first_video.get('views', 'Not found')
                
                # Deep inspection of video structure for debugging
                has_statistics = 'statistics' in first_video
                statistics_obj = first_video.get('statistics', {})
                has_viewCount = 'viewCount' in statistics_obj if has_statistics else False
                statistics_viewCount = statistics_obj.get('viewCount', 'Not found') if has_statistics else 'No statistics object'
                
                # Try to force-extract views with updated utility
                debug_log(f"Attempting to force-extract views from raw data...")
                
                # Fix video data for display
                if original_views == "0" or original_views == 0:
                    debug_log(f"Found placeholder value, attempting repair")
                    first_video = first_video.copy()  # Create a copy to avoid modifying original
                    # Remove the placeholder to allow our extraction logic to work
                    first_video.pop('views', None)
                
                # Get views using our improved utility function
                views_extracted = extract_video_views(first_video)
                views_formatted = extract_video_views(first_video, format_number)
                
                # Get comment info using our improved utility function
                comments_extracted = extract_video_comments(first_video)
                comments_formatted = extract_video_comments(first_video, format_number)

                # Display comprehensive debug info
                st.code(f"Original 'views' field: {original_views}")
                st.code(f"Original 'comment_count' field: {first_video.get('comment_count', 'Not found')}")
                st.code(f"Has statistics object: {has_statistics}")
                if has_statistics:
                    st.code(f"Raw statistics object: {statistics_obj}")
                st.code(f"Has viewCount in statistics: {has_viewCount}")
                st.code(f"Has commentCount in statistics: {'commentCount' in statistics_obj if has_statistics else False}")
                st.code(f"statistics.viewCount: {statistics_viewCount}")
                st.code(f"statistics.commentCount: {statistics_obj.get('commentCount', 'Not found') if has_statistics else 'No statistics object'}")
                st.code(f"contentDetails.statistics.viewCount: {first_video.get('contentDetails', {}).get('statistics', {}).get('viewCount', 'Not found')}")
                st.code(f"contentDetails.statistics.commentCount: {first_video.get('contentDetails', {}).get('statistics', {}).get('commentCount', 'Not found')}")
                st.code(f"Extracted views raw value: {views_extracted}")
                st.code(f"Extracted views formatted value: {views_formatted}")
                st.code(f"Extracted comments raw value: {comments_extracted}")
                st.code(f"Extracted comments formatted value: {comments_formatted}")
                st.code(f"Final used views value: {views_extracted if views_extracted != '0' else 'No valid views found'}")
                st.code(f"Final used comments value: {comments_extracted if comments_extracted != '0' else 'No valid comments found'}")
                
                # If we couldn't extract real views, show error
                if views_extracted == '0' and original_views == '0':
                    st.error("⚠️ Could not find valid view count data in API response. Please check raw JSON data below for structure.")
                
                st.write("### Other Details")
                st.code(f"Published: {first_video.get('published_at', 'Unknown')}")
                st.code(f"All keys: {', '.join(first_video.keys()) if isinstance(first_video, dict) else 'Not a dictionary'}")
                
                # Show statistics object if it exists
                if 'statistics' in first_video and isinstance(first_video['statistics'], dict):
                    st.write("### Statistics Object")
                    st.json(first_video['statistics'])
                
                # Add raw JSON display for the first video
                st.write("### Raw First Video JSON")
                st.json(first_video)
        
            # Show full data for all videos
            st.subheader("All Video Data")
            st.json(videos_data)
    
    # We've already standardized the videos at the start of the function
    # so no need to process them again
    
    # Display a sample of videos
    st.subheader("Recently Published Videos")
    
    # Determine if any video has delta fields
    has_deltas = any(
        any(f in v for f in ("view_delta", "like_delta", "comment_delta")) for v in videos_data
    )

    # Create a dataframe for videos
    video_data_for_display = []
    for i, video in enumerate(videos_data[:10]):  # Show up to 10 videos
        # Extract video details, navigating nested structures
        video_id = video.get('video_id', video.get('id', 'Unknown'))
        title = video.get('title', video.get('snippet', {}).get('title', 'Unknown Title'))
        published = video.get('published_at', video.get('snippet', {}).get('publishedAt', 'Unknown Date'))
        
        # Handle views data with better fallback navigation through structure 
        views = extract_video_views(video, format_func=None)  # Disable formatting for test compatibility
        
        # Extract comment count with better extraction logic
        comment_count = extract_video_comments(video)
        debug_log(f"Video {video_id} comment_count: {comment_count}")
        
        # Format comment count
        formatted_comment_count = format_number(comment_count) if comment_count else '0'
        
        row = {
            "Video ID": video_id,
            "Title": title,
            "Published Date": published,
            "Views": views,
            "Comments": formatted_comment_count
        }
        if has_deltas:
            row["View Δ"] = video.get("view_delta", "")
            row["Like Δ"] = video.get("like_delta", "")
            row["Comment Δ"] = video.get("comment_delta", "")
        
        video_data_for_display.append(row)
    
    if video_data_for_display:
        # Add pagination for videos
        videos_per_page = 10
        
        # Initialize pagination in session state if not present
        if 'video_page_number' not in st.session_state:
            st.session_state['video_page_number'] = 0
        
        total_pages = max(1, (len(videos_data) + videos_per_page - 1) // videos_per_page)
        
        # Create a dataframe for the current page of videos
        start_idx = st.session_state['video_page_number'] * videos_per_page
        end_idx = min(start_idx + videos_per_page, len(videos_data))
        
        # Create page selector
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if st.button("← Previous Page", disabled=st.session_state['video_page_number'] <= 0, key="video_section_prev_page_btn"):
                st.session_state['video_page_number'] -= 1
                st.rerun()
        
        with col2:
            st.write(f"Page {st.session_state['video_page_number'] + 1} of {total_pages}")
        
        with col3:
            if st.button("Next Page →", disabled=st.session_state['video_page_number'] >= total_pages - 1, key="video_section_next_page_btn"):
                st.session_state['video_page_number'] += 1
                st.rerun()
        
        # Get videos for the current page
        debug_log("Getting videos for current page")
        paginated_videos = videos_data[start_idx:end_idx]
        
        # Display current page data
        video_data_for_current_page = []
        for i, video in enumerate(paginated_videos):
            # Extract video details, navigating nested structures
            video_id = video.get('video_id', video.get('id', 'Unknown'))
            title = video.get('title', video.get('snippet', {}).get('title', 'Unknown Title'))
            published = video.get('published_at', video.get('snippet', {}).get('publishedAt', 'Unknown Date'))
            
            # Get views directly from the fixed data
            views = extract_video_views(video, format_func=None)  # Disable formatting for test compatibility
            
            # All YouTube videos should have at least 1 view (from the uploader)
            # If we're getting 0 views, there's either an API issue or extraction problem
            if views == '0':
                # Display as '0' rather than 'Not Available'
                views = format_number('0') if format_number else '0'
                debug_log(f"ERROR: Video {video_id} has 0 views - API response issue or extraction failure")
            
            debug_log(f"Video {video_id} views for pagination: {views}")
            
            # Extract comment count with better extraction logic
            comment_count = extract_video_comments(video)
            
            # Ensure all values are strings to prevent ArrowInvalid errors when creating dataframe
            row = {
                "Video ID": str(video_id),
                "Title": str(title),
                "Published Date": str(published),
                "Views": str(views),
                "Comments": str(comment_count)
            }
            if has_deltas:
                row["View Δ"] = str(video.get("view_delta", ""))
                row["Like Δ"] = str(video.get("like_delta", ""))
                row["Comment Δ"] = str(video.get("comment_delta", ""))
            
            video_data_for_current_page.append(row)
        
        try:
            # Handle potential ArrowInvalid errors when converting data for dataframe
            video_df = pd.DataFrame(video_data_for_current_page)
            st.dataframe(video_df)
        except Exception as e:
            debug_log(f"Error creating dataframe: {str(e)}")
            st.error("Error displaying video data. Please check the console for details.")
            # Display raw data as fallback
            for row in video_data_for_current_page:
                st.write(row)
        st.dataframe(video_df)
    else:
        st.info("No videos found or videos have not been loaded yet.")

def configure_video_collection():
    """
    Configure video collection options.
    
    Returns:
        dict: Options for video collection
    """
    st.subheader("Video Collection Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fetch_all_videos = st.checkbox("Fetch All Available Videos", value=False)
    
    with col2:
        if not fetch_all_videos:
            max_videos = st.number_input("Maximum Videos to Collect", 
                                      min_value=10, 
                                      max_value=1000, 
                                      value=50,
                                      step=10)
        else:
            max_videos = 0  # 0 means no limit in our API
            st.info("All available videos will be fetched (may use more API quota)")
    
    # Create options for video collection
    options = {
        'fetch_channel_data': False,
        'fetch_videos': True,
        'fetch_comments': False,
        'analyze_sentiment': False,
        'max_videos': 0 if fetch_all_videos else max_videos,  # 0 means no limit
        'max_comments_per_video': 0
    }
    
    return options
