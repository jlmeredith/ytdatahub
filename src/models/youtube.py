"""
Data models for the YouTube scraper application.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class VideoComment:
    """Model representing a YouTube comment"""
    comment_id: str
    comment_text: str
    author_name: str
    published_at: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoComment':
        """Create a Comment object from a dictionary"""
        return cls(
            comment_id=data.get('comment_id', ''),
            comment_text=data.get('comment_text', ''),
            author_name=data.get('comment_authorc', ''),
            published_at=data.get('comment_published_at', '')
        )

@dataclass
class YouTubeVideo:
    """Model representing a YouTube video"""
    video_id: str
    title: str
    description: str = ''
    published_at: str = ''
    views: int = 0
    likes: int = 0
    duration: str = ''
    thumbnail_url: str = ''
    caption_status: str = ''
    channel_id: str = ''
    channel_title: str = ''
    category_id: str = ''
    tags: List[str] = field(default_factory=list)
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    comments: List[VideoComment] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YouTubeVideo':
        """Create a Video object from a dictionary"""
        comments_list = []
        for comment_data in data.get('comments', []):
            comments_list.append(VideoComment.from_dict(comment_data))
            
        return cls(
            video_id=data.get('video_id', ''),
            title=data.get('title', ''),
            description=data.get('video_description', '') or data.get('description', ''),
            published_at=data.get('published_at', ''),
            views=int(data.get('views', 0)),
            likes=int(data.get('likes', 0)),
            view_count=int(data.get('views', 0)),
            like_count=int(data.get('likes', 0)),
            duration=data.get('duration', ''),
            thumbnail_url=data.get('thumbnails', '') or data.get('thumbnail_url', ''),
            caption_status=data.get('caption_status', ''),
            channel_id=data.get('channel_id', ''),
            channel_title=data.get('channel_title', ''),
            category_id=data.get('category_id', ''),
            tags=data.get('tags', []),
            comment_count=int(data.get('comment_count', 0)),
            comments=comments_list
        )

@dataclass
class YouTubeChannel:
    """Model representing a YouTube channel"""
    channel_id: str
    channel_name: str
    subscribers: int = 0
    views: int = 0
    total_videos: int = 0
    channel_description: str = ''
    playlist_id: str = ''
    subscriber_count: int = 0
    video_count: int = 0
    view_count: int = 0
    thumbnail_url: str = ''
    published_at: str = ''
    country: str = ''
    videos: List[YouTubeVideo] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YouTubeChannel':
        """Create a Channel object from a dictionary"""
        videos_list = []
        for video_data in data.get('video_id', []):
            videos_list.append(YouTubeVideo.from_dict(video_data))
            
        return cls(
            channel_id=data.get('channel_id', ''),
            channel_name=data.get('channel_name', ''),
            subscribers=int(data.get('subscribers', 0)),
            views=int(data.get('views', 0)),
            total_videos=int(data.get('total_videos', 0)),
            channel_description=data.get('channel_description', ''),
            playlist_id=data.get('playlist_id', ''),
            subscriber_count=int(data.get('subscribers', 0)),
            video_count=int(data.get('total_videos', 0)),
            view_count=int(data.get('views', 0)),
            thumbnail_url=data.get('thumbnail_url', ''),
            published_at=data.get('published_at', ''),
            country=data.get('country', ''),
            videos=videos_list
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Channel object to a dictionary for storage"""
        videos_data = []
        for video in self.videos:
            comments_data = []
            for comment in video.comments:
                comments_data.append({
                    'comment_id': comment.comment_id,
                    'comment_text': comment.comment_text,
                    'comment_authorc': comment.author_name,
                    'comment_published_at': comment.published_at
                })
                
            videos_data.append({
                'video_id': video.video_id,
                'title': video.title,
                'video_description': video.description,
                'published_at': video.published_at,
                'views': str(video.views) if video.views else str(video.view_count),
                'likes': str(video.likes) if video.likes else str(video.like_count),
                'duration': video.duration,
                'thumbnails': video.thumbnail_url,
                'caption_status': video.caption_status,
                'comments': comments_data
            })
            
        return {
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'subscribers': str(self.subscribers) if self.subscribers else str(self.subscriber_count),
            'views': str(self.views) if self.views else str(self.view_count),
            'total_videos': str(self.total_videos) if self.total_videos else str(self.video_count),
            'channel_description': self.channel_description,
            'playlist_id': self.playlist_id,
            'video_id': videos_data
        }

# For backward compatibility
Video = YouTubeVideo
Channel = YouTubeChannel
Comment = VideoComment

# Explicitly expose these classes in __all__
__all__ = ['YouTubeChannel', 'YouTubeVideo', 'VideoComment', 'Video', 'Channel', 'Comment']