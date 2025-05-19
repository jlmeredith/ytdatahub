"""
Data loading functionality for the channel selector component.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sqlite3
from src.utils.helpers import debug_log

def load_channel_data(channels, db, analysis):
    """
    Load and process channel data from the database.
    
    Args:
        channels: List of channel names
        db: Database connection
        analysis: YouTubeAnalysis instance
        
    Returns:
        Tuple of (channels_df, full_channels_df, recent_channels_df)
    """
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
                        fetch_channel_dates(db, youtube_id, channel_name, created_date, fetched_date, fetched_timestamp)
                        
                        # Calculate engagement metric (likes/views ratio as percentage)
                        avg_likes = total_likes / total_videos if total_videos > 0 else 0
                        avg_views = int(views / total_videos) if total_videos > 0 else 0
                        engagement = (avg_likes / avg_views * 100) if avg_views > 0 else 0
                        
                        # Add to channel data
                        channel_record = {
                            'Channel': channel_name,
                            'Subscribers': subscribers,
                            'Views': views,
                            'Videos': total_videos,
                            'Created': created_date,
                            'Last Updated': fetched_date,
                            'Update Timestamp': fetched_timestamp,
                            'Engagement': engagement,
                            'Avg Views': avg_views,
                            'ID': youtube_id
                        }
                        
                        channels_data.append(channel_record)
                except Exception as e:
                    debug_log(f"Error loading data for {channel_name}: {str(e)}")
            
            debug_log("Finished loading channel data", performance_tag="end_channel_data_loading")
            
            # Create dataframe
            channels_df = pd.DataFrame(channels_data)
    
    # Handle empty dataframe case
    if channels_df.empty:
        st.warning("No channel data available. Please import some channels first.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Sort channels by update timestamp (most recent first) if available
    if 'Update Timestamp' in channels_df.columns:
        # Handle NaN values by replacing with 0
        channels_df['Update Timestamp'] = channels_df['Update Timestamp'].fillna(0)
        
        # Sort by timestamp in descending order (most recent first)
        channels_df = channels_df.sort_values('Update Timestamp', ascending=False)
    
    # Try to get DB IDs for better sorting
    if db:
        try:
            # Connect to the database directly
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            # Get the order based on internal database ID (most recent first)
            cursor.execute("SELECT id, title FROM channels ORDER BY id DESC")
            db_order = cursor.fetchall()
            conn.close()
            
            # Create a mapping of channel names to DB IDs
            channel_to_id = {title: db_id for db_id, title in db_order}
            
            # Add DB ID column
            channels_df['DB_ID'] = channels_df['Channel'].map(channel_to_id)
            
            # Sort by DB ID (most recent first)
            channels_df = channels_df.sort_values('DB_ID', ascending=False)
            
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
    
    # Limit to only the most recently updated channels by default, but allow loading more
    if not channels_df.empty:
        # Store the full dataset
        full_channels_df = channels_df.copy()
        
        # Apply current limit to the dataframe
        if len(channels_df) > st.session_state.channel_display_limit:
            recent_channels_df = channels_df.head(st.session_state.channel_display_limit).copy()
            debug_log(f"Limited channel display from {len(channels_df)} to {st.session_state.channel_display_limit} channels")
        else:
            recent_channels_df = channels_df.copy()
    else:
        recent_channels_df = channels_df
        full_channels_df = channels_df
    
    return channels_df, full_channels_df, recent_channels_df

def fetch_channel_dates(db, youtube_id, channel_name, created_date, fetched_date, fetched_timestamp):
    """
    Fetch channel dates from the database.
    
    Args:
        db: Database connection
        youtube_id: YouTube channel ID
        channel_name: Channel name
        created_date: Variable to store the created date
        fetched_date: Variable to store the fetched date
        fetched_timestamp: Variable to store the fetched timestamp
        
    Returns:
        Tuple of (created_date, fetched_date, fetched_timestamp)
    """
    try:
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
        debug_log(f"Error fetching channel dates: {str(e)}")
    
    return created_date, fetched_date, fetched_timestamp
