"""
Provides functionality to process batches in dry run mode.
This simulates API responses without making actual API calls.
"""
import time
import pandas as pd

from src.ui.bulk_import.logger import update_debug_log
from src.ui.bulk_import.processor import update_results_table

def process_dry_run_batch(batch_channel_ids, debug_container, progress_container, results_table_container, batch_index, batch_count, api_delay):
    """
    Process a batch of channel IDs in dry run mode, simulating API calls.
    
    Args:
        batch_channel_ids: List of channel IDs to process
        debug_container: Streamlit container for debug logs
        progress_container: Streamlit container for progress bar
        results_table_container: Streamlit container for results table
        batch_index: Current batch index
        batch_count: Total number of batches
        api_delay: Delay between simulated API calls in seconds
    """
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
