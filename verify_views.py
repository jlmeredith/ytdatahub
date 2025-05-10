#!/usr/bin/env python3
"""
Script to verify view count extraction from YouTube API response
This script doubles as a manual test utility and a test runner for our automated tests.
"""

import json
import sys
import pytest
from src.utils.helpers import debug_log
from src.utils.video_formatter import fix_missing_views, extract_video_views

# Sample video data from actual YouTube API - with the problematic view structure
SAMPLE_VIDEO = {
    "video_id": "sTsT1rFkMCA",
    "title": "The True Life Story of a Former Satanic Vampire",
    "published_at": "2025-04-21T19:00:58Z",
    "snippet": {
        "title": "The True Life Story of a Former Satanic Vampire",
        "publishedAt": "2025-04-21T19:00:58Z"
    },
    "contentDetails": {
        "duration": "PT14M57S",
        "definition": "hd",
        "caption": "false"
    },
    "statistics": {
        "likeCount": "1293",
        "favoriteCount": "0",
        "commentCount": "183"
        # ViewCount is intentionally missing to test our fix
    }
}

# Version with views directly set to "0" placeholder, which happens in some cases
SAMPLE_VIDEO_WITH_ZERO = {
    "video_id": "sTsT1rFkMCA",
    "title": "The True Life Story of a Former Satanic Vampire",
    "published_at": "2025-04-21T19:00:58Z", 
    "views": "0",  # This is a placeholder value
    "statistics": {
        "likeCount": "1293",
        "favoriteCount": "0",
        "commentCount": "183"
        # ViewCount is intentionally missing
    }
}

def main():
    print("Verifying view count extraction...")
    print("=" * 50)
    
    # Check for command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--run-tests':
        print("Running automated tests with pytest...")
        # Run our automated test suite
        pytest.main(['-xvs', 'tests/unit/test_video_views.py', 'tests/ui/test_video_views_display.py'])
        return
    
    # Test 1: Missing views and viewCount entirely
    print("Test 1: Missing views and viewCount entirely")
    video1 = SAMPLE_VIDEO.copy()
    print(f"Original video keys: {list(video1.keys())}")
    print(f"Original statistics keys: {list(video1['statistics'].keys())}")
    print(f"Direct views value: {video1.get('views', 'Not present')}")
    
    # Fix the video using our utility
    fixed_video1 = fix_missing_views([video1])[0]
    print(f"After fix, views = {fixed_video1.get('views', 'Still missing')}")
    print(f"Extracted views = {extract_video_views(fixed_video1)}")
    print("-" * 50)
    
    # Test 2: Video with placeholder "0" value
    print("Test 2: Video with placeholder '0' value")
    video2 = SAMPLE_VIDEO_WITH_ZERO.copy()
    print(f"Original video: views = {video2.get('views', 'Not present')}")
    
    # Fix the video
    fixed_video2 = fix_missing_views([video2])[0]
    print(f"After fix, views = {fixed_video2.get('views', 'Still missing')}")
    print("-" * 50)
    
    # Test 3: Valid viewCount in statistics
    print("Test 3: Valid viewCount in statistics")
    video3 = SAMPLE_VIDEO.copy()
    video3['statistics']['viewCount'] = "12345"
    print(f"Original video: views = {video3.get('views', 'Not present')}, statistics.viewCount = {video3['statistics']['viewCount']}")
    
    # Fix the video
    fixed_video3 = fix_missing_views([video3])[0]
    print(f"After fix, views = {fixed_video3.get('views', 'Still missing')}")
    print("-" * 50)
    
    # Test 4: Deeply nested viewCount in contentDetails.statistics
    print("Test 4: Deeply nested viewCount")
    video4 = SAMPLE_VIDEO.copy()
    # Create a nested structure
    video4['contentDetails']['statistics'] = {'viewCount': '54321'}
    print(f"Original video: nested structure with contentDetails.statistics.viewCount = {video4['contentDetails']['statistics']['viewCount']}")
    
    # Fix the video
    fixed_video4 = fix_missing_views([video4])[0]
    print(f"After fix, views = {fixed_video4.get('views', 'Still missing')}")
    print("-" * 50)
    
    # Test 5: API response with string-encoded statistics
    print("Test 5: String-encoded statistics")
    video5 = SAMPLE_VIDEO.copy()
    # Remove the regular statistics and replace with a string version
    string_stats = json.dumps({'viewCount': '98765', 'likeCount': '1000'})
    video5['statistics'] = string_stats
    print(f"Original video: statistics = '{string_stats}'")
    
    # Fix the video
    fixed_video5 = fix_missing_views([video5])[0]
    print(f"After fix, views = {fixed_video5.get('views', 'Still missing')}")
    print("-" * 50)
    
    # Test 6: Alternative field names like 'viewcount' (lowercase)
    print("Test 6: Alternative field names")
    video6 = SAMPLE_VIDEO.copy()
    video6['viewcount'] = '87654'  # Non-standard field name
    print(f"Original video with non-standard field: viewcount = {video6['viewcount']}")
    
    # Fix the video
    fixed_video6 = fix_missing_views([video6])[0]
    print(f"After fix, views = {fixed_video6.get('views', 'Still missing')}")
    print("-" * 50)
    
    print("Manual tests complete!")
    print()
    print("To run full automated tests with pytest, use: python verify_views.py --run-tests")

if __name__ == "__main__":
    main()
