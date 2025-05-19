"""
Analytics dashboard component for the data analysis UI.

This module has been refactored into the analytics_dashboard package.
This file now re-exports functions from the new modules for backward compatibility.
"""
import streamlit as st  # Keep this import for backward compatibility

# Re-export all public functions from the new modules
from .analytics_dashboard import (
    render_analytics_dashboard,
    render_performance_metrics,
    render_publication_timeline,
    render_duration_analysis,
    render_top_videos,
    render_channel_comparison,
    create_engagement_timeline_chart,
)

# Maintain backward compatibility with any other exported functions/classes
__all__ = [
    'render_analytics_dashboard',
    'render_performance_metrics',
    'render_publication_timeline', 
    'render_duration_analysis',
    'render_top_videos',
    'render_channel_comparison',
    'create_engagement_timeline_chart',
]