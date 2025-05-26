"""
Main integration module for the metrics dashboard component.
This file integrates the metrics functionality with the analytics dashboard.
"""
import streamlit as st
from typing import Dict, Any, Optional

from src.services.youtube.metrics_tracking import MetricsTrackingService
from src.ui.data_analysis.components.metrics_dashboard import (
    render_metrics_dashboard,
    render_alert_dashboard
)

def integrate_metrics_dashboard(metrics_service: Optional[MetricsTrackingService] = None) -> None:
    """
    Integrate the metrics dashboard into the analytics dashboard.
    
    Args:
        metrics_service: Optional MetricsTrackingService instance
    """
    # Create tabs for different sections of the metrics dashboard
    tab1, tab2 = st.tabs(["Trend Analysis", "Alerts"])
    
    # Initialize metrics service if not provided
    if metrics_service is None:
        metrics_service = create_metrics_service()
    
    with tab1:
        render_metrics_dashboard(metrics_service)
        
    with tab2:
        render_alert_dashboard(metrics_service)

def create_metrics_service() -> MetricsTrackingService:
    """
    Create a MetricsTrackingService instance.
    
    Returns:
        MetricsTrackingService instance
    """
    # Check if we already have an instance in the session state
    if 'metrics_service' not in st.session_state:
        # Create a new instance
        from src.storage.db_service import DatabaseService
        
        # Try to get db service from session state
        db_service = st.session_state.get('db_service')
        
        # If not available, create a new one
        if db_service is None:
            try:
                db_service = DatabaseService()
            except Exception as e:
                st.error(f"Error creating database service: {str(e)}")
                db_service = None
                
        # Create the metrics service
        metrics_service = MetricsTrackingService(db=db_service)
        
        # Store in session state
        st.session_state['metrics_service'] = metrics_service
        
    return st.session_state['metrics_service']
