"""
YTDataHub Comment Collection Examples

This module provides examples of the enhanced comment collection functionality.
"""

def collect_comments_example(youtube_service, channel_id):
    """Example function showing different comment collection options."""
    print("=== YTDataHub Comment Collection Examples ===\n")
    
    # First, get basic channel info
    print(f"Fetching channel data for {channel_id}...")
    channel_info = youtube_service.get_channel_info(channel_id)
    if not channel_info:
        print("Channel not found")
        return
    
    print(f"Channel: {channel_info.get('title', 'Unknown')}")
    print(f"Videos: {channel_info.get('total_videos', 0)}")
    print()
    
    # Example 1: Top-level comments only (no replies)
    print("EXAMPLE 1: Top-level comments only")
    print("--------------------------------")
    options1 = {
        'fetch_channel_data': False,
        'fetch_videos': True,
        'fetch_comments': True,
        'max_videos': 2,  # Limit to 2 videos for the example
        'max_comments_per_video': 10,
        'max_replies_per_comment': 0  # No replies
    }
    result1 = youtube_service.collect_channel_data(channel_id, options1)
    print_comment_summary(result1)
    
    # Example 2: Balanced collection (some replies)
    print("\nEXAMPLE 2: Balanced collection (with replies)")
    print("-------------------------------------------")
    options2 = {
        'fetch_channel_data': False,
        'fetch_videos': True,
        'fetch_comments': True,
        'max_videos': 2,  # Limit to 2 videos for the example
        'max_comments_per_video': 10,
        'max_replies_per_comment': 5  # Up to 5 replies per comment
    }
    result2 = youtube_service.collect_channel_data(channel_id, options2)
    print_comment_summary(result2)
    
    # Example 3: Comprehensive collection
    print("\nEXAMPLE 3: Comprehensive collection")
    print("-----------------------------------")
    options3 = {
        'fetch_channel_data': False,
        'fetch_videos': True,
        'fetch_comments': True,
        'max_videos': 1,  # Limit to 1 video for the example (to save quota)
        'max_comments_per_video': 20,
        'max_replies_per_comment': 10  # Up to 10 replies per comment
    }
    result3 = youtube_service.collect_channel_data(channel_id, options3)
    print_comment_summary(result3)
    
    print("\nComparison of Collection Methods:")
    print("-------------------------------")
    print("Top-level only:   Quick analysis, minimal quota usage")
    print("Balanced:         Good conversation context, moderate quota")
    print("Comprehensive:    Complete engagement data, highest quota usage")

def print_comment_summary(result):
    """Print a summary of the collected comments."""
    if not result or 'video_id' not in result:
        print("No video data found")
        return
    
    videos = result.get('video_id', [])
    total_videos = len(videos)
    total_comments = 0
    total_top_level = 0
    total_replies = 0
    
    for video in videos:
        if 'comments' not in video:
            continue
        
        comments = video['comments']
        top_level = [c for c in comments if 'parent_id' not in c]
        replies = [c for c in comments if 'parent_id' in c]
        
        total_top_level += len(top_level)
        total_replies += len(replies)
        total_comments += len(comments)
        
        print(f"Video: {video.get('title', 'Unknown')}")
        print(f"  - Top-level comments: {len(top_level)}")
        print(f"  - Replies: {len(replies)}")
    
    print(f"\nTotal videos processed: {total_videos}")
    print(f"Total top-level comments: {total_top_level}")
    print(f"Total replies: {total_replies}")
    print(f"Total comments: {total_comments}")


if __name__ == "__main__":
    # This can be run as a standalone script with appropriate imports
    # Or imported and called from another module
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python examples/comment_collection.py API_KEY CHANNEL_ID")
        sys.exit(1)
        
    from src.services.youtube_service import YouTubeService
    
    service = YouTubeService(api_key=sys.argv[1])
    collect_comments_example(service, sys.argv[2])
