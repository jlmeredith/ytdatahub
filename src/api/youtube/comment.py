"""
YouTube API client for comment-related operations.
"""
from typing import Dict, List, Any, Optional
import sys
import googleapiclient.errors

from src.utils.helpers import debug_log
from src.api.youtube.base import YouTubeBaseClient

# Try to import streamlit but don't fail if it's not available
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    STREAMLIT_AVAILABLE = False
    # Create a dummy st module for compatibility
    class DummySt:
        def progress(self, *args, **kwargs):
            return DummyComponent()
        
        def empty(self, *args, **kwargs):
            return DummyComponent()
            
        def warning(self, message):
            print(f"WARNING: {message}")
            
        def error(self, message):
            print(f"ERROR: {message}")
            
        def info(self, message):
            print(f"INFO: {message}")
            
        @property
        def session_state(self):
            if not hasattr(self, '_session_state'):
                self._session_state = {}
            return self._session_state
            
    class DummyComponent:
        def progress(self, *args, **kwargs):
            pass
            
        def text(self, *args, **kwargs):
            pass
            
    st = DummySt()

class CommentClient(YouTubeBaseClient):
    """YouTube Data API client focused on comment operations"""
    
    def get_video_comments(self, channel_info: Dict[str, Any], max_comments_per_video: int = 10, max_replies_per_comment: int = 2, page_token: str = None, optimize_quota: bool = False) -> Optional[Dict[str, Any]]:
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
            max_comments_per_video: Maximum number of top-level comments to fetch per video (0 to skip)
            max_replies_per_comment: Maximum number of replies to fetch per top-level comment
            page_token: Token for pagination support across multiple calls
            optimize_quota: Whether to optimize quota usage (currently unused)
            
        Returns:
            Updated channel_info dictionary with comment data or None if failed
        """
        # Enhanced debugging at the start
        print(f"🔍 [DEBUG] get_video_comments called with:")
        print(f"  - max_comments_per_video: {max_comments_per_video}")
        print(f"  - max_replies_per_comment: {max_replies_per_comment}")
        print(f"  - page_token: {page_token}")
        print(f"  - optimize_quota: {optimize_quota}")
        print(f"  - API client initialized: {self.is_initialized()}")
        print(f"  - API key present: {'Yes' if self.api_key else 'No'}")
        
        videos = channel_info.get('video_id', [])
        debug_log(f"[COMMENT FETCH ENTRY] get_video_comments called. videos type={type(videos)}, len={len(videos)}, sample={videos[0] if videos else 'EMPTY'}")
        print(f"🔍 [DEBUG] Videos to process: {len(videos)}")
        
        if not self.is_initialized():
            error_msg = "YouTube API client not initialized. Please check your API key."
            print(f"❌ [DEBUG] {error_msg}")
            if hasattr(st, 'error'):
                st.error(error_msg)
            return None
        
        # Diagnostic: print first 3 video dicts as seen by comment fetching
        for i, v in enumerate(videos[:3]):
            debug_log(f"[COMMENT FETCH DIAG] Video {i+1}: keys={list(v.keys())}, video_id={v.get('video_id')}, id={v.get('id')}, sample={str(v)[:300]}")
        
        if not videos:
            print("WARNING: No videos found to fetch comments for.")
            if STREAMLIT_AVAILABLE:
                st.warning("No videos found to fetch comments for.")
            return channel_info
            
        # Zero max_comments means skip comment fetching
        if max_comments_per_video <= 0:
            debug_log("COMMENT DEBUG: max_comments_per_video is 0 or negative, skipping comment fetching")
            return channel_info
        
        debug_log(f"COMMENT DEBUG: Starting to fetch comments for {len(videos)} videos, max {max_comments_per_video} per video")
        print(f"INFO: Fetching comments for {len(videos)} videos, max {max_comments_per_video} per video")
        if STREAMLIT_AVAILABLE:
            st.info("ℹ️ Fetching comments. This may take some time depending on the number of videos.")
        
        # Initialize caches
        self.ensure_api_cache()
        if STREAMLIT_AVAILABLE:
            if 'etag_cache' not in st.session_state:
                st.session_state.etag_cache = {}
        else:
            # Use a dummy cache when Streamlit isn't available
            if not hasattr(self, '_dummy_etag_cache'):
                self._dummy_etag_cache = {}
            # Attach to st for API compatibility in the rest of the code
            st.session_state = getattr(st, 'session_state', {})
            st.session_state.etag_cache = self._dummy_etag_cache
        
        try:
            # Repair video_id for each video dict if missing
            repaired_videos = []
            for i, v in enumerate(videos):
                vid = v.get('video_id')
                if not vid:
                    # Try to extract from other fields
                    vid = (
                        v.get('id') if isinstance(v.get('id'), str) else None or
                        (v.get('id', {}).get('videoId') if isinstance(v.get('id'), dict) else None) or
                        (v.get('contentDetails', {}).get('videoId') if isinstance(v.get('contentDetails'), dict) else None) or
                        (v.get('snippet', {}).get('resourceId', {}).get('videoId') if isinstance(v.get('snippet', {}).get('resourceId'), dict) else None)
                    )
                    if vid:
                        v['video_id'] = vid
                        debug_log(f"[COMMENT FETCH REPAIR] Set video_id for video {i+1} from alternate field: {vid}")
                    else:
                        debug_log(f"[COMMENT FETCH REPAIR] Skipping video {i+1} with no valid video_id. Keys: {list(v.keys())}")
                        continue
                repaired_videos.append(v)
            videos = repaired_videos
            
            # Progress tracking
            total_videos = len(videos)
            comments_fetched_total = 0
            videos_with_comments = 0
            videos_with_disabled_comments = 0
            videos_with_errors = 0
            
            # Create progress tracking elements if Streamlit is available
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process each video
            for i, video in enumerate(videos):
                vid_id = video.get('video_id') if isinstance(video, dict) else video
                debug_log(f"[COMMENT FETCH] Fetching comments for video {i+1}/{len(videos)}: video_id={vid_id}")
                video_title = video.get('title', 'Unknown')
                
                debug_log(f"COMMENT DEBUG: Processing video {i+1}/{total_videos}: '{video_title}' (ID: {vid_id})")
                
                # Update progress
                progress = (i + 1) / total_videos
                if STREAMLIT_AVAILABLE:
                    progress_bar.progress(progress)
                    status_text.text(f"Fetching comments for video {i+1} of {total_videos}...")
                if i % 5 == 0 or i == len(videos) - 1:  # Print progress every 5 videos or on the last video
                    print(f"Progress: {i+1}/{total_videos} videos processed ({int(progress*100)}%)")
                
                # Check cache first
                cache_key = f"comments_{vid_id}"
                cached_comments = self.get_from_cache(cache_key)
                
                if cached_comments is not None:
                    debug_log(f"COMMENT DEBUG: Using cached comments for video: {vid_id}")
                    # Initialize comments array if it doesn't exist
                    if 'comments' not in video:
                        video['comments'] = []
                    # Extend existing comments with cached ones
                    video['comments'].extend(cached_comments)
                    debug_log(f"COMMENT DEBUG: Retrieved {len(cached_comments)} comments from cache for '{video_title}'")
                    comments_fetched_total += len(cached_comments)
                    if len(cached_comments) > 0:
                        videos_with_comments += 1
                    continue
                
                # If not in cache, fetch from API
                debug_log(f"COMMENT DEBUG: No cache found, fetching comments from API for video: {vid_id}")
                
                # Always initialize comments to an empty array
                video['comments'] = []
                
                try:
                    # First verify that comments are enabled for this video by checking video.statistics.commentCount
                    # This saves quota by avoiding unnecessary commentThreads.list calls
                    print(f"🔍 [DEBUG] Checking video statistics for: {vid_id}")
                    video_details_request = self.youtube.videos().list(
                        part="statistics",
                        id=vid_id
                    )
                    video_details_response = video_details_request.execute()
                    print(f"🔍 [DEBUG] Video details API response: {video_details_response}")
                    
                    if (not video_details_response.get('items') or 
                        'statistics' not in video_details_response['items'][0]):
                        print(f"❌ [DEBUG] Video '{video_title}' missing statistics")
                        debug_log(f"COMMENT DEBUG: Video '{video_title}' missing statistics")
                        videos_with_errors += 1
                        continue
                        
                    statistics = video_details_response['items'][0]['statistics']
                    print(f"🔍 [DEBUG] Video statistics: {statistics}")
                        
                    # First check if comments are disabled via the statistics
                    # The commentCount field might not exist if comments are disabled
                    if 'commentCount' not in statistics:
                        print(f"⚠️ [DEBUG] Video '{video_title}' has comments disabled (no commentCount in statistics)")
                        debug_log(f"COMMENT DEBUG: Video '{video_title}' has comments disabled (no commentCount in statistics)")
                        video['comments_disabled'] = True
                        videos_with_disabled_comments += 1
                        continue
                        
                    # If commentCount is 0, don't waste an API call trying to fetch comments
                    comment_count = int(statistics['commentCount'])
                    print(f"🔍 [DEBUG] Video '{video_title}' has {comment_count} comments according to API statistics")
                    if comment_count == 0:
                        debug_log(f"COMMENT DEBUG: Video '{video_title}' has 0 comments according to statistics")
                        video['comments'] = []
                        continue
                        
                    debug_log(f"COMMENT DEBUG: Video '{video_title}' has {comment_count} comments according to statistics")
                    
                    # Now retrieve comments with pagination to get up to max_comments_per_video
                    comments = []
                    total_added = 0  # Track total comments added for this video
                    # First check if this video already has a nextPageToken from a previous call
                    # This is important for continuing pagination where we left off
                    next_page_token = None
                    
                    # Option 1: Check if the video has a nextPageToken property directly
                    if 'nextPageToken' in video:
                        next_page_token = video.get('nextPageToken')
                        debug_log(f"COMMENT DEBUG: Found video-specific nextPageToken: {next_page_token}")
                    
                    # Option 2: If no token in the video object, use the provided page_token parameter 
                    # This is from the service-level pagination
                    if not next_page_token and page_token:
                        next_page_token = page_token
                        debug_log(f"COMMENT DEBUG: Using service-provided page_token: {next_page_token}")
                        
                    # Store the page token on the video object to ensure it's preserved across calls
                    if next_page_token:
                        video['nextPageToken'] = next_page_token
                        
                    comments_to_fetch = max_comments_per_video
                    
                    # Initialize comment tracking counters
                    existing_top_level_count = 0
                    
                    # If this video already has comments (from previous pagination), include them in our count
                    if 'comments' in video and isinstance(video['comments'], list) and len(video['comments']) > 0:
                        # Count only top-level comments (no parent_id)
                        existing_top_level_count = sum(1 for c in video['comments'] if 'parent_id' not in c)
                        debug_log(f"COMMENT DEBUG: Video already has {existing_top_level_count} top-level comments from previous pagination")
                        
                        # Adjust our fetch count based on existing top-level comments
                        if max_comments_per_video > 0:  # Only adjust if we have a limit
                            comments_to_fetch = max(0, max_comments_per_video - existing_top_level_count)
                            debug_log(f"COMMENT DEBUG: Adjusted comments_to_fetch to {comments_to_fetch} (max={max_comments_per_video}, existing={existing_top_level_count})")
                    
                    # Check if we have an ETag for this video's comments
                    etag_key = f"etag_comments_{vid_id}"
                    etag = st.session_state.etag_cache.get(etag_key)
                    
                    # If we already have enough comments, skip the API call
                    if comments_to_fetch <= 0:
                        debug_log(f"COMMENT DEBUG: Already have enough top-level comments for video '{video_title}' ({existing_top_level_count}/{max_comments_per_video}), skipping API call")
                        continue
                        
                    # Continue fetching until we have enough comments or run out of pages
                    while comments_to_fetch > 0:
                        # Request can fetch up to 100 comments at a time
                        current_fetch_count = min(100, comments_to_fetch)
                        
                        # Create base request
                        request_params = {
                            "part": "snippet,replies",  # Get both top-level comments and their replies
                            "videoId": vid_id,
                            "maxResults": current_fetch_count,
                            "textFormat": "plainText",   
                            "order": "relevance"
                        }
                        
                        # Add page token if we're paginating
                        if next_page_token:
                            request_params["pageToken"] = next_page_token
                            debug_log(f"COMMENT DEBUG: Using page token {next_page_token} for pagination")
                            
                        print(f"🔍 [DEBUG] About to call commentThreads().list() with params: {request_params}")
                        comments_request = self.youtube.commentThreads().list(**request_params)
                        
                        # Add ETag for conditional request if available
                        if etag:
                            debug_log(f"COMMENT DEBUG: Using ETag for video '{video_title}': {etag}")
                            comments_request.headers['If-None-Match'] = etag
                        
                        debug_log(f"COMMENT DEBUG: Sending API request for comments on video '{video_title}' (max: {current_fetch_count})")
                        print(f"🌐 [DEBUG] Making API call to YouTube commentThreads.list()...")
                        comments_response = comments_request.execute()
                        print(f"🔍 [DEBUG] API call completed. Response keys: {list(comments_response.keys())}")
                        print(f"🔍 [DEBUG] Items in response: {len(comments_response.get('items', []))}")
                        
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
                        # Start with existing top-level count if any
                        top_level_count = existing_top_level_count
                        debug_log(f"[COMMENT PROCESSING] Starting with {top_level_count} existing top-level comments out of max {max_comments_per_video}")
                        
                        for item in response_items:
                            if top_level_count >= max_comments_per_video:
                                debug_log(f"[COMMENT FETCH LIMIT] Reached max_comments_per_video={max_comments_per_video} for video {vid_id} (top-level: {top_level_count})")
                                break
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
                                top_level_count += 1
                                # Add up to max_replies_per_comment replies
                                if 'replies' in item and item['replies']['comments']:
                                    reply_count = 0
                                    for reply in item['replies']['comments']:
                                        if reply_count >= max_replies_per_comment:
                                            debug_log(f"[COMMENT FETCH LIMIT] Reached max_replies_per_comment={max_replies_per_comment} for top-level comment {item['id']}")
                                            break
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
                                        reply_count += 1
                            except KeyError as ke:
                                debug_log(f"COMMENT DEBUG: KeyError accessing comment structure: {ke}. Item structure: {item}")
                                continue
                        # If we've reached the limit, break out of the while loop
                        if top_level_count >= max_comments_per_video:
                            break
                        
                        # Update remaining comments to fetch
                        comments_to_fetch -= comments_fetched_this_page
                        
                        # Check if there are more pages of comments
                        if 'nextPageToken' in comments_response and comments_to_fetch > 0:
                            next_page_token = comments_response['nextPageToken']
                            # Store the next page token on the video for subsequent pagination
                            video['nextPageToken'] = next_page_token
                            debug_log(f"COMMENT DEBUG: More comments available, storing pageToken on video: {next_page_token}")
                        else:
                            # Clear the nextPageToken if we've reached the end
                            if 'nextPageToken' in video:
                                del video['nextPageToken']
                            debug_log(f"COMMENT DEBUG: No more comment pages or reached max limit for video '{video_title}'")
                            break
                    
                    # Add comments to the video - if there are already comments, append to them
                    if 'comments' not in video:
                        video['comments'] = []  # Initialize to empty list first
                    
                    # Log reply statistics
                    reply_counts = {}
                    for comment in comments:
                        if 'parent_id' in comment:
                            parent_id = comment['parent_id']
                            if parent_id not in reply_counts:
                                reply_counts[parent_id] = 0
                            reply_counts[parent_id] += 1
                    
                    # Log top-level comments with replies
                    if reply_counts:
                        debug_log(f"COMMENT DEBUG: Reply distribution: {reply_counts}")
                        debug_log(f"COMMENT DEBUG: Max replies: {max(reply_counts.values()) if reply_counts else 0}, Limit: {max_replies_per_comment}")
                    
                    # Always extend with comments from this page
                    video['comments'].extend(comments)
                    
                    # Double-check that we haven't exceeded our limit for top-level comments
                    top_level = [c for c in video['comments'] if 'parent_id' not in c]
                    if max_comments_per_video > 0 and len(top_level) > max_comments_per_video:
                        debug_log(f"COMMENT DEBUG: Too many top-level comments ({len(top_level)}/{max_comments_per_video}), trimming...")
                        # Find indices of top-level comments after the limit
                        indices_to_remove = []
                        top_level_count = 0
                        for i, comment in enumerate(video['comments']):
                            if 'parent_id' not in comment:
                                top_level_count += 1
                                if top_level_count > max_comments_per_video:
                                    indices_to_remove.append(i)
                        
                        # Remove excess comments (in reverse order to maintain indices)
                        for i in sorted(indices_to_remove, reverse=True):
                            video['comments'].pop(i)
                    
                    debug_log(f"COMMENT DEBUG: Added/Updated to total of {len(video['comments'])} comments for video '{video_title}' (limit was {max_comments_per_video})")
                    
                    # Update statistics
                    comments_fetched_total += len(comments)
                    if len(comments) > 0:
                        videos_with_comments += 1
                    
                    # Log comment breakdown
                    top_level = [c for c in comments if 'parent_id' not in c]
                    replies = [c for c in comments if 'parent_id' in c]
                    debug_log(f"COMMENT DEBUG: Final count for video '{video_title}': {len(top_level)} top-level comments, {len(replies)} replies")
                    
                    # Store in cache
                    self.store_in_cache(cache_key, comments)
                    
                except googleapiclient.errors.HttpError as e:
                    error_text = str(e)
                    # Comments might be disabled for the video
                    if 'commentsDisabled' in error_text:
                        debug_log(f"COMMENT DEBUG: Comments are disabled for video: '{video_title}' (ID: {vid_id})")
                        videos_with_disabled_comments += 1
                    elif 'quotaExceeded' in error_text:
                        debug_log(f"COMMENT DEBUG: API quota exceeded when fetching comments for '{video_title}'")
                        st.warning("⚠️ YouTube API quota exceeded. Please try again later or use a different API key.")
                        videos_with_errors += 1
                        # Don't continue trying if we've hit quota limits
                        break
                    else:
                        debug_log(f"COMMENT DEBUG: Error fetching comments for video '{video_title}' (ID: {vid_id}): {error_text}")
                        videos_with_errors += 1
            
            # Clear progress indicators
            status_text.empty()
            progress_bar.empty()                    # Final debug summary
            debug_log(f"COMMENT DEBUG: ===== COMMENT FETCHING SUMMARY =====")
            debug_log(f"COMMENT DEBUG: Total videos processed: {total_videos}")
            debug_log(f"COMMENT DEBUG: Videos with comments: {videos_with_comments}")
            debug_log(f"COMMENT DEBUG: Videos with disabled comments: {videos_with_disabled_comments}")
            debug_log(f"COMMENT DEBUG: Videos with errors: {videos_with_errors}")
            debug_log(f"COMMENT DEBUG: Total comments fetched: {comments_fetched_total}")
            debug_log(f"COMMENT DEBUG: Average comments per video: {comments_fetched_total/total_videos if total_videos > 0 else 0:.2f}")
            
            # Check if any videos have nextPageToken and need more pagination
            has_more_comments = False
            for video in videos:
                if video.get('nextPageToken'):
                    has_more_comments = True
                    debug_log(f"COMMENT DEBUG: Video {video.get('video_id')} has more comments available via nextPageToken: {video.get('nextPageToken')}")
            
            # Add summary to channel_info for easy access
            channel_info['comment_stats'] = {
                'total_comments': comments_fetched_total,
                'videos_with_comments': videos_with_comments,
                'videos_with_disabled_comments': videos_with_disabled_comments,
                'videos_with_errors': videos_with_errors,
                'has_more_comments': has_more_comments
            }
            
            # If we have more comments to fetch in a subsequent call, ensure that's reflected in response
            if has_more_comments:
                # Find a video with a nextPageToken to use as the main response nextPageToken
                for video in videos:
                    if video.get('nextPageToken'):
                        channel_info['nextPageToken'] = video.get('nextPageToken')
                        debug_log(f"COMMENT DEBUG: Setting channel_info nextPageToken to {channel_info['nextPageToken']}")
                        break
            
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
            self._handle_api_error(e, "get_video_comments")
            debug_log(f"[COMMENT FETCH ERROR] Exception in get_video_comments: {str(e)}")
            # Try to return partial data if available, but also return error
            if isinstance(channel_info, dict):
                channel_info['error_comments'] = str(e)
                return channel_info
            return {'error_comments': str(e)}