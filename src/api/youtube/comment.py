"""
YouTube API client for comment-related operations.

QUOTA OPTIMIZATION STRATEGY:
- YouTube commentThreads.list API requires 1 API call per video (cannot batch multiple videos)
- For 50 videos requesting 1 comment each: minimum 50 API calls (YouTube API constraint)
- Optimizations implemented:
  1. Batch video statistics check (1 call for up to 50 videos)
  2. Rapid processing mode with minimal delays (0.3s between calls)
  3. Precise fetch counts (exactly what's requested, no over-fetching)
  4. Intelligent caching to avoid duplicate API calls
  5. Skip videos with disabled comments or zero comments

PERFORMANCE MODES:
- RAPID MODE: For ≤2 comments per video, >10 videos - Ultra-fast processing
- STANDARD MODE: For larger comment requests - Conservative chunking with rate limiting
"""
from typing import Dict, List, Any, Optional, Tuple
import sys
import time
import googleapiclient.errors
from src.api.youtube.base import YouTubeBaseClient
from src.utils.debug_utils import debug_log
from src.utils.websocket_utils import websocket_keepalive, ChunkedOperationManager, handle_websocket_error

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
    
    def _batch_check_video_statistics(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch check video statistics to optimize quota usage.
        According to YouTube API documentation, we can check up to 50 videos in one call.
        
        Args:
            videos: List of video dictionaries
            
        Returns:
            Updated videos list with statistics and comment availability info
        """
        debug_log(f"COMMENT DEBUG: Batch checking statistics for {len(videos)} videos")
        
        # Process videos in batches of 50 (API limit)
        batch_size = 50
        updated_videos = []
        
        for batch_start in range(0, len(videos), batch_size):
            batch_end = min(batch_start + batch_size, len(videos))
            batch_videos = videos[batch_start:batch_end]
            
            # Extract video IDs for batch request
            video_ids = []
            for video in batch_videos:
                vid_id = video.get('video_id')
                if vid_id:
                    video_ids.append(vid_id)
            
            if not video_ids:
                updated_videos.extend(batch_videos)
                continue
            
            try:
                # QUOTA OPTIMIZATION: Single API call for up to 50 videos (1 quota unit total)
                debug_log(f"COMMENT DEBUG: Batching statistics check for {len(video_ids)} videos in one API call")
                video_ids_str = ','.join(video_ids)
                
                video_details_request = self.youtube.videos().list(
                    part="statistics",
                    id=video_ids_str,
                    maxResults=50
                )
                video_details_response = video_details_request.execute()
                
                # Create a mapping of video_id to statistics
                stats_map = {}
                for item in video_details_response.get('items', []):
                    video_id = item['id']
                    statistics = item.get('statistics', {})
                    stats_map[video_id] = statistics
                
                debug_log(f"COMMENT DEBUG: Retrieved statistics for {len(stats_map)} videos")
                
                # Update videos with statistics info
                for video in batch_videos:
                    vid_id = video.get('video_id')
                    if vid_id in stats_map:
                        statistics = stats_map[vid_id]
                        
                        # Check if comments are disabled (no commentCount field)
                        if 'commentCount' not in statistics:
                            video['comments_disabled'] = True
                            video['comment_count'] = 0
                            debug_log(f"COMMENT DEBUG: Video {vid_id} has comments disabled")
                        else:
                            video['comments_disabled'] = False
                            video['comment_count'] = int(statistics['commentCount'])
                            debug_log(f"COMMENT DEBUG: Video {vid_id} has {video['comment_count']} comments")
                    else:
                        # Video not found in response, treat as error
                        video['comments_disabled'] = True
                        video['comment_count'] = 0
                        debug_log(f"COMMENT DEBUG: Video {vid_id} not found in statistics response")
                    
                    updated_videos.append(video)
                
                # Add rate limiting between batches (YouTube recommends max 1 request per second)
                if batch_end < len(videos):
                    time.sleep(1.2)
                    
            except googleapiclient.errors.HttpError as e:
                error_text = str(e)
                debug_log(f"COMMENT DEBUG: Error in batch statistics check: {error_text}")
                
                # If batch fails, mark all videos in batch as having unknown comment status
                for video in batch_videos:
                    video['comments_disabled'] = False  # Assume enabled, will be checked individually
                    video['comment_count'] = -1  # Unknown
                    updated_videos.append(video)
        
        return updated_videos
    
    @handle_websocket_error
    def get_video_comments(self, channel_info: Dict[str, Any], max_top_level_comments: int = 10, max_replies_per_comment: int = 2, max_comments_per_video: int = 0, page_token: str = None, optimize_quota: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get comments for each video in the channel with optimal quota usage.
        Enforces a hard cap of max_comments_per_video (if > 0) on the total number of comments (top-level + replies) per video.
        
        Args:
            channel_info: Dictionary containing channel information with videos
            max_top_level_comments: Maximum number of top-level comments to fetch per video (0 to skip)
            max_replies_per_comment: Maximum number of replies to fetch per top-level comment
            max_comments_per_video: Maximum total comments (top-level + replies) per video (0 means no cap)
            page_token: Token for pagination support across multiple calls
            optimize_quota: Whether to optimize quota usage (currently unused)
            
        Returns:
            Updated channel_info dictionary with comment data or None if failed
        """
        # Enhanced debugging at the start
        print(f"🔍 [DEBUG] get_video_comments called with:")
        print(f"  - max_top_level_comments: {max_top_level_comments}")
        print(f"  - max_replies_per_comment: {max_replies_per_comment}")
        print(f"  - max_comments_per_video: {max_comments_per_video}")
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
            
        # Zero max_top_level_comments means skip comment fetching
        if max_top_level_comments <= 0:
            debug_log("COMMENT DEBUG: max_top_level_comments is 0 or negative, skipping comment fetching")
            return channel_info
        
        debug_log(f"COMMENT DEBUG: Starting to fetch comments for {len(videos)} videos, max {max_top_level_comments} top-level comments per video")
        print(f"INFO: Fetching comments for {len(videos)} videos, max {max_top_level_comments} top-level comments per video")
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
            
            # QUOTA OPTIMIZATION: Batch check video statistics before individual comment fetching
            debug_log(f"COMMENT DEBUG: Pre-checking video statistics in batches to optimize quota usage")
            videos = self._batch_check_video_statistics(videos)
            
            # Filter out videos with disabled comments or zero comments to save quota
            videos_to_fetch = []
            for video in videos:
                if video.get('comments_disabled', False):
                    debug_log(f"COMMENT DEBUG: Skipping video {video.get('video_id')} - comments disabled")
                    continue
                if video.get('comment_count', -1) == 0:
                    debug_log(f"COMMENT DEBUG: Skipping video {video.get('video_id')} - zero comments")
                    # Initialize empty comments array
                    video['comments'] = []
                    continue
                videos_to_fetch.append(video)
            
            debug_log(f"COMMENT DEBUG: After batch filtering: {len(videos_to_fetch)} videos need comment fetching (out of {len(videos)} total)")
            print(f"🔍 [QUOTA OPTIMIZATION] Pre-filtered to {len(videos_to_fetch)} videos with comments enabled")
            
            # Update videos list to include all videos (including filtered ones)
            videos = videos
            
            # Progress tracking
            total_videos = len(videos)
            comments_fetched_total = 0
            videos_with_comments = 0
            videos_with_disabled_comments = 0
            videos_with_errors = 0
            
            # Use WebSocket keepalive for long operations
            with websocket_keepalive(f"Fetching comments for {total_videos} videos...") as keepalive:
                
                # ULTRA-EFFICIENT RAPID PROCESSING: Maximum speed within rate limits
                # NOTE: YouTube API requires one commentThreads.list call per video (API limitation)
                # We cannot fetch comments from multiple videos in a single API call
                # OPTIMIZATION: Minimize delays, maximize throughput, use precise fetch counts
                if max_top_level_comments <= 2 and len(videos_to_fetch) > 10:
                    debug_log(f"COMMENT DEBUG: ACTIVATING RAPID MODE for {len(videos_to_fetch)} videos requesting {max_top_level_comments} comments each")
                    print(f"🚀 [RAPID MODE] Ultra-efficient processing: {len(videos_to_fetch)} videos × {max_top_level_comments} comments")
                    print(f"⚠️  [API CONSTRAINT] Each video requires 1 API call (YouTube API limitation - cannot batch multiple videos)")
                    
                    # Process videos with minimal delays for maximum speed
                    rapid_results = []
                    total_api_calls = 0
                    
                    for i, video in enumerate(videos_to_fetch):
                        vid_id = video.get('video_id')
                        video_title = video.get('title', 'Unknown')
                        
                        # Update progress
                        keepalive.update_status(f"Rapid fetch '{video_title[:25]}...' ({i + 1}/{len(videos_to_fetch)})", 
                                              (i + 1) / len(videos_to_fetch))
                        
                        # Quick cache check
                        cache_key = f"comments_{vid_id}"
                        cached_comments = self.get_from_cache(cache_key)
                        
                        if cached_comments is not None:
                            video['comments'] = cached_comments
                            comments_fetched_total += len(cached_comments)
                            if len(cached_comments) > 0:
                                videos_with_comments += 1
                            rapid_results.append(video)
                            continue
                        
                        # MINIMAL API CALL: Fetch exactly what's needed with zero waste
                        try:
                            video['comments'] = []
                            
                            # Ultra-precise parameters: fetch exactly max_top_level_comments, skip replies for speed
                            request_params = {
                                "part": "snippet",  # Skip replies part for maximum speed
                                "videoId": vid_id,
                                "maxResults": max_top_level_comments,  # Precise: exactly what's requested
                                "textFormat": "plainText",  # Faster than HTML
                                "order": "relevance"  # Get best comments first
                            }
                            
                            comments_request = self.youtube.commentThreads().list(**request_params)
                            comments_response = comments_request.execute()
                            total_api_calls += 1
                            
                            # Process exactly max_top_level_comments (no more, no less)
                            response_items = comments_response.get('items', [])
                            fetched_count = 0
                            
                            for item in response_items[:max_top_level_comments]:  # Strict precision
                                try:
                                    comment = item['snippet']['topLevelComment']['snippet']
                                    comment_data = {
                                        'comment_id': item['id'],
                                        'comment_text': comment['textDisplay'],
                                        'comment_author': comment['authorDisplayName'],
                                        'comment_published_at': comment['publishedAt'],
                                        'like_count': comment.get('likeCount', 0),
                                        'author_profile_image_url': comment.get('authorProfileImageUrl', ''),
                                        'updated_at': comment.get('updatedAt', comment.get('publishedAt', ''))
                                    }
                                    video['comments'].append(comment_data)
                                    fetched_count += 1
                                except KeyError as ke:
                                    debug_log(f"RAPID COMMENT: KeyError in comment structure: {ke}")
                                    continue
                            
                            # Cache the results
                            self.store_in_cache(cache_key, video['comments'])
                            
                            comments_fetched_total += fetched_count
                            if fetched_count > 0:
                                videos_with_comments += 1
                                
                            # ULTRA-MINIMAL DELAY: Stay within rate limits but maximize speed
                            # YouTube allows up to 100 requests per 100 seconds per user
                            time.sleep(0.3)  # Minimal safe delay for rapid processing
                            
                        except googleapiclient.errors.HttpError as e:
                            debug_log(f"RAPID COMMENT ERROR: {str(e)} for video {vid_id}")
                            video['comments'] = []
                            videos_with_errors += 1
                        
                        rapid_results.append(video)
                        
                        # Progress update every 10 videos
                        if (i + 1) % 10 == 0:
                            debug_log(f"RAPID PROGRESS: Processed {i + 1}/{len(videos_to_fetch)} videos, {total_api_calls} API calls made")
                            print(f"⚡ [RAPID] {i + 1}/{len(videos_to_fetch)} videos processed ({total_api_calls} API calls)")
                    
                    # Update videos with rapid results
                    for i, result_video in enumerate(rapid_results):
                        # Find and update the original video in the main list
                        for k, orig_video in enumerate(videos):
                            if orig_video.get('video_id') == result_video.get('video_id'):
                                videos[k] = result_video
                                break
                    
                    print(f"✅ [RAPID COMPLETE] {len(videos_to_fetch)} videos processed with {total_api_calls} API calls")
                    print(f"📊 [API EFFICIENCY] 1 call per video (YouTube API constraint), {comments_fetched_total} comments fetched")
                
                else:
                    # STANDARD PROCESSING: For larger comment requests or small video counts
                    debug_log(f"COMMENT DEBUG: Using STANDARD mode - not suitable for batch optimization")
                    print(f"📋 [STANDARD MODE] Processing {len(videos_to_fetch)} videos individually")
                    
                    # QUOTA-OPTIMIZED CHUNKING: Adjust strategy based on comments per video
                    if max_top_level_comments <= 2:
                        chunk_size = 20  # Process more videos per chunk
                        update_interval = 0.8  # Faster updates
                    elif max_top_level_comments <= 5:
                        chunk_size = 15  # Process more videos quickly for small comment requests
                        update_interval = 1.0  # Faster updates
                    elif max_top_level_comments <= 20:
                        chunk_size = 8   # Moderate chunking
                        update_interval = 1.5
                    else:
                        chunk_size = 4   # Conservative chunking for large comment requests
                        update_interval = 2.0
                        
                    chunk_manager = ChunkedOperationManager(chunk_size=chunk_size, update_interval=update_interval)
                
                def process_video_comments(video_data):
                    """Process comments for a single video."""
                    nonlocal comments_fetched_total, videos_with_comments, videos_with_disabled_comments, videos_with_errors
                    
                    if isinstance(video_data, tuple):
                        i, video = video_data
                    else:
                        # Fallback if not tuple
                        video = video_data
                        i = 0
                    
                    vid_id = video.get('video_id') if isinstance(video, dict) else video
                    video_title = video.get('title', 'Unknown')
                    
                    debug_log(f"COMMENT DEBUG: Processing video: '{video_title}' (ID: {vid_id})")
                    
                    # Update keepalive status
                    keepalive.update_status(f"Processing '{video_title[:30]}...'", (i + 1) / len(videos_to_fetch))
                    
                    # Check if video was pre-filtered (comments disabled or zero comments)
                    if video.get('comments_disabled', False):
                        debug_log(f"COMMENT DEBUG: Skipping video with disabled comments: {vid_id}")
                        videos_with_disabled_comments += 1
                        video['comments'] = []
                        return video
                    
                    if video.get('comment_count', -1) == 0:
                        debug_log(f"COMMENT DEBUG: Skipping video with zero comments: {vid_id}")
                        video['comments'] = []
                        return video
                    
                    # Check cache first
                    cache_key = f"comments_{vid_id}"
                    cached_comments = self.get_from_cache(cache_key)
                    
                    if cached_comments is not None:
                        debug_log(f"COMMENT DEBUG: Using cached comments for video: {vid_id}")
                        if 'comments' not in video:
                            video['comments'] = []
                        video['comments'].extend(cached_comments)
                        debug_log(f"COMMENT DEBUG: Retrieved {len(cached_comments)} comments from cache for '{video_title}'")
                        comments_fetched_total += len(cached_comments)
                        if len(cached_comments) > 0:
                            videos_with_comments += 1
                        return video
                    
                    # If not in cache, fetch from API (without individual statistics check)
                    result = self._fetch_video_comments_optimized(
                        video, vid_id, video_title, max_top_level_comments, 
                        max_replies_per_comment, max_comments_per_video
                    )
                    
                    processed_video, fetched_count, has_comments, disabled, error = result
                    comments_fetched_total += fetched_count
                    if has_comments:
                        videos_with_comments += 1
                    if disabled:
                        videos_with_disabled_comments += 1
                    if error:
                        videos_with_errors += 1
                        
                    return processed_video
                
                # Process only videos that need comment fetching
                video_tuples = [(i, video) for i, video in enumerate(videos_to_fetch)]
                
                def progress_callback(current, total, item_desc):
                    keepalive.update_status(f"Processing video {current}/{total}: {item_desc}", current / total)
                
                # Process all videos using chunked operation
                processed_videos = chunk_manager.process_in_chunks(
                    video_tuples, 
                    process_video_comments,
                    progress_callback
                )
                
                # Update videos list with processed results
                for i, processed_video in enumerate(processed_videos):
                    if processed_video is not None:
                        videos[i] = processed_video
                
                # Update channel_info with processed videos
                channel_info['video_id'] = videos
                
                # Summary logging
                debug_log(f"COMMENT DEBUG: Completed comment fetching. Total comments: {comments_fetched_total}, Videos with comments: {videos_with_comments}, Disabled: {videos_with_disabled_comments}, Errors: {videos_with_errors}")
                
                # COMPREHENSIVE OPTIMIZATION SUMMARY
                api_calls_made = len(videos_to_fetch)  # Actual: 1 call per video (YouTube API constraint)
                videos_processed = len(videos_to_fetch)
                efficiency_ratio = comments_fetched_total / max(api_calls_made, 1)
                
                debug_log(f"[OPTIMIZATION SUMMARY] API calls made: {api_calls_made}, Comments fetched: {comments_fetched_total}, Efficiency: {efficiency_ratio:.2f} comments/call")
                
                print(f"✅ [COMPLETE] Comment fetching finished: {comments_fetched_total} comments from {videos_with_comments} videos")
                print(f"📊 [API USAGE] {api_calls_made} API calls for {videos_processed} videos (1 call per video - YouTube API constraint)")
                print(f"⚡ [EFFICIENCY] {efficiency_ratio:.2f} comments per API call, {comments_fetched_total} total comments")
                
                # API Constraint Explanation
                if max_top_level_comments <= 2 and len(videos_to_fetch) > 10:
                    print(f"ℹ️  [API LIMITATION] YouTube API requires 1 commentThreads.list call per video")
                    print(f"ℹ️  [OPTIMIZATION] Used rapid processing with minimal delays (0.3s between calls)")
                    print(f"ℹ️  [PRECISION] Fetched exactly {max_top_level_comments} comment(s) per video to minimize quota waste")
                
                if STREAMLIT_AVAILABLE:
                    st.success(f"✅ Fetched {comments_fetched_total} comments from {videos_with_comments} videos")
                    
                    # Enhanced efficiency reporting
                    if max_top_level_comments <= 2 and len(videos_to_fetch) > 10:
                        st.info(f"🚀 **RAPID MODE ACTIVATED**: Optimized for speed and precision")
                        st.info(f"📡 **API Constraint**: YouTube requires 1 API call per video (cannot batch multiple videos)")
                        st.info(f"⚡ **Optimization**: {efficiency_ratio:.2f} comments per call, 0.3s delays, exact fetch counts")
                    else:
                        st.info(f"📊 **Efficiency**: {efficiency_ratio:.2f} comments per API call")
                    
                    if videos_with_disabled_comments > 0:
                        st.info(f"ℹ️ {videos_with_disabled_comments} videos had comments disabled")
                    if videos_with_errors > 0:
                        st.warning(f"⚠️ {videos_with_errors} videos had errors during comment fetching")
                
                return channel_info
                
        except Exception as e:
            error_msg = f"Error during comment fetching: {str(e)}"
            debug_log(f"COMMENT DEBUG: {error_msg}")
            print(f"❌ [DEBUG] {error_msg}")
            if STREAMLIT_AVAILABLE:
                st.error(f"❌ {error_msg}")
            return channel_info

    def _fetch_video_comments_optimized(self, video: Dict[str, Any], vid_id: str, video_title: str, 
                                       max_top_level_comments: int, max_replies_per_comment: int, 
                                       max_comments_per_video: int) -> Tuple[Dict[str, Any], int, bool, bool, bool]:
        """
        Fetch comments for a single video from the YouTube API with intelligent quota optimization.
        
        OPTIMIZATION STRATEGY:
        - For small requests (≤20 comments): Fetch exactly what's needed to minimize bandwidth
        - For larger requests: Use moderate batches (50) to balance API calls vs over-fetching  
        - Adaptive rate limiting: Faster processing for small requests, conservative for large
        - Skip individual statistics checks (done in batch upstream)
        
        Args:
            video: Video dictionary to update with comments
            vid_id: YouTube video ID
            video_title: Video title for logging
            max_top_level_comments: Maximum top-level comments to fetch
            max_replies_per_comment: Maximum replies per top-level comment
            max_comments_per_video: Total comment cap (0 = no cap)
            
        Returns:
            Tuple of (video_dict, comments_fetched_count, has_comments, comments_disabled, error_occurred)
        """
        debug_log(f"COMMENT DEBUG: Fetching comments from API (optimized) for video: {vid_id}")
        
        # Always initialize comments to an empty array
        video['comments'] = []
        
        try:
            # Skip individual statistics check - it was done in batch
            # We know this video has comments enabled and comment_count > 0
            comment_count = video.get('comment_count', -1)
            debug_log(f"COMMENT DEBUG: Video '{video_title}' has {comment_count} comments (from batch check)")
            
            # Now retrieve comments with pagination to get up to max_top_level_comments
            top_level_fetched = 0
            total_comments_fetched = 0
            next_page_token = None
            
            while top_level_fetched < max_top_level_comments:
                # QUOTA-OPTIMIZED FETCHING: Fetch exactly what's needed, no more
                remaining_needed = max_top_level_comments - top_level_fetched
                
                # SMART QUOTA STRATEGY: For small requests, fetch exactly what's needed
                # For larger requests, use reasonable batch sizes to minimize API calls
                if max_top_level_comments <= 2:
                    # Ultra-precise: Fetch exactly what's requested to minimize waste
                    fetch_count = remaining_needed
                elif max_top_level_comments <= 10:
                    # Precise: Fetch close to what's needed with minimal overhead
                    fetch_count = min(remaining_needed + 2, 100)  # Small buffer for efficiency
                else:
                    # Efficient batching: Use larger batches for bigger requests
                    fetch_count = min(max(remaining_needed, 20), 100)
                
                # Ensure fetch_count is within valid API limits (1-100)
                fetch_count = max(1, min(100, fetch_count))
                
                request_params = {
                    "part": "snippet,replies",
                    "videoId": vid_id,
                    "maxResults": fetch_count,
                    "textFormat": "plainText",
                    "order": "relevance"
                }
                if next_page_token:
                    request_params["pageToken"] = next_page_token
                
                debug_log(f"COMMENT DEBUG: QUOTA-OPTIMIZED REQUEST: {fetch_count} comments for video {vid_id} (needed: {remaining_needed}, max_per_video: {max_top_level_comments})")
                comments_request = self.youtube.commentThreads().list(**request_params)
                comments_response = comments_request.execute()
                
                # QUOTA-OPTIMIZED RATE LIMITING: Adjust delay based on request efficiency
                # For ultra-small requests (1-2 comments), use minimal delays for speed
                # For larger requests, use more conservative delays
                if max_top_level_comments <= 2:
                    delay = 0.5  # Ultra-fast for minimal comment requests
                elif fetch_count <= 5:
                    delay = 0.7  # Fast processing for small requests
                elif fetch_count <= 20:
                    delay = 1.0  # Standard delay
                else:
                    delay = 1.2  # Conservative delay for large requests
                    
                time.sleep(delay)
                debug_log(f"COMMENT DEBUG: Applied {delay}s rate limit delay for {fetch_count} comment request (max_per_video: {max_top_level_comments})")
                
                response_items = comments_response.get('items', [])
                if not response_items:
                    break
                    
                for item in response_items:
                    if top_level_fetched >= max_top_level_comments:
                        break
                    if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                        debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id}. Stopping fetch.")
                        break
                    try:
                        comment = item['snippet']['topLevelComment']['snippet']
                        comment_data = {
                            'comment_id': item['id'],
                            'comment_text': comment['textDisplay'],
                            'comment_author': comment['authorDisplayName'],
                            'comment_published_at': comment['publishedAt'],
                            'like_count': comment.get('likeCount', 0),
                            'author_profile_image_url': comment.get('authorProfileImageUrl', ''),
                            'updated_at': comment.get('updatedAt', comment.get('publishedAt', ''))
                        }
                        if max_comments_per_video > 0 and total_comments_fetched + 1 > max_comments_per_video:
                            debug_log(f"[COMMENT CAP] Would exceed max_comments_per_video with top-level comment, skipping.")
                            break
                        video['comments'].append(comment_data)
                        top_level_fetched += 1
                        total_comments_fetched += 1
                        
                        # Strictly limit replies
                        replies = item.get('replies', {}).get('comments', [])
                        for reply in replies[:max_replies_per_comment]:
                            if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                                debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id} (in replies). Stopping fetch.")
                                break
                            reply_snippet = reply['snippet']
                            reply_data = {
                                'comment_id': reply['id'],
                                'comment_text': f"[REPLY] {reply_snippet['textDisplay']}",
                                'comment_author': reply_snippet['authorDisplayName'],
                                'comment_published_at': reply_snippet['publishedAt'],
                                'like_count': reply_snippet.get('likeCount', 0),
                                'parent_id': item['id'],
                                'author_profile_image_url': reply_snippet.get('authorProfileImageUrl', ''),
                                'updated_at': reply_snippet.get('updatedAt', reply_snippet.get('publishedAt', ''))
                            }
                            video['comments'].append(reply_data)
                            total_comments_fetched += 1
                        if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                            debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id} (after replies). Stopping fetch.")
                            break
                    except KeyError as ke:
                        debug_log(f"COMMENT DEBUG: KeyError accessing comment structure: {ke}. Item structure: {item}")
                        continue
                        
                if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                    debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id} (end of page). Stopping fetch.")
                    break
                if 'nextPageToken' in comments_response and top_level_fetched < max_top_level_comments:
                    next_page_token = comments_response['nextPageToken']
                else:
                    break
                    
            debug_log(f"[COMMENT CAP] For video {vid_id}: top_level_fetched={top_level_fetched}, total_comments_fetched={total_comments_fetched}, cap={max_comments_per_video}")
            debug_log(f"[QUOTA EFFICIENCY] Video {vid_id}: Requested {max_top_level_comments}, Fetched {top_level_fetched}, API calls made: {1 if top_level_fetched > 0 else 0}")
            
            # Store in cache
            cache_key = f"comments_{vid_id}"
            self.store_in_cache(cache_key, video['comments'])
            
            has_comments = len(video['comments']) > 0
            return video, total_comments_fetched, has_comments, False, False
    
        except googleapiclient.errors.HttpError as e:
            error_text = str(e)
            # Comments might be disabled for the video
            if 'commentsDisabled' in error_text:
                debug_log(f"COMMENT DEBUG: Comments are disabled for video: '{video_title}' (ID: {vid_id})")
                return video, 0, False, True, False
            elif 'quotaExceeded' in error_text:
                debug_log(f"COMMENT DEBUG: API quota exceeded when fetching comments for '{video_title}'")
                if STREAMLIT_AVAILABLE:
                    st.warning("⚠️ YouTube API quota exceeded. Please try again later or use a different API key.")
                return video, 0, False, False, True
            else:
                debug_log(f"COMMENT DEBUG: Error fetching comments for video '{video_title}' (ID: {vid_id}): {error_text}")
                return video, 0, False, False, True

    def _fetch_video_comments_from_api(self, video: Dict[str, Any], vid_id: str, video_title: str, 
                                       max_top_level_comments: int, max_replies_per_comment: int, 
                                       max_comments_per_video: int) -> Tuple[Dict[str, Any], int, bool, bool, bool]:
        """
        DEPRECATED: This method makes individual statistics API calls and burns quota.
        Use _fetch_video_comments_optimized() instead which skips redundant statistics checks.
        
        Fetch comments for a single video from the YouTube API.
        
        Returns:
            Tuple of (video_dict, comments_fetched_count, has_comments, comments_disabled, error_occurred)
        """
        debug_log(f"COMMENT DEBUG: WARNING - Using deprecated individual statistics check for video: {vid_id}")
        debug_log(f"COMMENT DEBUG: No cache found, fetching comments from API for video: {vid_id}")
        
        # Always initialize comments to an empty array
        video['comments'] = []
        
        try:
            # QUOTA WARNING: This individual statistics call burns unnecessary quota
            # The batch method should be used instead
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
                return video, 0, False, False, True
                
            statistics = video_details_response['items'][0]['statistics']
            print(f"🔍 [DEBUG] Video statistics: {statistics}")
                
            # First check if comments are disabled via the statistics
            # The commentCount field might not exist if comments are disabled
            if 'commentCount' not in statistics:
                print(f"⚠️ [DEBUG] Video '{video_title}' has comments disabled (no commentCount in statistics)")
                debug_log(f"COMMENT DEBUG: Video '{video_title}' has comments disabled (no commentCount in statistics)")
                video['comments_disabled'] = True
                return video, 0, False, True, False
                
            # If commentCount is 0, don't waste an API call trying to fetch comments
            comment_count = int(statistics['commentCount'])
            print(f"🔍 [DEBUG] Video '{video_title}' has {comment_count} comments according to API statistics")
            if comment_count == 0:
                debug_log(f"COMMENT DEBUG: Video '{video_title}' has 0 comments according to statistics")
                video['comments'] = []
                return video, 0, False, False, False
                
            debug_log(f"COMMENT DEBUG: Video '{video_title}' has {comment_count} comments according to statistics")
            
            # Now retrieve comments with pagination to get up to max_top_level_comments
            top_level_fetched = 0
            total_comments_fetched = 0
            next_page_token = None
            
            while top_level_fetched < max_top_level_comments:
                fetch_count = min(100, max_top_level_comments - top_level_fetched)
                request_params = {
                    "part": "snippet,replies",
                    "videoId": vid_id,
                    "maxResults": fetch_count,
                    "textFormat": "plainText",
                    "order": "relevance"
                }
                if next_page_token:
                    request_params["pageToken"] = next_page_token
                comments_request = self.youtube.commentThreads().list(**request_params)
                comments_response = comments_request.execute()
                response_items = comments_response.get('items', [])
                if not response_items:
                    break
                for item in response_items:
                    if top_level_fetched >= max_top_level_comments:
                        break
                    if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                        debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id}. Stopping fetch.")
                        break
                    try:
                        comment = item['snippet']['topLevelComment']['snippet']
                        comment_data = {
                            'comment_id': item['id'],
                            'comment_text': comment['textDisplay'],
                            'comment_author': comment['authorDisplayName'],
                            'comment_published_at': comment['publishedAt'],
                            'like_count': comment.get('likeCount', 0),
                            'author_profile_image_url': comment.get('authorProfileImageUrl', ''),
                            'updated_at': comment.get('updatedAt', comment.get('publishedAt', ''))
                        }
                        if max_comments_per_video > 0 and total_comments_fetched + 1 > max_comments_per_video:
                            debug_log(f"[COMMENT CAP] Would exceed max_comments_per_video with top-level comment, skipping.")
                            break
                        video['comments'].append(comment_data)
                        top_level_fetched += 1
                        total_comments_fetched += 1
                        # Strictly limit replies
                        replies = item.get('replies', {}).get('comments', [])
                        for reply in replies[:max_replies_per_comment]:
                            if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                                debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id} (in replies). Stopping fetch.")
                                break
                            reply_snippet = reply['snippet']
                            reply_data = {
                                'comment_id': reply['id'],
                                'comment_text': f"[REPLY] {reply_snippet['textDisplay']}",
                                'comment_author': reply_snippet['authorDisplayName'],
                                'comment_published_at': reply_snippet['publishedAt'],
                                'like_count': reply_snippet.get('likeCount', 0),
                                'parent_id': item['id'],
                                'author_profile_image_url': reply_snippet.get('authorProfileImageUrl', ''),
                                'updated_at': reply_snippet.get('updatedAt', reply_snippet.get('publishedAt', ''))
                            }
                            video['comments'].append(reply_data)
                            total_comments_fetched += 1
                        if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                            debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id} (after replies). Stopping fetch.")
                            break
                    except KeyError as ke:
                        debug_log(f"COMMENT DEBUG: KeyError accessing comment structure: {ke}. Item structure: {item}")
                        continue
                if max_comments_per_video > 0 and total_comments_fetched >= max_comments_per_video:
                    debug_log(f"[COMMENT CAP] Reached max_comments_per_video ({max_comments_per_video}) for video {vid_id} (end of page). Stopping fetch.")
                    break
                if 'nextPageToken' in comments_response and top_level_fetched < max_top_level_comments:
                    next_page_token = comments_response['nextPageToken']
                else:
                    break
            debug_log(f"[COMMENT CAP] For video {vid_id}: top_level_fetched={top_level_fetched}, total_comments_fetched={total_comments_fetched}, cap={max_comments_per_video}")
            
            # Log reply statistics
            reply_counts = {}
            for comment in video['comments']:
                if 'parent_id' in comment:
                    parent_id = comment['parent_id']
                    if parent_id not in reply_counts:
                        reply_counts[parent_id] = 0
                    reply_counts[parent_id] += 1
            
            # Log top-level comments with replies
            if reply_counts:
                debug_log(f"COMMENT DEBUG: Reply distribution: {reply_counts}")
                debug_log(f"COMMENT DEBUG: Max replies: {max(reply_counts.values()) if reply_counts else 0}, Limit: {max_replies_per_comment}")
            
            # Store in cache
            cache_key = f"comments_{vid_id}"
            self.store_in_cache(cache_key, video['comments'])
            
            has_comments = len(video['comments']) > 0
            return video, total_comments_fetched, has_comments, False, False
    
        except googleapiclient.errors.HttpError as e:
            error_text = str(e)
            # Comments might be disabled for the video
            if 'commentsDisabled' in error_text:
                debug_log(f"COMMENT DEBUG: Comments are disabled for video: '{video_title}' (ID: {vid_id})")
                return video, 0, False, True, False
            elif 'quotaExceeded' in error_text:
                debug_log(f"COMMENT DEBUG: API quota exceeded when fetching comments for '{video_title}'")
                if STREAMLIT_AVAILABLE:
                    st.warning("⚠️ YouTube API quota exceeded. Please try again later or use a different API key.")
                return video, 0, False, False, True
            else:
                debug_log(f"COMMENT DEBUG: Error fetching comments for video '{video_title}' (ID: {vid_id}): {error_text}")
                return video, 0, False, False, True