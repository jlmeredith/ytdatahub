"""
Unit tests for video view count extraction functionality
"""
import pytest
from src.utils.video_formatter import extract_video_views, fix_missing_views
from src.utils.debug_utils import debug_log

# Sample video data from actual YouTube API - with the problematic view structure
SAMPLE_VIDEO = {
    "video_id": "sTsT1rFkMCA",
    "title": "Sample Video Title",
    "published_at": "2025-04-21T19:00:58Z",
    "snippet": {
        "title": "Sample Video Title",
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
    "title": "Sample Video Title",
    "published_at": "2025-04-21T19:00:58Z", 
    "views": "0",  # This is a placeholder value
    "statistics": {
        "likeCount": "1293",
        "favoriteCount": "0",
        "commentCount": "183"
        # ViewCount is intentionally missing
    }
}

# Version with proper viewCount in statistics (normal case)
SAMPLE_VIDEO_WITH_VIEWCOUNT = {
    "video_id": "sTsT1rFkMCA",
    "title": "Sample Video Title",
    "published_at": "2025-04-21T19:00:58Z",
    "statistics": {
        "viewCount": "12345",
        "likeCount": "1293",
        "favoriteCount": "0",
        "commentCount": "183"
    }
}

# Version with nested viewCount structure (edge case)
SAMPLE_VIDEO_WITH_NESTED_VIEWCOUNT = {
    "video_id": "sTsT1rFkMCA",
    "title": "Sample Video Title",
    "published_at": "2025-04-21T19:00:58Z",
    "contentDetails": {
        "statistics": {
            "viewCount": "54321"
        }
    }
}

class TestVideoViewExtraction:
    """Test cases for video view count extraction"""
    
    def test_missing_views_and_viewcount(self):
        """Test extraction when both views and viewCount are missing"""
        video = SAMPLE_VIDEO.copy()
        
        # Direct extraction should return '0' as fallback
        assert extract_video_views(video) == '0'
        
        # Fix missing views and then extract
        fixed_video = fix_missing_views([video])[0]
        assert fixed_video.get('views', None) == '0'
    
    def test_placeholder_zero_views(self):
        """Test handling of placeholder '0' value for views"""
        video = SAMPLE_VIDEO_WITH_ZERO.copy()
        
        # Direct extraction should return the placeholder value
        assert extract_video_views(video) == '0'
        
        # Fix should attempt to find better data but will still return '0' 
        # since there's no viewCount in statistics
        fixed_video = fix_missing_views([video])[0]
        assert fixed_video.get('views', None) == '0'
    
    def test_viewcount_in_statistics(self):
        """Test extraction from statistics.viewCount"""
        video = SAMPLE_VIDEO_WITH_VIEWCOUNT.copy()
        
        # Direct extraction without views field should find viewCount in statistics
        assert extract_video_views(video) == '12345'
        
        # The fix function should populate the views field
        fixed_video = fix_missing_views([video])[0]
        assert fixed_video.get('views', None) == '12345'
    
    def test_nested_viewcount(self):
        """Test extraction from contentDetails.statistics.viewCount"""
        video = SAMPLE_VIDEO_WITH_NESTED_VIEWCOUNT.copy()
        
        # Direct extraction should navigate to the nested location
        assert extract_video_views(video) == '54321'
        
        # The fix function should extract and set views field
        fixed_video = fix_missing_views([video])[0]
        assert fixed_video.get('views', None) == '54321'
    
    def test_mixed_video_batch(self):
        """Test fixing a batch of videos with different view data structures"""
        # Create a mixed batch of videos
        videos = [
            SAMPLE_VIDEO.copy(),
            SAMPLE_VIDEO_WITH_ZERO.copy(),
            SAMPLE_VIDEO_WITH_VIEWCOUNT.copy(),
            SAMPLE_VIDEO_WITH_NESTED_VIEWCOUNT.copy()
        ]
        
        # Fix all videos in batch
        fixed_videos = fix_missing_views(videos)
        
        # Verify each was handled correctly
        assert fixed_videos[0].get('views', None) == '0'  # Missing viewCount
        assert fixed_videos[1].get('views', None) == '0'  # Placeholder zero
        assert fixed_videos[2].get('views', None) == '12345'  # Standard viewCount
        assert fixed_videos[3].get('views', None) == '54321'  # Nested viewCount
    
    def test_regex_extraction_fallback(self):
        """Test view count extraction using regex when other methods fail"""
        # Create a video with viewCount as a string property
        video = {
            "video_id": "abc123",
            "raw_data": '{"statistics": {"viewCount": "9876"}}'
        }
        
        # The fix function should use regex to extract viewCount from raw_data
        fixed_video = fix_missing_views([video])[0]
        assert fixed_video.get('views', None) == '9876'

if __name__ == "__main__":
    pytest.main()
