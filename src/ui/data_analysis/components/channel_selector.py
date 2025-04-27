"""
Channel selector component for the data analysis UI.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.utils.helpers import debug_log

def render_channel_selector(channels, db):
    """
    Render the channel selector as a sortable table with key metrics for each channel.
    
    Args:
        channels: List of channel names
        db: Database connection
        
    Returns:
        Tuple of (selected_channels, channel_data_dict)
    """
    # Initialize caching settings if not already set
    if 'use_data_cache' not in st.session_state:
        st.session_state.use_data_cache = True
    
    # Initialize selected_channels as a list in session state for multi-selection
    if 'selected_channels' not in st.session_state:
        st.session_state.selected_channels = []
    
    # Set default channel if we have no selections but have channels available
    if not st.session_state.selected_channels and channels:
        st.session_state.selected_channels = [channels[0]]
    
    # Initialize YouTube Analysis for channel metrics
    analysis = YouTubeAnalysis()
    
    # Check if we have a cached channels dataframe
    cache_key = "analysis_channels_table"
    if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
        debug_log("Using cached channels table data")
        channels_df = st.session_state[cache_key]
    else:
        # Create a dataframe to display channels in a table
        with st.spinner("Loading channel data for comparison table..."):
            channels_data = []
            for channel_name in channels:
                try:
                    # Load basic channel data
                    channel_data = db.get_channel_data(channel_name)
                    if channel_data:
                        # Get channel statistics
                        stats = analysis.get_channel_statistics(channel_data)
                        
                        # Get creation date
                        created_date = "Unknown"
                        if 'channel_info' in channel_data and 'snippet' in channel_data['channel_info']:
                            created = channel_data['channel_info']['snippet'].get('publishedAt', 'Unknown')
                            if created and created != 'Unknown':
                                try:
                                    # Format date
                                    created_date = datetime.fromisoformat(created.replace('Z', '+00:00')).strftime('%b %d, %Y')
                                except:
                                    created_date = created
                        
                        # Add latest fetch date if available
                        fetched_date = "Unknown"
                        if 'channel_info' in channel_data and 'fetched_at' in channel_data['channel_info']:
                            fetched = channel_data['channel_info'].get('fetched_at', '')
                            if fetched:
                                try:
                                    # Format date - might be already formatted or timestamp
                                    if isinstance(fetched, str) and 'T' in fetched:
                                        fetched_date = datetime.fromisoformat(fetched.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                                    else:
                                        fetched_date = fetched
                                except:
                                    fetched_date = fetched
                        
                        # Calculate average views per video
                        avg_views = 0
                        if stats['total_videos'] > 0:
                            avg_views = int(stats['views'] / stats['total_videos'])
                        
                        # Calculate like rate if data is available
                        like_rate = 0
                        if 'total_likes' in stats and 'views' in stats and stats['views'] > 0:
                            like_rate = (stats['total_likes'] / stats['views']) * 100
                        
                        # Add to channels data
                        channels_data.append({
                            'Channel': stats['name'],
                            'Subscribers': stats['subscribers'],
                            'Total Views': stats['views'],
                            'Videos': stats['total_videos'],
                            'Avg Views/Video': avg_views,
                            'Likes Rate': like_rate,  # New field for like rate
                            'Created': created_date,
                            'Last Updated': fetched_date
                        })
                except Exception as e:
                    debug_log(f"Error loading data for channel {channel_name}: {str(e)}")
                    # Add minimal data for channel
                    channels_data.append({
                        'Channel': channel_name,
                        'Subscribers': 0,
                        'Total Views': 0,
                        'Videos': 0,
                        'Avg Views/Video': 0,
                        'Likes Rate': 0,
                        'Created': 'Unknown',
                        'Last Updated': 'Unknown'
                    })
            
            # Create dataframe from collected data
            channels_df = pd.DataFrame(channels_data)
            
            # Sort by last updated date as default (newest first)
            if not channels_df.empty and 'Last Updated' in channels_df.columns:
                try:
                    channels_df = channels_df.sort_values('Last Updated', ascending=False)
                except:
                    debug_log("Could not sort channels by Last Updated date")
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = channels_df
    
    # Create a collapsible container for the channel selector
    with st.expander("Channel Selection", expanded=True):
        st.write("Select one or more channels to analyze and compare. The current view will be maintained.")
        
        # Create column layout for search and sort options
        col1, col2 = st.columns([4, 1])
        with col1:
            # Add search box for filtering channels
            if len(channels) > 3:
                search_term = st.text_input("Search channels", 
                                            value=st.session_state.get('channel_search_term', ''),
                                            key="channel_search_box")
                
                # Update session state if search term changed
                if 'channel_search_term' not in st.session_state or st.session_state.channel_search_term != search_term:
                    st.session_state.channel_search_term = search_term
                
                # Filter channels if search term provided
                if search_term:
                    channels_df = channels_df[channels_df['Channel'].str.contains(search_term, case=False)]
        
        with col2:
            # Add sort options
            sort_options = ["Last Updated", "Subscribers", "Total Views", "Videos", "Avg Views/Video", "Likes Rate"]
            sort_by = st.selectbox("Sort by", 
                                options=sort_options, 
                                index=sort_options.index(st.session_state.get('channel_sort_by', 'Last Updated')),
                                key="channel_sort_selector")
            
            # Update session state if sort option changed
            if 'channel_sort_by' not in st.session_state or st.session_state.channel_sort_by != sort_by:
                st.session_state.channel_sort_by = sort_by
            
            # Sort the dataframe
            if not channels_df.empty and sort_by in channels_df.columns:
                try:
                    # Sort numerically if possible, otherwise as strings
                    if sort_by in ['Subscribers', 'Total Views', 'Videos', 'Avg Views/Video', 'Likes Rate']:
                        channels_df = channels_df.sort_values(sort_by, ascending=False)
                    else:
                        channels_df = channels_df.sort_values(sort_by, ascending=False)
                except:
                    debug_log(f"Could not sort channels by {sort_by}")
        
        # Enhance the dataframe display with formatting
        if not channels_df.empty:
            # Format number columns
            for col in ['Subscribers', 'Total Views', 'Videos', 'Avg Views/Video']:
                if col in channels_df.columns:
                    channels_df[col] = channels_df[col].apply(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x)
            
            # Format like rate with percentage
            if 'Likes Rate' in channels_df.columns:
                channels_df['Likes Rate'] = channels_df['Likes Rate'].apply(lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x)
            
            # Display selected channels count
            if st.session_state.selected_channels:
                st.write(f"Selected: {len(st.session_state.selected_channels)} channel(s)")
            
            # Create a custom CSS for the dataframe display
            st.markdown("""
            <style>
                .stDataFrame {max-height: 350px; overflow-y: auto;}
                .row-highlight {background-color: rgba(0, 180, 255, 0.1) !important;}
                .dataframe th {text-align: left !important; padding: 8px !important;}
                .dataframe td {text-align: left !important; padding: 8px !important;}
            </style>
            """, unsafe_allow_html=True)
            
            # Add multiselect for channel selection
            all_channels = channels_df['Channel'].tolist()
            selected_channels = st.multiselect(
                "Select channels to compare",
                options=all_channels,
                default=st.session_state.selected_channels if all(ch in all_channels for ch in st.session_state.selected_channels) else [],
                key="channel_multiselect"
            )
            
            # Update session state with selected channels
            st.session_state.selected_channels = selected_channels
            
            # Display the dataframe with manual selection checkboxes instead of using on_select
            # This avoids the WebSocketClosedError when clicking on table rows
            
            # Create a dictionary to map channel names to their indices for quick lookup
            channel_to_idx = {row['Channel']: i for i, row in channels_df.iterrows()}
            
            # First display the dataframe without the problematic on_select callback
            st.dataframe(
                channels_df,
                column_config={
                    "Selected": st.column_config.TextColumn(
                        "Selected",
                        width="small"
                    ),
                    "Channel": st.column_config.TextColumn(
                        "Channel",
                        help="YouTube channel name"
                    ),
                    "Subscribers": st.column_config.TextColumn(
                        "Subscribers",
                        help="Total subscribers"
                    ),
                    "Total Views": st.column_config.TextColumn(
                        "Total Views",
                        help="Total video views"
                    ),
                    "Videos": st.column_config.TextColumn(
                        "Videos",
                        help="Total video count"
                    ),
                    "Avg Views/Video": st.column_config.TextColumn(
                        "Avg Views/Video",
                        help="Average views per video"
                    ),
                    "Likes Rate": st.column_config.TextColumn(
                        "Likes Rate",
                        help="Percentage of views resulting in likes"
                    ),
                    "Created": st.column_config.TextColumn(
                        "Created",
                        help="Channel creation date"
                    ),
                    "Last Updated": st.column_config.TextColumn(
                        "Last Updated",
                        help="Last data update"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Add manual selection controls below the table with a better UI
            st.write("**Quick Selection Controls:**")
            
            # Create layout for selection controls
            col1, col2 = st.columns([1, 1])
            with col1:
                st.button("Select All", 
                         key="select_all_channels", 
                         on_click=lambda: st.session_state.update({"selected_channels": all_channels}),
                         use_container_width=True)
            
            with col2:
                st.button("Clear Selection", 
                         key="clear_all_channels", 
                         on_click=lambda: st.session_state.update({"selected_channels": []}),
                         use_container_width=True)
            
            # Add individual channel selection checkboxes in a compact form
            st.write("**Individual Channel Selection:**")
            
            # Create a 3-column layout for the checkboxes to save vertical space
            checkbox_cols = st.columns(3)
            
            # Distribute channels across the columns
            channels_per_col = len(all_channels) // 3 + (1 if len(all_channels) % 3 > 0 else 0)
            
            # Create checkboxes for each channel
            for i, channel in enumerate(all_channels):
                col_idx = i // channels_per_col
                with checkbox_cols[min(col_idx, 2)]:
                    # The 'key' needs to be unique for each checkbox
                    is_selected = channel in st.session_state.selected_channels
                    if st.checkbox(channel, value=is_selected, key=f"channel_cb_{i}"):
                        if channel not in st.session_state.selected_channels:
                            st.session_state.selected_channels.append(channel)
                    elif channel in st.session_state.selected_channels:
                        st.session_state.selected_channels.remove(channel)
        
        # Warning if no channel is selected
        if not st.session_state.selected_channels:
            st.warning("Please select at least one channel to analyze.")
            # Select the first channel by default if none selected
            if channels:
                st.session_state.selected_channels = [channels[0]]
                st.rerun()
    
    # Now load channel data for all selected channels
    channel_data_dict = {}
    for channel_name in st.session_state.selected_channels:
        try:
            channel_data = db.get_channel_data(channel_name)
            if channel_data:
                channel_data_dict[channel_name] = channel_data
        except Exception as e:
            debug_log(f"Error loading data for channel {channel_name}: {str(e)}")
            
    return st.session_state.selected_channels, channel_data_dict

def handle_table_selection(selection_data, channels_df):
    """Handle selection from the dataframe UI."""
    # Handle case where selection_data is not provided
    if selection_data is None:
        return
    
    try:
        # Get selected indices from the selection data
        indices = [row for row in selection_data]
        
        # Get channel names from the selected rows
        selected_channels = []
        for idx in indices:
            # Get channel name from dataframe by row index
            if 0 <= idx < len(channels_df):
                channel_name = channels_df.iloc[idx]['Channel']
                selected_channels.append(channel_name)
        
        # Update session state with the new selection
        st.session_state.selected_channels = selected_channels
    except Exception as e:
        debug_log(f"Error processing table selection: {str(e)}")