"""
Analytics functions for YouTube data.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from src.utils.helpers import duration_to_seconds, format_duration, debug_log

"""
Main YouTube analysis facade that integrates all specialized analyzers.
"""
from src.analysis.channel_analyzer import ChannelAnalyzer
from src.analysis.video_analyzer import VideoAnalyzer
from src.analysis.comment_analyzer import CommentAnalyzer
from src.analysis.visualization.trend_line import add_trend_line

class YouTubeAnalysis:
    """
    Facade class that integrates all specialized analyzers.
    Maintains backward compatibility with existing code while using the new modular structure.
    """
    
    def __init__(self):
        """Initialize the analyzers."""
        self.channel_analyzer = ChannelAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.comment_analyzer = CommentAnalyzer()
    
    def get_channel_statistics(self, channel_data):
        """
        Get basic channel statistics.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with channel statistics
        """
        # Define a cache key based on channel data
        if channel_data and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
            channel_name = channel_data['channel_info']['title']
            cache_key = f"analysis_channel_stats_{channel_name}"
            
            # Check if we have cached results
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached channel statistics for: {channel_name}")
                return st.session_state[cache_key]
            
            # Compute statistics
            result = self.channel_analyzer.get_channel_statistics(channel_data)
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = result
                debug_log(f"Cached channel statistics for: {channel_name}")
            
            return result
        else:
            return self.channel_analyzer.get_channel_statistics(channel_data)
    
    def get_video_statistics(self, channel_data):
        """
        Get detailed video statistics.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with video statistics and DataFrame
        """
        # Define a cache key based on channel data
        if channel_data and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
            channel_name = channel_data['channel_info']['title']
            cache_key = f"analysis_video_stats_{channel_name}"
            
            # Check if we have cached results
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached video statistics for: {channel_name}")
                return st.session_state[cache_key]
            
            # Compute statistics
            result = self.video_analyzer.get_video_statistics(channel_data)
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = result
                debug_log(f"Cached video statistics for: {channel_name}")
            
            return result
        else:
            return self.video_analyzer.get_video_statistics(channel_data)
    
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
        # Define a cache key based on channel data and parameters
        if channel_data and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
            channel_name = channel_data['channel_info']['title']
            cache_key = f"analysis_top_videos_{channel_name}_{n}_{by}"
            
            # Check if we have cached results
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached top videos for: {channel_name}")
                return st.session_state[cache_key]
            
            # Compute top videos
            result = self.video_analyzer.get_top_videos(channel_data, n, by)
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = result
                debug_log(f"Cached top videos for: {channel_name}")
            
            return result
        else:
            return self.video_analyzer.get_top_videos(channel_data, n, by)
    
    def get_publication_timeline(self, channel_data):
        """
        Analyze publication timeline.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with timeline DataFrames
        """
        # Define a cache key based on channel data
        if channel_data and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
            channel_name = channel_data['channel_info']['title']
            cache_key = f"analysis_timeline_{channel_name}"
            
            # Check if we have cached results
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached publication timeline for: {channel_name}")
                return st.session_state[cache_key]
            
            # Compute timeline
            result = self.video_analyzer.get_publication_timeline(channel_data)
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = result
                debug_log(f"Cached publication timeline for: {channel_name}")
            
            return result
        else:
            return self.video_analyzer.get_publication_timeline(channel_data)
    
    def get_duration_analysis(self, channel_data):
        """
        Analyze video durations.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with duration analysis
        """
        # Define a cache key based on channel data
        if channel_data and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
            channel_name = channel_data['channel_info']['title']
            cache_key = f"analysis_duration_{channel_name}"
            
            # Check if we have cached results
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached duration analysis for: {channel_name}")
                return st.session_state[cache_key]
            
            # Compute duration analysis
            result = self.video_analyzer.get_duration_analysis(channel_data)
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = result
                debug_log(f"Cached duration analysis for: {channel_name}")
            
            return result
        else:
            return self.video_analyzer.get_duration_analysis(channel_data)
    
    def get_comment_analysis(self, channel_data):
        """
        Analyze video comments.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with comment analysis
        """
        # Define a cache key based on channel data
        if channel_data and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
            channel_name = channel_data['channel_info']['title']
            cache_key = f"analysis_comments_{channel_name}"
            
            # Check if we have cached results
            if cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached comment analysis for: {channel_name}")
                return st.session_state[cache_key]
            
            # Compute comment analysis
            result = self.comment_analyzer.get_comment_analysis(channel_data)
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = result
                debug_log(f"Cached comment analysis for: {channel_name}")
            
            return result
        else:
            return self.comment_analyzer.get_comment_analysis(channel_data)

    def get_data_coverage(self, channel_data, db=None):
        """
        Calculate the data coverage for a channel - how complete the collected data is.
        
        Args:
            channel_data: Dictionary containing channel data
            db: Database connection (optional)
            
        Returns:
            Dictionary with coverage statistics and metrics
        """
        # Define a cache key based on channel data
        if channel_data and 'channel_info' in channel_data and 'title' in channel_data['channel_info']:
            channel_name = channel_data['channel_info']['title']
            cache_key = f"analysis_data_coverage_{channel_name}"
            
            # Check if we have cached results - but skip cache if explicitly told to
            skip_cache = st.session_state.get('skip_coverage_cache', False)
            if not skip_cache and cache_key in st.session_state and st.session_state.get('use_data_cache', True):
                debug_log(f"Using cached data coverage for: {channel_name}")
                return st.session_state[cache_key]
            
            # Calculate coverage metrics
            result = {
                'total_videos_reported': 0,  # Total videos reported by YouTube API
                'total_videos_collected': 0,  # Videos we've actually collected
                'videos_with_details': 0,     # Videos with full details
                'videos_with_comments': 0,    # Videos with comments collected
                'latest_video_date': None,    # Date of the latest video
                'oldest_video_date': None,    # Date of the oldest video
                'last_updated': None,         # When this data was last updated
                'update_recommendations': [],  # Recommended actions
                'video_coverage_percent': 0,  # Percentage of videos collected
                'comment_coverage_percent': 0, # Percentage of videos with comments
                'historical_completeness': 0,  # How far back in time we've collected
                'is_complete': False,          # Whether we have all videos
                'temporal_coverage': {         # Coverage by time period
                    'last_month': 0,
                    'last_6_months': 0,
                    'last_year': 0,
                    'older': 0
                }
            }
            
            try:
                # Get channel info from data
                if 'channel_info' in channel_data:
                    channel_info = channel_data['channel_info']
                    
                    # Get total videos reported by YouTube API - with multiple fallback methods
                    if 'statistics' in channel_info and 'videoCount' in channel_info['statistics']:
                        # Method 1: Direct statistics field
                        try:
                            result['total_videos_reported'] = int(channel_info['statistics']['videoCount'])
                        except (ValueError, TypeError):
                            debug_log(f"Error converting videoCount to int: {channel_info['statistics']['videoCount']}")
                    
                    # Method 2: Check if there's a total_videos field directly
                    if result['total_videos_reported'] == 0 and 'total_videos' in channel_info:
                        try:
                            result['total_videos_reported'] = int(channel_info['total_videos'])
                        except (ValueError, TypeError):
                            debug_log(f"Error converting total_videos to int: {channel_info['total_videos']}")
                    
                    # Get last updated timestamp if available
                    if 'fetched_at' in channel_info:
                        try:
                            result['last_updated'] = datetime.fromisoformat(channel_info['fetched_at'].replace('Z', '+00:00'))
                        except:
                            try:
                                # Try an alternative format used in some API responses
                                result['last_updated'] = datetime.fromisoformat(channel_info['fetched_at'])
                            except:
                                pass
                
                # Get video data from channel data
                videos = []
                if 'videos' in channel_data:
                    videos = channel_data['videos']
                    result['total_videos_collected'] = len(videos)
                    
                    # If we still don't have a total videos count from the API, use our collected count
                    # but mark it as potentially incomplete
                    if result['total_videos_reported'] == 0:
                        result['total_videos_reported'] = max(len(videos), 1)  # Ensure at least 1
                        debug_log(f"Using collected videos count as total: {result['total_videos_reported']}")
                    
                    # Check which videos have details and comments
                    videos_with_details = 0
                    videos_with_comments = 0
                    comment_counts = []
                    publish_dates = []
                    
                    # Current date for temporal analysis
                    now = datetime.now()
                    last_month = 0
                    last_6_months = 0
                    last_year = 0
                    older = 0
                    
                    for video in videos:
                        # Check for details
                        if 'snippet' in video and 'statistics' in video:
                            videos_with_details += 1
                            
                            # Check for publish date
                            if 'publishedAt' in video['snippet']:
                                try:
                                    publish_date = datetime.fromisoformat(video['snippet']['publishedAt'].replace('Z', '+00:00'))
                                    publish_dates.append(publish_date)
                                    
                                    # Temporal analysis
                                    days_ago = (now - publish_date).days
                                    if days_ago <= 30:
                                        last_month += 1
                                    elif days_ago <= 180:
                                        last_6_months += 1
                                    elif days_ago <= 365:
                                        last_year += 1
                                    else:
                                        older += 1
                                except Exception:
                                    pass
                        
                        # Check for comments - enhanced detection logic
                        comment_found = False
                        
                        # Method 1: Direct comments array
                        if 'comments' in video and video['comments']:
                            comment_found = True
                        # Method 2: Comment count in statistics
                        elif 'statistics' in video and 'commentCount' in video['statistics'] and int(video['statistics']['commentCount']) > 0:
                            comment_found = True
                        # Method 3: comment_count as a direct attribute
                        elif 'comment_count' in video and int(video.get('comment_count', 0)) > 0:
                            comment_found = True
                        # Method 4: Check video ID in comments dictionary
                        elif 'comments' in channel_data and video.get('id') in channel_data['comments']:
                            comment_found = True
                        
                        if comment_found:
                            videos_with_comments += 1
                            # Try to get comment count for statistics
                            if 'comments' in video and isinstance(video['comments'], list):
                                comment_counts.append(len(video['comments']))
                            elif 'statistics' in video and 'commentCount' in video['statistics']:
                                comment_counts.append(int(video['statistics']['commentCount']))
                            elif 'comment_count' in video:
                                comment_counts.append(int(video.get('comment_count', 0)))
                    
                    result['videos_with_details'] = videos_with_details
                    result['videos_with_comments'] = videos_with_comments
                    
                    # Calculate coverage percentages
                    if result['total_videos_reported'] > 0:
                        # Calculate percentage with proper handling of full coverage
                        video_coverage = min(100.0, (result['total_videos_collected'] / result['total_videos_reported']) * 100)
                        result['video_coverage_percent'] = video_coverage
                        
                        # Mark as complete if we have all videos or very close to it (allowing for API count discrepancies)
                        if (result['total_videos_collected'] >= result['total_videos_reported'] or 
                            video_coverage >= 99.0):
                            result['is_complete'] = True
                    
                    if result['total_videos_collected'] > 0:
                        # Calculate comment coverage with proper handling of full coverage
                        comment_coverage = min(100.0, (result['videos_with_comments'] / result['total_videos_collected']) * 100)
                        result['comment_coverage_percent'] = comment_coverage
                    
                    # Set date ranges
                    if publish_dates:
                        result['latest_video_date'] = max(publish_dates)
                        result['oldest_video_date'] = min(publish_dates)
                        
                        # Calculate historical completeness (days between oldest and newest)
                        if result['latest_video_date'] and result['oldest_video_date']:
                            days_range = (result['latest_video_date'] - result['oldest_video_date']).days
                            channel_age_days = (now - result['oldest_video_date']).days
                            
                            if channel_age_days > 0:
                                result['historical_completeness'] = min(100.0, (days_range / channel_age_days) * 100)
                    
                    # Set temporal coverage
                    total_temporal = last_month + last_6_months + last_year + older
                    if total_temporal > 0:
                        result['temporal_coverage'] = {
                            'last_month': last_month / total_temporal * 100,
                            'last_6_months': last_6_months / total_temporal * 100,
                            'last_year': last_year / total_temporal * 100,
                            'older': older / total_temporal * 100
                        }
                
                # Generate update recommendations
                recommendations = []
                
                # Missing videos recommendation
                if result['total_videos_reported'] > result['total_videos_collected']:
                    missing_count = result['total_videos_reported'] - result['total_videos_collected']
                    if missing_count > 0:
                        if missing_count == 1:
                            recommendations.append(f"Collect 1 missing video")
                        else:
                            recommendations.append(f"Collect {missing_count} missing videos")
                
                # Missing comments recommendation
                if result['videos_with_comments'] < result['total_videos_collected']:
                    missing_comments = result['total_videos_collected'] - result['videos_with_comments']
                    if missing_comments > 0:
                        if missing_comments == 1:
                            recommendations.append(f"Collect comments for 1 video")
                        else:
                            recommendations.append(f"Collect comments for {missing_comments} videos")
                
                # Data refresh recommendation if we have all videos but data is old
                if result['is_complete'] and result['last_updated']:
                    days_since_update = (datetime.now() - result['last_updated']).days
                    if days_since_update > 30:  # If data is older than a month
                        recommendations.append(f"Refresh data (last updated {days_since_update} days ago)")
                
                # Historical data recommendation
                if result['historical_completeness'] < 80 and not result['is_complete']:
                    recommendations.append("Collect more historical data to improve coverage")
                
                # Recent data recommendation
                if result['temporal_coverage']['last_month'] < 10 and result['temporal_coverage']['last_6_months'] < 20:
                    recommendations.append("Collect more recent videos (last 6 months)")
                
                # Set final recommendations (or a "complete" message if everything is there)
                if not recommendations and result['is_complete'] and result['comment_coverage_percent'] >= 99.0:
                    recommendations.append("Data collection is complete! ✅")
                
                result['update_recommendations'] = recommendations
                
            except Exception as e:
                import traceback
                debug_log(f"Error calculating data coverage: {str(e)}")
                debug_log(traceback.format_exc())
            
            # Cache the result
            if st.session_state.get('use_data_cache', True):
                st.session_state[cache_key] = result
                debug_log(f"Cached data coverage for: {channel_name}")
            
            return result
        else:
            # Default return if no valid channel data
            return {
                'total_videos_reported': 0,
                'total_videos_collected': 0,
                'videos_with_details': 0,
                'videos_with_comments': 0,
                'video_coverage_percent': 0,
                'comment_coverage_percent': 0,
                'historical_completeness': 0,
                'is_complete': False,
                'update_recommendations': ['No channel data available']
            }

# Keep this function outside the class for backward compatibility
def add_trend_line(fig, x, y, color="red", width=2, dash="dash", name="Trend Line", visible="legendonly"):
    """
    Add a trend line to a plotly figure using statsmodels for proper statistical analysis.
    
    Parameters:
    -----------
    fig : plotly.graph_objects.Figure
        The figure to add the trend line to
    x : array-like
        The x values (usually dates)
    y : array-like
        The y values to fit the trend line to
    color : str
        The color of the trend line
    width : int
        The width of the trend line
    dash : str
        The dash style of the trend line (e.g., "dash", "dot", "solid")
    name : str
        The name of the trend line for the legend
    visible : str
        Whether the trend line is visible or hidden (e.g., "legendonly")
        
    Returns:
    --------
    plotly.graph_objects.Figure
        The figure with the trend line added
    """
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    
    # First check if statsmodels is available
    try:
        import statsmodels.api as sm
        STATSMODELS_AVAILABLE = True
    except ImportError:
        print("Warning: statsmodels not available, using simple linear regression instead.")
        STATSMODELS_AVAILABLE = False
    
    try:
        # Only proceed if we have valid data
        if len(x) < 2 or len(y) < 2 or len(x) != len(y):
            return fig
            
        # Clean data by removing NaN values
        df = pd.DataFrame({'x': x, 'y': y})
        df = df.dropna(subset=['x', 'y'])
        
        # Only proceed if we have enough data after cleaning
        if len(df) < 2:
            return fig
        
        # If x is datetime, convert to numeric for regression
        if pd.api.types.is_datetime64_dtype(df['x']):
            # Convert dates to ordinal numbers (days since 1970-01-01)
            df['x_numeric'] = (df['x'] - pd.Timestamp('1970-01-01')) // pd.Timedelta('1D')
        else:
            df['x_numeric'] = df['x']
        
        if STATSMODELS_AVAILABLE:
            # Add constant for statsmodels (intercept term)
            X = sm.add_constant(df['x_numeric'])
            
            # Fit OLS model
            model = sm.OLS(df['y'], X).fit()
            
            # Get the trend line predictions
            df['trend'] = model.predict()
        else:
            # Fallback to simple NumPy polyfit if statsmodels is not available
            coeffs = np.polyfit(df['x_numeric'], df['y'], 1)
            polynomial = np.poly1d(coeffs)
            df['trend'] = polynomial(df['x_numeric'])
        
        # Add to figure
        fig.add_trace(
            go.Scatter(
                x=df['x'],
                y=df['trend'],
                mode='lines',
                line=dict(color=color, width=width, dash=dash),
                name=name,
                visible=visible
            )
        )
        
        return fig
    except Exception as e:
        # If there's an error, just return the original figure without a trend line
        import traceback
        print(f"Error adding trend line: {str(e)}")
        print(traceback.format_exc())
        return fig