#!/usr/bin/env python3
"""
YTDataHub Comment Collection Unit Test

This script tests the enhanced comment collection functionality
by validating that max_replies_per_comment is correctly applied.

Usage:
  python test_comment_collection.py
"""

import os
import json
import unittest
from unittest import mock
from src.api.youtube import YouTubeAPI, CommentClient

class CommentCollectionTest(unittest.TestCase):
    """Test cases for enhanced comment collection."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load mock responses
        self.mock_channel = {
            "id": "UC123456789",
            "snippet": {
                "title": "Test Channel",
                "description": "Channel for testing"
            }
        }
        
        self.mock_videos = {
            "video_id": [
                {
                    "video_id": "video1",
                    "title": "Test Video 1",
                    "statistics": {"commentCount": "10"}
                }
            ]
        }
        
        # Mock comment thread response - top level comments with replies
        self.mock_comments_response = {
            "items": [
                {
                    "id": "comment1",
                    "snippet": {
                        "topLevelComment": {
                            "id": "comment1",
                            "snippet": {
                                "textDisplay": "Top level comment 1",
                                "authorDisplayName": "User1",
                                "publishedAt": "2023-01-01T12:00:00Z",
                                "likeCount": 5
                            }
                        }
                    },
                    "replies": {
                        "comments": [
                            {
                                "id": "reply1-1",
                                "snippet": {
                                    "textDisplay": "This is reply 1 to comment 1",
                                    "authorDisplayName": "User2",
                                    "publishedAt": "2023-01-01T12:30:00Z",
                                    "likeCount": 1
                                }
                            },
                            {
                                "id": "reply1-2",
                                "snippet": {
                                    "textDisplay": "This is reply 2 to comment 1",
                                    "authorDisplayName": "User3",
                                    "publishedAt": "2023-01-01T12:35:00Z",
                                    "likeCount": 0
                                }
                            },
                            {
                                "id": "reply1-3",
                                "snippet": {
                                    "textDisplay": "This is reply 3 to comment 1",
                                    "authorDisplayName": "User4",
                                    "publishedAt": "2023-01-01T12:40:00Z",
                                    "likeCount": 2
                                }
                            },
                            {
                                "id": "reply1-4",
                                "snippet": {
                                    "textDisplay": "This is reply 4 to comment 1",
                                    "authorDisplayName": "User5",
                                    "publishedAt": "2023-01-01T12:45:00Z",
                                    "likeCount": 1
                                }
                            }
                        ]
                    }
                },
                {
                    "id": "comment2",
                    "snippet": {
                        "topLevelComment": {
                            "id": "comment2",
                            "snippet": {
                                "textDisplay": "Top level comment 2",
                                "authorDisplayName": "User6",
                                "publishedAt": "2023-01-02T12:00:00Z",
                                "likeCount": 10
                            }
                        }
                    },
                    "replies": {
                        "comments": [
                            {
                                "id": "reply2-1",
                                "snippet": {
                                    "textDisplay": "This is reply 1 to comment 2",
                                    "authorDisplayName": "User7",
                                    "publishedAt": "2023-01-02T12:30:00Z",
                                    "likeCount": 3
                                }
                            },
                            {
                                "id": "reply2-2",
                                "snippet": {
                                    "textDisplay": "This is reply 2 to comment 2",
                                    "authorDisplayName": "User8",
                                    "publishedAt": "2023-01-02T12:35:00Z",
                                    "likeCount": 2
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        # Create a mock for the YouTube API
        self.mock_youtube = mock.MagicMock()
        
        # Set up mock for video details request
        mock_video_details = mock.MagicMock()
        mock_video_details.execute.return_value = {
            "items": [
                {
                    "id": "video1",
                    "statistics": {
                        "commentCount": "10"
                    }
                }
            ]
        }
        self.mock_youtube.videos().list.return_value = mock_video_details
        
        # Set up mock for comment threads request
        mock_comments = mock.MagicMock()
        mock_comments.execute.return_value = self.mock_comments_response
        self.mock_youtube.commentThreads().list.return_value = mock_comments
    
    @mock.patch('src.api.youtube.comment.build')
    def test_max_replies_parameter(self, mock_build):
        """Test that max_replies_per_comment limits the number of replies collected."""
        mock_build.return_value = self.mock_youtube
        
        # Create comment client with mocked API
        client = CommentClient("dummy_api_key")
        
        # Test Case 1: No replies (max_replies_per_comment=0)
        result1 = client.get_video_comments(
            self.mock_videos,
            max_comments_per_video=2,
            max_replies_per_comment=0
        )
        
        # Extract comments for analysis
        video_comments1 = result1['video_id'][0]['comments']
        
        # Verify we have only top-level comments, no replies
        top_level1 = [c for c in video_comments1 if 'parent_id' not in c]
        replies1 = [c for c in video_comments1 if 'parent_id' in c]
        
        print("=== TEST CASE 1: max_replies_per_comment=0 ===")
        print(f"Top-level comments: {len(top_level1)}")
        print(f"Replies: {len(replies1)}")
        self.assertEqual(len(top_level1), 2, "Should have 2 top-level comments")
        self.assertEqual(len(replies1), 0, "Should have 0 replies with max_replies_per_comment=0")
        
        # Test Case 2: Limited replies (max_replies_per_comment=2)
        result2 = client.get_video_comments(
            self.mock_videos,
            max_comments_per_video=2,
            max_replies_per_comment=2
        )
        
        # Extract comments for analysis
        video_comments2 = result2['video_id'][0]['comments']
        
        # Verify we have top-level comments and limited replies
        top_level2 = [c for c in video_comments2 if 'parent_id' not in c]
        replies2 = [c for c in video_comments2 if 'parent_id' in c]
        
        print("\n=== TEST CASE 2: max_replies_per_comment=2 ===")
        print(f"Top-level comments: {len(top_level2)}")
        print(f"Replies: {len(replies2)}")
        
        # Count replies per top-level comment
        reply_counts = {}
        for reply in replies2:
            parent_id = reply['parent_id']
            reply_counts[parent_id] = reply_counts.get(parent_id, 0) + 1
        
        print(f"Replies per top-level comment: {reply_counts}")
        
        self.assertEqual(len(top_level2), 2, "Should have 2 top-level comments")
        self.assertEqual(len(replies2), 4, "Should have 4 total replies (2 per comment)")
        for comment_id, count in reply_counts.items():
            self.assertLessEqual(count, 2, f"Each comment should have at most 2 replies")
        
        # Test Case 3: All replies (max_replies_per_comment=10)
        result3 = client.get_video_comments(
            self.mock_videos,
            max_comments_per_video=2,
            max_replies_per_comment=10
        )
        
        # Extract comments for analysis
        video_comments3 = result3['video_id'][0]['comments']
        
        # Verify we have top-level comments and all available replies
        top_level3 = [c for c in video_comments3 if 'parent_id' not in c]
        replies3 = [c for c in video_comments3 if 'parent_id' in c]
        
        print("\n=== TEST CASE 3: max_replies_per_comment=10 ===")
        print(f"Top-level comments: {len(top_level3)}")
        print(f"Replies: {len(replies3)}")
        
        self.assertEqual(len(top_level3), 2, "Should have 2 top-level comments")
        self.assertEqual(len(replies3), 6, "Should have 6 total replies (all available)")
        
        print("\nTest completed successfully!")

if __name__ == "__main__":
    unittest.main()
