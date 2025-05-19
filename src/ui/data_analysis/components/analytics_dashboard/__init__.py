"""
Analytics dashboard component package.
This package contains modules for different parts of the analytics dashboard.
"""

# Re-export main functions for backward compatibility
from .core import render_analytics_dashboard
from .performance_metrics import render_performance_metrics
from .publication_timeline import render_publication_timeline
from .duration_analysis import render_duration_analysis
from .top_videos import render_top_videos
from .comparison import render_channel_comparison
from .engagement_timeline import create_engagement_timeline_chart

__all__ = [
    'render_analytics_dashboard',
    'render_performance_metrics',
    'render_publication_timeline', 
    'render_duration_analysis',
    'render_top_videos',
    'render_channel_comparison',
    'create_engagement_timeline_chart',
]
