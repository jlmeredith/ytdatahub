"""
YTDataHub - YouTube Data Collection, Storage, and Analysis Application.
"""
import streamlit as st

# Set Streamlit page configuration at the top of the file as required
# This MUST be the first Streamlit command in the entire app
st.set_page_config(
    page_title="YTDataHub",
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Created by Jamie Meredith 'https://www.linkedin.com/in/jlmeredith/'"
    }
)

from src.app import YTDataHubApp

def main():
    """Main application entry point"""
    # Create and run the application
    app = YTDataHubApp()
    app.run()

if __name__ == "__main__":
    main()

