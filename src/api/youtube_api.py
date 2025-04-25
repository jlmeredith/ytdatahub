"""
YouTube API client implementation for the YouTube scraper application.
"""
import os
import streamlit as st
import googleapiclient.discovery
import googleapiclient.errors
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from src.config import API_SERVICE_NAME, API_VERSION
from src.utils.helpers import debug_log, validate_api_key, validate_channel_id

class YouTubeAPI:
    """YouTube Data API client for fetching channel and video data"""
    
    def __init__(self, api_key: str):
        """Initialize the YouTube API client"""
        self.api_key = api_key
        self.youtube = None
        
        # Initialize the API client if a valid API key is provided
        if validate_api_key(api_key):
            try:
                self.youtube = googleapiclient.discovery.build(
                    API_SERVICE_NAME,
                    API_VERSION,
                    developerKey=api_key,
                    cache_discovery=False
                )
                debug_log("YouTube API client initialized successfully")
            except Exception as e:
                st.error(f"Error initializing YouTube API client: {str(e)}")
                debug_log(f"API client initialization failed: {str(e)}", e)
        else:
            st.error("Invalid API key format. Please provide a valid YouTube Data API key.")
    
    def is_initialized(self) -> bool:
        """Check if the API client is properly initialized"""
        return self.youtube is not None
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel information by channel ID"""
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return None
        
        if not validate_channel_id(channel_id):
            st.error("Invalid channel ID format. Channel IDs typically start with 'UC'.")
            return None
        
        debug_log(f"Fetching channel info for: {channel_id}")
        
        try:
            # Check cache first
            cache_key = f"channel_info_{channel_id}"
            if cache_key in st.session_state.api_cache:
                debug_log(f"Using cached channel info for: {channel_id}")
                return st.session_state.api_cache[cache_key]
            
            # Request channel information
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                id=channel_id
            )
            response = request.execute()
            
            # Check if channel was found
            if not response['items']:
                st.error(f"Channel with ID '{channel_id}' not found. Please check the channel ID.")
                return None
            
            # Extract relevant information
            channel_data = response['items'][0]
            uploads_playlist_id = channel_data['contentDetails']['relatedPlaylists']['uploads']
            
            # Format channel info
            channel_info = {
                'channel_id': channel_id,
                'channel_name': channel_data['snippet']['title'],
                'channel_description': channel_data['snippet']['description'],
                'subscribers': channel_data['statistics']['subscriberCount'],
                'views': channel_data['statistics']['viewCount'],
                'total_videos': channel_data['statistics']['videoCount'],
                'playlist_id': uploads_playlist_id,
                'video_id': []  # Will be populated later
            }
            
            # Store in cache
            st.session_state.api_cache[cache_key] = channel_info
            
            debug_log(f"Channel info fetched successfully for: {channel_info['channel_name']}")
            return channel_info
            
        except googleapiclient.errors.HttpError as e:
            st.error(f"YouTube API error: {str(e)}")
            debug_log(f"API error in get_channel_info: {str(e)}", e)
            return None
        except Exception as e:
            st.error(f"Error fetching channel info: {str(e)}")
            debug_log(f"Exception in get_channel_info: {str(e)}", e)
            return None
    
    def get_channel_videos(self, channel_info: Dict[str, Any], max_videos: int = 25) -> Optional[Dict[str, Any]]:
        """Get videos from a channel's uploads playlist"""
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return None
        
        playlist_id = channel_info.get('playlist_id')
        if not playlist_id:
            st.error("No uploads playlist ID found in channel info.")
            return None
        
        debug_log(f"Fetching up to {max_videos} videos for channel: {channel_info.get('channel_name')}")
        
        try:
            # Request videos from the uploads playlist
            videos = []
            next_page_token = None
            total_videos = 0
            
            # Progress bar for video fetching
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            while total_videos < max_videos:
                # Check cache first
                cache_key = f"playlist_{playlist_id}_{next_page_token}"
                playlist_response = None
                
                if cache_key in st.session_state.api_cache:
                    debug_log(f"Using cached playlist page for token: {next_page_token}")
                    playlist_response = st.session_state.api_cache[cache_key]
                else:
                    # Make API request for playlist items
                    playlist_request = self.youtube.playlistItems().list(
                        part="snippet,contentDetails",
                        playlistId=playlist_id,
                        maxResults=50,  # Maximum allowed by the API
                        pageToken=next_page_token
                    )
                    playlist_response = playlist_request.execute()
                    
                    # Store in cache
                    st.session_state.api_cache[cache_key] = playlist_response
                
                # Process video items
                items_to_process = min(len(playlist_response['items']), max_videos - total_videos)
                
                # Collect video IDs for batch processing
                video_ids = []
                for i in range(items_to_process):
                    video_id = playlist_response['items'][i]['contentDetails']['videoId']
                    video_ids.append(video_id)
                
                # Fetch video details in batches
                video_details = self._get_videos_details(video_ids)
                
                # Add video details to the list
                for i in range(items_to_process):
                    video_item = playlist_response['items'][i]
                    video_id = video_item['contentDetails']['videoId']
                    
                    # Get the matching video details
                    video_detail = None
                    for detail in video_details:
                        if detail.get('id') == video_id:
                            video_detail = detail
                            break
                    
                    if video_detail:
                        # Basic video info from playlist item
                        video_info = {
                            'video_id': video_id,
                            'title': video_item['snippet']['title'],
                            'published_at': video_item['snippet']['publishedAt'],
                            'published_date': video_item['snippet']['publishedAt'].split('T')[0],
                            'thumbnails': video_item['snippet']['thumbnails']['high']['url'],
                            'video_description': video_detail.get('snippet', {}).get('description', ''),
                            'views': video_detail.get('statistics', {}).get('viewCount', '0'),
                            'likes': video_detail.get('statistics', {}).get('likeCount', '0'),
                            'duration': video_detail.get('contentDetails', {}).get('duration', 'PT0S'),
                            'caption_status': video_detail.get('contentDetails', {}).get('caption', 'none'),
                            'comments': []  # Will be populated if needed
                        }
                        
                        videos.append(video_info)
                    
                    # Update progress
                    total_videos += 1
                    progress = min(total_videos / max_videos, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Fetched {total_videos} of {max_videos} videos...")
                
                # Check if there are more videos to fetch
                if 'nextPageToken' in playlist_response and total_videos < max_videos:
                    next_page_token = playlist_response['nextPageToken']
                else:
                    break
            
            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()
            
            # Update channel info with video data
            channel_info['video_id'] = videos
            
            debug_log(f"Fetched {len(videos)} videos for channel: {channel_info.get('channel_name')}")
            return channel_info
            
        except googleapiclient.errors.HttpError as e:
            st.error(f"YouTube API error: {str(e)}")
            debug_log(f"API error in get_channel_videos: {str(e)}", e)
            return None
        except Exception as e:
            st.error(f"Error fetching channel videos: {str(e)}")
            debug_log(f"Exception in get_channel_videos: {str(e)}", e)
            return None
    
    def _get_videos_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information for a batch of videos by their IDs"""
        if not video_ids:
            return []
        
        try:
            # Join IDs with commas for the API request
            video_ids_str = ','.join(video_ids)
            
            # Check cache first
            cache_key = f"video_details_{video_ids_str}"
            if cache_key in st.session_state.api_cache:
                debug_log(f"Using cached video details for {len(video_ids)} videos")
                return st.session_state.api_cache[cache_key]
            
            # Request video details
            video_request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_ids_str
            )
            video_response = video_request.execute()
            
            # Store in cache
            st.session_state.api_cache[cache_key] = video_response.get('items', [])
            
            return video_response.get('items', [])
            
        except googleapiclient.errors.HttpError as e:
            st.error(f"YouTube API error: {str(e)}")
            debug_log(f"API error in _get_videos_details: {str(e)}", e)
            return []
        except Exception as e:
            st.error(f"Error fetching video details: {str(e)}")
            debug_log(f"Exception in _get_videos_details: {str(e)}", e)
            return []
    
    def get_video_comments(self, channel_info: Dict[str, Any], max_comments_per_video: int = 10) -> Optional[Dict[str, Any]]:
        """Get comments for each video in the channel"""
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return None
        
        videos = channel_info.get('video_id', [])
        if not videos:
            st.warning("No videos found to fetch comments for.")
            return channel_info
        
        debug_log(f"Fetching up to {max_comments_per_video} comments per video for {len(videos)} videos")
        
        try:
            # Progress tracking
            total_videos = len(videos)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process each video
            for i, video in enumerate(videos):
                video_id = video.get('video_id')
                
                # Update progress
                progress = (i + 1) / total_videos
                progress_bar.progress(progress)
                status_text.text(f"Fetching comments for video {i+1} of {total_videos}...")
                
                # Check cache first
                cache_key = f"comments_{video_id}"
                
                if cache_key in st.session_state.api_cache:
                    debug_log(f"Using cached comments for video: {video_id}")
                    video['comments'] = st.session_state.api_cache[cache_key]
                    continue
                
                try:
                    # Request comments for the video
                    comments_request = self.youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id,
                        maxResults=max_comments_per_video
                    )
                    comments_response = comments_request.execute()
                    
                    # Extract comment data
                    comments = []
                    for item in comments_response.get('items', []):
                        comment = item['snippet']['topLevelComment']['snippet']
                        comment_data = {
                            'comment_id': item['id'],
                            'comment_text': comment['textDisplay'],
                            'comment_authorc': comment['authorDisplayName'],
                            'comment_published_at': comment['publishedAt']
                        }
                        comments.append(comment_data)
                    
                    # Add comments to the video
                    video['comments'] = comments
                    
                    # Store in cache
                    st.session_state.api_cache[cache_key] = comments
                    
                except googleapiclient.errors.HttpError as e:
                    # Comments might be disabled for the video
                    if 'commentsDisabled' in str(e):
                        debug_log(f"Comments are disabled for video: {video_id}")
                        video['comments'] = []
                    else:
                        debug_log(f"Error fetching comments for video {video_id}: {str(e)}")
                        video['comments'] = []
            
            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()
            
            debug_log(f"Finished fetching comments for {len(videos)} videos")
            return channel_info
            
        except Exception as e:
            st.error(f"Error fetching video comments: {str(e)}")
            debug_log(f"Exception in get_video_comments: {str(e)}", e)
            return channel_info  # Return the channel info even if comments fetching failed