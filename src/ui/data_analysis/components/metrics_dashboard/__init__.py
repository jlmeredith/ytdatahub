"""
Metrics dashboard module for YTDataHub analytics.
"""
from .trend_analysis_view import render_metrics_dashboard
from .alert_dashboard import render_alert_dashboard

__all__ = [
    'render_metrics_dashboard',
    'render_alert_dashboard'
]
