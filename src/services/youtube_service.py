"""
YouTube service module to handle business logic related to YouTube data operations.
This layer sits between the UI and the API/storage layers.
"""
from src.api.youtube_api import YouTubeAPI
from src.storage.factory import StorageFactory
from src.utils.helpers import debug_log

class YouTubeService:
    """
    Service class that handles business logic for YouTube data operations.
    It coordinates interactions between the API and storage layers.
    """
    
    def __init__(self, api_key):
        """
        Initialize the YouTube service with an API key.
        
        Args:
            api_key (str): The YouTube Data API key
        """
        self.api = YouTubeAPI(api_key)
    
    def collect_channel_data(self, channel_id, options, existing_data=None):
        """
        Collect data for a YouTube channel according to specified options.
        
        Args:
            channel_id (str): The YouTube channel ID, custom URL, or handle
            options (dict): Dictionary containing collection options
                - fetch_channel_data (bool): Whether to fetch channel info
                - fetch_videos (bool): Whether to fetch videos
                - fetch_comments (bool): Whether to fetch comments
                - max_videos (int): Maximum number of videos to fetch
                - max_comments_per_video (int): Maximum comments per video
            existing_data (dict, optional): Existing channel data to update instead of fetching fresh
        
        Returns:
            dict or None: The collected channel data or None if collection failed
        """
        debug_log(f"Starting data collection for channel: {channel_id} with options: {options}")
        
        # Use existing data if provided, otherwise initialize to None
        channel_info = existing_data
        
        # First, check if we need to resolve a custom URL
        is_valid, validated_channel_id = self.validate_and_resolve_channel_id(channel_id)
        if not is_valid:
            debug_log(f"Failed to validate or resolve channel ID: {channel_id}")
            return None
            
        # Use the validated/resolved channel ID from now on
        channel_id = validated_channel_id
        debug_log(f"Using validated/resolved channel ID: {channel_id}")
        
        # Fetch channel data if requested and not already available
        if options.get('fetch_channel_data', True) and not channel_info:
            channel_info = self.api.get_channel_info(channel_id)
        
        # Only proceed if we have channel info (either from existing data or just fetched)
        if channel_info:
            # Fetch videos if requested
            if options.get('fetch_videos', False):
                debug_log(f"Fetching videos for channel: {channel_info.get('channel_name')}")
                channel_info = self.api.get_channel_videos(
                    channel_info, 
                    max_videos=options.get('max_videos', 25)
                )
                
            # Fetch comments if requested
            if channel_info and options.get('fetch_comments', False) and 'video_id' in channel_info:
                videos_count = len(channel_info.get('video_id', []))
                max_comments = options.get('max_comments_per_video', 10)
                debug_log(f"SERVICE DEBUG: Initiating comment fetch for {videos_count} videos with max_comments_per_video={max_comments}")
                
                # Check if there are any videos to fetch comments for
                if videos_count == 0:
                    debug_log(f"SERVICE DEBUG: No videos available to fetch comments for")
                    return channel_info
                    
                # Check the structure of the videos list to verify it's as expected
                if videos_count > 0:
                    sample_video = channel_info['video_id'][0]
                    debug_log(f"SERVICE DEBUG: Sample video structure: {list(sample_video.keys())}")
                    if 'video_id' not in sample_video:
                        debug_log(f"SERVICE DEBUG: WARNING - Sample video doesn't have video_id field. Keys: {list(sample_video.keys())}")
                
                # Execute the comment fetching
                channel_info = self.api.get_video_comments(
                    channel_info,
                    max_comments_per_video=max_comments
                )
                
                # Verify that comments were stored properly
                if 'comment_stats' in channel_info:
                    stats = channel_info['comment_stats']
                    debug_log(f"SERVICE DEBUG: Comment fetching completed. Stats: {stats}")
                else:
                    debug_log(f"SERVICE DEBUG: Comment fetching completed but no stats were returned")
                    
                # Check if comments exist in the first video with comments
                for video in channel_info.get('video_id', []):
                    comments = video.get('comments', [])
                    if comments:
                        debug_log(f"SERVICE DEBUG: Found video with {len(comments)} comments. First comment from: {comments[0].get('comment_author', 'Unknown')}")
                        break
        
        return channel_info
    
    def save_channel_data(self, channel_data, storage_type, config=None):
        """
        Save channel data to the specified storage provider.
        
        Args:
            channel_data (dict): The channel data to save
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
        
        Returns:
            bool: True if data was saved successfully, False otherwise
        """
        try:
            storage_provider = StorageFactory.get_storage_provider(storage_type, config)
            return storage_provider.store_channel_data(channel_data)
        except Exception as e:
            debug_log(f"Error saving data to {storage_type}: {str(e)}")
            return False
    
    def get_channels_list(self, storage_type, config=None):
        """
        Get list of channels from the specified storage provider.
        
        Args:
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
            
        Returns:
            list: List of channel IDs/names 
        """
        try:
            storage_provider = StorageFactory.get_storage_provider(storage_type, config)
            return storage_provider.get_channels_list()
        except Exception as e:
            debug_log(f"Error getting channels list from {storage_type}: {str(e)}")
            return []
    
    def get_channel_data(self, channel_id_or_name, storage_type, config=None):
        """
        Get channel data from the specified storage provider.
        
        Args:
            channel_id_or_name (str): Channel ID or name
            storage_type (str): Type of storage to use
            config (Settings, optional): Application configuration
            
        Returns:
            dict or None: The channel data or None if retrieval failed
        """
        try:
            storage_provider = StorageFactory.get_storage_provider(storage_type, config)
            return storage_provider.get_channel_data(channel_id_or_name)
        except Exception as e:
            debug_log(f"Error getting channel data from {storage_type}: {str(e)}")
            return None

    def validate_and_resolve_channel_id(self, channel_id):
        """
        Validate a channel ID and resolve custom URLs or handles if needed.
        
        Args:
            channel_id (str): The channel ID, custom URL, or handle to validate
            
        Returns:
            tuple: (is_valid, channel_id_or_message)
                - is_valid (bool): Whether the input is valid
                - channel_id_or_message (str): The validated channel ID or an error message
        """
        from src.utils.helpers import validate_channel_id
        
        # First try direct validation
        is_valid, validated_id = validate_channel_id(channel_id)
        
        # If the ID is directly valid, return it
        if is_valid:
            debug_log(f"Channel ID is directly valid: {channel_id}")
            return True, validated_id
            
        # If validator returns a resolution request, try to resolve it
        if validated_id.startswith("resolve:"):
            custom_url = validated_id[8:]  # Remove 'resolve:' prefix
            debug_log(f"Attempting to resolve custom URL or handle: {custom_url}")
            
            # Use the YouTube API to resolve the custom URL or handle
            resolved_id = self.api.resolve_custom_channel_url(custom_url)
            
            if resolved_id:
                debug_log(f"Successfully resolved {custom_url} to channel ID: {resolved_id}")
                return True, resolved_id
            else:
                debug_log(f"Failed to resolve custom URL or handle: {custom_url}")
                return False, f"Could not resolve the custom URL or handle: {custom_url}"
        
        # If we get here, the ID is invalid and couldn't be resolved
        debug_log(f"Invalid channel ID format and not a resolvable custom URL: {channel_id}")
        return False, "Invalid channel ID format. Please enter a valid YouTube channel ID, custom URL, or handle."