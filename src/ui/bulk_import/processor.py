"""
Channel batch processing module for Bulk Import.
This module handles the processing of batches of YouTube channel IDs.
"""
import os
import time
import math
import streamlit as st
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH
from src.api.youtube_api import YouTubeAPI
from src.ui.bulk_import.logger import update_debug_log

def batch_process_channels(channel_ids, log_container, progress_container, results_table_container):
    """
    Process a batch of channel IDs by fetching their data from the YouTube API
    and storing it in the database.
    
    Args:
        channel_ids: List of YouTube channel IDs to process
        log_container: Streamlit container for logging messages
        progress_container: Streamlit container for showing progress
        results_table_container: Streamlit container for showing results table
    """
    try:
        # Check if we're in dry run mode
        dry_run = st.session_state.get('import_dry_run', False)
        if dry_run:
            update_debug_log(log_container, "🛑 DRY RUN MODE ACTIVE - No API calls or database changes will be made", is_success=True)
        
        # Get the API delay setting
        api_delay = st.session_state.get('import_api_delay', 0.5)
        update_debug_log(log_container, f"API request delay set to {api_delay} seconds")
        
        # Get the API key
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
                
                # Create simulated response data
                simulated_data = {'items': []}
                
                # Simulate successful API processing for some channels and failures for others
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
                    if 'found_channel_ids' not in locals() or channel_id not in found_channel_ids:
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

def update_results_table(container):
    """
    Update the real-time results table displaying import progress and results.
    
    Args:
        container: Streamlit container to update
    """
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
