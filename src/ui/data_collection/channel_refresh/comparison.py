"""
This module handles the comparison between database and API data for channels.
"""
import streamlit as st
import pandas as pd
from src.utils.helpers import debug_log
from ..components.comprehensive_display import render_detailed_change_dashboard, render_collapsible_field_explorer

def display_comparison_results(db_data, api_data):
    """Displays a comparison between database and API data using comprehensive display components."""
    st.subheader("Data Comparison")
    # Show detailed delta report if available
    if 'delta' in st.session_state:
        st.subheader("Detailed Change Report")
        delta = st.session_state['delta']
        
        # Get comparison options for display
        comparison_options = None
        if '_comparison_options' in api_data:
            comparison_options = api_data.get('_comparison_options')
        elif 'comparison_options' in st.session_state:
            comparison_options = st.session_state.get('comparison_options')
        
        # Display comparison level used for this data
        comparison_level = "standard"
        if comparison_options:
            comparison_level = comparison_options.get('comparison_level', 'standard')
        
        st.info(f"Comparison level: {comparison_level.upper()}")
        
        # Process the delta report for display using the comprehensive display components
        if delta and isinstance(delta, dict):
            # Store delta information in the API data for rendering
            enhanced_api_data = api_data.copy() if api_data else {}
            enhanced_api_data['delta'] = delta
            
            # Use the comprehensive display component to render the detailed change dashboard
            render_detailed_change_dashboard(enhanced_api_data)
            
            # For significant changes, still show a clear alert at the top
            if 'significant_changes' in delta and delta['significant_changes']:
                st.error("⚠️ Significant changes detected!")
                sig_changes = delta['significant_changes']
                
                # Format significant changes for display
                sig_formatted = []
                for change in sig_changes:
                    sig_formatted.append({
                        'Metric': change.get('metric', ''),
                        'Change': f"{change.get('old', '')} → {change.get('new', '')}" if 'old' in change else 
                                f"{change.get('change', '')} ({change.get('percentage', '')}%)" if 'percentage' in change else 
                                str(change.get('keywords', '')),
                        'Significance': change.get('significance', 'medium').upper()
                    })
                
                if sig_formatted:
                    st.table(pd.DataFrame(sig_formatted))
            
            # Format all changes for display
            formatted_changes = []
            for field, change in delta.items():
                # Skip internal fields and significant_changes which was already displayed
                if field.startswith('_') or field == 'significant_changes':
                    continue
                    
                if isinstance(change, dict):
                    if 'old' in change and 'new' in change:
                        # Handle standard change fields
                        formatted_changes.append({
                            'Field': field,
                            'Previous Value': str(change['old']),
                            'New Value': str(change['new']),
                            'Change Type': 'Modified'
                        })
                    elif field.endswith('_keywords'):
                        # Handle keyword tracking results
                        base_field = field.replace('_keywords', '')
                        keywords_added = change.get('added', [])
                        keywords_removed = change.get('removed', [])
                        
                        if keywords_added or keywords_removed:
                            formatted_changes.append({
                                'Field': f"{base_field} Keywords",
                                'Previous Value': ', '.join(keywords_removed) if keywords_removed else '-',
                                'New Value': ', '.join(keywords_added) if keywords_added else '-',
                                'Change Type': 'Keywords'
                            })
                            
                            # Show keyword context if available
                            if 'context' in change:
                                for context_key, context_text in change['context'].items():
                                    formatted_changes.append({
                                        'Field': f"{context_key} Context",
                                        'Previous Value': '',
                                        'New Value': context_text,
                                        'Change Type': 'Context'
                                    })
                    elif 'value' in change:
                        # Handle unchanged fields (comprehensive mode)
                        status = "Unchanged"
                        if field.endswith('_unchanged'):
                            field = field.replace('_unchanged', '')
                        elif field.endswith('_new'):
                            field = field.replace('_new', '')
                            status = "New Field"
                            
                        formatted_changes.append({
                            'Field': field,
                            'Previous Value': str(change['value']) if status == "Unchanged" else "-",
                            'New Value': str(change['value']),
                            'Change Type': status
                        })
                elif isinstance(change, (int, float)) and field not in ('old', 'new', 'diff'):
                    # Legacy numeric difference format
                    formatted_changes.append({
                        'Field': field,
                        'Previous Value': "-",
                        'New Value': str(change),
                        'Change Type': 'Numeric Difference'
                    })
                    
            # Add any API fields not in delta but present in API data (for comprehensive mode)
            if comparison_level == 'comprehensive':
                # Filter to only include fields not already in formatted_changes
                existing_fields = {fc['Field'] for fc in formatted_changes}
                for field, value in api_data.items():
                    if (not field.startswith('_') and field != 'delta' and 
                        field not in existing_fields and not isinstance(value, dict) and not isinstance(value, list)):
                        formatted_changes.append({
                            'Field': field,
                            'Previous Value': "-",
                            'New Value': str(value),
                            'Change Type': 'API Field'
                        })
            
            # Sort changes by field name
            formatted_changes.sort(key=lambda x: x['Field'])
            
            # Create toggles for different views
            show_all = st.checkbox("Show all fields", value=False)
            
            # Filter based on selected view
            display_changes = formatted_changes
            if not show_all:
                # Show only modified fields by default
                display_changes = [fc for fc in formatted_changes if fc['Change Type'] in ('Modified', 'Keywords')]
                
                if not display_changes:
                    st.info("No modified fields detected. Check 'Show all fields' to see all available data.")
            
            # Display the table
            if display_changes:
                st.table(pd.DataFrame(display_changes))
            return
            
        st.warning("Delta information is not available")
        return
    if not db_data or not api_data:
        # Skip showing the warning here since it's already shown in the workflow
        return
    
    # Extract channel info data
    db_channel = db_data.get('channel_info', {})
    api_channel = api_data
    
    # Extract basic stats for comparison
    db_stats = db_channel.get('statistics', {})
    
    # Convert values to integers for comparison
    db_subs = int(db_stats.get('subscriberCount', 0))
    db_views = int(db_stats.get('viewCount', 0))
    db_videos = int(db_stats.get('videoCount', 0))
    
    api_subs = int(api_channel.get('subscribers', 0))
    api_views = int(api_channel.get('views', 0))
    api_videos = int(api_channel.get('total_videos', 0))
    
    # Calculate deltas
    delta_subs = api_subs - db_subs
    delta_views = api_views - db_views
    delta_videos = api_videos - db_videos
    
    # Display metrics with deltas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Subscribers",
            value=f"{api_subs:,}",
            delta=f"{delta_subs:+,}",
            delta_color="normal" if delta_subs >= 0 else "inverse"
        )
    
    with col2:
        st.metric(
            label="Total Views",
            value=f"{api_views:,}",
            delta=f"{delta_views:+,}",
            delta_color="normal" if delta_views >= 0 else "inverse"
        )
    
    with col3:
        st.metric(
            label="Videos",
            value=f"{api_videos:,}",
            delta=f"{delta_videos:+,}",
            delta_color="normal" if delta_videos >= 0 else "inverse"
        )

def compare_data(db_data, api_data):
    """
    Compare database data with API data and return a delta report.
    
    Args:
        db_data: Data from the database
        api_data: Data from the API
        
    Returns:
        dict: A report of differences between the two data sources
    """
    debug_log(f"compare_data called with db_data={repr(db_data)} api_data={repr(api_data)}")
    # Initialize delta dictionary
    delta = {}
    
    # Extract channel info data
    db_channel = db_data.get('channel_info', {})
    api_channel = api_data
    
    # Compare basic channel info
    if 'title' in db_channel and 'channel_name' in api_channel:
        if db_channel['title'] != api_channel['channel_name']:
            delta['channel_name'] = {
                'old': db_channel['title'],
                'new': api_channel['channel_name']
            }
    
    # Compare statistics
    db_stats = db_channel.get('statistics', {})
    
    # Convert values to integers for comparison
    db_subs = int(db_stats.get('subscriberCount', 0))
    db_views = int(db_stats.get('viewCount', 0))
    db_videos = int(db_stats.get('videoCount', 0))
    
    api_subs = int(api_channel.get('subscribers', 0))
    api_views = int(api_channel.get('views', 0))
    api_videos = int(api_channel.get('total_videos', 0))
    
    # Record differences in statistics
    if db_subs != api_subs:
        delta['subscribers'] = {'old': db_subs, 'new': api_subs}
    
    if db_views != api_views:
        delta['views'] = {'old': db_views, 'new': api_views}
    
    if db_videos != api_videos:
        delta['videos'] = {'old': db_videos, 'new': api_videos}
    
    debug_log(f"compare_data returning delta={repr(delta)}")
    return delta
