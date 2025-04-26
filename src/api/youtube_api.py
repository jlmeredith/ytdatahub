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
        
        # Use the improved channel ID validation that returns a tuple
        is_valid, validated_channel_id = validate_channel_id(channel_id)
        
        if not is_valid:
            # Check if we need to resolve a custom URL or handle
            if validated_channel_id.startswith("resolve:"):
                # Extract the part after "resolve:"
                to_resolve = validated_channel_id[8:]
                debug_log(f"Need to resolve custom URL or handle: {to_resolve}")
                
                # Use the resolve method to get the actual channel ID
                resolved_id = self.resolve_custom_channel_url(to_resolve)
                
                if resolved_id:
                    debug_log(f"Successfully resolved to channel ID: {resolved_id}")
                    validated_channel_id = resolved_id
                    is_valid = True
                else:
                    st.error(f"Could not resolve '{to_resolve}' to a valid channel ID. Please use a direct channel ID or URL.")
                    return None
            else:
                st.error("Invalid channel ID format. Please enter a valid YouTube channel ID or URL.")
                return None
        
        debug_log(f"Fetching channel info for: {validated_channel_id}")
        
        try:
            # Check cache first
            cache_key = f"channel_info_{validated_channel_id}"
            if cache_key in st.session_state.api_cache:
                debug_log(f"Using cached channel info for: {validated_channel_id}")
                return st.session_state.api_cache[cache_key]
            
            # Request channel information
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                id=validated_channel_id
            )
            response = request.execute()
            
            # Check if channel was found
            if not response['items']:
                st.error(f"Channel with ID '{validated_channel_id}' not found. Please check the channel ID.")
                return None
            
            # Extract relevant information
            channel_data = response['items'][0]
            uploads_playlist_id = channel_data['contentDetails']['relatedPlaylists']['uploads']
            
            # Format channel info
            channel_info = {
                'channel_id': validated_channel_id,
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
                playlist_response = None
                
                if cache_key in st.session_state.api_cache:
                    debug_log(f"Using cached playlist page for token: {next_page_token}")
                    playlist_response = st.session_state.api_cache[cache_key]
                else:
                    # Make API request for playlist items
                    playlist_request = self.youtube.playlistItems().list(
                        part="snippet,contentDetails",
                        playlistId=playlist_id,
                        maxResults=50,  # Maximum allowed by the API per page
                        pageToken=next_page_token
                    )
                    playlist_response = playlist_request.execute()
                    
                    # Store in cache
                    st.session_state.api_cache[cache_key] = playlist_response
                
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
                video_details = self._get_videos_details(video_ids)
                
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
                            'comments': []  # Will be populated if fetch_comments is called
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
        """
        Get comments for each video in the channel with optimal quota usage.
        
        This method efficiently retrieves comments by:
        1. Using maxResults=100 to minimize API calls
        2. Implementing pagination to retrieve more comments per video if needed
        3. Checking for disabled comments before making API calls
        4. Using ETag caching for repeat retrievals
        5. Properly handling and including replies
        
        Args:
            channel_info: Dictionary containing channel information with videos
            max_comments_per_video: Maximum number of comments to fetch per video (0 to skip)
            
        Returns:
            Updated channel_info dictionary with comment data or None if failed
        """
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return None
        
        videos = channel_info.get('video_id', [])
        if not videos:
            st.warning("No videos found to fetch comments for.")
            return channel_info
            
        # Zero max_comments means skip comment fetching
        if max_comments_per_video <= 0:
            debug_log("COMMENT DEBUG: max_comments_per_video is 0 or negative, skipping comment fetching")
            return channel_info
        
        debug_log(f"COMMENT DEBUG: Starting to fetch comments for {len(videos)} videos, max {max_comments_per_video} per video")
        st.info("ℹ️ Fetching comments. This may take some time depending on the number of videos.")
        
        # Make sure the API cache is initialized
        if 'api_cache' not in st.session_state:
            st.session_state.api_cache = {}
        # Initialize ETag cache if not present
        if 'etag_cache' not in st.session_state:
            st.session_state.etag_cache = {}
        
        try:
            # Progress tracking
            total_videos = len(videos)
            progress_bar = st.progress(0)
            status_text = st.empty()
            comments_fetched_total = 0
            videos_with_comments = 0
            videos_with_disabled_comments = 0
            videos_with_errors = 0
            
            # Process each video
            for i, video in enumerate(videos):
                video_id = video.get('video_id')
                video_title = video.get('title', 'Unknown')
                
                debug_log(f"COMMENT DEBUG: Processing video {i+1}/{total_videos}: '{video_title}' (ID: {video_id})")
                
                # Update progress
                progress = (i + 1) / total_videos
                progress_bar.progress(progress)
                status_text.text(f"Fetching comments for video {i+1} of {total_videos}...")
                
                # Check cache first
                cache_key = f"comments_{video_id}"
                
                if cache_key in st.session_state.api_cache:
                    debug_log(f"COMMENT DEBUG: Using cached comments for video: {video_id}")
                    cached_comments = st.session_state.api_cache[cache_key]
                    video['comments'] = cached_comments
                    debug_log(f"COMMENT DEBUG: Retrieved {len(cached_comments)} comments from cache for '{video_title}'")
                    comments_fetched_total += len(cached_comments)
                    if len(cached_comments) > 0:
                        videos_with_comments += 1
                    continue
                
                # If not in cache, fetch from API
                debug_log(f"COMMENT DEBUG: No cache found, fetching comments from API for video: {video_id}")
                
                # Always initialize comments to an empty array
                video['comments'] = []
                
                try:
                    # First verify that comments are enabled for this video by checking video.statistics.commentCount
                    # This saves quota by avoiding unnecessary commentThreads.list calls
                    video_details_request = self.youtube.videos().list(
                        part="statistics",
                        id=video_id
                    )
                    video_details_response = video_details_request.execute()
                    
                    if (not video_details_response.get('items') or 
                        'statistics' not in video_details_response['items'][0]):
                        debug_log(f"COMMENT DEBUG: Video '{video_title}' missing statistics")
                        videos_with_errors += 1
                        continue
                        
                    # First check if comments are disabled via the statistics
                    # The commentCount field might not exist if comments are disabled
                    if 'commentCount' not in video_details_response['items'][0]['statistics']:
                        debug_log(f"COMMENT DEBUG: Video '{video_title}' has comments disabled (no commentCount in statistics)")
                        video['comments_disabled'] = True
                        videos_with_disabled_comments += 1
                        continue
                        
                    # If commentCount is 0, don't waste an API call trying to fetch comments
                    comment_count = int(video_details_response['items'][0]['statistics']['commentCount'])
                    if comment_count == 0:
                        debug_log(f"COMMENT DEBUG: Video '{video_title}' has 0 comments according to statistics")
                        video['comments'] = []
                        continue
                        
                    debug_log(f"COMMENT DEBUG: Video '{video_title}' has {comment_count} comments according to statistics")
                    
                    # Now retrieve comments with pagination to get up to max_comments_per_video
                    comments = []
                    next_page_token = None
                    comments_to_fetch = max_comments_per_video
                    
                    # Check if we have an ETag for this video's comments
                    etag_key = f"etag_comments_{video_id}"
                    etag = st.session_state.etag_cache.get(etag_key)
                    
                    # Continue fetching until we have enough comments or run out of pages
                    while comments_to_fetch > 0:
                        # Request can fetch up to 100 comments at a time
                        current_fetch_count = min(100, comments_to_fetch)
                        
                        # Create base request
                        comments_request = self.youtube.commentThreads().list(
                            part="snippet,replies",  # Get both top-level comments and their replies
                            videoId=video_id,
                            maxResults=current_fetch_count,
                            textFormat="plainText",   
                            order="relevance"         
                        )
                        
                        # Add page token if we're paginating
                        if next_page_token:
                            comments_request.uri = comments_request.uri + "&pageToken=" + next_page_token
                        
                        # Add ETag for conditional request if available
                        if etag:
                            debug_log(f"COMMENT DEBUG: Using ETag for video '{video_title}': {etag}")
                            comments_request.headers['If-None-Match'] = etag
                        
                        debug_log(f"COMMENT DEBUG: Sending API request for comments on video '{video_title}' (max: {current_fetch_count})")
                        comments_response = comments_request.execute()
                        
                        # Store new ETag if present
                        if 'etag' in comments_response:
                            st.session_state.etag_cache[etag_key] = comments_response['etag']
                            debug_log(f"COMMENT DEBUG: Stored new ETag for video '{video_title}': {comments_response['etag']}")
                        
                        # Log detailed API response for debugging
                        debug_log(f"COMMENT DEBUG: Raw API response keys: {list(comments_response.keys())}")
                        
                        # Extract comment data
                        response_items = comments_response.get('items', [])
                        comments_fetched_this_page = len(response_items)
                        debug_log(f"COMMENT DEBUG: Response contains {comments_fetched_this_page} comments for video '{video_title}'")
                        
                        if not response_items:
                            debug_log(f"COMMENT DEBUG: No comments found in API response for video '{video_title}'")
                            break
                        
                        # Process comments from this page
                        for item in response_items:
                            try:
                                comment = item['snippet']['topLevelComment']['snippet']
                                comment_data = {
                                    'comment_id': item['id'],
                                    'comment_text': comment['textDisplay'],
                                    'comment_author': comment['authorDisplayName'],
                                    'comment_published_at': comment['publishedAt'],
                                    'like_count': comment.get('likeCount', 0)
                                }
                                comments.append(comment_data)
                                
                                # Also check for replies if present
                                if 'replies' in item and item['replies']['comments']:
                                    for reply in item['replies']['comments']:
                                        reply_snippet = reply['snippet']
                                        reply_data = {
                                            'comment_id': reply['id'],
                                            'comment_text': f"[REPLY] {reply_snippet['textDisplay']}",
                                            'comment_author': reply_snippet['authorDisplayName'],
                                            'comment_published_at': reply_snippet['publishedAt'],
                                            'like_count': reply_snippet.get('likeCount', 0),
                                            'parent_id': item['id']
                                        }
                                        comments.append(reply_data)
                            except KeyError as ke:
                                debug_log(f"COMMENT DEBUG: KeyError accessing comment structure: {ke}. Item structure: {item}")
                                continue
                        
                        # Update remaining comments to fetch
                        comments_to_fetch -= comments_fetched_this_page
                        
                        # Check if there are more pages of comments
                        if 'nextPageToken' in comments_response and comments_to_fetch > 0:
                            next_page_token = comments_response['nextPageToken']
                            debug_log(f"COMMENT DEBUG: More comments available, using pageToken: {next_page_token}")
                        else:
                            debug_log(f"COMMENT DEBUG: No more comment pages or reached max limit for video '{video_title}'")
                            break
                    
                    # Add comments to the video
                    video['comments'] = comments
                    debug_log(f"COMMENT DEBUG: Added {len(comments)} comments to video '{video_title}'")
                    
                    # Update statistics
                    comments_fetched_total += len(comments)
                    if len(comments) > 0:
                        videos_with_comments += 1
                    
                    # Store in cache
                    st.session_state.api_cache[cache_key] = comments
                    
                except googleapiclient.errors.HttpError as e:
                    error_text = str(e)
                    # Comments might be disabled for the video
                    if 'commentsDisabled' in error_text:
                        debug_log(f"COMMENT DEBUG: Comments are disabled for video: '{video_title}' (ID: {video_id})")
                        videos_with_disabled_comments += 1
                    elif 'quotaExceeded' in error_text:
                        debug_log(f"COMMENT DEBUG: API quota exceeded when fetching comments for '{video_title}'")
                        st.warning("⚠️ YouTube API quota exceeded. Please try again later or use a different API key.")
                        videos_with_errors += 1
                        # Don't continue trying if we've hit quota limits
                        break
                    else:
                        debug_log(f"COMMENT DEBUG: Error fetching comments for video '{video_title}' (ID: {video_id}): {error_text}")
                        videos_with_errors += 1
            
            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()
            
            # Final debug summary
            debug_log(f"COMMENT DEBUG: ===== COMMENT FETCHING SUMMARY =====")
            debug_log(f"COMMENT DEBUG: Total videos processed: {total_videos}")
            debug_log(f"COMMENT DEBUG: Videos with comments: {videos_with_comments}")
            debug_log(f"COMMENT DEBUG: Videos with disabled comments: {videos_with_disabled_comments}")
            debug_log(f"COMMENT DEBUG: Videos with errors: {videos_with_errors}")
            debug_log(f"COMMENT DEBUG: Total comments fetched: {comments_fetched_total}")
            debug_log(f"COMMENT DEBUG: Average comments per video: {comments_fetched_total/total_videos if total_videos > 0 else 0:.2f}")
            
            # Add summary to channel_info for easy access
            channel_info['comment_stats'] = {
                'total_comments': comments_fetched_total,
                'videos_with_comments': videos_with_comments,
                'videos_with_disabled_comments': videos_with_disabled_comments,
                'videos_with_errors': videos_with_errors
            }
            
            # Show summary to user
            if comments_fetched_total > 0:
                st.success(f"✅ Successfully fetched {comments_fetched_total} comments across {videos_with_comments} videos")
            else:
                if videos_with_disabled_comments > 0:
                    st.info(f"ℹ️ No comments fetched. {videos_with_disabled_comments} videos have comments disabled.")
                elif videos_with_errors > 0:
                    st.warning(f"⚠️ No comments fetched. Encountered errors on {videos_with_errors} videos.")
                else:
                    st.info("ℹ️ No comments found for any of the videos.")
            
            return channel_info
            
        except Exception as e:
            st.error(f"Error fetching video comments: {str(e)}")
            debug_log(f"COMMENT DEBUG: CRITICAL ERROR in get_video_comments: {str(e)}", e)
            # Try to return partial data if available
            return channel_info

    def resolve_custom_channel_url(self, custom_url_or_handle: str) -> Optional[str]:
        """
        Resolve a custom URL or handle (@username) to a channel ID.
        
        Args:
            custom_url_or_handle (str): The custom URL, handle, or username to resolve
            
        Returns:
            str or None: The resolved channel ID or None if resolution failed
        """
        if not self.is_initialized():
            st.error("YouTube API client not initialized. Please check your API key.")
            return None
            
        debug_log(f"Resolving custom URL or handle: {custom_url_or_handle}")
        
        # Clean up input
        query = custom_url_or_handle.strip()
        
        # Remove 'resolve:' prefix if present (internal format)
        if query.startswith('resolve:'):
            query = query[8:].strip()  # Fixed typo: was 'trip()'
        
        # Process based on URL format
        if query.startswith('@'):
            handle = query
            debug_log(f"Processing as channel handle: {handle}")
        elif '/' in query:
            # Extract the last part of the URL
            parts = query.strip('/').split('/')
            handle = parts[-1]
            if handle.startswith('@'):
                debug_log(f"Extracted handle from URL: {handle}")
            else:
                handle = '@' + handle
                debug_log(f"Converted URL part to handle format: {handle}")
        else:
            # If it doesn't have @ or /, add @ to make it a handle format
            handle = '@' + query
            debug_log(f"Added @ prefix to make it a handle: {handle}")
            
        try:
            # Try to resolve handle or custom URL using search endpoint
            search_request = self.youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=5
            )
            search_response = search_request.execute()
            
            # Check if we got any results
            if not search_response.get('items'):
                debug_log(f"No channels found for query: {handle}")
                return None
                
            # Find the best match by comparing titles and custom URLs
            best_match = None
            
            for item in search_response['items']:
                channel_id = item['id']['channelId']
                channel_title = item['snippet']['title']
                
                # Get more details about the channel to check custom URL
                channel_request = self.youtube.channels().list(
                    part="snippet",
                    id=channel_id
                )
                channel_response = channel_request.execute()
                
                if not channel_response.get('items'):
                    continue
                    
                channel_data = channel_response['items'][0]
                
                # Check if this is an exact match for handle or custom URL
                # CustomUrl field might not be available in all channel data
                channel_custom_url = channel_data['snippet'].get('customUrl', '')
                
                debug_log(f"Checking channel: ID={channel_id}, title='{channel_title}', customUrl='{channel_custom_url}'")
                
                # Match priority:
                # 1. Exact match on customUrl (without @)
                # 2. If we're searching for a handle (@username), match on username
                # 3. Exact match on title
                # 4. First result if nothing else matches
                
                # Clean handle for comparison by removing @ if present
                clean_handle = handle[1:] if handle.startswith('@') else handle
                
                if channel_custom_url and (
                    channel_custom_url.lower() == clean_handle.lower() or 
                    channel_custom_url.lower() == handle.lower()
                ):
                    debug_log(f"Found exact match on customUrl: {channel_custom_url}")
                    best_match = channel_id
                    break
                elif handle.startswith('@') and clean_handle.lower() in channel_custom_url.lower():
                    debug_log(f"Found handle match: @{clean_handle} in {channel_custom_url}")
                    best_match = channel_id
                    # Continue looking for exact matches
                elif clean_handle.lower() in channel_title.lower():
                    debug_log(f"Found channel with matching title for handle {handle}: {channel_id}")
                    if not best_match:  # Only set if we don't have a better match
                        best_match = channel_id
                elif not best_match:
                    debug_log(f"Setting initial match: {channel_title} ({channel_id})")
                    best_match = channel_id
            
            # Return the best match if found
            if best_match:
                debug_log(f"Resolved {query} to channel ID: {best_match}")
                return best_match
            
            # If we got items but didn't find a good match, use the first result
            if search_response.get('items'):
                first_result = search_response.get('items')[0]
                channel_id = first_result['id']['channelId']
                debug_log(f"No exact match found, using first search result for {handle}: {channel_id}")
                return channel_id
                
            debug_log(f"Failed to find a good match for: {query}")
            return None
            
        except googleapiclient.errors.HttpError as e:
            st.error(f"YouTube API error: {str(e)}")
            debug_log(f"API error in resolve_custom_channel_url: {str(e)}", e)
            return None
        except Exception as e:
            st.error(f"Error resolving custom URL: {str(e)}")
            debug_log(f"Exception in resolve_custom_channel_url: {str(e)}", e)
            return None