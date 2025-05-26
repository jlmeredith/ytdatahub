"""
YouTube API Response Validator

This tool helps diagnose issues with YouTube API responses and 
ensures they are properly formatted for the application.
"""
import streamlit as st
import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.api.youtube_api import YouTubeAPI
from src.utils.video_processor import process_video_data
from src.utils.video_formatter import fix_missing_views, extract_video_views
from src.utils.helpers import debug_log
from src.ui.data_collection.components.enhanced_video_list import render_enhanced_video_list

st.set_page_config(layout="wide")
st.title("YouTube API Response Validator")

# User inputs
api_key = st.text_input("YouTube API Key", type="password")
channel_id = st.text_input("YouTube Channel ID", help="Enter a channel ID like 'UCxxxxx'")
max_videos = st.slider("Maximum Videos to Fetch", min_value=1, max_value=50, value=10)

if api_key and channel_id and st.button("Analyze API Response", type="primary"):
    with st.spinner("Fetching data from YouTube API..."):
        try:
            api = YouTubeAPI(api_key)
            
            # STEP 1: Get channel videos (basic data)
            st.subheader("1. Initial Channel Videos Response")
            videos_response = api.get_channel_videos(channel_id, max_videos=max_videos)
            
            if 'video_id' in videos_response:
                videos = videos_response['video_id']
                st.success(f"Successfully fetched basic data for {len(videos)} videos")
                
                # Display sample of raw video data
                with st.expander("Raw Video Data Sample (First Video)"):
                    if videos:
                        st.json(videos[0])
                        
                # Check for key fields in videos
                video_ids = []
                for i, video in enumerate(videos):
                    if 'video_id' in video:
                        video_ids.append(video['video_id'])
                    else:
                        st.warning(f"Video at index {i} is missing 'video_id' field")
                
                st.info(f"Found {len(video_ids)} valid video IDs")
                
                # STEP 2: Get detailed video information
                if video_ids:
                    st.subheader("2. Video Details Response")
                    
                    details_response = api.get_video_details_batch(video_ids)
                    
                    if 'items' in details_response and details_response['items']:
                        details = details_response['items']
                        st.success(f"Successfully fetched details for {len(details)} videos")
                        
                        # Display sample of raw details
                        with st.expander("Raw Video Details Sample (First Video)"):
                            if details:
                                st.json(details[0])
                                
                        # Check for key fields in details
                        stats_count = sum(1 for d in details if 'statistics' in d)
                        views_count = sum(1 for d in details if 'statistics' in d and 'viewCount' in d['statistics'])
                        
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Videos with Statistics", f"{stats_count}/{len(details)}")
                        with col2:
                            st.metric("Videos with View Counts", f"{views_count}/{len(details)}")
                        with col3:
                            st.metric("Missing View Counts", len(details) - views_count)
                            
                        # STEP 3: Process data for UI display
                        st.subheader("3. Data Processing for UI")
                        
                        # Merge basic data and details
                        processed_videos = []
                        for video in videos:
                            video_id = video.get('video_id')
                            # Find matching details
                            for detail in details:
                                if detail.get('id') == video_id:
                                    # Update video with details
                                    video.update({
                                        'snippet': detail.get('snippet', {}),
                                        'statistics': detail.get('statistics', {}),
                                        'contentDetails': detail.get('contentDetails', {})
                                    })
                                    break
                            processed_videos.append(video)
                            
                        # Apply processing pipeline
                        st.write("##### Processing Pipeline Results")
                        
                        with st.expander("Original Video Data"):
                            # Show videos with views before processing
                            views_before = sum(1 for v in processed_videos if v.get('views') and str(v.get('views')) != '0')
                            st.metric("Videos with View Data", f"{views_before}/{len(processed_videos)}")
                            
                            # Show example
                            if processed_videos:
                                st.json(processed_videos[0])
                        
                        # Apply video formatter to fix missing views
                        fixed_videos = fix_missing_views(processed_videos)
                        
                        with st.expander("After fix_missing_views()"):
                            views_after_fixing = sum(1 for v in fixed_videos if v.get('views') and str(v.get('views')) != '0')
                            st.metric("Videos with View Data", f"{views_after_fixing}/{len(fixed_videos)}")
                            
                            # Count videos with stats
                            stats_count_after = sum(1 for v in fixed_videos if 'statistics' in v and v['statistics'])
                            st.metric("Videos with Statistics", f"{stats_count_after}/{len(fixed_videos)}")
                            
                            # Show example
                            if fixed_videos:
                                st.json(fixed_videos[0])
                                
                        # Apply full video processing
                        final_videos = process_video_data(fixed_videos)
                        
                        with st.expander("After process_video_data()"):
                            views_after_processing = sum(1 for v in final_videos if v.get('views') and str(v.get('views')) != '0')
                            st.metric("Videos with View Data", f"{views_after_processing}/{len(final_videos)}")
                            
                            # Count videos with each metric
                            views_count = sum(1 for v in final_videos if v.get('views') and str(v.get('views')) != '0')
                            likes_count = sum(1 for v in final_videos if v.get('likes') and str(v.get('likes')) != '0')
                            comments_count = sum(1 for v in final_videos if v.get('comment_count') and str(v.get('comment_count')) != '0')
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Videos with Views", f"{views_count}/{len(final_videos)}")
                            with col2:
                                st.metric("Videos with Likes", f"{likes_count}/{len(final_videos)}")
                            with col3:
                                st.metric("Videos with Comments", f"{comments_count}/{len(final_videos)}")
                            
                            # Show example
                            if final_videos:
                                st.json(final_videos[0])
                        
                        # STEP 4: Test UI rendering
                        st.subheader("4. UI Rendering Test")
                        
                        # Sample 3 videos for rendering test
                        sample_videos = final_videos[:3] if len(final_videos) >= 3 else final_videos
                        
                        # Render using the enhanced_video_list component
                        st.write("##### Enhanced Video List Component Test")
                        render_enhanced_video_list(sample_videos)
                        
                    else:
                        st.error("Failed to get video details - response did not contain 'items'")
                        if 'items' in details_response:
                            st.warning(f"'items' field is empty: {details_response['items']}")
                        if details_response:
                            st.json(details_response)
            else:
                st.error("Failed to get videos - response did not contain 'video_id'")
                st.json(videos_response)
                
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            
else:
    st.info("Enter your YouTube API key and a channel ID, then click 'Analyze API Response'")
    
    # Show some sample channel IDs
    st.markdown("""
    ### Sample Channel IDs for Testing
    - `UCsT0YIqwnpJCM-mx7-gSA4Q` - Google for Developers
    - `UCmGxH-W-R5BNK0_-azVXZ2w` - Data with Benji
    - `UC0e3QhIYukixgh5VVpKHH9Q` - Code With Haley
    """)
