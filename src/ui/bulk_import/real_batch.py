"""
Provides functionality to process batches of channel IDs with real API calls.
This module handles the actual fetching of data from the YouTube API and storing it in the database.
"""
import time
from datetime import datetime

from src.ui.bulk_import.logger import update_debug_log
from src.ui.bulk_import.processor import update_results_table

def process_real_batch(batch_channel_ids, api, db, debug_container, progress_container, results_table_container, batch_index, batch_count, api_delay):
    """
    Process a batch of channel IDs with real API calls.
    
    Args:
        batch_channel_ids: List of channel IDs to process
        api: Initialized YouTube API client
        db: Database connection
        debug_container: Streamlit container for debug logs
        progress_container: Streamlit container for progress bar
        results_table_container: Streamlit container for results table
        batch_index: Current batch index
        batch_count: Total number of batches
        api_delay: Delay between API calls in seconds
    """
    try:
        # Track counters for current batch
        processed_count = st.session_state.import_results['total_processed']
        total_channels = st.session_state.import_results['total_to_process']
        
        # Fetch batch of channels from API
        comma_separated_ids = ','.join(batch_channel_ids)
        update_debug_log(debug_container, f"Fetching data for batch {batch_index+1}/{batch_count} from YouTube API...")
        
        # Execute the batch API request with all possible parts to get complete data
        batch_data = api.channel_client.youtube.channels().list(
            part="snippet,contentDetails,statistics,brandingSettings,status,topicDetails,localizations",
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
