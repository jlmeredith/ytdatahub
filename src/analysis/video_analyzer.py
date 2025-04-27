"""
Video-specific analytics module.
"""
import pandas as pd
import numpy as np
from src.analysis.base_analyzer import BaseAnalyzer
from src.utils.helpers import duration_to_seconds, format_duration

class VideoAnalyzer(BaseAnalyzer):
    """Class for analyzing YouTube video data."""
    
    def get_video_statistics(self, channel_data):
        """
        Get detailed video statistics.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with video statistics and DataFrame
        """
        if not self.validate_data(channel_data, ['videos']):
            return {
                'total_videos': 0,
                'total_views': 0,
                'avg_views': 0,
                'df': None
            }
            
        videos = channel_data['videos']
        if not videos:
            return {
                'total_videos': 0,
                'total_views': 0,
                'avg_views': 0,
                'df': None
            }
            
        # Create pandas DataFrame from videos
        data = []
        for video in videos:
            row = {
                'Video ID': video.get('id', 'Unknown'),
                'Title': video.get('snippet', {}).get('title', 'Unknown'),
                'Published': video.get('snippet', {}).get('publishedAt', ''),
                'Views': self.safe_int_value(video.get('statistics', {}).get('viewCount', 0)),
                'Likes': self.safe_int_value(video.get('statistics', {}).get('likeCount', 0)),
                'Comments': self.safe_int_value(video.get('statistics', {}).get('commentCount', 0)),
                'Duration': format_duration(duration_to_seconds(video.get('contentDetails', {}).get('duration', ''))),
                'Duration_Seconds': duration_to_seconds(video.get('contentDetails', {}).get('duration', ''))
            }
            data.append(row)
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add date information (clean dates)
        if 'Published' in df.columns:
            try:
                df['Published'] = pd.to_datetime(df['Published']).dt.date
            except:
                pass
        
        # Calculate statistics
        total_views = df['Views'].sum() if 'Views' in df.columns else 0
        avg_views = int(df['Views'].mean()) if 'Views' in df.columns and len(df) > 0 else 0
        
        return {
            'total_videos': len(videos),
            'total_views': int(total_views),
            'avg_views': avg_views,
            'df': df
        }
    
    def get_top_videos(self, channel_data, n=10, by='Views'):
        """
        Get top videos by a specific metric.
        
        Args:
            channel_data: Dictionary containing channel data
            n: Number of top videos to return
            by: Metric to sort by ('Views', 'Likes', 'Comments')
            
        Returns:
            Dictionary with top videos DataFrame
        """
        # Get video statistics first
        video_stats = self.get_video_statistics(channel_data)
        
        if video_stats['df'] is None:
            return {'df': None}
            
        df = video_stats['df']
        
        # Sort by the requested metric and get top n
        if by in df.columns:
            top_df = df.sort_values(by=by, ascending=False).head(n).reset_index(drop=True)
            return {'df': top_df}
        else:
            return {'df': df.head(n)}
    
    def get_publication_timeline(self, channel_data):
        """
        Analyze publication timeline.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with timeline DataFrames
        """
        video_stats = self.get_video_statistics(channel_data)
        
        if video_stats['df'] is None:
            return {'monthly_df': None, 'yearly_df': None}
            
        df = video_stats['df']
        
        if 'Published' not in df.columns:
            return {'monthly_df': None, 'yearly_df': None}
            
        # Ensure date is in datetime format
        try:
            df['Published'] = pd.to_datetime(df['Published'])
        except:
            return {'monthly_df': None, 'yearly_df': None}
        
        # Extract year and month
        df['Year'] = df['Published'].dt.year
        df['Month'] = df['Published'].dt.month
        df['Month-Year'] = df['Published'].dt.strftime('%b %Y')
        
        # Monthly analysis
        monthly = df.groupby('Month-Year').size().reset_index(name='Count')
        
        # Make sure we're sorted chronologically
        try:
            # Add a hidden datetime column to sort by
            monthly['__date'] = pd.to_datetime(monthly['Month-Year'], format='%b %Y')
            monthly = monthly.sort_values('__date').drop('__date', axis=1).reset_index(drop=True)
        except:
            # Fallback if the conversion fails
            pass
            
        # Yearly analysis
        yearly = df.groupby('Year').size().reset_index(name='Videos')
        yearly = yearly.sort_values('Year')
        
        return {
            'monthly_df': monthly,
            'yearly_df': yearly
        }
    
    def get_duration_analysis(self, channel_data):
        """
        Analyze video durations.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with duration analysis
        """
        video_stats = self.get_video_statistics(channel_data)
        
        if video_stats['df'] is None:
            return {'category_df': None, 'stats': {}}
            
        df = video_stats['df']
        
        if 'Duration_Seconds' not in df.columns:
            return {'category_df': None, 'stats': {}}
            
        # Categorize videos by duration
        def categorize_duration(seconds):
            if seconds < 60:
                return 'Under 1 min'
            elif seconds < 300:
                return '1-5 mins'
            elif seconds < 600:
                return '5-10 mins'
            elif seconds < 1200:
                return '10-20 mins'
            elif seconds < 1800:
                return '20-30 mins'
            elif seconds < 3600:
                return '30-60 mins'
            else:
                return 'Over 60 mins'
                
        df['Duration Category'] = df['Duration_Seconds'].apply(categorize_duration)
        
        # Create category DataFrame
        categories = ['Under 1 min', '1-5 mins', '5-10 mins', '10-20 mins', 
                      '20-30 mins', '30-60 mins', 'Over 60 mins']
        category_counts = df['Duration Category'].value_counts().reindex(categories).fillna(0).astype(int)
        category_df = pd.DataFrame({
            'Duration Category': category_counts.index,
            'Count': category_counts.values
        })
        
        # Calculate statistics
        min_duration = df['Duration_Seconds'].min()
        max_duration = df['Duration_Seconds'].max()
        avg_duration = df['Duration_Seconds'].mean()
        
        # Import the human-friendly formatter
        from src.utils.helpers import format_duration, format_duration_human_friendly
        
        stats = {
            'min_duration_seconds': int(min_duration),
            'max_duration_seconds': int(max_duration),
            'avg_duration_seconds': int(avg_duration),
            'min_duration_formatted': format_duration(min_duration),
            'max_duration_formatted': format_duration(max_duration),
            'avg_duration_formatted': format_duration(avg_duration),
            'min_duration_human': format_duration_human_friendly(min_duration),
            'max_duration_human': format_duration_human_friendly(max_duration),
            'avg_duration_human': format_duration_human_friendly(avg_duration)
        }
        
        return {
            'category_df': category_df,
            'stats': stats
        }