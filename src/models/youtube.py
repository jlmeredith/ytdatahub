"""
Data models for the YouTube scraper application.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class VideoLocation:
    """Model representing a location associated with a YouTube video"""
    location_type: str
    location_name: str
    confidence: float = 0.0
    source: str = 'auto'
    created_at: str = ''
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoLocation':
        """Create a VideoLocation object from a dictionary"""
        return cls(
            location_type=data.get('location_type', ''),
            location_name=data.get('location_name', ''),
            confidence=float(data.get('confidence', 0.0)),
            source=data.get('source', 'auto'),
            created_at=data.get('created_at', '')
        )

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
    # New fields from updated schema
    dislike_count: int = 0
    favorite_count: int = 0
    dimension: str = ''
    definition: str = ''
    licensed_content: bool = False
    projection: str = ''
    privacy_status: str = ''
    license: str = ''
    embeddable: bool = True
    public_stats_viewable: bool = True
    made_for_kids: bool = False
    thumbnail_default: str = '' 
    thumbnail_medium: str = ''
    thumbnail_high: str = ''
    live_broadcast_content: str = ''
    fetched_at: str = ''
    updated_at: str = ''
    # Location data support
    locations: List[VideoLocation] = field(default_factory=list)
    comments: List[VideoComment] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YouTubeVideo':
        """Create a Video object from a dictionary"""
        comments_list = []
        for comment_data in data.get('comments', []):
            comments_list.append(VideoComment.from_dict(comment_data))
            
        locations_list = []
        for location_data in data.get('locations', []):
            locations_list.append(VideoLocation.from_dict(location_data))
            
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
            # New fields from updated schema
            dislike_count=int(data.get('dislike_count', 0)),
            favorite_count=int(data.get('favorite_count', 0)),
            dimension=data.get('dimension', ''),
            definition=data.get('definition', ''),
            licensed_content=data.get('licensed_content', False),
            projection=data.get('projection', ''),
            privacy_status=data.get('privacy_status', ''),
            license=data.get('license', ''),
            embeddable=data.get('embeddable', True),
            public_stats_viewable=data.get('public_stats_viewable', True),
            made_for_kids=data.get('made_for_kids', False),
            thumbnail_default=data.get('thumbnail_default', ''),
            thumbnail_medium=data.get('thumbnail_medium', ''),
            thumbnail_high=data.get('thumbnail_high', '') or data.get('thumbnails', ''),
            live_broadcast_content=data.get('live_broadcast_content', ''),
            fetched_at=data.get('fetched_at', ''),
            updated_at=data.get('updated_at', ''),
            locations=locations_list,
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
    # New fields from updated schema
    custom_url: str = ''
    default_language: str = ''
    privacy_status: str = ''
    is_linked: bool = False
    long_uploads_status: str = ''
    made_for_kids: bool = False
    hidden_subscriber_count: bool = False
    thumbnail_default: str = ''
    thumbnail_medium: str = ''
    thumbnail_high: str = ''
    keywords: str = ''
    topic_categories: str = ''
    fetched_at: str = ''
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
            # New fields
            custom_url=data.get('custom_url', ''),
            default_language=data.get('default_language', ''),
            privacy_status=data.get('privacy_status', ''),
            is_linked=data.get('is_linked', False),
            long_uploads_status=data.get('long_uploads_status', ''),
            made_for_kids=data.get('made_for_kids', False),
            hidden_subscriber_count=data.get('hidden_subscriber_count', False),
            thumbnail_default=data.get('thumbnail_default', ''),
            thumbnail_medium=data.get('thumbnail_medium', ''),
            thumbnail_high=data.get('thumbnail_high', '') or data.get('thumbnails', ''),
            keywords=data.get('keywords', ''),
            topic_categories=data.get('topic_categories', ''),
            fetched_at=data.get('fetched_at', ''),
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
                
            # Process video locations
            locations_data = []
            for location in video.locations:
                locations_data.append({
                    'location_type': location.location_type,
                    'location_name': location.location_name,
                    'confidence': location.confidence,
                    'source': location.source,
                    'created_at': location.created_at
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
                'comments': comments_data,
                'locations': locations_data
            })
            
        return {
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'subscribers': str(self.subscribers) if self.subscribers else str(self.subscriber_count),
            'views': str(self.views) if self.views else str(self.view_count),
            'total_videos': str(self.total_videos) if self.total_videos else str(self.video_count),
            'channel_description': self.channel_description,
            'playlist_id': self.playlist_id,
            # New fields
            'custom_url': self.custom_url,
            'published_at': self.published_at,
            'country': self.country,
            'default_language': self.default_language,
            'privacy_status': self.privacy_status,
            'is_linked': self.is_linked,
            'long_uploads_status': self.long_uploads_status,
            'made_for_kids': self.made_for_kids,
            'hidden_subscriber_count': self.hidden_subscriber_count,
            'thumbnail_default': self.thumbnail_default,
            'thumbnail_medium': self.thumbnail_medium,
            'thumbnail_high': self.thumbnail_high,
            'keywords': self.keywords,
            'topic_categories': self.topic_categories,
            'fetched_at': self.fetched_at,
            'video_id': videos_data
        }

# For backward compatibility
Video = YouTubeVideo
Channel = YouTubeChannel
Comment = VideoComment

# Explicitly expose these classes in __all__
__all__ = ['YouTubeChannel', 'YouTubeVideo', 'VideoComment', 'Video', 'Channel', 'Comment']