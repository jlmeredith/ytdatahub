"""
Service for handling YouTube video operations.
Provides methods for fetching and processing video data.
"""
import logging
import time
import json
import copy
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.api.youtube_api import YouTubeAPI, YouTubeAPIError
from src.utils.debug_utils import debug_log
from src.services.youtube.base_service import BaseService

class VideoService(BaseService):
    """
    Service for managing YouTube video operations.
    """
    
    def __init__(self, api_key=None, api_client=None):
        """
        Initialize the video service.
        
        Args:
            api_key (str, optional): YouTube API key
            api_client (obj, optional): Existing API client to use
        """
        super().__init__(api_key, api_client)
        self.api = api_client if api_client else (YouTubeAPI(api_key) if api_key else None)
        self.logger = logging.getLogger(__name__)
    
    def collect_channel_videos(self, channel_data, max_results=50, quota_optimize=False):
        """Fetch and populate videos for a channel"""
        try:
            debug_logs = []
            def log(msg):
                debug_logs.append(msg)
                debug_log(msg)
            # Initialize variables
            next_page_token = None
            quota_used = 0
            videos = []
            
            playlist_id = channel_data.get('playlist_id')
            if not playlist_id:
                log(f"[ERROR] No playlist_id found in channel_data for channel: {channel_data.get('channel_id')}")
                return {'video_id': [], 'error_videos': 'No playlist_id found. Cannot fetch videos.', 'debug_logs': debug_logs}
            log(f"[WORKFLOW] About to fetch videos using playlist_id: {playlist_id}")
            response = self.api.video_client.get_channel_videos({'playlist_id': playlist_id}, max_videos=max_results)
            log(f"[WORKFLOW] Video API response: {json.dumps(response)[:500]}")
            quota_used += 1  # Track quota usage
            if response and 'video_id' in response and isinstance(response['video_id'], list):
                log(f"[DIAG] Number of videos in response: {len(response['video_id'])}")
                if response['video_id']:
                    log(f"[DIAG] Keys of first video: {list(response['video_id'][0].keys())}")
            else:
                log(f"[DIAG] No 'video_id' key or not a list in response: keys={list(response.keys()) if response else 'None'}")
            
            if not response or 'video_id' not in response:
                log(f"No videos found or API call failed for channel: {channel_data.get('channel_id')}")
                return {'video_id': [], 'error_videos': 'No videos found', 'debug_logs': debug_logs}
            log(f"Number of videos returned: {len(response['video_id'])}")
            
            # Process video response
            for video in response['video_id']:
                # Ensure video has required fields
                if 'video_id' not in video:
                    log(f"Video missing video_id: {video}")
                    continue
                log(f"Processing video: {video['video_id']}")
                # PATCH: Always append video, even if statistics are missing or malformed
                # Initialize metrics with explicit string values (not integers)
                video['views'] = '0'
                video['likes'] = '0'
                video['comment_count'] = '0'
                # Try to get statistics from various locations
                stats = None
                if isinstance(video.get('statistics'), dict):
                    stats = video['statistics']
                    debug_log(f"Found statistics dict for video {video.get('video_id')}: {stats}")
                elif isinstance(video.get('statistics'), str):
                    try:
                        stats = json.loads(video['statistics'])
                        debug_log(f"Parsed statistics string for video {video.get('video_id')}")
                    except Exception as e:
                        debug_log(f"Failed to parse statistics string: {str(e)}")
                        pass
                elif isinstance(video.get('contentDetails', {}).get('statistics'), dict):
                    stats = video['contentDetails']['statistics']
                    debug_log(f"Found contentDetails.statistics for video {video.get('video_id')}")
                elif isinstance(video.get('snippet', {}).get('statistics'), dict):
                    stats = video['snippet']['statistics']
                    debug_log(f"Found snippet.statistics for video {video.get('video_id')}")
                if stats:
                    # Set metrics from statistics if available, else fallback to 0
                    def safe_int(val):
                        if isinstance(val, (int, float)):
                            return int(val)
                        if isinstance(val, str) and val.isdigit():
                            return int(val)
                        return 0
                    video['views'] = safe_int(stats.get('viewCount', video.get('views', 0)))
                    video['likes'] = safe_int(stats.get('likeCount', video.get('likes', 0)))
                    video['comment_count'] = safe_int(stats.get('commentCount', video.get('comment_count', 0)))
                    debug_log(f"Set metrics from statistics for video {video.get('video_id')}: views={video['views']}, likes={video['likes']}, comments={video['comment_count']}")
                # Coerce metrics to int if they are digit strings
                for metric in ['views', 'likes', 'comment_count']:
                    if metric in video and isinstance(video[metric], str) and video[metric].isdigit():
                        video[metric] = int(video[metric])
                # Attach the full API response for this video
                if 'raw_api_response' not in video:
                    video['raw_api_response'] = copy.deepcopy(video)
                # Always append the video, even if stats are missing
                videos.append(video)
            
            # Handle pagination if needed
            if not quota_optimize and 'nextPageToken' in response:
                log(f"Pagination detected. nextPageToken: {response['nextPageToken']}")
                next_page_token = response['nextPageToken']
                while next_page_token and len(videos) < max_results:
                    response = self.api.video_client.get_channel_videos(
                        channel_data,
                        max_videos=max_results,
                        page_token=next_page_token
                    )
                    quota_used += 1
                    
                    if not response or 'video_id' not in response:
                        log(f"No videos found or API call failed on pagination for channel: {channel_data.get('channel_id')}")
                        break
                    
                    log(f"Number of videos returned in page: {len(response['video_id'])}")
                    
                    for video in response['video_id']:
                        if len(videos) >= max_results:
                            break
                        if 'video_id' not in video:
                            log(f"Video missing video_id on pagination: {video}")
                            continue
                        log(f"Processing video in pagination: {video['video_id']}")
                        
                        # Initialize metrics
                        video['views'] = '0'
                        video['likes'] = '0'
                        video['comment_count'] = '0'
                        
                        # Try to get statistics from various locations
                        stats = None
                        if isinstance(video.get('statistics'), dict):
                            stats = video['statistics']
                        elif isinstance(video.get('statistics'), str):
                            try:
                                stats = json.loads(video['statistics'])
                            except:
                                pass
                        elif isinstance(video.get('contentDetails', {}).get('statistics'), dict):
                            stats = video['contentDetails']['statistics']
                        elif isinstance(video.get('snippet', {}).get('statistics'), dict):
                            stats = video['snippet']['statistics']
                        
                        if stats:
                            # Set metrics from statistics if available, else fallback to 0
                            def safe_int(val):
                                if isinstance(val, (int, float)):
                                    return int(val)
                                if isinstance(val, str) and val.isdigit():
                                    return int(val)
                                return 0
                            video['views'] = safe_int(stats.get('viewCount', video.get('views', 0)))
                            video['likes'] = safe_int(stats.get('likeCount', video.get('likes', 0)))
                            video['comment_count'] = safe_int(stats.get('commentCount', video.get('comment_count', 0)))
                        
                        # Coerce metrics to int if they are digit strings
                        for metric in ['views', 'likes', 'comment_count']:
                            if metric in video and isinstance(video[metric], str) and video[metric].isdigit():
                                video[metric] = int(video[metric])
                        
                        # Attach the full API response for this video
                        if 'raw_api_response' not in video:
                            video['raw_api_response'] = copy.deepcopy(video)
                        
                        videos.append(video)
                    
                    next_page_token = response.get('nextPageToken')
            
            result = {
                'video_id': videos,
                'quota_used': quota_used,
                'videos_fetched': len(videos),
                'debug_logs': debug_logs
            }
            # Merge all unique logs from debug_logs and ui_debug_logs
            try:
                import streamlit as st
                if hasattr(st, 'session_state') and 'ui_debug_logs' in st.session_state:
                    debug_logs = list({*debug_logs, *st.session_state['ui_debug_logs']})
                    result['debug_logs'] = debug_logs
            except Exception:
                pass
            log(f"Returning {len(videos)} videos to caller.")
            if len(videos) == 0:
                log(f"API call succeeded but no videos were returned for channel: {channel_data.get('channel_id')}")
                result['error_videos'] = 'No videos returned from API'
            return result
            
        except YouTubeAPIError as e:
            msg = f"YouTubeAPIError: {str(e)} for channel: {channel_data.get('channel_id')}"
            debug_log(msg)
            return {'video_id': [], 'error_videos': str(e), 'debug_logs': [msg]}
        except Exception as e:
            msg = f"Exception: {str(e)} for channel: {channel_data.get('channel_id')}"
            debug_log(msg)
            return {'video_id': [], 'error_videos': str(e), 'debug_logs': [msg]}

    def _process_video_details(self, channel_data: Dict) -> None:
        """
        Process video details and handle errors for individual videos.
        
        Args:
            channel_data: Channel data dictionary with videos
        """
        if 'video_id' in channel_data and isinstance(channel_data['video_id'], list):
            # Check if any video has an error
            for video in channel_data['video_id']:
                video_id = video.get('video_id')
                if not video_id:
                    continue
                
                try:
                    # Try to get video details if the API supports it
                    if hasattr(self.api, 'get_video_info'):
                        details = self.api.get_video_info(video_id)
                        # Update video with details
                        if details:
                            video.update(details)
                except YouTubeAPIError as e:
                    # If the video is unavailable, mark it with error info
                    if e.status_code == 404 or e.error_type == "videoNotFound":
                        video['error'] = f"Video unavailable: {str(e)}"
                        debug_log(f"Marked video {video_id} as unavailable")
                    else:
                        # For other errors, also record them
                        video['error'] = f"Error fetching video: {str(e)}"
                        debug_log(f"Error fetching details for video {video_id}: {str(e)}")

    def get_video_details_batch(self, video_ids: List[str]) -> Dict:
        """
        Get detailed information about a batch of videos.
        
        Args:
            video_ids: List of video IDs
            
        Returns:
            dict: Video details response
        """
        if not video_ids:
            return None
            
        debug_log(f"Getting details for {len(video_ids)} videos in batch")
        
        try:
            # Request video details
            return self.api.get_video_details_batch(video_ids)
        except Exception as e:
            debug_log(f"Error getting video details batch: {str(e)}")
            raise

    def refresh_video_details(self, channel_data: Dict) -> Dict:
        """
        Refresh video details for videos in the channel data.
        
        Args:
            channel_data: Dictionary containing channel data with videos
            
        Returns:
            dict: Updated channel data with refreshed video details
        """
        if not channel_data or 'video_id' not in channel_data or not isinstance(channel_data['video_id'], list):
            return channel_data
            
        debug_log(f"Refreshing video details for {len(channel_data['video_id'])} videos")
        
        try:
            # Extract all video IDs from existing data
            all_video_ids = []
            for video in channel_data.get('video_id', []):
                if isinstance(video, dict) and 'video_id' in video:
                    all_video_ids.append(video['video_id'])
            
            debug_log(f"Extracted {len(all_video_ids)} video IDs for refresh")
                    
            # Process in batches of 50 (YouTube API limit)
            batch_size = 50
            videos_updated = 0
            
            for i in range(0, len(all_video_ids), batch_size):
                batch = all_video_ids[i:i + batch_size]
                debug_log(f"Processing batch {i//batch_size + 1} with {len(batch)} videos")
                
                # Get details for this batch of videos
                details_response = self.get_video_details_batch(batch)
                
                if details_response and 'items' in details_response:
                    # Create lookup map for efficiency
                    details_map = {}
                    for item in details_response['items']:
                        details_map[item['id']] = item
                    
                    debug_log(f"Received details for {len(details_map)} videos")
                    
                    # Update videos with details
                    for video in channel_data['video_id']:
                        if 'video_id' in video and video['video_id'] in details_map:
                            item = details_map[video['video_id']]
                            videos_updated += 1
                            
                            # Update from snippet
                            if 'snippet' in item:
                                for field in ['title', 'description', 'publishedAt']:
                                    if field in item['snippet']:
                                        # Convert publishedAt to published_at to match our schema
                                        dest_field = 'published_at' if field == 'publishedAt' else field
                                        video[dest_field] = item['snippet'][field]
                                
                                # Ensure we have thumbnails
                                if 'thumbnails' in item['snippet']:
                                    video['thumbnails'] = item['snippet']['thumbnails']
                                    
                                    # Also add flattened thumbnail_url for simpler access
                                    if 'medium' in item['snippet']['thumbnails']:
                                        video['thumbnail_url'] = item['snippet']['thumbnails']['medium'].get('url', '')
                                    elif 'default' in item['snippet']['thumbnails']:
                                        video['thumbnail_url'] = item['snippet']['thumbnails']['default'].get('url', '')
                            
                            # Update from statistics - ensure we always have string values
                            if 'statistics' in item:
                                # Keep original values as fallback
                                orig_views = video.get('views', '0')
                                orig_likes = video.get('likes', '0')
                                orig_comment_count = video.get('comment_count', '0')
                                
                                # Update with new values, falling back to original if not present
                                video['views'] = str(item['statistics'].get('viewCount', orig_views))
                                video['likes'] = str(item['statistics'].get('likeCount', orig_likes))
                                video['comment_count'] = str(item['statistics'].get('commentCount', orig_comment_count))
                                
                                # Also store statistics object for consistency with new channel flow
                                video['statistics'] = item['statistics']
                                
                                # Log for debugging
                                debug_log(f"Updated video {video['video_id']} with stats: views={video['views']}, likes={video['likes']}, comments={video['comment_count']}")
            
            debug_log(f"Successfully updated details for {videos_updated}/{len(all_video_ids)} videos")
            
            # Apply video processor to ensure consistent data structure
            from src.utils.video_formatter import fix_missing_views
            from src.utils.video_processor import process_video_data
            
            # First ensure views data is properly set
            channel_data['video_id'] = fix_missing_views(channel_data['video_id'])
            
            # Then process all video data consistently
            channel_data['video_id'] = process_video_data(channel_data['video_id'])
            
            return channel_data
            
        except Exception as e:
            debug_log(f"Error refreshing video details: {str(e)}")
            channel_data['error_videos'] = f"Error refreshing videos: {str(e)}"
            return channel_data
