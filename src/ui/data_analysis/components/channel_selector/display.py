"""
Display functionality for the channel selector component.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from src.utils.helpers import debug_log, format_number

def render_channel_table(channels_df):
    """
    Render the interactive channel table with selection functionality.
    
    Args:
        channels_df: DataFrame containing channel information
        
    Returns:
        List of selected channel names
    """
    # Check if we have any channels to display
    if channels_df.empty:
        st.info("No channels match your search criteria.")
        return []
    
    # Determine which columns to show based on screen width/space available
    core_columns = ['Channel', 'Subscribers', 'Videos', 'Last Updated']
    additional_columns = ['Views', 'Created', 'Engagement', 'Avg Views']
    
    # Create a simplified dataframe for display
    display_df = channels_df.copy()
    
    # Format numbers for better display
    if 'Subscribers' in display_df.columns:
        display_df['Subscribers'] = display_df['Subscribers'].apply(format_number)
    if 'Views' in display_df.columns:
        display_df['Views'] = display_df['Views'].apply(format_number)
    if 'Videos' in display_df.columns:
        display_df['Videos'] = display_df['Videos'].apply(lambda x: f"{x:,}")
    if 'Avg Views' in display_df.columns:
        display_df['Avg Views'] = display_df['Avg Views'].apply(format_number)
    if 'Engagement' in display_df.columns:
        display_df['Engagement'] = display_df['Engagement'].apply(lambda x: f"{x:.2f}%")
    
    # Create a column set used for display only
    display_columns = core_columns + [col for col in additional_columns if col in display_df.columns]
    
    # Get column widths with relative sizing
    col_config = {
        "Channel": st.column_config.TextColumn("Channel", width="large"),
        "Subscribers": st.column_config.TextColumn("Subscribers", width="small"),
        "Views": st.column_config.TextColumn("Views", width="medium"),
        "Videos": st.column_config.TextColumn("Videos", width="small"),
        "Last Updated": st.column_config.TextColumn("Last Updated", width="medium"),
        "Created": st.column_config.TextColumn("Created", width="medium"),
        "Engagement": st.column_config.TextColumn("Engagement", width="small"),
        "Avg Views": st.column_config.TextColumn("Avg Views", width="small")
    }
    
    # Create the selectable table
    selected_rows = st.data_editor(
        display_df[display_columns],
        column_config=col_config,
        hide_index=True,
        use_container_width=True,
        key="channel_selector_table",
        selection_mode="multi-row",
        on_selection_change=handle_selection_change,
    )
    
    # Process selection
    if selected_rows:
        selected_indices = selected_rows['rows']
        selected_channels = []
        for idx in selected_indices:
            if 0 <= idx < len(channels_df):
                channel_name = channels_df.iloc[idx]['Channel']
                selected_channels.append(channel_name)
        
        st.session_state.selected_channels = selected_channels
    else:
        selected_channels = st.session_state.selected_channels if 'selected_channels' in st.session_state else []
    
    # Display the channel selection status
    if selected_channels:
        st.success(f"Selected {len(selected_channels)} channels: {', '.join(selected_channels)}")
    else:
        st.info("No channels selected. Please select one or more channels to analyze.")
    
    return selected_channels

def render_metadata_card(channel_data):
    """
    Render a metadata card for a channel.
    
    Args:
        channel_data: Dictionary containing channel information
    """
    if not channel_data or 'channel_info' not in channel_data:
        st.warning("No channel metadata available")
        return
    
    # Extract metadata
    channel_info = channel_data['channel_info']
    title = channel_info.get('title', channel_info.get('snippet', {}).get('title', 'Unknown'))
    description = channel_info.get('description', channel_info.get('snippet', {}).get('description', 'No description available'))
    
    # Format dates
    created_date = get_formatted_channel_date(channel_data, 'snippet.publishedAt')
    
    # Display metadata
    with st.container():
        st.subheader(f"📺 {title}")
        st.caption(f"Created: {created_date}")
        
        # Show truncated description with expand option
        if description and len(description) > 200:
            st.markdown(f"{description[:200]}...")
            with st.expander("Show full description"):
                st.markdown(description)
        else:
            st.markdown(description or "No description available")

def handle_selection_change(event):
    """
    Handle changes to the table selection.
    
    Args:
        event: Selection event data
    """
    if not event or not hasattr(event, 'data'):
        return
    
    selection_data = event.data
    
    try:
        # Get selected indices from the selection data
        indices = [row for row in selection_data]
        
        # Get channel names from the selected rows
        selected_channels = []
        for idx in indices:
            # Get channel name from dataframe by row index
            if 0 <= idx < len(st.session_state.channel_selector_table):
                channel_name = st.session_state.channel_selector_table.iloc[idx]['Channel']
                selected_channels.append(channel_name)
        
        # Update session state with the new selection
        st.session_state.selected_channels = selected_channels
    except Exception as e:
        debug_log(f"Error processing table selection: {str(e)}")

def get_formatted_channel_date(channel_data, field_path):
    """
    Helper function to extract and format date from channel data.
    
    Args:
        channel_data: Channel data dictionary
        field_path: Path to the date field in the dictionary
        
    Returns:
        Formatted date string
    """
    try:
        if not channel_data or 'channel_info' not in channel_data:
            return "Unknown"
            
        # Navigate through the JSON path
        current = channel_data['channel_info']
        
        # Handle special case for publishedAt which is in snippet
        if field_path == 'snippet.publishedAt':
            if 'snippet' in current and 'publishedAt' in current['snippet']:
                date_str = current['snippet']['publishedAt']
                try:
                    # Handle ISO format with Z timezone marker
                    date_str = date_str.replace('Z', '+00:00') if 'Z' in date_str else date_str
                    date_obj = datetime.fromisoformat(date_str)
                    return date_obj.strftime('%b %d, %Y')
                except (ValueError, AttributeError):
                    return "Unknown"
            else:
                # Try published_at at the top level
                if 'published_at' in current:
                    date_str = current['published_at']
                    try:
                        # Handle ISO format with Z timezone marker
                        date_str = date_str.replace('Z', '+00:00') if 'Z' in date_str else date_str
                        date_obj = datetime.fromisoformat(date_str)
                        return date_obj.strftime('%b %d, %Y')
                    except (ValueError, AttributeError):
                        return "Unknown"
                return "Unknown"
                
        # Regular path handling for other fields
        parts = field_path.split('.')
        
        for part in parts:
            if part in current:
                current = current[part]
            else:
                return "Unknown"
        
        # Check if we have a valid value
        if not current or current == "Unknown":
            return "Unknown"
            
        # Handle ISO format date string
        if isinstance(current, str) and ('T' in current or '-' in current):
            # Remove Z if present and add timezone info
            date_str = current.replace('Z', '+00:00') if 'Z' in current else current
            try:
                date_obj = datetime.fromisoformat(date_str)
                return date_obj.strftime('%b %d, %Y')
            except ValueError:
                # Try another format
                try:
                    return datetime.strptime(current, '%Y-%m-%d').strftime('%b %d, %Y')
                except ValueError:
                    pass
        
        return current
    except Exception as e:
        debug_log(f"Error formatting date: {str(e)}")
        return "Unknown"
