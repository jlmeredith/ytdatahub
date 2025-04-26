"""
Analytics functions for YouTube data.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.helpers import duration_to_seconds, format_duration

class YouTubeAnalysis:
    """Class for analyzing YouTube data."""
    
    def get_channel_statistics(self, channel_data):
        """
        Get basic channel statistics.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with channel statistics
        """
        if not channel_data or 'channel_info' not in channel_data:
            return {
                'name': 'Unknown Channel',
                'subscribers': 0,
                'views': 0,
                'total_videos': 0,
                'description': 'No channel data available'
            }
            
        channel_info = channel_data['channel_info']
        video_list = channel_data.get('videos', [])
        
        return {
            'name': channel_info.get('title', 'Unknown'),
            'subscribers': int(channel_info.get('statistics', {}).get('subscriberCount', 0)),
            'views': int(channel_info.get('statistics', {}).get('viewCount', 0)),
            'total_videos': len(video_list),
            'description': channel_info.get('description', 'No description available')
        }
    
    def get_video_statistics(self, channel_data):
        """
        Get detailed video statistics.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with video statistics and DataFrame
        """
        if not channel_data or 'videos' not in channel_data or not channel_data['videos']:
            return {
                'total_videos': 0,
                'total_views': 0,
                'avg_views': 0,
                'df': None
            }
            
        videos = channel_data['videos']
        
        # Create pandas DataFrame from videos
        data = []
        for video in videos:
            row = {
                'Video ID': video.get('id', 'Unknown'),
                'Title': video.get('snippet', {}).get('title', 'Unknown'),
                'Published': video.get('snippet', {}).get('publishedAt', ''),
                'Views': int(video.get('statistics', {}).get('viewCount', 0)),
                'Likes': int(video.get('statistics', {}).get('likeCount', 0)),
                'Comments': int(video.get('statistics', {}).get('commentCount', 0)),
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
        avg_views = int(df['Views'].mean()) if 'Views' in df.columns else 0
        
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
    
    def get_comment_analysis(self, channel_data):
        """
        Analyze video comments.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with comment analysis
        """
        if not channel_data or 'comments' not in channel_data or not channel_data['comments']:
            return {
                'total_comments': 0,
                'df': None,
                'temporal_data': None,
                'thread_data': None,
                'engagement_data': None
            }
            
        comments = channel_data['comments']
        
        # Flatten nested comment structure
        data = []
        for video_id, video_comments in comments.items():
            video_title = "Unknown"
            video_publish_date = None
            
            # Try to find the video title and publish date
            if 'videos' in channel_data:
                for video in channel_data['videos']:
                    if video.get('id') == video_id:
                        video_title = video.get('snippet', {}).get('title', "Unknown")
                        video_publish_date = video.get('snippet', {}).get('publishedAt', '')
                        break
            
            for comment in video_comments:
                # Get top-level comment data
                comment_snippet = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
                
                # Determine if it's a thread parent or a reply
                is_reply = False
                parent_id = None
                reply_level = 0
                
                # IMPROVED REPLY DETECTION: Check comment ID format for reply pattern
                comment_id = comment.get('comment_id', comment.get('id', 'Unknown'))
                
                # If this is a reply based on the comment_id structure (contains a dot)
                if '.' in comment_id:
                    is_reply = True
                    # Extract parent_id as everything before the dot
                    parent_id = comment_id.split('.')[0]
                    reply_level = 1
                
                # Additional checks from previous implementation
                elif 'parent_id' in comment:
                    is_reply = True
                    parent_id = comment.get('parent_id')
                    reply_level = 1
                
                # For replies marked with [REPLY] in text (from our API)
                elif isinstance(comment.get('comment_text', ''), str) and comment.get('comment_text', '').startswith('[REPLY]'):
                    is_reply = True
                    # The parent_id might already be available in the comment object
                    if not parent_id and 'parent_id' in comment:
                        parent_id = comment.get('parent_id')
                    reply_level = 1
                
                # Get author and text from either structure
                if 'comment_author' in comment:
                    author = comment.get('comment_author', 'Unknown')
                    text = comment.get('comment_text', 'Unknown')
                    published = comment.get('comment_published_at', '')
                    likes = int(comment.get('like_count', 0))
                    comment_id = comment.get('comment_id', 'Unknown')
                else:
                    author = comment_snippet.get('authorDisplayName', 'Unknown')
                    text = comment_snippet.get('textDisplay', 'Unknown')
                    published = comment_snippet.get('publishedAt', '')
                    likes = int(comment_snippet.get('likeCount', 0))
                    comment_id = comment.get('id', 'Unknown')
                
                # Remove [REPLY] prefix if present in text
                if is_reply and text.startswith('[REPLY] '):
                    text = text[8:]  # Remove the prefix
                
                # Create the row
                row = {
                    'Video ID': video_id,
                    'Video': video_title,
                    'Video Published': video_publish_date, 
                    'Comment ID': comment_id,
                    'Author': author,
                    'Text': text,
                    'Likes': likes,
                    'Published': published,
                    'Is Reply': is_reply,
                    'Parent ID': parent_id,
                    'Reply Level': reply_level
                }
                data.append(row)
                
        if not data:
            return {
                'total_comments': 0,
                'df': None,
                'temporal_data': None,
                'thread_data': None,
                'engagement_data': None
            }
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Process temporal data
        try:
            # Convert string dates to datetime objects for analysis
            df['Published_DateTime'] = pd.to_datetime(df['Published'])
            
            # Extract time components
            df['Date'] = df['Published_DateTime'].dt.date
            df['Year'] = df['Published_DateTime'].dt.year
            df['Month'] = df['Published_DateTime'].dt.month
            df['Month_Name'] = df['Published_DateTime'].dt.strftime('%b')
            df['Day'] = df['Published_DateTime'].dt.day
            df['Weekday'] = df['Published_DateTime'].dt.day_name()
            df['Hour'] = df['Published_DateTime'].dt.hour
            
            # Comments by day
            daily_comments = df.groupby('Date').size().reset_index(name='Count')
            daily_comments = daily_comments.sort_values('Date')
            
            # Comments by month
            monthly_comments = df.groupby(['Year', 'Month', 'Month_Name']).size().reset_index(name='Count')
            monthly_comments['YearMonth'] = monthly_comments['Year'].astype(str) + '-' + monthly_comments['Month_Name']
            monthly_comments = monthly_comments.sort_values(['Year', 'Month'])
            
            # Comments by hour of day
            hourly_comments = df.groupby('Hour').size().reset_index(name='Count')
            
            # Comments by day of week
            dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekday_comments = df.groupby('Weekday').size().reset_index(name='Count')
            weekday_comments['Weekday'] = pd.Categorical(weekday_comments['Weekday'], categories=dow_order, ordered=True)
            weekday_comments = weekday_comments.sort_values('Weekday')
            
            temporal_data = {
                'daily': daily_comments,
                'monthly': monthly_comments,
                'hourly': hourly_comments,
                'weekday': weekday_comments
            }
        except Exception as e:
            # Fallback if there's a problem processing dates
            temporal_data = None
        
        # Analyze comment threads
        try:
            # Count how many comments are replies vs top-level
            thread_data = {
                'top_level_count': len(df[~df['Is Reply']]) if 'Is Reply' in df.columns else len(df),
                'reply_count': len(df[df['Is Reply']]) if 'Is Reply' in df.columns else 0
            }
            
            # Count comments per thread (group by parent ID for replies)
            if 'Parent ID' in df.columns and df['Parent ID'].notna().any():
                # Group replies by parent ID to find threads with most activity
                thread_counts = df[df['Parent ID'].notna()].groupby('Parent ID').size().reset_index(name='Reply Count')
                thread_counts = thread_counts.sort_values('Reply Count', ascending=False)
                
                # Get the threads with the most replies
                top_threads = thread_counts.head(10)
                
                # For each top thread, get the original comment
                top_thread_data = []
                for _, row in top_threads.iterrows():
                    parent_id = row['Parent ID']
                    parent_comment = df[df['Comment ID'] == parent_id]
                    
                    if not parent_comment.empty:
                        thread_info = {
                            'parent_id': parent_id,
                            'reply_count': row['Reply Count'],
                            'parent_text': parent_comment.iloc[0]['Text'],
                            'parent_author': parent_comment.iloc[0]['Author'],
                            'parent_likes': parent_comment.iloc[0]['Likes'],
                            'video': parent_comment.iloc[0]['Video']
                        }
                        top_thread_data.append(thread_info)
                
                thread_data['top_threads'] = top_thread_data
                thread_data['thread_counts'] = thread_counts
                
                # Build a complete thread structure for all comments
                thread_structure = {}
                root_comments = df[~df['Is Reply']].copy()
                
                # First collect all root comments
                for _, root in root_comments.iterrows():
                    thread_structure[root['Comment ID']] = {
                        'comment': root.to_dict(),
                        'replies': []
                    }
                
                # Then add all replies to their parents
                reply_comments = df[df['Is Reply']].copy()
                for _, reply in reply_comments.iterrows():
                    parent_id = reply['Parent ID']
                    if parent_id in thread_structure:
                        thread_structure[parent_id]['replies'].append(reply.to_dict())
                
                thread_data['thread_structure'] = thread_structure
                
        except Exception as e:
            # Fallback if there's a problem processing thread data
            thread_data = {
                'top_level_count': len(df),
                'reply_count': 0
            }
        
        # Engagement analysis
        try:
            # Likes distribution for comments
            engagement_data = {
                'avg_likes': df['Likes'].mean(),
                'max_likes': df['Likes'].max(),
                'total_likes': df['Likes'].sum(),
                'likes_distribution': df['Likes'].value_counts().sort_index().reset_index().rename(columns={'index': 'Like Count', 'Likes': 'Comment Count'})
            }
            
            # Get top liked comments
            top_liked_comments = df.sort_values('Likes', ascending=False).head(10)
            engagement_data['top_liked_comments'] = top_liked_comments
            
        except Exception as e:
            engagement_data = None
        
        # For display compatibility, keep the basic date conversion for the main dataframe
        if 'Published' in df.columns:
            try:
                df['Published'] = pd.to_datetime(df['Published']).dt.date
            except:
                pass
        
        # Drop intermediate columns used for analysis
        if 'Published_DateTime' in df.columns:
            df = df.drop(columns=['Published_DateTime'])
        
        return {
            'total_comments': len(data),
            'df': df,
            'temporal_data': temporal_data,
            'thread_data': thread_data,
            'engagement_data': engagement_data
        }