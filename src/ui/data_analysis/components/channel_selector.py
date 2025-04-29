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
    Render the channel selector as a sortable table with only the last 5 imported channels.
    
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
    
    # Initialize YouTube Analysis for channel metrics
    analysis = YouTubeAnalysis()
    
    debug_log("Starting channel list processing", performance_tag="start_channel_selector")
    
    # Check if we have a cached channels dataframe
    cache_key = "analysis_channels_table"
    if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
        debug_log("Using cached channels table data")
        channels_df = st.session_state[cache_key]
    else:
        # Create a dataframe to display channels in a table
        with st.spinner("Loading channel data for comparison table..."):
            debug_log("Loading channel data from database", performance_tag="start_channel_data_loading")
            channels_data = []
            for channel_name in channels:
                try:
                    # Load basic channel data
                    channel_data = db.get_channel_data(channel_name)
                    if channel_data:
                        # Get channel statistics
                        stats = analysis.get_channel_statistics(channel_data)
                        
                        # Ensure all numeric values are properly converted to integers
                        subscribers = int(stats.get('subscribers', 0))
                        views = int(stats.get('views', 0))
                        total_videos = int(stats.get('total_videos', 0))
                        total_likes = int(stats.get('total_likes', 0))
                        
                        # Initialize date variables
                        created_date = "Unknown"
                        fetched_date = "Unknown"
                        fetched_timestamp = None
                        
                        # Get YouTube channel ID for direct database queries
                        youtube_id = None
                        if 'channel_info' in channel_data and 'id' in channel_data['channel_info']:
                            youtube_id = channel_data['channel_info']['id']
                        
                        # Direct database query for accurate dates
                        try:
                            import sqlite3
                            conn = sqlite3.connect(db.db_path)
                            cursor = conn.cursor()
                            
                            # First, try to get the channel by youtube_id
                            cursor.execute("""
                                SELECT published_at, last_updated, updated_at, title, subscriber_count 
                                FROM channels 
                                WHERE youtube_id = ?
                            """, (youtube_id,))
                            
                            date_row = cursor.fetchone()
                            
                            # If that fails, try getting by title
                            if not date_row:
                                cursor.execute("""
                                    SELECT published_at, last_updated, updated_at, title, subscriber_count 
                                    FROM channels 
                                    WHERE title = ?
                                """, (channel_name,))
                                date_row = cursor.fetchone()
                            
                            conn.close()
                            
                            if date_row:
                                # Format the creation date (published_at)
                                if date_row[0]:  # published_at
                                    try:
                                        date_str = date_row[0]
                                        if isinstance(date_str, str) and 'T' in date_str:
                                            date_str = date_str.replace('Z', '+00:00')
                                            date_obj = datetime.fromisoformat(date_str)
                                            created_date = date_obj.strftime('%b %d, %Y')
                                    except Exception as e:
                                        pass
                                
                                # Format the last updated date
                                if date_row[1]:  # last_updated
                                    try:
                                        # The last_updated field is a timestamp
                                        fetched_date = datetime.fromtimestamp(float(date_row[1])).strftime('%b %d, %Y')
                                        fetched_timestamp = float(date_row[1])
                                    except (ValueError, TypeError):
                                        try:
                                            # Try parsing as a string date
                                            date_str = date_row[1]
                                            if isinstance(date_str, str) and 'T' in date_str:
                                                date_str = date_str.replace('Z', '+00:00')
                                                date_obj = datetime.fromisoformat(date_str)
                                                fetched_date = date_obj.strftime('%b %d, %Y')
                                                fetched_timestamp = date_obj.timestamp()
                                            else:
                                                fetched_date = str(date_row[1])
                                        except Exception:
                                            pass
                                
                                # Try updated_at as fallback
                                if fetched_date == "Unknown" and date_row[2]:
                                    try:
                                        date_str = date_row[2]
                                        if isinstance(date_str, str) and 'T' in date_str:
                                            date_str = date_str.replace('Z', '+00:00')
                                            date_obj = datetime.fromisoformat(date_str)
                                            fetched_date = date_obj.strftime('%b %d, %Y')
                                    except Exception:
                                        pass
                        
                        except Exception as e:
                            # If direct DB query failed, try extracting from channel_data
                            if 'channel_info' in channel_data:
                                if 'published_at' in channel_data['channel_info']:
                                    published_at = channel_data['channel_info']['published_at']
                                    if published_at:
                                        try:
                                            date_str = published_at.replace('Z', '+00:00') if 'Z' in published_at else published_at
                                            date_obj = datetime.fromisoformat(date_str)
                                            created_date = date_obj.strftime('%b %d, %Y')
                                        except Exception:
                                            pass
                                
                                if 'fetched_at' in channel_data['channel_info']:
                                    fetched_at = channel_data['channel_info']['fetched_at']
                                    if fetched_at:
                                        try:
                                            date_str = fetched_at.replace('Z', '+00:00') if 'Z' in fetched_at else fetched_at
                                            date_obj = datetime.fromisoformat(date_str)
                                            fetched_date = date_obj.strftime('%b %d, %Y')
                                        except Exception:
                                            pass
                        
                        # Calculate average views per video
                        avg_views = 0
                        if stats['total_videos'] > 0:
                            avg_views = int(stats['views'] / stats['total_videos'])
                        
                        # Calculate like rate if data is available - improved formula
                        like_rate = 0
                        total_likes = stats.get('total_likes', 0)
                        if total_likes > 0 and stats['views'] > 0:
                            like_rate = (total_likes / stats['views']) * 100
                            # Cap like rate at 100% for display purposes (some data inconsistencies)
                            like_rate = min(like_rate, 100.0)
                        
                        # Add debugging info for likes
                        debug_log(f"Channel {channel_name}: Total Likes = {stats.get('total_likes', 0)}, Views = {stats.get('views', 0)}, Like Rate = {like_rate:.2f}%")
                        
                        # Format numeric values as strings to avoid formatting issues
                        formatted_subscribers = f"{int(subscribers):,}" if subscribers else "0"
                        formatted_views = f"{int(views):,}" if views else "0"
                        formatted_videos = f"{int(total_videos):,}" if total_videos else "0"
                        formatted_avg_views = f"{int(avg_views):,}" if avg_views else "0"
                        formatted_likes = f"{int(total_likes):,}" if total_likes else "0"
                        formatted_like_rate = f"{like_rate:.2f}%" if like_rate else "0.00%"
                        
                        # Clean up the Last Updated timestamp to match Created date format
                        formatted_last_updated = fetched_date
                        if isinstance(fetched_date, str) and "202" in fetched_date:  # If it's a raw timestamp
                            try:
                                # Try to convert to friendly format
                                if "T" in fetched_date or "-" in fetched_date:
                                    if ":" in fetched_date:
                                        # Parse ISO format or database timestamp
                                        date_str = fetched_date.replace('Z', '+00:00') if 'Z' in fetched_date else fetched_date
                                        try:
                                            date_obj = datetime.fromisoformat(date_str)
                                            formatted_last_updated = date_obj.strftime('%b %d, %Y')
                                        except ValueError:
                                            # Try another format with explicit pattern
                                            try:
                                                date_obj = datetime.strptime(fetched_date, '%Y-%m-%d %H:%M:%S')
                                                formatted_last_updated = date_obj.strftime('%b %d, %Y')
                                            except ValueError:
                                                pass
                            except Exception:
                                # Keep the original if parsing fails
                                pass
                        
                        # Add to channels data
                        channels_data.append({
                            'Channel': stats['name'],
                            'Channel_URL': f"https://youtube.com/channel/{channel_data['channel_info'].get('id', '')}",
                            'Subscribers': formatted_subscribers,
                            'Total Views': formatted_views,
                            'Videos': formatted_videos,
                            'Avg Views/Video': formatted_avg_views,
                            'Likes Rate': formatted_like_rate,
                            'Total Likes': formatted_likes,
                            'Created': created_date,
                            'Last Updated': formatted_last_updated,
                            'Update Timestamp': fetched_timestamp  # Internal field for sorting
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
                        'Last Updated': 'Unknown',
                        'Update Timestamp': 0
                    })
            
            debug_log("Finished loading channel data", performance_tag="end_channel_data_loading")
            
            # Create dataframe from collected data
            channels_df = pd.DataFrame(channels_data)
            
            # DIRECT SORT SOLUTION: Get the latest import values from the database
            debug_log("Implementing direct database ordering for channels")
            
            try:
                # Connect to the database to get direct ordering information
                import sqlite3
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                
                # Get all channel IDs with their timestamps in descending order (newest first)
                cursor.execute("""
                    SELECT id, title, last_updated 
                    FROM channels 
                    ORDER BY id DESC
                """)
                
                # Fetch all results to analyze
                all_db_records = cursor.fetchall()
                debug_log(f"Database query returned {len(all_db_records)} channel records")
                
                # Log some sample data to understand what we're dealing with
                if all_db_records:
                    debug_log(f"Sample DB records: {all_db_records[:3]}")
                
                # Create a dictionary mapping channel names to their database ID
                channel_order = {}
                for row in all_db_records:
                    channel_id = row[0]
                    channel_name = row[1]
                    channel_order[channel_name] = channel_id
                    debug_log(f"Channel '{channel_name}' has DB ID: {channel_id}")
                
                conn.close()
                
                # Now add the database ID to our dataframe for sorting
                channels_df['DB_ID'] = channels_df['Channel'].apply(
                    lambda x: channel_order.get(x, 0)
                )
                
                # Add the DB ID values to the dataframe for informational purposes
                debug_log(f"Channel DB IDs before sorting: {channels_df[['Channel', 'DB_ID']].values.tolist()}")
                
                # Sort by the database ID in descending order (higher ID = newer channel)
                channels_df = channels_df.sort_values('DB_ID', ascending=False)
                
                # Display the sorted order for debugging
                debug_log(f"Channels sorted by DB ID (descending): {channels_df['Channel'].tolist()}")
                debug_log(f"With DB IDs: {channels_df['DB_ID'].tolist()}")
                
            except Exception as e:
                debug_log(f"Error getting direct database ordering: {str(e)}")
                # Fallback to basic sorting if database access fails
                channels_df['DB_ID'] = range(len(channels_df), 0, -1)
            
            # FORCEFULLY CLEAR CACHE to ensure we're using fresh data
            if cache_key in st.session_state:
                del st.session_state[cache_key]
                debug_log("Cleared channel table cache to ensure fresh sorting")
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = channels_df
    
    # Limit to only the 5 most recently updated channels by default, but allow loading more
    if not channels_df.empty:
        # Store the full dataset
        full_channels_df = channels_df.copy()
        
        # By default, only show the most recent 5 channels
        default_limit = 5
        
        # Initialize session state for channel limit if it doesn't exist
        if 'channel_display_limit' not in st.session_state:
            st.session_state.channel_display_limit = default_limit
        
        # Initialize session state for channel search if it doesn't exist
        if 'channel_search_query' not in st.session_state:
            st.session_state.channel_search_query = ""
            
        # Apply current limit to the dataframe
        if len(channels_df) > st.session_state.channel_display_limit:
            recent_channels_df = channels_df.head(st.session_state.channel_display_limit).copy()
            debug_log(f"Limited channel display from {len(channels_df)} to {st.session_state.channel_display_limit} channels")
        else:
            recent_channels_df = channels_df.copy()
    else:
        recent_channels_df = channels_df
        full_channels_df = channels_df
    
    # Get the list of recent channel names
    recent_channel_names = recent_channels_df['Channel'].tolist() if not recent_channels_df.empty else []
    
    # Filter selected channels to only include recent ones shown in current view
    st.session_state.selected_channels = [ch for ch in st.session_state.selected_channels if ch in recent_channel_names]
    
    # Create a collapsible container for the channel selector
    with st.expander("Channel Selection", expanded=True):
        total_channels = len(full_channels_df) if not full_channels_df.empty else 0
        st.write(f"Available channels: {total_channels}. Showing the most recent {len(recent_channels_df)}.")
        
        # Add search and display controls in more logical layout
        st.write("Find and select channels to analyze:")
        
        # First row: Search with full width
        search_query = st.text_input(
            "Search channels by name:",
            value=st.session_state.channel_search_query,
            key="channel_search_input"
        )
        
        # If search query changed, update session state and apply filter
        if search_query != st.session_state.channel_search_query:
            st.session_state.channel_search_query = search_query
            
            # Reset display limit when searching to avoid confusion
            if search_query:
                st.session_state.channel_display_limit = total_channels
            else:
                st.session_state.channel_display_limit = default_limit
            
            # Re-render
            st.rerun()
        
        # Second row: Display limit control and selection count in more balanced columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Add control for number of channels to display
            display_options = [5, 10, 20, 50, 100, "All"]
            selected_display = st.selectbox(
                "Number of channels to display:",
                options=display_options,
                index=display_options.index(st.session_state.channel_display_limit if st.session_state.channel_display_limit in display_options else 5),
                key="display_limit_selector"
            )
            
            # Convert "All" to the total number of channels
            if selected_display == "All":
                selected_display = total_channels
            
            # Update session state if changed
            if selected_display != st.session_state.channel_display_limit:
                st.session_state.channel_display_limit = selected_display
                st.rerun()
                
        with col2:
            # Display selected channels count with more visibility
            if st.session_state.selected_channels:
                st.info(f"Selected: {len(st.session_state.selected_channels)} channel(s)")
            else:
                st.warning("No channels selected. Please select at least one channel to analyze.")
        
        # Apply search filter if there's a query
        if search_query and not full_channels_df.empty:
            # Filter channels by name using case-insensitive contains
            filtered_df = full_channels_df[full_channels_df['Channel'].str.lower().str.contains(search_query.lower())]
            
            if filtered_df.empty:
                st.warning(f"No channels found matching '{search_query}'")
                # Keep showing the recent channels instead
                search_active = False
            else:
                # Use the filtered dataframe
                recent_channels_df = filtered_df.copy()
                all_channels = recent_channels_df['Channel'].tolist()
                search_active = True
                
                st.success(f"Found {len(filtered_df)} channels matching '{search_query}'")
        else:
            search_active = False
        
        # Format the channel selection table
        if not recent_channels_df.empty:
            # Store original numeric data before formatting (important for data_editor)
            selection_df = recent_channels_df.copy()
            
            # Extract and convert numeric values to integers for proper sorting
            if 'Subscribers' in selection_df.columns:
                # Extract numeric values, removing commas
                selection_df['Subscribers_Num'] = selection_df['Subscribers'].apply(
                    lambda x: int(''.join(c for c in str(x) if c.isdigit())) if any(c.isdigit() for c in str(x)) else 0
                )
            
            if 'Total Views' in selection_df.columns:
                selection_df['Total_Views_Num'] = selection_df['Total Views'].apply(
                    lambda x: int(''.join(c for c in str(x) if c.isdigit())) if any(c.isdigit() for c in str(x)) else 0
                )
            
            if 'Videos' in selection_df.columns:
                selection_df['Videos_Num'] = selection_df['Videos'].apply(
                    lambda x: int(''.join(c for c in str(x) if c.isdigit())) if any(c.isdigit() for c in str(x)) else 0
                )
            
            if 'Avg Views/Video' in selection_df.columns:
                selection_df['Avg_Views_Num'] = selection_df['Avg Views/Video'].apply(
                    lambda x: int(''.join(c for c in str(x) if c.isdigit())) if any(c.isdigit() for c in str(x)) else 0
                )
            
            if 'Total Likes' in selection_df.columns:
                selection_df['Total_Likes_Num'] = selection_df['Total Likes'].apply(
                    lambda x: int(''.join(c for c in str(x) if c.isdigit())) if any(c.isdigit() for c in str(x)) else 0
                )
            
            if 'Likes Rate' in selection_df.columns:
                # Extract numerical percentage value, or 0 if not available
                selection_df['Likes_Rate_Num'] = selection_df['Likes Rate'].apply(
                    lambda x: float(x.replace('%', '')) if isinstance(x, str) and '%' in x else 
                             (float(x) if isinstance(x, (int, float)) else 0)
                )
            
            # Format number columns with commas for display (keeping original values for display)
            for col in ['Subscribers', 'Total Views', 'Videos', 'Avg Views/Video']:
                if col in recent_channels_df.columns:
                    recent_channels_df[col] = recent_channels_df[col].apply(lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x)
            
            # Format like rate with percentage
            if 'Likes Rate' in recent_channels_df.columns:
                recent_channels_df['Likes Rate'] = recent_channels_df['Likes Rate'].apply(lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x)
            
            # Remove internal timestamp column before display
            if 'Update Timestamp' in recent_channels_df.columns:
                recent_channels_df = recent_channels_df.drop(columns=['Update Timestamp'])
            
            # Display selected channels count
            if st.session_state.selected_channels:
                st.write(f"Selected: {len(st.session_state.selected_channels)} channel(s)")
            
            # Add multiselect for channel selection
            all_channels = recent_channels_df['Channel'].tolist()
            selected_channels = st.multiselect(
                "Select channels to analyze",
                options=all_channels,
                default=st.session_state.selected_channels if all(ch in all_channels for ch in st.session_state.selected_channels) else [],
                key="channel_multiselect"
            )
            
            # Update session state with selected channels
            st.session_state.selected_channels = selected_channels
            
            # NOTE: Removed the st.rerun() call here to prevent page reloading
            
            # Add checkboxes column to the dataframe for selection
            selection_df = recent_channels_df.copy()
            
            # Pre-set checkboxes for already selected channels
            selection_df['Select'] = selection_df['Channel'].apply(
                lambda x: x in st.session_state.selected_channels
            )
            
            # Create channel URLs for links (if not already present)
            if 'Channel_URL' not in selection_df.columns:
                selection_df['Channel_URL'] = selection_df['Channel']
            
            # Create a container for the dataframe to better control spacing
            table_container = st.container()
            with table_container:
                # Add a helpful instruction about using the table
                st.caption("Check the boxes below to select channels for analysis. Click on a channel name to view just that channel.")
                
                # Create a clickable channel name column that uses Streamlit's built-in callback
                selection_df['Channel Name'] = selection_df['Channel']
                
                # Remove any existing custom HTML columns to avoid confusion
                if 'Channel_HTML' in selection_df.columns:
                    selection_df = selection_df.drop(columns=['Channel_HTML'])
                
                # Define channel click handler
                def handle_channel_click(channel_name):
                    st.session_state.selected_channel = channel_name
                    st.session_state.selected_channels = [channel_name]
                    st.session_state.active_analysis_section = 'dashboard'
                    st.rerun()
                
                # Display the dataframe with checkbox column using the modern data_editor component
                edited_df = st.data_editor(
                    selection_df,
                    column_config={
                        "Select": st.column_config.CheckboxColumn(
                            "Select",
                            help="Select this channel",
                            default=False,
                            required=False,
                            width="auto"
                        ),
                        "Channel": st.column_config.TextColumn(
                            "Channel",
                            help="Click to view only this channel",
                            width="auto"
                        ),
                        "Channel_URL": st.column_config.LinkColumn(
                            "Channel Link",
                            help="Go to YouTube channel",
                            display_text="View on YouTube", 
                            width="auto",
                        ),
                        "Subscribers": st.column_config.NumberColumn(
                            "Subscribers",
                            help="Total channel subscribers",
                            width="auto",
                            format="%d",
                            step=1,
                            default=0,
                            min_value=0
                        ),
                        "Total Views": st.column_config.NumberColumn(
                            "Total Views",
                            help="Total video views",
                            width="auto",
                            format="%d",
                            step=1,
                            default=0
                        ),
                        "Videos": st.column_config.NumberColumn(
                            "Videos", 
                            help="Total video count",
                            width="auto",
                            format="%d",
                            step=1,
                            default=0
                        ),
                        "Avg Views/Video": st.column_config.NumberColumn(
                            "Avg Views/Video",
                            help="Average views per video",
                            width="auto",
                            format="%d",
                            step=1,
                            default=0
                        ),
                        "Total Likes": st.column_config.NumberColumn(
                            "Total Likes",
                            help="Total likes across all videos",
                            width="auto",
                            format="%d",
                            step=1,
                            default=0
                        ),
                        "Likes Rate": st.column_config.ProgressColumn(
                            "Likes Rate",
                            help="Percentage of views resulting in likes",
                            format="%.2f%%",
                            min_value=0,
                            max_value=100,
                            width="auto"
                        ),
                        "Created": st.column_config.TextColumn(
                            "Created",
                            help="Channel creation date",
                            width="auto"
                        ),
                        "Last Updated": st.column_config.TextColumn(
                            "Last Updated",
                            help="Last data update",
                            width="auto"
                        )
                    },
                    column_order=["Select", "Channel", "Channel_URL", "Subscribers", "Total Views", "Videos", 
                                "Avg Views/Video", "Total Likes", "Likes Rate", "Created", "Last Updated"],
                    hide_index=True,
                    use_container_width=True,
                    disabled=["Subscribers", "Total Views", "Videos", 
                              "Avg Views/Video", "Total Likes", "Created", "Last Updated"],
                    key="channel_table_editor",
                    num_rows="fixed"
                )
                
                # Add some helpful CSS to make the table more readable
                st.markdown("""
                <style>
                /* Make the channel name column look clickable */
                [data-testid="stDataEditor"] table tr td:nth-child(2) {
                    cursor: pointer;
                    color: #1E88E5;
                    font-weight: 500;
                }
                
                [data-testid="stDataEditor"] table tr td:nth-child(2):hover {
                    text-decoration: underline;
                    color: #0D47A1;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Around line 415 - Add a JavaScript handler for the table row clicks
                # Add script to make the channel name cells clickable
                st.markdown("""
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(function() {
                        // Get all table rows in the data editor
                        const tableRows = document.querySelectorAll('[data-testid="stDataEditor"] table tbody tr');
                        
                        tableRows.forEach(function(row) {
                            // Get the second cell (channel name cell)
                            const channelCell = row.cells[1];
                            
                            if (channelCell) {
                                channelCell.style.cursor = 'pointer';
                                channelCell.style.color = '#1E88E5';
                                channelCell.style.fontWeight = '500';
                                
                                channelCell.addEventListener('click', function() {
                                    // Get the channel name from the cell
                                    const channelName = channelCell.textContent.trim();
                                    
                                    // Store in session state and trigger rerun
                                    window.parent.postMessage({
                                        type: 'streamlit:setSessionState', 
                                        session_state: {
                                            selected_channel: channelName,
                                            selected_channels: [channelName],
                                            active_analysis_section: 'dashboard'
                                        }
                                    }, '*');
                                    
                                    // Force reload to apply the change
                                    setTimeout(() => window.parent.postMessage({
                                        type: 'streamlit:forceRerun'
                                    }, '*'), 100);
                                });
                            }
                        });
                    }, 500); // Small delay to ensure the table is rendered
                });
                </script>
                """, unsafe_allow_html=True)
                
                # Process selections from the edited dataframe
                if edited_df is not None and not edited_df.equals(selection_df):
                    # Get selected channels from the edited dataframe
                    table_selected_channels = []
                    for idx, row in edited_df.iterrows():
                        if row['Select']:
                            table_selected_channels.append(row['Channel'])
                    
                    # Store previous selection for comparison
                    previous_selection = st.session_state.selected_channels.copy() if st.session_state.selected_channels else []
                    
                    # Update session state with new selections
                    st.session_state.selected_channels = table_selected_channels
                    
                    # Only reload if there was an actual change in the selection
                    if set(table_selected_channels) != set(previous_selection):
                        # Store the previous channel to track changes for the main component
                        if 'previous_channel' not in st.session_state:
                            st.session_state.previous_channel = None
                        
                        # If we have a single channel selected, update the selected_channel for backward compatibility
                        if len(table_selected_channels) == 1 and 'selected_channel' in st.session_state:
                            st.session_state.previous_channel = st.session_state.get('selected_channel')
                            st.session_state.selected_channel = table_selected_channels[0]
                        
                        # Rerun to update the UI with new channel data
                        st.rerun()
            
            # Add select all button if there are channels to select
            if all_channels:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Select All", 
                               key="select_all_channels", 
                               use_container_width=True):
                        st.session_state.selected_channels = all_channels
                        # We need to rerun here to update the checkboxes in the table
                        st.rerun()
                
                with col2:
                    if st.button("Clear Selection", 
                               key="clear_all_channels", 
                               use_container_width=True):
                        st.session_state.selected_channels = []
                        # Only rerun if there were actually channels selected before
                        if len(selected_channels) > 0:
                            st.rerun()
                        
            # Display clear instruction if no channel is selected
            if not st.session_state.selected_channels:
                st.info("Please select at least one channel to view analysis data.")
        
        # Warning if no channels are available
        if not recent_channel_names:
            st.warning("No channels found in the database. Please collect data first.")
    
    debug_log("Finished channel selector rendering", performance_tag="end_channel_selector")
    
    # Now load channel data for selected channels
    channel_data_dict = {}
    
    if st.session_state.selected_channels:
        debug_log(f"Loading data for {len(st.session_state.selected_channels)} selected channels", 
                  performance_tag="start_selected_channel_loading")
        
        for channel_name in st.session_state.selected_channels:
            try:
                # Add performance tracking per channel
                debug_log(f"Loading data for channel: {channel_name}", 
                          performance_tag=f"start_channel_load_{channel_name}")
                
                # Check if we have cached data for this channel
                channel_cache_key = f"channel_data_{channel_name}"
                if st.session_state.get('use_data_cache', True) and channel_cache_key in st.session_state:
                    debug_log(f"Using cached data for channel: {channel_name}")
                    channel_data = st.session_state[channel_cache_key]
                else:
                    # Fetch from database with timing
                    start_time = time.time()
                    channel_data = db.get_channel_data(channel_name)
                    load_time = time.time() - start_time
                    debug_log(f"Loaded channel data from DB in {load_time:.2f}s")
                    
                    # Cache the result
                    if st.session_state.get('use_data_cache', True) and channel_data:
                        st.session_state[channel_cache_key] = channel_data
                
                if channel_data:
                    channel_data_dict[channel_name] = channel_data
                    
                debug_log(f"Finished loading data for channel: {channel_name}", 
                          performance_tag=f"end_channel_load_{channel_name}")
            except Exception as e:
                debug_log(f"Error loading data for channel {channel_name}: {str(e)}")
        
        debug_log(f"Finished loading all selected channel data", 
                  performance_tag="end_selected_channel_loading")
    
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

# Update the function to better extract channel creation date
def get_formatted_channel_date(channel_data, field_path):
    """Helper function to extract and format date from channel data."""
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