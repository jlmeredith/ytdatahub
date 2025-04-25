"""
Local storage functions for the YouTube scraper application.
"""
import json
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

from src.config import CHANNELS_FILE
from src.utils.helpers import debug_log, parse_duration_with_regex

class LocalStorage:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.channels_file = self.data_dir / "channels.json"
        
    def store_channel_data(self, channel_data):
        """
        Store channel data to local JSON file
        """
        try:
            # Create a filename based on channel ID
            channel_id = channel_data.get('channel_id')
            filename = self.data_dir / f"{channel_id}.json"
            
            # Write the data to file
            with open(filename, 'w') as f:
                json.dump(channel_data, f, indent=2)
            
            # Update the channels.json file with the list of channels
            channels = self.get_channels_list()
            channel_name = channel_data.get('channel_name')
            
            if channel_id not in channels:
                self._update_channels_list(channel_id, channel_name)
            
            return True
        except Exception as e:
            debug_log(f"Error storing channel data locally: {str(e)}")
            return False
    
    def _update_channels_list(self, channel_id, channel_name):
        """Update the channels list file with a new channel"""
        try:
            channels = {}
            
            # Read existing channels if file exists
            if self.channels_file.exists():
                with open(self.channels_file, 'r') as f:
                    channels = json.load(f)
            
            # Add or update channel
            channels[channel_id] = channel_name
            
            # Write back to file
            with open(self.channels_file, 'w') as f:
                json.dump(channels, f, indent=2)
                
            return True
        except Exception as e:
            debug_log(f"Error updating channels list: {str(e)}")
            return False
    
    def get_channels_list(self):
        """Get list of stored channels"""
        try:
            if self.channels_file.exists():
                with open(self.channels_file, 'r') as f:
                    channels = json.load(f)
                return channels
            return {}
        except Exception as e:
            debug_log(f"Error reading channels list: {str(e)}")
            return {}
    
    def get_channel_data(self, channel_id):
        """Get data for a specific channel"""
        try:
            filename = self.data_dir / f"{channel_id}.json"
            if filename.exists():
                with open(filename, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            debug_log(f"Error reading channel data: {str(e)}")
            return None

def save_to_local_storage(data):
    """Legacy function for backward compatibility"""
    storage = LocalStorage(Path("./data"))
    return storage.store_channel_data(data)

def get_local_channels_data():
    """Get all channels from local storage"""
    debug_log("Loading channels from local storage")
    
    try:
        if CHANNELS_FILE.exists():
            with open(CHANNELS_FILE, "r") as f:
                channels = json.load(f)
            
            debug_log(f"Loaded {len(channels)} channels from local storage")
            
            # Create a list to hold simplified channel data
            data_rows = []
            for channel in channels:
                # Get video count
                video_count = len(channel.get('video_id', []))
                
                # Calculate total views and average views per video
                total_views = int(channel.get('views', 0))
                avg_views = 0
                if video_count > 0:
                    avg_views = total_views / video_count
                
                data_rows.append([
                    channel.get('channel_name', 'Unknown'),
                    channel.get('channel_id', 'Unknown'),
                    int(channel.get('subscribers', 0)),
                    total_views,
                    int(channel.get('total_videos', 0)),
                    video_count,
                    int(avg_views)
                ])
            
            columns = [
                'Channel Name', 
                'Channel ID', 
                'Subscribers', 
                'Total Views', 
                'Total Videos', 
                'Fetched Videos', 
                'Avg Views/Video'
            ]
            
            # Display the data
            if data_rows:
                st.dataframe(pd.DataFrame(data_rows, columns=columns))
            else:
                st.info("No channels found in local storage.")
                
            return True
        else:
            st.warning("No local data available. Please fetch and save channel data first.")
            return False
    except Exception as e:
        st.error(f"Error loading local data: {str(e)}")
        debug_log(f"Exception in get_local_channels_data: {str(e)}", e)
        return False

def get_local_videos_data():
    """Get all videos from local storage"""
    debug_log("Loading videos from local storage")
    
    try:
        if CHANNELS_FILE.exists():
            with open(CHANNELS_FILE, "r") as f:
                channels = json.load(f)
            
            # Create a list to hold all videos
            videos = []
            for channel in channels:
                channel_name = channel.get('channel_name', 'Unknown')
                channel_id = channel.get('channel_id', 'Unknown')
                
                for video in channel.get('video_id', []):
                    # Parse video duration
                    duration_sec = parse_duration_with_regex(video.get('duration', 'PT0S'))
                    
                    # Get view and like counts
                    views = int(video.get('views', 0))
                    likes = int(video.get('likes', 0))
                    
                    # Calculate engagement (likes per view)
                    engagement = 0
                    if views > 0:
                        engagement = likes / views
                    
                    videos.append({
                        'channel_name': channel_name,
                        'channel_id': channel_id,
                        'video_id': video.get('video_id', ''),
                        'title': video.get('title', 'Unknown'),
                        'published_at': video.get('published_at', ''),
                        'views': views,
                        'likes': likes,
                        'duration_sec': duration_sec,
                        'engagement': engagement
                    })
            
            # Convert to DataFrame
            if videos:
                videos_df = pd.DataFrame(videos)
                
                # Add a date column for easier filtering
                videos_df['published_date'] = pd.to_datetime(videos_df['published_at']).dt.date
                
                # Display the data
                st.write(f"Showing {len(videos)} videos from {len(channels)} channels")
                st.dataframe(videos_df)
            else:
                st.info("No videos found in local storage.")
            
            return True
        else:
            st.warning("No local data available. Please fetch and save channel data first.")
            return False
    except Exception as e:
        st.error(f"Error loading video data: {str(e)}")
        debug_log(f"Exception in get_local_videos_data: {str(e)}", e)
        return False

def local_get_video_duration_stats():
    """Analyze video duration from local storage"""
    debug_log("Analyzing video durations from local storage")
    
    try:
        if CHANNELS_FILE.exists():
            with open(CHANNELS_FILE, "r") as f:
                channels = json.load(f)
            
            # Calculate video durations
            durations = []
            for channel in channels:
                for video in channel.get('video_id', []):
                    duration_sec = parse_duration_with_regex(video.get('duration', 'PT0S'))
                    durations.append(duration_sec)
            
            if durations:
                # Basic statistics
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)
                
                # Create duration buckets (in minutes)
                buckets = {
                    '< 1 min': 0,
                    '1-5 mins': 0,
                    '5-10 mins': 0,
                    '10-20 mins': 0,
                    '20-30 mins': 0,
                    '30-60 mins': 0,
                    '> 60 mins': 0
                }
                
                for duration in durations:
                    if duration < 60:
                        buckets['< 1 min'] += 1
                    elif duration < 300:
                        buckets['1-5 mins'] += 1
                    elif duration < 600:
                        buckets['5-10 mins'] += 1
                    elif duration < 1200:
                        buckets['10-20 mins'] += 1
                    elif duration < 1800:
                        buckets['20-30 mins'] += 1
                    elif duration < 3600:
                        buckets['30-60 mins'] += 1
                    else:
                        buckets['> 60 mins'] += 1
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Duration", f"{avg_duration/60:.1f} mins")
                col2.metric("Min Duration", f"{min_duration/60:.1f} mins")
                col3.metric("Max Duration", f"{max_duration/60:.1f} mins")
                
                # Display distribution
                st.write("### Video Duration Distribution")
                bucket_df = pd.DataFrame({
                    'Duration Range': list(buckets.keys()),
                    'Number of Videos': list(buckets.values())
                })
                st.bar_chart(bucket_df.set_index('Duration Range'))
                
                return True
            else:
                st.info("No video duration data available.")
                return False
        else:
            st.warning("No local data available. Please fetch and save channel data first.")
            return False
    except Exception as e:
        st.error(f"Error analyzing video durations: {str(e)}")
        debug_log(f"Exception in local_get_video_duration_stats: {str(e)}", e)
        return False

def local_get_video_published_data():
    """Get channels that published videos in 2022 from local storage"""
    try:
        if CHANNELS_FILE.exists():
            with open(CHANNELS_FILE, "r") as f:
                channels = json.load(f)
                
            # Create a list to hold channel data
            data_rows = []
            channels_found = set()  # To avoid duplicate channel names
            
            for channel in channels:
                channel_name = channel.get('channel_name', 'Unknown')
                
                # Check each video's published date
                for video in channel.get('video_id', []):
                    published_at = video.get('published_date', '')
                    
                    # Check if the video was published in 2022
                    if published_at and '2022' in published_at and channel_name not in channels_found:
                        data_rows.append([channel_name])
                        channels_found.add(channel_name)
                        break
            
            columns = ['Channel Name']
            
            # Display the data
            st.table(pd.DataFrame(data_rows, columns=columns))
            return True
        else:
            st.warning("No local data available. Please fetch and save channel data first.")
            return False
    except Exception as e:
        st.error(f"Error processing local data: {str(e)}")
        return False