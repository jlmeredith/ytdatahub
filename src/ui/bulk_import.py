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
    
    # Function to update the debug log
    def update_debug_log(log_container, message, is_error=False, is_success=False):
        # Get existing log content if any
        if 'import_log' not in st.session_state:
            st.session_state.import_log = ""
        
        # Add timestamp to message
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format message based on type
        if is_error:
            formatted_message = f"<div style='color:red'>[{timestamp}] ❌ {message}</div>"
        elif is_success:
            formatted_message = f"<div style='color:green'>[{timestamp}] ✅ {message}</div>"
        else:
            formatted_message = f"<div>[{timestamp}] ℹ️ {message}</div>"
        
        # Append to log in session state instead of updating UI directly
        st.session_state.import_log += formatted_message
        
        # Add message to a queue of pending log messages
        if 'pending_log_messages' not in st.session_state:
            st.session_state.pending_log_messages = []
        
        st.session_state.pending_log_messages.append({
            'message': message,
            'is_error': is_error,
            'is_success': is_success,
            'timestamp': timestamp
        })
        
        # Only try to update the UI if in the main thread (not in background thread)
        try:
            log_container.markdown(
                f"<div style='height:400px;overflow-y:auto;background-color:#f0f2f6;padding:10px;border-radius:5px'>{st.session_state.import_log}</div>", 
                unsafe_allow_html=True
            )
        except streamlit.errors.NoSessionContext:
            # Silently ignore NoSessionContext errors - we'll update the UI on the next rerun
            pass
    
    # Function to batch process channel IDs
    def batch_process_channels(channel_ids, log_container, progress_container, results_table_container):
        try:
            # Check if we're in dry run mode
            dry_run = st.session_state.get('import_dry_run', False)
            if dry_run:
                update_debug_log(log_container, "🛑 DRY RUN MODE ACTIVE - No API calls or database changes will be made", is_success=True)
            
            # Get the API delay setting
            api_delay = st.session_state.get('import_api_delay', 0.5)
            update_debug_log(log_container, f"API request delay set to {api_delay} seconds")
            
            # Get the API key
            import os
            from dotenv import load_dotenv
            
            # Reload .env to ensure we have the latest values
            load_dotenv()
            
            # Get API key from environment or session state
            api_key = os.getenv('YOUTUBE_API_KEY')
            
            # If no API key in environment, check session state
            if not api_key and 'youtube_api_key' in st.session_state:
                api_key = st.session_state.youtube_api_key
                update_debug_log(log_container, "Using API key from session state.")
            elif api_key:
                update_debug_log(log_container, "Using API key from environment variables.")
            else:
                update_debug_log(log_container, "No YouTube API key found. Please set an API key in the Utilities page or enter one below.", is_error=True)
                st.session_state.import_running = False
                return
            
            # Initialize YouTube API with the API key (even in dry run mode to validate the key)
            update_debug_log(log_container, "Initializing YouTube API...")
            api = None
            
            if not dry_run:
                api = YouTubeAPI(api_key)
                
                # Verify API initialization
                if not api.is_initialized():
                    update_debug_log(log_container, "Failed to initialize YouTube API. Please check your API key.", is_error=True)
                    st.session_state.import_running = False
                    return
            else:
                # In dry run mode, we'll just log what would happen
                update_debug_log(log_container, "DRY RUN: Would initialize YouTube API with provided key")
            
            # Initialize database
            update_debug_log(log_container, "Connecting to database...")
            db = None
            
            if not dry_run:
                db = SQLiteDatabase(SQLITE_DB_PATH)
            else:
                update_debug_log(log_container, "DRY RUN: Would connect to SQLite database")
            
            # Initialize counters
            total_channels = len(channel_ids)
            processed_count = 0
            successful_count = 0
            failed_count = 0
            
            # Prepare batch processing
            batch_size = 50  # YouTube API allows up to 50 channel IDs per batch
            batch_count = math.ceil(total_channels / batch_size)
            
            update_debug_log(log_container, f"Processing {total_channels} channels in {batch_count} batches (max 50 channels per batch).")
            
            # Initialize results
            st.session_state.import_results = {
                'successful': [],
                'failed': [],
                'total_processed': 0,
                'total_to_process': total_channels,
                'in_progress': True
            }
            
            # Process batches
            for batch_index in range(batch_count):
                # Check if we should stop
                if st.session_state.import_should_stop:
                    update_debug_log(log_container, "Import process stopped by user.", is_error=True)
                    st.session_state.import_running = False
                    st.session_state.import_results['in_progress'] = False
                    return
                
                # Get batch of channel IDs
                start_idx = batch_index * batch_size
                end_idx = min(start_idx + batch_size, total_channels)
                batch_channel_ids = channel_ids[start_idx:end_idx]
                
                # Clean channel IDs (remove any whitespace)
                batch_channel_ids = [channel_id.strip() for channel_id in batch_channel_ids if channel_id and not pd.isna(channel_id) and channel_id.strip()]
                
                if not batch_channel_ids:
                    update_debug_log(log_container, f"Skipping empty batch {batch_index+1}/{batch_count}")
                    continue
                
                update_debug_log(log_container, f"Processing batch {batch_index+1}/{batch_count} with {len(batch_channel_ids)} channels...")
                
                # If in dry run mode, simulate the API call and response
                if dry_run:
                    update_debug_log(log_container, f"DRY RUN: Would make API call with these channel IDs: {', '.join(batch_channel_ids[:5])}{'...' if len(batch_channel_ids) > 5 else ''}")
                    
                    # Simulate successful API processing for channels
                    for i, channel_id in enumerate(batch_channel_ids):
                        # Consider valid channel IDs (those starting with 'UC') as successful
                        # Only fail channels that don't start with 'UC' or have obviously invalid formats
                        if channel_id.startswith('UC'):
                            # Create a fake response that mimics YouTube API structure
                            simulated_item = {
                                'id': channel_id,
                                'snippet': {
                                    'title': f'Simulated Channel {i+1}',
                                    'description': 'This is a simulated channel response for dry run testing',
                                    'publishedAt': '2020-01-01T00:00:00Z',
                                    'country': 'US',
                                    'thumbnails': {
                                        'default': {'url': 'https://example.com/default.jpg'},
                                        'medium': {'url': 'https://example.com/medium.jpg'},
                                        'high': {'url': 'https://example.com/high.jpg'}
                                    }
                                },
                                'statistics': {
                                    'subscriberCount': str(i * 1000 + 500),
                                    'viewCount': str(i * 10000 + 5000),
                                    'videoCount': str(i * 10 + 5)
                                },
                                'contentDetails': {
                                    'relatedPlaylists': {'uploads': f'UU{channel_id[2:]}'}
                                },
                                'status': {
                                    'privacyStatus': 'public',
                                    'isLinked': True,
                                    'longUploadsStatus': 'enabled',
                                    'madeForKids': False
                                }
                            }
                            simulated_data['items'].append(simulated_item)
                    
                    # Simulate the API response and processing delay
                    update_debug_log(log_container, f"DRY RUN: Simulating API response time ({api_delay}s)...")
                    time.sleep(api_delay)
                    
                    update_debug_log(log_container, f"DRY RUN: Got response with {len(simulated_data['items'])} channels")
                    
                    # Process the simulated response like we would a real one
                    found_channel_ids = [item['id'] for item in simulated_data['items']]
                    missing_channel_ids = [channel_id for channel_id in batch_channel_ids if channel_id not in found_channel_ids]
                    
                    # Add missing channel IDs to failed imports
                    for channel_id in missing_channel_ids:
                        update_debug_log(log_container, f"DRY RUN: No data returned for channel ID: {channel_id}", is_error=True)
                        st.session_state.import_results['failed'].append(channel_id)
                        failed_count += 1
                        processed_count += 1
                    
                    # Process simulated successful responses
                    for channel_item in simulated_data['items']:
                        try:
                            channel_id = channel_item['id']
                            snippet = channel_item.get('snippet', {})
                            statistics = channel_item.get('statistics', {})
                            
                            channel_title = snippet.get('title', 'Unknown Channel')
                            
                            update_debug_log(log_container, f"DRY RUN: Would process channel: {channel_title} ({channel_id})")
                            update_debug_log(log_container, f"DRY RUN: Would store channel data in database", is_success=True)
                            
                            # Add to successful imports with simulated data for display
                            channel_info = {
                                'channel_id': channel_id,
                                'channel_name': channel_title,
                                'subscribers': statistics.get('subscriberCount', 0),
                                'views': statistics.get('viewCount', 0),
                                'videos': statistics.get('videoCount', 0),
                                'country': snippet.get('country', ''),
                                'published_at': snippet.get('publishedAt', '')
                            }
                            
                            st.session_state.import_results['successful'].append(channel_info)
                            successful_count += 1
                            
                            # Update processed count
                            processed_count += 1
                            
                            # Update progress after each channel
                            progress_percentage = processed_count / total_channels
                            progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
                            
                            # Update results summary
                            st.session_state.import_results['total_processed'] = processed_count
                            
                            # Update real-time results table
                            update_results_table(results_table_container)
                            
                        except Exception as e:
                            update_debug_log(log_container, f"DRY RUN: Error in simulation for channel {channel_id}: {str(e)}", is_error=True)
                            st.session_state.import_results['failed'].append(channel_id)
                            failed_count += 1
                            processed_count += 1
                    
                    # Add small delay between batches for better UI updates
                    time.sleep(0.5)
                    continue
                
                # Real processing code for non-dry-run mode
                try:
                    # Fetch batch of channels from API
                    # The YouTube API channel.list endpoint accepts multiple IDs in a comma-separated list
                    # and returns data for all requested channels in a single API call
                    comma_separated_ids = ','.join(batch_channel_ids)
                    update_debug_log(log_container, f"Fetching data for batch {batch_index+1} from YouTube API...")
                    
                    # Execute the batch API request with all possible parts to get complete data
                    # Based on the documentation, we'll request all relevant parts in one call
                    batch_data = api.channel_client.youtube.channels().list(
                        part="snippet,contentDetails,statistics,status,topicDetails,brandingSettings",
                        id=comma_separated_ids,
                        maxResults=50
                    ).execute()
                    
                    # Check if items were returned
                    if 'items' not in batch_data or not batch_data['items']:
                        update_debug_log(log_container, f"No data returned for batch {batch_index+1}.", is_error=True)
                        
                        # Add all IDs in this batch to failed imports
                        for channel_id in batch_channel_ids:
                            st.session_state.import_results['failed'].append(channel_id)
                            failed_count += 1
                            processed_count += 1
                        
                        # Update progress
                        progress_percentage = processed_count / total_channels
                        progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
                        
                        # Update real-time results table
                        update_results_table(results_table_container)
                        
                        continue
                    
                    # Process each channel in the batch response
                    update_debug_log(log_container, f"Received data for {len(batch_data['items'])} channels in batch {batch_index+1}.")
                    
                    # Track which channel IDs were found in the response
                    found_channel_ids = [item['id'] for item in batch_data['items']]
                    missing_channel_ids = [channel_id for channel_id in batch_channel_ids if channel_id not in found_channel_ids]
                    
                    # Add missing channel IDs to failed imports
                    for channel_id in missing_channel_ids:
                        update_debug_log(log_container, f"No data returned for channel ID: {channel_id}", is_error=True)
                        st.session_state.import_results['failed'].append(channel_id)
                        failed_count += 1
                        processed_count += 1
                    
                    # Process each channel that was found
                    for channel_item in batch_data['items']:
                        try:
                            channel_id = channel_item['id']
                            snippet = channel_item.get('snippet', {})
                            statistics = channel_item.get('statistics', {})
                            content_details = channel_item.get('contentDetails', {})
                            status = channel_item.get('status', {})
                            topic_details = channel_item.get('topicDetails', {})
                            branding_settings = channel_item.get('brandingSettings', {})
                            
                            channel_title = snippet.get('title', 'Unknown Channel')
                            
                            update_debug_log(log_container, f"Processing channel: {channel_title} ({channel_id})")
                            
                            # Prepare the data for storage with all available fields
                            db_data = {
                                'channel_id': channel_id,
                                'channel_name': channel_title,
                                'subscribers': statistics.get('subscriberCount', 0),
                                'views': statistics.get('viewCount', 0),
                                'total_videos': statistics.get('videoCount', 0),
                                'channel_description': snippet.get('description', ''),
                                'custom_url': snippet.get('customUrl', ''),
                                'published_at': snippet.get('publishedAt', ''),
                                'country': snippet.get('country', ''),
                                'default_language': snippet.get('defaultLanguage', ''),
                                'fetched_at': datetime.now().isoformat(),
                                
                                # Add additional fields from content details
                                'uploads_playlist_id': content_details.get('relatedPlaylists', {}).get('uploads', ''),
                                
                                # Add fields from status
                                'privacy_status': status.get('privacyStatus', ''),
                                'is_linked': status.get('isLinked', False),
                                'long_uploads_status': status.get('longUploadsStatus', ''),
                                'made_for_kids': status.get('madeForKids', False),
                                'hidden_subscriber_count': statistics.get('hiddenSubscriberCount', False),
                                
                                # Add fields from topicDetails
                                'topic_categories': ','.join(topic_details.get('topicCategories', [])) if 'topicCategories' in topic_details else '',
                                
                                # Add fields from brandingSettings
                                'keywords': branding_settings.get('channel', {}).get('keywords', '')
                            }
                            
                            # Add thumbnails if available
                            if 'thumbnails' in snippet:
                                thumbnails = snippet['thumbnails']
                                db_data['thumbnail_default'] = thumbnails.get('default', {}).get('url', '')
                                db_data['thumbnail_medium'] = thumbnails.get('medium', {}).get('url', '')
                                db_data['thumbnail_high'] = thumbnails.get('high', {}).get('url', '')
                            
                            # Store in database
                            update_debug_log(log_container, f"Storing data for channel: {channel_title}")
                            success = db.store_channel_data(db_data)
                            
                            if success:
                                update_debug_log(log_container, f"Successfully imported channel: {channel_title}", is_success=True)
                                
                                # Add to successful imports with complete data for display
                                channel_info = {
                                    'channel_id': channel_id,
                                    'channel_name': channel_title,
                                    'subscribers': statistics.get('subscriberCount', 0),
                                    'views': statistics.get('viewCount', 0),
                                    'videos': statistics.get('videoCount', 0),
                                    'country': snippet.get('country', ''),
                                    'published_at': snippet.get('publishedAt', '')
                                }
                                
                                st.session_state.import_results['successful'].append(channel_info)
                                successful_count += 1
                            else:
                                update_debug_log(log_container, f"Failed to store data for channel: {channel_title}", is_error=True)
                                st.session_state.import_results['failed'].append(channel_id)
                                failed_count += 1
                        
                        except Exception as e:
                            update_debug_log(log_container, f"Error processing channel {channel_id}: {str(e)}", is_error=True)
                            st.session_state.import_results['failed'].append(channel_id)
                            failed_count += 1
                        
                        # Update processed count
                        processed_count += 1
                        
                        # Update progress after each channel
                        progress_percentage = processed_count / total_channels
                        progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
                        
                        # Update results summary
                        st.session_state.import_results['total_processed'] = processed_count
                        
                        # Update real-time results table
                        update_results_table(results_table_container)
                
                except Exception as e:
                    update_debug_log(log_container, f"Error processing batch {batch_index+1}: {str(e)}", is_error=True)
                    
                    # Mark all IDs in the batch as failed
                    for channel_id in batch_channel_ids:
                        if channel_id not in found_channel_ids:
                            st.session_state.import_results['failed'].append(channel_id)
                            failed_count += 1
                            processed_count += 1
                
                # Sleep briefly to avoid API rate limits and allow for UI updates
                time.sleep(0.5)
            
            # Final summary
            update_debug_log(log_container, f"Import process completed.", is_success=True)
            update_debug_log(log_container, f"Successfully imported {successful_count} channels.")
            
            if failed_count > 0:
                update_debug_log(log_container, f"Failed to import {failed_count} channels.", is_error=True)
            
            # Complete the import process
            st.session_state.import_running = False
            st.session_state.import_results['in_progress'] = False
            
        except Exception as e:
            update_debug_log(log_container, f"Error in import process: {str(e)}", is_error=True)
            st.session_state.import_running = False
            st.session_state.import_results['in_progress'] = False
    
    # Function to update the real-time results table
    def update_results_table(container):
        with container.container():
            # Only show if we have results
            if st.session_state.import_results['successful'] or st.session_state.import_results['failed']:
                # Show current stats
                st.subheader("Import Progress")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Processed", 
                             f"{st.session_state.import_results['total_processed']}/{st.session_state.import_results['total_to_process']}")
                
                with col2:
                    st.metric("Successfully Imported", 
                             str(len(st.session_state.import_results['successful'])))
                
                with col3:
                    st.metric("Failed Imports", 
                             str(len(st.session_state.import_results['failed'])))
                
                # Show successful imports table
                if st.session_state.import_results['successful']:
                    st.subheader("Successfully Imported Channels")
                    
                    # Create a dataframe for the successful imports
                    successful_df = pd.DataFrame(st.session_state.import_results['successful'])
                    
                    # Format the numbers with commas
                    if 'subscribers' in successful_df.columns:
                        successful_df['subscribers'] = successful_df['subscribers'].apply(
                            lambda x: f"{int(x):,}" if pd.notna(x) and x != '' else '0'
                        )
                    
                    if 'views' in successful_df.columns:
                        successful_df['views'] = successful_df['views'].apply(
                            lambda x: f"{int(x):,}" if pd.notna(x) and x != '' else '0'
                        )
                    
                    if 'videos' in successful_df.columns:
                        successful_df['videos'] = successful_df['videos'].apply(
                            lambda x: f"{int(x):,}" if pd.notna(x) and x != '' else '0'
                        )
                    
                    # Display the dataframe
                    st.dataframe(successful_df, use_container_width=True)
                
                # Show failed imports table
                if st.session_state.import_results['failed']:
                    st.subheader("Failed Imports")
                    failed_df = pd.DataFrame({'Channel ID': st.session_state.import_results['failed']})
                    st.dataframe(failed_df, use_container_width=True)
    
    # Function to process a batch in dry run mode
    def process_dry_run_batch(batch_channel_ids, debug_container, progress_container, results_table_container, batch_index, batch_count, api_delay):
        try:
            # Create simulated response data
            simulated_data = {'items': []}
            
            # Track counters for current batch
            processed_count = st.session_state.import_results['total_processed']
            total_channels = st.session_state.import_results['total_to_process']
            
            update_debug_log(debug_container, f"DRY RUN: Would make API call with these channel IDs: {', '.join(batch_channel_ids[:5])}{'...' if len(batch_channel_ids) > 5 else ''}")
            
            # Simulate API delay
            update_debug_log(debug_container, f"DRY RUN: Simulating API response time ({api_delay}s)...")
            time.sleep(api_delay)
            
            # Simulate successful API processing for some channels and failures for others
            for i, channel_id in enumerate(batch_channel_ids):
                # Simulate that about 90% of valid channel IDs succeed
                # For dry run testing, we'll consider IDs starting with 'UC' as valid
                if channel_id.startswith('UC'):
                    # Create a fake response that mimics YouTube API structure
                    simulated_item = {
                        'id': channel_id,
                        'snippet': {
                            'title': f'Simulated Channel {i+1}',
                            'description': 'This is a simulated channel response for dry run testing',
                            'publishedAt': '2020-01-01T00:00:00Z',
                            'country': 'US',
                            'thumbnails': {
                                'default': {'url': 'https://example.com/default.jpg'},
                                'medium': {'url': 'https://example.com/medium.jpg'},
                                'high': {'url': 'https://example.com/high.jpg'}
                            }
                        },
                        'statistics': {
                            'subscriberCount': str(i * 1000 + 500),
                            'viewCount': str(i * 10000 + 5000),
                            'videoCount': str(i * 10 + 5)
                        },
                        'contentDetails': {
                            'relatedPlaylists': {'uploads': f'UU{channel_id[2:]}'}
                        },
                        'status': {
                            'privacyStatus': 'public',
                            'isLinked': True,
                            'longUploadsStatus': 'enabled',
                            'madeForKids': False
                        }
                    }
                    simulated_data['items'].append(simulated_item)
            
            update_debug_log(debug_container, f"DRY RUN: Got response with {len(simulated_data['items'])} channels")
            
            # Process the simulated response like we would a real one
            found_channel_ids = [item['id'] for item in simulated_data['items']]
            missing_channel_ids = [channel_id for channel_id in batch_channel_ids if channel_id not in found_channel_ids]
            
            # Add missing channel IDs to failed imports
            for channel_id in missing_channel_ids:
                update_debug_log(debug_container, f"DRY RUN: No data returned for channel ID: {channel_id}", is_error=True)
                st.session_state.import_results['failed'].append(channel_id)
                processed_count += 1
                
                # Update progress
                progress_percentage = processed_count / total_channels
                progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
                
                # Update total processed count
                st.session_state.import_results['total_processed'] = processed_count
            
            # Process simulated successful responses
            for channel_item in simulated_data['items']:
                channel_id = channel_item['id']
                snippet = channel_item.get('snippet', {})
                statistics = channel_item.get('statistics', {})
                
                channel_title = snippet.get('title', 'Unknown Channel')
                
                update_debug_log(debug_container, f"DRY RUN: Would process channel: {channel_title} ({channel_id})")
                update_debug_log(debug_container, f"DRY RUN: Would store channel data in database", is_success=True)
                
                # Add to successful imports with simulated data for display
                channel_info = {
                    'channel_id': channel_id,
                    'channel_name': channel_title,
                    'subscribers': statistics.get('subscriberCount', 0),
                    'views': statistics.get('viewCount', 0),
                    'videos': statistics.get('videoCount', 0),
                    'country': snippet.get('country', ''),
                    'published_at': snippet.get('publishedAt', '')
                }
                
                st.session_state.import_results['successful'].append(channel_info)
                processed_count += 1
                
                # Update progress
                progress_percentage = processed_count / total_channels
                progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
                
                # Update total processed count
                st.session_state.import_results['total_processed'] = processed_count
            
            # Update the results table
            update_results_table(results_table_container)
            
        except Exception as e:
            update_debug_log(debug_container, f"DRY RUN: Error in simulation: {str(e)}", is_error=True)
    
    # Function to process a batch in real mode
    def process_real_batch(batch_channel_ids, api, db, debug_container, progress_container, results_table_container, batch_index, batch_count, api_delay):
        try:
            # Track counters for current batch
            processed_count = st.session_state.import_results['total_processed']
            total_channels = st.session_state.import_results['total_to_process']
            
            # Fetch batch of channels from API
            comma_separated_ids = ','.join(batch_channel_ids)
            update_debug_log(debug_container, f"Fetching data for batch {batch_index+1}/{batch_count} from YouTube API...")
            
            # Execute the batch API request with all possible parts to get complete data
            batch_data = api.channel_client.youtube.channels().list(
                part="snippet,contentDetails,statistics,status,topicDetails,brandingSettings",
                id=comma_separated_ids,
                maxResults=50
            ).execute()
            
            # Check if items were returned
            if 'items' not in batch_data or not batch_data['items']:
                update_debug_log(debug_container, f"No data returned for batch {batch_index+1}/{batch_count}.", is_error=True)
                
                # Add all IDs in this batch to failed imports
                for channel_id in batch_channel_ids:
                    st.session_state.import_results['failed'].append(channel_id)
                    processed_count += 1
                
                # Update progress
                progress_percentage = processed_count / total_channels
                progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
                
                # Update total processed count
                st.session_state.import_results['total_processed'] = processed_count
                
                # Update results table
                update_results_table(results_table_container)
                
                # Apply API delay to avoid rate limiting
                time.sleep(api_delay)
                return
            
            # Process each channel in the batch response
            update_debug_log(debug_container, f"Received data for {len(batch_data['items'])} channels in batch {batch_index+1}/{batch_count}.")
            
            # Track which channel IDs were found in the response
            found_channel_ids = [item['id'] for item in batch_data['items']]
            missing_channel_ids = [channel_id for channel_id in batch_channel_ids if channel_id not in found_channel_ids]
            
            # Add missing channel IDs to failed imports
            for channel_id in missing_channel_ids:
                update_debug_log(debug_container, f"No data returned for channel ID: {channel_id}", is_error=True)
                st.session_state.import_results['failed'].append(channel_id)
                processed_count += 1
            
            # Process each channel that was found
            for channel_item in batch_data['items']:
                try:
                    channel_id = channel_item['id']
                    snippet = channel_item.get('snippet', {})
                    statistics = channel_item.get('statistics', {})
                    content_details = channel_item.get('contentDetails', {})
                    status = channel_item.get('status', {})
                    topic_details = channel_item.get('topicDetails', {})
                    branding_settings = channel_item.get('brandingSettings', {})
                    
                    channel_title = snippet.get('title', 'Unknown Channel')
                    
                    update_debug_log(debug_container, f"Processing channel: {channel_title} ({channel_id})")
                    
                    # Prepare the data for storage with all available fields
                    db_data = {
                        'channel_id': channel_id,
                        'channel_name': channel_title,
                        'subscribers': statistics.get('subscriberCount', 0),
                        'views': statistics.get('viewCount', 0),
                        'total_videos': statistics.get('videoCount', 0),
                        'channel_description': snippet.get('description', ''),
                        'custom_url': snippet.get('customUrl', ''),
                        'published_at': snippet.get('publishedAt', ''),
                        'country': snippet.get('country', ''),
                        'default_language': snippet.get('defaultLanguage', ''),
                        'fetched_at': datetime.now().isoformat(),
                        
                        # Add additional fields from content details
                        'uploads_playlist_id': content_details.get('relatedPlaylists', {}).get('uploads', ''),
                        
                        # Add fields from status
                        'privacy_status': status.get('privacyStatus', ''),
                        'is_linked': status.get('isLinked', False),
                        'long_uploads_status': status.get('longUploadsStatus', ''),
                        'made_for_kids': status.get('madeForKids', False),
                        'hidden_subscriber_count': statistics.get('hiddenSubscriberCount', False),
                        
                        # Add fields from topicDetails
                        'topic_categories': ','.join(topic_details.get('topicCategories', [])) if 'topicCategories' in topic_details else '',
                        
                        # Add fields from brandingSettings
                        'keywords': branding_settings.get('channel', {}).get('keywords', '')
                    }
                    
                    # Add thumbnails if available
                    if 'thumbnails' in snippet:
                        thumbnails = snippet['thumbnails']
                        db_data['thumbnail_default'] = thumbnails.get('default', {}).get('url', '')
                        db_data['thumbnail_medium'] = thumbnails.get('medium', {}).get('url', '')
                        db_data['thumbnail_high'] = thumbnails.get('high', {}).get('url', '')
                    
                    # Store in database
                    update_debug_log(debug_container, f"Storing data for channel: {channel_title}")
                    success = db.store_channel_data(db_data)
                    
                    if success:
                        update_debug_log(debug_container, f"Successfully imported channel: {channel_title}", is_success=True)
                        
                        # Add to successful imports with complete data for display
                        channel_info = {
                            'channel_id': channel_id,
                            'channel_name': channel_title,
                            'subscribers': statistics.get('subscriberCount', 0),
                            'views': statistics.get('viewCount', 0),
                            'videos': statistics.get('videoCount', 0),
                            'country': snippet.get('country', ''),
                            'published_at': snippet.get('publishedAt', '')
                        }
                        
                        st.session_state.import_results['successful'].append(channel_info)
                    else:
                        update_debug_log(debug_container, f"Failed to store data for channel: {channel_title}", is_error=True)
                        st.session_state.import_results['failed'].append(channel_id)
                
                except Exception as e:
                    update_debug_log(debug_container, f"Error processing channel {channel_id}: {str(e)}", is_error=True)
                    st.session_state.import_results['failed'].append(channel_id)
                
                # Update processed count
                processed_count += 1
                
                # Update progress
                progress_percentage = processed_count / total_channels
                progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
                
                # Update total processed count
                st.session_state.import_results['total_processed'] = processed_count
                
                # Update results table
                update_results_table(results_table_container)
            
            # Apply API delay to avoid rate limiting
            time.sleep(api_delay)
            
        except Exception as e:
            update_debug_log(debug_container, f"Error processing batch {batch_index+1}/{batch_count}: {str(e)}", is_error=True)
            
            # Mark all IDs in this batch as failed
            for channel_id in batch_channel_ids:
                if 'found_channel_ids' not in locals() or channel_id not in found_channel_ids:
                    st.session_state.import_results['failed'].append(channel_id)
                    processed_count += 1
            
            # Update progress
            progress_percentage = processed_count / total_channels
            progress_container.progress(progress_percentage, text=f"Processed: {processed_count}/{total_channels} ({progress_percentage:.1%})")
            
            # Update total processed count
            st.session_state.import_results['total_processed'] = processed_count
    
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