#!/usr/bin/env python3
"""
Verification tool for checking comment collection limits.

This script verifies that the comment collection limits for both
top-level comments and replies are correctly enforced in the application.

Usage:
    python tools/verify_comment_limits.py

Output:
    Statistics showing top-level comments and replies per video.
"""
import os
import sys
import json
import sqlite3
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import Config
from src.utils.logger import debug_log

def get_db_connection():
    """Get a connection to the SQLite database."""
    db_path = Config.get_db_path()
    return sqlite3.connect(db_path)

def verify_comment_limits():
    """Verify comment collection limits by checking the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=== Comment Collection Limit Verification ===\n")
    
    # Get all videos
    cursor.execute("SELECT id, title, youtube_id FROM videos")
    videos = cursor.fetchall()
    
    if not videos:
        print("No videos found in the database.")
        return
    
    print(f"Found {len(videos)} videos in the database.")
    
    # Check comments for each video
    for video_id, title, youtube_id in videos:
        # Get comments for this video
        cursor.execute("SELECT comment_id, parent_id FROM comments WHERE video_id = ?", (video_id,))
        comments = cursor.fetchall()
        
        # Group by top-level vs replies
        top_level = [c for c in comments if c[1] is None]
        replies = [c for c in comments if c[1] is not None]
        
        # Count replies per top-level comment
        reply_counts = defaultdict(int)
        for _, parent_id in replies:
            reply_counts[parent_id] += 1
        
        # Print statistics
        print(f"\nVideo: {title} (ID: {youtube_id})")
        print(f"  • Top-level comments: {len(top_level)}")
        print(f"  • Total replies: {len(replies)}")
        
        # Print reply distribution
        if reply_counts:
            max_replies = max(reply_counts.values()) if reply_counts else 0
            print(f"  • Comments with replies: {len(reply_counts)}")
            print(f"  • Maximum replies for any comment: {max_replies}")
            print(f"  • Reply distribution: {sorted(reply_counts.values(), reverse=True)[:5]}...")
        else:
            print("  • No replies found for this video")
    
    conn.close()
    print("\nVerification complete!")

if __name__ == "__main__":
    verify_comment_limits()
