"""
Package initialization for comment analysis tab components.
"""
from src.ui.data_analysis.components.comment_analysis.temporal_tab import render_temporal_tab
from src.ui.data_analysis.components.comment_analysis.commenter_tab import render_commenter_tab
from src.ui.data_analysis.components.comment_analysis.engagement_tab import render_engagement_tab

__all__ = [
    'render_temporal_tab',
    'render_commenter_tab',
    'render_engagement_tab'
]