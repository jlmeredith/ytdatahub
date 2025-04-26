"""
UI components for the Data Storage tab.
"""
import streamlit as st
from src.services.youtube_service import YouTubeService
from src.config import Settings

def render_data_storage_tab():
    """
    Render the Data Storage tab UI.
    """
    st.header("Data Storage Options")
    
    # Initialize application settings
    app_settings = Settings()
    
    # Check if we have data to store
    if 'current_channel_data' in st.session_state and st.session_state.current_channel_data:
        channel_data = st.session_state.current_channel_data
        st.success(f"Data ready for storage: {channel_data.get('channel_name')}")
        
        # Storage options
        storage_option = st.radio(
            "Select Storage Option:", 
            app_settings.get_available_storage_options()
        )
        
        if st.button("Save Data", type="primary"):
            with st.spinner("Saving data..."):
                try:
                    # Use the YouTubeService to save the data
                    youtube_service = YouTubeService(st.session_state.api_key)
                    success = youtube_service.save_channel_data(channel_data, storage_option, app_settings)
                    
                    if success:
                        st.success(f"Data saved to {storage_option} successfully!")
                    else:
                        st.error(f"Failed to save data to {storage_option}")
                except Exception as e:
                    st.error(f"Error saving data: {str(e)}")
    else:
        st.info("No data available for storage. Collect data first from the 'Data Collection' tab.")