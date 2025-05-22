"""
UI components for the Bulk Import tab.
This module contains the main render function for the Bulk Import tab.
"""
import streamlit as st
import pandas as pd
import time
import io
from datetime import datetime

from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.api.youtube_api import YouTubeAPI
from src.utils.helpers import debug_log

# Import functions from the bulk_import package
from src.ui.bulk_import.logger import update_debug_log
from src.ui.bulk_import.processor import batch_process_channels, update_results_table
from src.ui.bulk_import.dry_run import process_dry_run_batch
from src.ui.bulk_import.real_batch import process_real_batch

def render_bulk_import_tab():
    """
    Render the Bulk Import tab UI.
    This tab allows users to bulk import channel IDs from a CSV file
    and fetch channel data from the YouTube API.
    """
    # Initialize global state for the import process
    if 'import_running' not in st.session_state:
        st.session_state.import_running = False
    
    if 'import_should_stop' not in st.session_state:
        st.session_state.import_should_stop = False
    
    if 'import_results' not in st.session_state:
        st.session_state.import_results = {
            'successful': [],
            'failed': [],
            'total_processed': 0,
            'total_to_process': 0,
            'in_progress': True
        }
    
    st.header("Bulk Import")
    
    st.write("""
    Use this tab to import data for multiple YouTube channels at once.
    Upload a CSV file containing channel IDs and we'll fetch data for each channel.
    """)
    
    # File uploader for CSV input
    uploaded_file = st.file_uploader("Upload CSV file with channel IDs", type=['csv'])
    
    # Process the uploaded file
    if uploaded_file is not None:
        # Read CSV data
        try:
            df = pd.read_csv(uploaded_file)
            
            # Extract channel IDs
            if 'channel_id' in df.columns:
                channel_ids = df['channel_id'].tolist()
                st.success(f"Found {len(channel_ids)} channel IDs in the CSV file.")
                
                # Create containers for different parts of the UI
                config_container = st.container()
                debug_container = st.container()
                progress_container = st.container()
                results_table_container = st.container()
                
                with config_container:
                    # Configuration options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        batch_size = st.number_input("Batch Size", min_value=1, max_value=50, value=5)
                    
                    with col2:
                        api_delay = st.number_input("API Delay (seconds)", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
                    
                    with col3:
                        dry_run = st.checkbox("Dry Run (simulate API calls)")
                        st.session_state.import_dry_run = dry_run
                
                # Display start/stop buttons
                if not st.session_state.import_running:
                    if st.button("Start Import"):
                        # Reset results
                        st.session_state.import_results = {
                            'successful': [],
                            'failed': [],
                            'total_processed': 0,
                            'total_to_process': len(channel_ids),
                            'in_progress': True
                        }
                        
                        st.session_state.import_running = True
                        st.session_state.import_should_stop = False
                        
                        # Rerun to update UI
                        st.rerun()
                else:
                    if st.button("Stop Import"):
                        st.session_state.import_should_stop = True
                        update_debug_log(debug_container, "Stopping import process...", is_error=False)
                
                # Process batches if import is running
                if st.session_state.import_running:
                    # Call the batch processor
                    batch_process_channels(channel_ids, debug_container, progress_container, results_table_container)
            else:
                st.error("The CSV file must contain a column named 'channel_id'.")
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")
    else:
        st.info("Please upload a CSV file to begin.")
        
        # Sample CSV template
        st.subheader("CSV Template")
        st.write("Your CSV file should have the following format:")
        
        sample_data = """channel_id
UC_x5XG1OV2P6uZZ5FSM9Ttw
UCsvqVGtbbyHaMoevxPAq9Fg
UCsBjURrPoezykLs9EqgamOA
"""
        st.code(sample_data)
        
        if st.button("Download Template"):
            csv = io.StringIO()
            csv.write("channel_id\n")
            csv.write("UC_x5XG1OV2P6uZZ5FSM9Ttw\n")  # Google Developers
            csv.write("UCsvqVGtbbyHaMoevxPAq9Fg\n")  # Example channel
            csv.write("UCsBjURrPoezykLs9EqgamOA\n")  # Example channel
            
            # Create download button
            st.download_button(
                label="Download CSV Template",
                data=csv.getvalue(),
                file_name="channel_ids_template.csv",
                mime="text/csv"
            )
