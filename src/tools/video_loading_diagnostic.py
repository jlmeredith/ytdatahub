"""
Video Loading Diagnostic Tool

This tool helps identify issues with video data processing
and display in the YouTube Data Hub application.
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.api.youtube_api import YouTubeAPI
from src.services.youtube.video_service import VideoService
from src.utils.video_formatter import fix_missing_views
from src.utils.video_processor import process_video_data
from src.utils.debug_utils import debug_log
from src.ui.data_collection.components.enhanced_video_list import render_enhanced_video_list

st.title("Video Loading Diagnostic Tool")

# API Key input
api_key = os.getenv('YOUTUBE_API_KEY', '')
user_api_key = st.text_input("Enter YouTube API Key:", value=api_key, type="password")

if not user_api_key:
    st.error("Please enter a YouTube API Key to proceed")
    st.stop()

# Channel ID input
channel_id = st.text_input(
    "Enter YouTube Channel ID:", 
    value="",
    help="For example: UCxxxxx"
)

if not channel_id:
    st.info("Enter a channel ID to test video loading")
    st.stop()

# Initialize services
try:
    api = YouTubeAPI(user_api_key)
    video_service = VideoService(api_key=user_api_key, api_client=api)
    
    # Make diagnostic request
    if st.button("Test Video Loading", type="primary"):
        st.write("### Diagnostic Results")
        
        with st.spinner("Fetching channel videos..."):
            # Step 1: Get basic channel videos
            st.write("#### Step 1: Fetching Basic Channel Data")
            
            channel_data = {'channel_id': channel_id}
            response = video_service.collect_channel_videos(channel_data, max_results=5)
            
            if 'error_videos' in response:
                st.error(f"Error fetching videos: {response['error_videos']}")
                st.stop()
            
            # Show basic video count
            video_count = len(response.get('video_id', []))
            st.success(f"Successfully fetched {video_count} videos")
            
            # Show first video data
            if video_count > 0:
                with st.expander("Sample Video Data (Initial)"):
                    first_video = response['video_id'][0]
                    st.json(first_video)
                    st.write(f"Keys present: {list(first_video.keys())}")
                    st.write(f"Has video_id: {'video_id' in first_video}")
                    st.write(f"Has views: {'views' in first_video}")
                    st.write(f"Has statistics: {'statistics' in first_video}")
            
            # Step 2: Get detailed video data
            st.write("#### Step 2: Fetching Detailed Video Data")
            
            # Get video IDs
            video_ids = [v['video_id'] for v in response.get('video_id', []) if 'video_id' in v]
            
            if not video_ids:
                st.error("No video IDs found to fetch details")
                st.stop()
            
            details_response = video_service.get_video_details_batch(video_ids)
            
            # Check if we got details
            if not details_response or 'items' not in details_response:
                st.error("No video details returned from API")
                st.stop()
            
            st.success(f"Successfully fetched details for {len(details_response.get('items', []))} videos")
            
            # Show first video details
            if details_response.get('items'):
                with st.expander("Sample Video Details"):
                    first_details = details_response['items'][0]
                    st.json(first_details)
                    st.write(f"Keys present: {list(first_details.keys())}")
                    st.write(f"Has id: {'id' in first_details}")
                    st.write(f"Has statistics: {'statistics' in first_details}")
            
            # Step 3: Process the video data
            st.write("#### Step 3: Processing and Formatting Video Data")
            
            # Create a lookup map for efficiency
            details_map = {}
            for item in details_response.get('items', []):
                details_map[item['id']] = item
            
            # Update videos with details
            videos_updated = 0
            for video in response['video_id']:
                if 'video_id' in video and video['video_id'] in details_map:
                    item = details_map[video['video_id']]
                    videos_updated += 1
                    
                    # Update from snippet
                    if 'snippet' in item:
                        for field in ['title', 'description', 'publishedAt']:
                            if field in item['snippet']:
                                # Convert publishedAt to published_at to match our schema
                                dest_field = 'published_at' if field == 'publishedAt' else field
                                video[dest_field] = item['snippet'][field]
                        
                        # Ensure we have thumbnails
                        if 'thumbnails' in item['snippet']:
                            video['thumbnails'] = item['snippet']['thumbnails']
                            
                            # Also add flattened thumbnail_url for simpler access
                            if 'medium' in item['snippet']['thumbnails']:
                                video['thumbnail_url'] = item['snippet']['thumbnails']['medium'].get('url', '')
                            elif 'default' in item['snippet']['thumbnails']:
                                video['thumbnail_url'] = item['snippet']['thumbnails']['default'].get('url', '')
                    
                    # Update from statistics
                    if 'statistics' in item:
                        video['views'] = str(item['statistics'].get('viewCount', video.get('views', '0')))
                        video['likes'] = str(item['statistics'].get('likeCount', video.get('likes', '0')))
                        video['comment_count'] = str(item['statistics'].get('commentCount', video.get('comment_count', '0')))
                        
                        # Also store statistics object for consistency with new channel flow
                        video['statistics'] = item['statistics']
            
            st.success(f"Updated {videos_updated}/{len(response['video_id'])} videos with details")
            
            # Show a processed video
            if response['video_id']:
                with st.expander("Sample Processed Video"):
                    proc_video = response['video_id'][0]
                    st.json(proc_video)
                    st.write(f"Keys present: {list(proc_video.keys())}")
                    st.write(f"Has views: {'views' in proc_video}")
                    st.write(f"Views value: {proc_video.get('views', 'N/A')}")
                    st.write(f"Has thumbnail_url: {'thumbnail_url' in proc_video}")
            
            # Apply video formatting
            videos_with_views = fix_missing_views(response['video_id'])
            
            # Process videos for UI
            processed_videos = process_video_data(videos_with_views)
            
            st.success(f"Processed {len(processed_videos)} videos for UI display")
            
            # Display metrics on processed videos
            view_count = sum(1 for v in processed_videos if isinstance(v, dict) and 'views' in v and v['views'] and v['views'] != '0')
            
            st.metric("Videos with valid view counts", f"{view_count}/{len(processed_videos)}")
            
            # Display the videos using our enhanced component
            st.write("### Final Video Display Test")
            render_enhanced_video_list(processed_videos)
except Exception as e:
    st.error(f"Error during diagnostics: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
