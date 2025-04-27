"""
YouTube API client for video-related operations.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime

import googleapiclient.errors

from src.utils.helpers import debug_log
from src.api.youtube.base import YouTubeBaseClient

class VideoClient(YouTubeBaseClient):
    """YouTube Data API client focused on video operations"""
    
    def get_channel_videos(self, channel_info: Dict[str, Any], max_videos: int = 0) -> Optional[Dict[str, Any]]:
        """
        Get videos from a channel's uploads playlist
        
        Args:
            channel_info: Dictionary containing channel information
            max_videos: Maximum number of videos to fetch (0 for all available videos)
        
        Returns:
            Updated channel_info dictionary with video data or None if failed
        """
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return None
        
        playlist_id = channel_info.get('playlist_id')
        if not playlist_id:
            st.error("No uploads playlist ID found in channel info.")
            return None
        
        # Determine how many videos to fetch
        total_channel_videos = int(channel_info.get('total_videos', '0'))
        if max_videos <= 0 or max_videos > total_channel_videos:
            max_videos = total_channel_videos
            target_text = "all available"
        else:
            target_text = str(max_videos)
            
        debug_log(f"Fetching {target_text} videos for channel: {channel_info.get('channel_name')}")
        
        try:
            # Request videos from the uploads playlist
            videos = []
            next_page_token = None
            videos_processed = 0
            unavailable_videos = 0
            videos_with_comments_disabled = 0
            total_comment_count = 0
            videos_with_comments = 0
            
            # Progress bar for video fetching
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            while videos_processed < max_videos:
                # Check cache first
                cache_key = f"playlist_{playlist_id}_{next_page_token}"
                playlist_response = self.get_from_cache(cache_key)
                
                if not playlist_response:
                    # Make API request for playlist items
                    playlist_request = self.youtube.playlistItems().list(
                        part="snippet,contentDetails",
                        playlistId=playlist_id,
                        maxResults=50,  # Maximum allowed by the API per page
                        pageToken=next_page_token
                    )
                    playlist_response = playlist_request.execute()
                    
                    # Store in cache
                    self.store_in_cache(cache_key, playlist_response)
                else:
                    debug_log(f"Using cached playlist page for token: {next_page_token}")
                
                # Check if we got any items
                if not playlist_response.get('items'):
                    debug_log("No videos found in this page of results.")
                    break
                
                # Process video items
                items_to_process = min(len(playlist_response['items']), max_videos - videos_processed)
                
                # Collect video IDs for batch processing
                video_ids = []
                for i in range(items_to_process):
                    video_id = playlist_response['items'][i]['contentDetails']['videoId']
                    video_ids.append(video_id)
                
                # Fetch video details in batches
                video_details = self.get_videos_details(video_ids)
                
                # Count how many videos we actually received details for
                received_details_count = len(video_details)
                if received_details_count < len(video_ids):
                    # Some videos might be private or deleted
                    unavailable_videos += (len(video_ids) - received_details_count)
                    debug_log(f"Some videos unavailable: requested {len(video_ids)} details, got {received_details_count}")
                
                # Add video details to the list
                for i in range(items_to_process):
                    if i >= len(playlist_response['items']):
                        break
                        
                    video_item = playlist_response['items'][i]
                    video_id = video_item['contentDetails']['videoId']
                    
                    # Get the matching video details
                    video_detail = None
                    for detail in video_details:
                        if detail.get('id') == video_id:
                            video_detail = detail
                            break
                    
                    if video_detail:
                        # Get current timestamp for fetched_at field
                        current_time = datetime.now().isoformat()
                        
                        # Basic video info from playlist item
                        video_info = {
                            'video_id': video_id,
                            'title': video_item['snippet']['title'],
                            'published_at': video_item['snippet']['publishedAt'],
                            'published_date': video_item['snippet']['publishedAt'].split('T')[0],
                            'video_description': video_detail.get('snippet', {}).get('description', ''),
                            'views': video_detail.get('statistics', {}).get('viewCount', '0'),
                            'likes': video_detail.get('statistics', {}).get('likeCount', '0'),
                            'duration': video_detail.get('contentDetails', {}).get('duration', 'PT0S'),
                            'caption_status': video_detail.get('contentDetails', {}).get('caption', 'none'),
                            'comments': [],  # Will be populated if fetch_comments is called
                            
                            # New fields extracted from video details
                            'dislike_count': video_detail.get('statistics', {}).get('dislikeCount', '0'),
                            'favorite_count': video_detail.get('statistics', {}).get('favoriteCount', '0'),
                            
                            # Content details fields
                            'dimension': video_detail.get('contentDetails', {}).get('dimension', '2d'),
                            'definition': video_detail.get('contentDetails', {}).get('definition', 'sd'),
                            'licensed_content': video_detail.get('contentDetails', {}).get('licensedContent', False),
                            'projection': video_detail.get('contentDetails', {}).get('projection', 'rectangular'),
                            
                            # Status fields
                            'privacy_status': video_detail.get('status', {}).get('privacyStatus', 'public'),
                            'license': video_detail.get('status', {}).get('license', 'youtube'),
                            'embeddable': video_detail.get('status', {}).get('embeddable', True),
                            'public_stats_viewable': video_detail.get('status', {}).get('publicStatsViewable', True),
                            'made_for_kids': video_detail.get('status', {}).get('madeForKids', False),
                            
                            # Thumbnail URLs
                            'thumbnail_default': video_detail.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url', ''),
                            'thumbnail_medium': video_detail.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url', ''),
                            'thumbnail_high': video_detail.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url', video_item['snippet']['thumbnails']['high']['url']),
                            
                            # Category and tags
                            'category_id': video_detail.get('snippet', {}).get('categoryId', ''),
                            'tags': video_detail.get('snippet', {}).get('tags', []),
                            
                            # Other metadata
                            'live_broadcast_content': video_detail.get('snippet', {}).get('liveBroadcastContent', 'none'),
                            'fetched_at': current_time,
                            'updated_at': current_time
                        }
                        
                        # Check if we can get comment count from the statistics
                        video_statistics = video_detail.get('statistics', {})
                        if 'commentCount' in video_statistics:
                            # Store the comment count separately from actual comments
                            comment_count = int(video_statistics['commentCount'])
                            video_info['comment_count'] = comment_count
                            total_comment_count += comment_count
                            if comment_count > 0:
                                videos_with_comments += 1
                            debug_log(f"Video '{video_info['title']}' has {comment_count} comments according to statistics")
                        else:
                            # If commentCount isn't in the statistics, comments are disabled
                            video_info['comments_disabled'] = True
                            video_info['comment_count'] = 0
                            videos_with_comments_disabled += 1
                            debug_log(f"Video '{video_info['title']}' has comments disabled (no commentCount in statistics)")
                        
                        videos.append(video_info)
                    else:
                        # Video might be private or deleted
                        debug_log(f"Video details not available for {video_id} (may be private or deleted)")
                        unavailable_videos += 1
                    
                    # Update progress
                    videos_processed += 1
                    progress = min(videos_processed / max_videos, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Fetched {len(videos)} of {max_videos} videos (processed {videos_processed}, {unavailable_videos} unavailable)...")
                
                # Check if there are more videos to fetch
                if 'nextPageToken' in playlist_response and videos_processed < max_videos:
                    next_page_token = playlist_response['nextPageToken']
                else:
                    break
            
            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()
            
            # Update channel info with video data and stats
            channel_info['video_id'] = videos
            channel_info['videos_fetched'] = len(videos)
            channel_info['videos_unavailable'] = unavailable_videos
            channel_info['videos_with_comments_disabled'] = videos_with_comments_disabled
            
            # Add comment count statistics from the video fetch
            channel_info['comment_counts'] = {
                'total_comment_count': total_comment_count,
                'videos_with_comments': videos_with_comments,
                'videos_with_comments_disabled': videos_with_comments_disabled
            }
            
            # If we couldn't fetch as many as expected, add a note
            if unavailable_videos > 0:
                st.info(f"Note: {unavailable_videos} videos were unavailable (may be private, deleted, or restricted).")
            
            if videos_with_comments_disabled > 0:
                st.info(f"Note: {videos_with_comments_disabled} videos have comments disabled.")
                
            debug_log(f"Fetched {len(videos)} videos for channel: {channel_info.get('channel_name')} ({unavailable_videos} unavailable)")
            debug_log(f"Comment counts from video stats: {total_comment_count} total comments across {videos_with_comments} videos")
            
            return channel_info
            
        except Exception as e:
            self._handle_api_error(e, "get_channel_videos")
            return None
    
    def get_videos_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed information for a batch of videos by their IDs
        
        Args:
            video_ids: List of YouTube video IDs to fetch details for
            
        Returns:
            List of video detail dictionaries
        """
        if not video_ids:
            return []
        
        try:
            # Join IDs with commas for the API request
            video_ids_str = ','.join(video_ids)
            
            # Check cache first
            cache_key = f"video_details_{video_ids_str}"
            cached_data = self.get_from_cache(cache_key)
            if cached_data:
                debug_log(f"Using cached video details for {len(video_ids)} videos")
                return cached_data
            
            # Request video details with more parts to get additional fields
            video_request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics,status,topicDetails,player,liveStreamingDetails",
                id=video_ids_str
            )
            video_response = video_request.execute()
            
            # Store in cache
            result = video_response.get('items', [])
            self.store_in_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            self._handle_api_error(e, "get_videos_details")
            return []