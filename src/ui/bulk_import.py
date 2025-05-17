"""
UI components for the Bulk Import tab.
This module handles CSV imports of channel IDs and API data fetching.
"""
import streamlit as st
import pandas as pd
import time
import io
import os
from datetime import datetime
import math
import streamlit.errors

from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.api.youtube_api import YouTubeAPI
from src.utils.helpers import debug_log
from src.ui.bulk_import.logger import update_debug_log
from src.ui.bulk_import.processor import batch_process_channels, update_results_table
from src.ui.bulk_import.dry_run import process_dry_run_batch
from src.ui.bulk_import.real_batch import process_real_batch

# Global variable to control the import process
IMPORT_RUNNING = False
IMPORT_SHOULD_STOP = False

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
    Import multiple YouTube channels at once from a CSV file. 
    The CSV should have a column named 'Channel ID' or 'Channel Id' containing valid YouTube channel IDs.
    This feature uses batch processing to optimize API quota usage.
    """)
    
    # Create debug log container that will show real-time updates
    debug_container = st.empty()
    
    # Create a container for progress bar and real-time stats
    progress_container = st.empty()
    
    # Create a container for the stop button
    stop_button_container = st.empty()
    
    # Create a container for real-time results table
    results_table_container = st.empty()
    
    # Initialize auto-rerun checkbox and other advanced options
    if 'import_auto_rerun' not in st.session_state:
        st.session_state.import_auto_rerun = True
        st.session_state.last_rerun_time = time.time()
    
    if 'import_dry_run' not in st.session_state:
        st.session_state.import_dry_run = False
    
    # Add advanced options section
    with st.expander("Advanced Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.import_auto_rerun = st.checkbox(
                "Auto-refresh UI during import", 
                value=st.session_state.import_auto_rerun,
                help="Automatically refreshes the UI every few seconds to show progress during imports"
            )
        
        with col2:
            st.session_state.import_dry_run = st.checkbox(
                "Dry Run Mode", 
                value=st.session_state.import_dry_run,
                help="Test the import process without making actual API calls or database changes"
            )
        
        # Add throttling control to avoid hitting quota limits
        st.slider(
            "API Request Delay (seconds)", 
            min_value=0.1, 
            max_value=5.0, 
            value=0.5, 
            step=0.1,
            key="import_api_delay",
            help="Delay between API requests to avoid hitting rate limits"
        )
    
        # Function moved to src.ui.bulk_import.logger
    
    # Function to batch process channel IDs - moved to src.ui.bulk_import.processor
    
    # Function to update the real-time results table - moved to src.ui.bulk_import.processor
    
    # Function to process a batch in dry run mode - moved to src.ui.bulk_import.dry_run
    
    # Function to process a batch in real mode - moved to src.ui.bulk_import.real_batch
    
    # Create file uploader
    uploaded_file = st.file_uploader("Upload CSV file with channel IDs", type="csv")
    
    # Add a sample CSV download option
    st.download_button(
        label="Download Sample CSV Template",
        data=pd.DataFrame({
            'Channel ID': ['UCxxx1234yyyy', 'UCzzzabcd1234'],
            'Name (optional)': ['Sample Channel 1', 'Sample Channel 2'],
            'Notes (optional)': ['Gaming channel', 'Music channel']
        }).to_csv(index=False),
        file_name="channel_ids_template.csv",
        mime="text/csv"
    )
    
    # Button to start the import process
    if uploaded_file is not None and not st.session_state.import_running:
        if st.button("Start Import", type="primary"):
            # Reset the import state
            st.session_state.import_running = True
            st.session_state.import_should_stop = False
            st.session_state.import_log = ""
            
            try:
                # Read CSV
                df = pd.read_csv(uploaded_file)
                
                # Check for Channel ID column (handle both "Channel ID" and "Channel Id" formats)
                channel_id_column = None
                
                if 'Channel ID' in df.columns:
                    channel_id_column = 'Channel ID'
                elif 'Channel Id' in df.columns:
                    channel_id_column = 'Channel Id'
                else:
                    # Try case-insensitive matching as a fallback
                    for col in df.columns:
                        if col.lower() == 'channel id':
                            channel_id_column = col
                            break
                
                if not channel_id_column:
                    st.error("CSV must contain a column named 'Channel ID' or 'Channel Id'.")
                    st.session_state.import_running = False
                    return
                
                # Get all channel IDs
                all_channel_ids = df[channel_id_column].astype(str).tolist()
                
                # Filter out empty values
                channel_ids = [channel_id.strip() for channel_id in all_channel_ids 
                              if channel_id and not pd.isna(channel_id) and channel_id.strip()]
                
                # Store channel IDs and setup state for incremental processing
                st.session_state.channel_ids_to_process = channel_ids
                st.session_state.current_batch_index = 0
                st.session_state.import_results = {
                    'successful': [],
                    'failed': [],
                    'total_processed': 0,
                    'total_to_process': len(channel_ids),
                    'in_progress': True
                }
                
                # Initialize API key and other settings
                import os
                from dotenv import load_dotenv
                load_dotenv()
                
                # Get API key from environment or session state
                api_key = os.getenv('YOUTUBE_API_KEY')
                if not api_key and 'youtube_api_key' in st.session_state:
                    api_key = st.session_state.youtube_api_key
                    update_debug_log(debug_container, "Using API key from session state.")
                elif api_key:
                    update_debug_log(debug_container, "Using API key from environment variables.")
                else:
                    update_debug_log(debug_container, "No YouTube API key found. Please set an API key in the Utilities page.", is_error=True)
                    st.session_state.import_running = False
                    return
                
                # Store API key in session state for processing
                st.session_state.import_api_key = api_key
                
                # Trigger first batch processing
                st.rerun()
                
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
                st.session_state.import_running = False
    
    # Process one batch of data per Streamlit run
    if st.session_state.get('import_running', False) and 'channel_ids_to_process' in st.session_state:
        # Check if we should stop
        if st.session_state.import_should_stop:
            update_debug_log(debug_container, "Import process stopped by user.", is_error=True)
            st.session_state.import_running = False
            if 'import_results' in st.session_state:
                st.session_state.import_results['in_progress'] = False
            # Clean up temporary processing state
            if 'channel_ids_to_process' in st.session_state:
                del st.session_state.channel_ids_to_process
            if 'current_batch_index' in st.session_state:
                del st.session_state.current_batch_index
            st.rerun()
        
        # Get state values
        batch_size = 50  # YouTube API allows up to 50 channel IDs per batch
        dry_run = st.session_state.get('import_dry_run', False)
        api_delay = st.session_state.get('import_api_delay', 0.5)
        channel_ids = st.session_state.channel_ids_to_process
        current_batch_index = st.session_state.current_batch_index
        api_key = st.session_state.import_api_key
        
        # Calculate number of batches
        total_channels = len(channel_ids)
        batch_count = math.ceil(total_channels / batch_size)
        
        # Show status on first run
        if current_batch_index == 0:
            update_debug_log(debug_container, f"Processing {total_channels} channels in {batch_count} batches (max 50 channels per batch).")
            
            if dry_run:
                update_debug_log(debug_container, "🛑 DRY RUN MODE ACTIVE - No API calls or database changes will be made", is_success=True)
            
            update_debug_log(debug_container, f"API request delay set to {api_delay} seconds")
            
            # Initialize progress bar
            progress_container.progress(0.0, text="Starting import process...")
            
            # Initialize API and database if not dry run
            if not dry_run:
                try:
                    # Initialize YouTube API
                    update_debug_log(debug_container, "Initializing YouTube API...")
                    api = YouTubeAPI(api_key)
                    
                    # Verify API initialization
                    if not api.is_initialized():
                        update_debug_log(debug_container, "Failed to initialize YouTube API. Please check your API key.", is_error=True)
                        st.session_state.import_running = False
                        if 'channel_ids_to_process' in st.session_state:
                            del st.session_state.channel_ids_to_process
                        st.rerun()
                        return
                    
                    # Store API client in session state for reuse
                    st.session_state.import_api_client = api
                    
                    # Initialize database
                    update_debug_log(debug_container, "Connecting to database...")
                    db = SQLiteDatabase(SQLITE_DB_PATH)
                    st.session_state.import_db_client = db
                    
                except Exception as e:
                    update_debug_log(debug_container, f"Error initializing: {str(e)}", is_error=True)
                    st.session_state.import_running = False
                    if 'channel_ids_to_process' in st.session_state:
                        del st.session_state.channel_ids_to_process
                    st.rerun()
                    return
            else:
                update_debug_log(debug_container, "DRY RUN: Would initialize YouTube API and database")
        
        # Process current batch
        if current_batch_index < batch_count:
            # Get batch of channel IDs
            start_idx = current_batch_index * batch_size
            end_idx = min(start_idx + batch_size, total_channels)
            batch_channel_ids = channel_ids[start_idx:end_idx]
            
            # Clean channel IDs (remove any whitespace)
            batch_channel_ids = [channel_id.strip() for channel_id in batch_channel_ids if channel_id and not pd.isna(channel_id) and channel_id.strip()]
            
            if not batch_channel_ids:
                update_debug_log(debug_container, f"Skipping empty batch {current_batch_index+1}/{batch_count}")
                
                # Move to next batch
                st.session_state.current_batch_index += 1
                if st.session_state.current_batch_index >= batch_count:
                    # Finished all batches
                    update_debug_log(debug_container, "Import process completed.", is_success=True)
                    update_debug_log(debug_container, f"Successfully imported {len(st.session_state.import_results['successful'])} channels.")
                    
                    if st.session_state.import_results['failed']:
                        update_debug_log(debug_container, f"Failed to import {len(st.session_state.import_results['failed'])} channels.", is_error=True)
                    
                    st.session_state.import_running = False
                    st.session_state.import_results['in_progress'] = False
                    # Clean up temporary processing state
                    if 'channel_ids_to_process' in st.session_state:
                        del st.session_state.channel_ids_to_process
                    if 'current_batch_index' in st.session_state:
                        del st.session_state.current_batch_index
                
                st.rerun()
                return
            
            update_debug_log(debug_container, f"Processing batch {current_batch_index+1}/{batch_count} with {len(batch_channel_ids)} channels...")
            
            # Display the current results table before processing the batch
            # This ensures the table from previous batches remains visible
            update_results_table(results_table_container)
            
            # Process in dry run mode
            if dry_run:
                process_dry_run_batch(
                    batch_channel_ids, 
                    debug_container, 
                    progress_container, 
                    results_table_container,
                    current_batch_index,
                    batch_count,
                    api_delay
                )
                
                # Move to next batch
                st.session_state.current_batch_index += 1
                if st.session_state.current_batch_index >= batch_count:
                    # Finished all batches
                    update_debug_log(debug_container, "Import process completed.", is_success=True)
                    update_debug_log(debug_container, f"Successfully imported {len(st.session_state.import_results['successful'])} channels.")
                    
                    if st.session_state.import_results['failed']:
                        update_debug_log(debug_container, f"Failed to import {len(st.session_state.import_results['failed'])} channels.", is_error=True)
                    
                    st.session_state.import_running = False
                    st.session_state.import_results['in_progress'] = False
                    # Clean up temporary processing state
                    if 'channel_ids_to_process' in st.session_state:
                        del st.session_state.channel_ids_to_process
                    if 'current_batch_index' in st.session_state:
                        del st.session_state.current_batch_index
                
                # Update results table before rerun
                update_results_table(results_table_container)
                
                # Wait before triggering rerun for next batch
                time.sleep(1.0)
                st.rerun()
                return
            
            # Process in real mode (with actual API calls)
            else:
                # Get API client from session state
                api = st.session_state.import_api_client
                db = st.session_state.import_db_client
                
                process_real_batch(
                    batch_channel_ids,
                    api,
                    db,
                    debug_container,
                    progress_container,
                    results_table_container,
                    current_batch_index,
                    batch_count,
                    api_delay
                )
                
                # Move to next batch
                st.session_state.current_batch_index += 1
                if st.session_state.current_batch_index >= batch_count:
                    # Finished all batches
                    update_debug_log(debug_container, "Import process completed.", is_success=True)
                    update_debug_log(debug_container, f"Successfully imported {len(st.session_state.import_results['successful'])} channels.")
                    
                    if st.session_state.import_results['failed']:
                        update_debug_log(debug_container, f"Failed to import {len(st.session_state.import_results['failed'])} channels.", is_error=True)
                    
                    st.session_state.import_running = False
                    st.session_state.import_results['in_progress'] = False
                    # Clean up temporary processing state
                    if 'channel_ids_to_process' in st.session_state:
                        del st.session_state.channel_ids_to_process
                    if 'current_batch_index' in st.session_state:
                        del st.session_state.current_batch_index
                
                # Update results table before rerun
                update_results_table(results_table_container)
                
                # Wait before triggering rerun for next batch
                time.sleep(1.0)
                st.rerun()
                return
    
    # Show stop button when import is running
    if st.session_state.import_running:
        with stop_button_container.container():
            if st.button("⚠️ Stop Import", type="primary", key="stop_import_btn"):
                st.session_state.import_should_stop = True
                st.warning("Stopping import process... Please wait for the current batch to complete.")
    
    # Initialize progress and results areas
    if st.session_state.import_running:
        # Show initial progress bar
        progress_container.progress(0.0, text="Starting import process...")
        
        # Initialize results table
        update_results_table(results_table_container)
    
    # Display debug log container
    if 'import_log' not in st.session_state:
        st.session_state.import_log = ""
    
    debug_container.markdown(
        f"<div style='height:400px;overflow-y:auto;background-color:#f0f2f6;padding:10px;border-radius:5px'>{st.session_state.import_log}</div>", 
        unsafe_allow_html=True
    )
    
    # Display detailed results when import is complete
    if not st.session_state.import_running and not st.session_state.import_results['in_progress']:
        # The results are already being displayed by the update_results_table function
        
        # Add option to view detailed channel data
        if st.session_state.import_results['successful']:
            if st.button("View Detailed Channel Data"):
                st.subheader("Detailed Channel Data")
                
                # Create database connection
                db = SQLiteDatabase(SQLITE_DB_PATH)
                
                # Fetch all channel data
                conn = db._get_connection()
                try:
                    # Query with full channel details
                    query = """
                    SELECT 
                        youtube_id, title, subscriber_count, view_count, video_count,
                        description, custom_url, published_at, country, default_language,
                        privacy_status, is_linked, long_uploads_status, made_for_kids, 
                        hidden_subscriber_count, thumbnail_default, thumbnail_medium, 
                        thumbnail_high, keywords, topic_categories, fetched_at
                    FROM channels 
                    WHERE youtube_id IN ({})
                    """.format(','.join(['?'] * len(st.session_state.import_results['successful'])))
                    
                    # Execute query with channel IDs
                    channel_ids = [channel['channel_id'] for channel in st.session_state.import_results['successful']]
                    detailed_df = pd.read_sql_query(query, conn, params=channel_ids)
                    
                    # Display detailed dataframe
                    st.dataframe(detailed_df, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error fetching detailed channel data: {str(e)}")
                finally:
                    conn.close()
        
        # Download failed channel IDs as CSV
        if st.session_state.import_results['failed']:
            st.download_button(
                label="Download Failed Imports",
                data=pd.DataFrame({'Channel ID': st.session_state.import_results['failed']}).to_csv(index=False),
                file_name="failed_imports.csv",
                mime="text/csv"
            )
    
    # Auto-refresh mechanism for updating the UI during imports
    if st.session_state.import_running and st.session_state.import_auto_rerun:
        # Check if it's time for a rerun (every 3 seconds)
        current_time = time.time()
        if 'last_rerun_time' not in st.session_state or (current_time - st.session_state.last_rerun_time) > 3:
            st.session_state.last_rerun_time = current_time
            # Use JavaScript to trigger a rerun
            st.markdown(
                """
                <script>
                    // Auto-refresh the page
                    setTimeout(function() {
                        window.location.reload();
                    }, 100);
                </script>
                """,
                unsafe_allow_html=True
            )