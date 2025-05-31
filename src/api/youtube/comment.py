"""
YouTube API client for comment-related operations.
"""
from typing import Dict, List, Any, Optional
import sys
import googleapiclient.errors

from src.utils.debug_utils import debug_log
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
                    self.store_in_cache(cache_key, video['comments'])
                    
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