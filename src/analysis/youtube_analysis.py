"""
Analytics functions for YouTube data.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.helpers import duration_to_seconds, format_duration

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
        return self.channel_analyzer.get_channel_statistics(channel_data)
    
    def get_video_statistics(self, channel_data):
        """
        Get detailed video statistics.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with video statistics and DataFrame
        """
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
        return self.video_analyzer.get_top_videos(channel_data, n, by)
    
    def get_publication_timeline(self, channel_data):
        """
        Analyze publication timeline.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with timeline DataFrames
        """
        return self.video_analyzer.get_publication_timeline(channel_data)
    
    def get_duration_analysis(self, channel_data):
        """
        Analyze video durations.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with duration analysis
        """
        return self.video_analyzer.get_duration_analysis(channel_data)
    
    def get_comment_analysis(self, channel_data):
        """
        Analyze video comments.
        
        Args:
            channel_data: Dictionary containing channel data
            
        Returns:
            Dictionary with comment analysis
        """
        return self.comment_analyzer.get_comment_analysis(channel_data)

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