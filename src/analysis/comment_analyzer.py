"""
Comment-specific analytics module.
"""
import pandas as pd
from datetime import datetime
from src.analysis.base_analyzer import BaseAnalyzer

class CommentAnalyzer(BaseAnalyzer):
    """Class for analyzing YouTube comment data."""
    
    def analyze(self, data):
        """
        Analyze comment data and return comprehensive metrics.
        
        Args:
            data: Dictionary containing channel data with comments
            
        Returns:
            Dictionary with analysis results
        """
        # Get comment analysis which contains all the sub-analyses
        comment_analysis = self.get_comment_analysis(data)
        
        # Return the complete analysis
        return {
            'comment_counts': {
                'total_comments': comment_analysis.get('total_comments', 0),
                'unique_authors': comment_analysis.get('author_stats', {}).get('unique_authors', 0) if comment_analysis.get('author_stats') else 0,
                'reply_percentage': comment_analysis.get('stats', {}).get('reply_percentage', 0) if comment_analysis.get('stats') else 0
            },
            'engagement': {
                'avg_likes_per_comment': comment_analysis.get('stats', {}).get('avg_likes_per_comment', 0) if comment_analysis.get('stats') else 0,
                'most_liked_count': comment_analysis.get('stats', {}).get('most_liked_count', 0) if comment_analysis.get('stats') else 0,
                'creator_comments': comment_analysis.get('stats', {}).get('creator_comments', 0) if comment_analysis.get('stats') else 0
            },
            'content': {
                'avg_comment_length': comment_analysis.get('stats', {}).get('avg_comment_length', 0) if comment_analysis.get('stats') else 0,
                'length_distribution': comment_analysis.get('stats', {}).get('length_distribution', {}) if comment_analysis.get('stats') else {}
            },
            'distribution': {
                'videos_with_comments': comment_analysis.get('stats', {}).get('videos_with_comments', 0) if comment_analysis.get('stats') else 0,
                'comments_per_video': comment_analysis.get('stats', {}).get('comments_per_video', 0) if comment_analysis.get('stats') else 0
            },
            'temporal_data': comment_analysis.get('temporal_data'),
            'thread_data': comment_analysis.get('thread_data'),
            'author_stats': comment_analysis.get('author_stats'),
            'raw_data': comment_analysis
        }
    
    def get_comment_analysis(self, channel_data):
        """
        Analyze video comments.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with comment analysis
        """
        # Create a default return structure for when no comments are found
        empty_result = {
            'total_comments': 0,
            'df': None,
            'temporal_data': None,
            'thread_data': None,
            'engagement_data': None,
            'author_stats': None,
            'stats': None
        }
        
        # Different ways comments might be stored in our data structure
        comments_found = False
        comments = {}
        
        # Method 1: Direct comments dictionary at top level
        if 'comments' in channel_data and channel_data['comments']:
            comments = channel_data['comments']
            comments_found = True
        
        # Method 2: Comments embedded in each video
        elif 'videos' in channel_data and channel_data['videos']:
            # Collect comments from all videos
            video_comments = {}
            for video in channel_data['videos']:
                if 'comments' in video and video['comments']:
                    video_id = video.get('id', video.get('video_id', f"unknown_{len(video_comments)}"))
                    video_comments[video_id] = video['comments']
                    comments_found = True
            
            if comments_found:
                comments = video_comments
        
        # Exit if no comments found through any method
        if not comments_found or not comments:
            return empty_result
            
        # Process comments data
        comment_df = self._process_comments_data(channel_data, comments)
        
        if comment_df.empty:
            return empty_result
        
        # Get temporal analysis
        temporal_data = self._analyze_temporal_data(comment_df)
        
        # Get thread analysis
        thread_data = self._analyze_thread_data(comment_df)
        
        # Get engagement analysis
        engagement_data = self._analyze_engagement_data(comment_df)
        
        # Get author stats
        author_stats = self._analyze_author_stats(comment_df)
        
        # Get basic stats
        stats = self._get_basic_stats(comment_df, channel_data)
        
        return {
            'total_comments': len(comment_df),
            'df': comment_df,
            'temporal_data': temporal_data,
            'thread_data': thread_data,
            'engagement_data': engagement_data,
            'author_stats': author_stats,
            'stats': stats
        }
        
    def _process_comments_data(self, channel_data, comments):
        """Process and flatten the nested comment structure."""
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
                # Check comment ID format for reply pattern
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
                    author = str(comment.get('comment_author', 'Unknown'))
                    text = str(comment.get('comment_text', 'Unknown'))
                    published = comment.get('comment_published_at', '') or ''
                    likes = self.safe_int_value(comment.get('like_count', 0))
                    comment_id = comment.get('comment_id', 'Unknown')
                else:
                    author = str(comment_snippet.get('authorDisplayName', 'Unknown'))
                    text = str(comment_snippet.get('textDisplay', 'Unknown'))
                    published = comment_snippet.get('publishedAt', '') or ''
                    likes = self.safe_int_value(comment_snippet.get('likeCount', 0))
                    comment_id = comment.get('id', 'Unknown')
                # Remove [REPLY] prefix if present in text
                if is_reply and text.startswith('[REPLY] '):
                    text = text[8:]  # Remove the prefix
                # Defensive: ensure all fields are valid types
                if not isinstance(likes, int):
                    try:
                        likes = int(likes)
                    except Exception:
                        likes = 0
                if not isinstance(text, str):
                    text = str(text) if text is not None else 'Unknown'
                if not isinstance(author, str):
                    author = str(author) if author is not None else 'Unknown'
                if published is None:
                    published = ''
                if not isinstance(comment_id, str):
                    comment_id = str(comment_id) if comment_id is not None else 'Unknown'
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
                    'Reply Level': reply_level,
                    'Text Length': len(text) if text else 0
                }
                data.append(row)
        # Create DataFrame
        df = pd.DataFrame(data) if data else pd.DataFrame()
        # Clean dates
        if not df.empty and 'Published' in df.columns:
            try:
                df['Published'] = pd.to_datetime(df['Published'], errors='coerce')
            except Exception:
                pass
        # Ensure Likes is always int and fill NaN with 0
        if not df.empty and 'Likes' in df.columns:
            df['Likes'] = pd.to_numeric(df['Likes'], errors='coerce').fillna(0).astype(int)
        # Ensure Text Length is always int and fill NaN with 0
        if not df.empty and 'Text Length' in df.columns:
            df['Text Length'] = pd.to_numeric(df['Text Length'], errors='coerce').fillna(0).astype(int)
        # Ensure Author and Text are always str
        if not df.empty and 'Author' in df.columns:
            df['Author'] = df['Author'].astype(str)
        if not df.empty and 'Text' in df.columns:
            df['Text'] = df['Text'].astype(str)
        return df

    def _analyze_temporal_data(self, df):
        """Analyze temporal patterns in comments."""
        if df.empty:
            return None
        try:
            # Convert string dates to datetime objects for analysis
            df['Published_DateTime'] = pd.to_datetime(df['Published'], errors='coerce')
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
            weekday_comments = weekday_comments.rename(columns={'Weekday': 'Day'})
            temporal_data = {
                'daily': daily_comments,
                'monthly': monthly_comments,
                'hourly': hourly_comments,
                'day_of_week': weekday_comments
            }
            return temporal_data
        except Exception as e:
            print('Exception in _analyze_temporal_data:', e)
            import traceback
            traceback.print_exc()
            return None

    def _analyze_thread_data(self, df):
        """Analyze comment threads."""
        if df.empty:
            return None
            
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
                
            return thread_data
        except Exception:
            return {
                'top_level_count': len(df),
                'reply_count': 0
            }

    def _analyze_engagement_data(self, df):
        """Analyze engagement metrics for comments."""
        if df.empty:
            return None
            
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
            
            return engagement_data
        except Exception:
            return None

    def _analyze_author_stats(self, df):
        """Analyze commenter statistics."""
        if df.empty:
            return None
            
        try:
            # Count comments by author
            author_counts = df.groupby('Author').size().reset_index(name='Comment Count')
            author_counts = author_counts.sort_values('Comment Count', ascending=False)
            
            # Calculate statistics
            unique_authors = len(author_counts)
            total_comments = len(df)
            
            # Find what percentage of authors account for 10% of comments
            if unique_authors > 0 and total_comments > 0:
                # Sort by comment count descending
                sorted_authors = author_counts.sort_values('Comment Count', ascending=False)
                
                # Calculate cumulative sum
                sorted_authors['Cumulative Count'] = sorted_authors['Comment Count'].cumsum()
                sorted_authors['Cumulative Percent'] = sorted_authors['Cumulative Count'] / total_comments * 100
                
                # Find the authors accounting for first 10% of comments
                top10_percent_authors = len(sorted_authors[sorted_authors['Cumulative Percent'] <= 10])
                
                # Calculate percentage of all authors that make up 10% of comments
                top10_percent = top10_percent_authors / unique_authors * 100 if unique_authors > 0 else 0
            else:
                top10_percent = 0
            
            author_stats = {
                'top_authors': author_counts.head(50),  # Top 50 commenters
                'unique_authors': unique_authors,
                'top10_percent': top10_percent
            }
            
            return author_stats
        except Exception:
            return None

    def _get_basic_stats(self, df, channel_data):
        """Get basic comment statistics."""
        if df.empty:
            return None
            
        try:
            # Calculate basic statistics
            total_comments = len(df)
            avg_comment_length = df['Text Length'].mean() if 'Text Length' in df.columns else 0
            
            # Reply percentage
            reply_count = len(df[df['Is Reply']]) if 'Is Reply' in df.columns else 0
            reply_percentage = reply_count / total_comments * 100 if total_comments > 0 else 0
            
            # Average likes per comment
            avg_likes_per_comment = df['Likes'].mean() if 'Likes' in df.columns else 0
            
            # Most liked comment
            most_liked_count = df['Likes'].max() if 'Likes' in df.columns and len(df) > 0 else 0
            
            # Creator comments if we can identify the channel owner
            channel_name = channel_data.get('channel_info', {}).get('title', '').lower()
            creator_comments = 0
            
            if channel_name:
                # Try to find comments by the creator
                creator_comments = len(df[df['Author'].str.lower() == channel_name]) if 'Author' in df.columns else 0
            
            # Length distribution
            length_categories = {
                'Very Short (<50 chars)': len(df[df['Text Length'] < 50]) if 'Text Length' in df.columns else 0,
                'Short (50-100 chars)': len(df[(df['Text Length'] >= 50) & (df['Text Length'] < 100)]) if 'Text Length' in df.columns else 0,
                'Medium (100-200 chars)': len(df[(df['Text Length'] >= 100) & (df['Text Length'] < 200)]) if 'Text Length' in df.columns else 0,
                'Long (200-500 chars)': len(df[(df['Text Length'] >= 200) & (df['Text Length'] < 500)]) if 'Text Length' in df.columns else 0,
                'Very Long (>500 chars)': len(df[df['Text Length'] >= 500]) if 'Text Length' in df.columns else 0
            }
            
            # Videos with comments
            video_count = len(channel_data.get('videos', [])) if 'videos' in channel_data else 0
            videos_with_comments = len(df['Video ID'].unique()) if 'Video ID' in df.columns else 0
            
            # Comments per video (on average)
            comments_per_video = total_comments / videos_with_comments if videos_with_comments > 0 else 0
            
            stats = {
                'total_comments': total_comments,
                'avg_comment_length': avg_comment_length,
                'reply_percentage': reply_percentage,
                'avg_likes_per_comment': avg_likes_per_comment,
                'most_liked_count': most_liked_count,
                'creator_comments': creator_comments,
                'length_distribution': length_categories,
                'videos_with_comments': videos_with_comments,
                'comments_per_video': comments_per_video
            }
            
            return stats
        except Exception:
            return None