#!/usr/bin/env python3
"""
YTDataHub Comment Collection Example

This script demonstrates the enhanced comment collection process in YTDataHub,
showing how to control both the number of top-level comments and replies per comment.

Usage:
  python comment_collection_example.py --api-key YOUR_API_KEY --channel "@channelname"
"""

import argparse
import json
from src.api.youtube import YouTubeAPI

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Demonstrate YTDataHub comment collection")
    parser.add_argument("--api-key", required=True, help="YouTube Data API key")
    parser.add_argument("--channel", required=True, help="Channel ID, handle or custom URL")
    parser.add_argument("--max-comments", type=int, default=10, 
                       help="Maximum number of top-level comments per video (0-100)")
    parser.add_argument("--max-replies", type=int, default=5,
                       help="Maximum number of replies per top-level comment (0-50)")
    parser.add_argument("--max-videos", type=int, default=3,
                       help="Maximum number of videos to process")
    args = parser.parse_args()
    
    # Initialize the API client
    api = YouTubeAPI(api_key=args.api_key)
    print(f"✅ API initialized")
    
    # Get channel information
    print(f"🔍 Fetching channel info for {args.channel}...")
    channel_info = api.get_channel_info(args.channel)
    if not channel_info:
        print("❌ Channel not found")
        return
    
    print(f"✅ Found channel: {channel_info['snippet']['title']}")
    
    # Get videos for the channel
    print(f"🔍 Fetching up to {args.max_videos} videos...")
    videos_response = api.get_channel_videos(channel_info, max_videos=args.max_videos)
    if not videos_response or 'video_id' not in videos_response or not videos_response['video_id']:
        print("❌ No videos found")
        return
    
    video_count = len(videos_response['video_id'])
    print(f"✅ Found {video_count} videos")
    
    # Collect comments
    print(f"🔍 Collecting comments with parameters:")
    print(f"   - Top-level comments per video: {args.max_comments}")
    print(f"   - Replies per top-level comment: {args.max_replies}")
    
    comments_response = api.get_video_comments(
        videos_response,
        max_comments_per_video=args.max_comments,
        max_replies_per_comment=args.max_replies
    )
    
    # Process results
    print("\n=== COMMENT COLLECTION RESULTS ===")
    
    total_top_level = 0
    total_replies = 0
    
    for video in comments_response['video_id']:
        if 'comments' not in video or not video['comments']:
            print(f"No comments for video: {video.get('title', 'Unknown')}")
            continue
        
        video_comments = video['comments']
        top_level_comments = [c for c in video_comments if 'parent_id' not in c]
        replies = [c for c in video_comments if 'parent_id' in c]
        
        print(f"\nVideo: {video.get('title', 'Unknown')}")
        print(f"  - Top-level comments: {len(top_level_comments)}")
        print(f"  - Replies: {len(replies)}")
        
        total_top_level += len(top_level_comments)
        total_replies += len(replies)
        
        # Print sample comments
        print("\n  Sample Comments:")
        for i, comment in enumerate(top_level_comments[:2]):  # Show first 2 top-level comments
            print(f"  {i+1}. {comment['comment_author']}: {comment['comment_text'][:100]}...")
            
            # Find replies to this comment
            comment_replies = [r for r in replies if r.get('parent_id') == comment['comment_id']]
            for j, reply in enumerate(comment_replies[:2]):  # Show first 2 replies
                print(f"     └─ {reply['comment_author']}: {reply['comment_text'][:80]}...")
    
    print("\n=== SUMMARY ===")
    print(f"Total top-level comments: {total_top_level}")
    print(f"Total replies: {total_replies}")
    print(f"Total comments: {total_top_level + total_replies}")
    
    # Quota impact estimation
    estimated_calls = video_count + (1 if total_replies > 0 else 0)
    print(f"\nEstimated API calls: ~{estimated_calls}")
    print("Note: Actual quota usage may vary based on pagination and caching")

if __name__ == "__main__":
    main()
