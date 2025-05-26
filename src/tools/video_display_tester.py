"""
Test script to verify video data processing and display.
"""
import streamlit as st
from src.utils.video_processor import process_video_data
from src.utils.video_formatter import fix_missing_views
from src.ui.data_collection.components.enhanced_video_list import render_enhanced_video_list

# Sample video data with different formats
sample_videos = [
    {
        'video_id': 'test1',
        'title': 'Test Video 1',
        'statistics': {
            'viewCount': '5000',
            'likeCount': '200',
            'commentCount': '50'
        },
        'snippet': {
            'title': 'Test Video 1',
            'description': 'Test description',
            'thumbnails': {
                'default': {'url': 'https://img.youtube.com/vi/test1/default.jpg'}
            }
        }
    },
    {
        'video_id': 'test2',
        'title': 'Test Video 2',
        'views': '1000',  # Already has views field
        'statistics': {
            'likeCount': '100',
            'commentCount': '20'
        }
    }
]

st.title("Video Processing and Display Test")

# Process the videos
processed_videos = process_video_data(sample_videos)
fixed_videos = fix_missing_views(processed_videos)

# Show the results
st.subheader("Video Processing Results")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Raw videos", len(sample_videos))
with col2:
    st.metric("Processed videos", len(processed_videos))
with col3:
    st.metric("Fixed videos", len(fixed_videos))

# Display sample of processed data
with st.expander("Sample Raw Data"):
    st.json(sample_videos[0])

with st.expander("Sample Processed Data"):
    st.json(processed_videos[0] if processed_videos else {})

with st.expander("Sample Fixed Data"):
    st.json(fixed_videos[0] if fixed_videos else {})

# Display the videos using our enhanced component
st.subheader("Video Display Test")
render_enhanced_video_list(fixed_videos)
