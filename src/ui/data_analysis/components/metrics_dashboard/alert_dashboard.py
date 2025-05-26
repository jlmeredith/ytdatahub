"""
Alert dashboard components for YTDataHub metrics tracking.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

from src.services.youtube.metrics_tracking import MetricsTrackingService
from src.ui.data_collection.utils.trend_visualization import render_trend_visualization

def render_alert_dashboard(metrics_service: MetricsTrackingService = None) -> None:
    """
    Render the alert dashboard.
    
    Args:
        metrics_service: MetricsTrackingService instance
    """
    st.title("Metrics Alerts Dashboard")
    
    # Check if metrics service is available
    if not metrics_service:
        st.warning("Metrics tracking service not available. Please initialize it first.")
        return
        
    # Scan for alerts button
    if st.button("Scan for Alerts"):
        with st.spinner("Scanning for threshold violations..."):
            alerts = _scan_for_alerts(metrics_service)
            _display_alerts(alerts, metrics_service)
            
    # Display current active alerts if available in session state
    if 'current_alerts' in st.session_state:
        _display_alerts(st.session_state['current_alerts'], metrics_service)
    else:
        st.info("Click 'Scan for Alerts' to check for threshold violations across your data.")
        
    # Display alert threshold settings
    with st.expander("Current Alert Configuration"):
        _display_alert_settings(metrics_service)
        
def _scan_for_alerts(metrics_service: MetricsTrackingService) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan all monitored channels and videos for alerts.
    
    Args:
        metrics_service: MetricsTrackingService instance
        
    Returns:
        Dictionary of alerts grouped by entity type
    """
    alerts = {
        'critical': [],
        'warning': []
    }
    
    # Get available channels
    channels = _get_available_channels(metrics_service)
    
    # Check each channel for threshold violations
    for channel in channels:
        channel_id = channel.get('channel_id')
        
        # Check common metrics for channels
        metrics_to_check = ['subscribers', 'views', 'total_videos']
        
        for metric in metrics_to_check:
            # Perform trend analysis
            trend_data = metrics_service.analyze_historical_trends(
                entity_id=channel_id,
                metric_name=metric,
                entity_type='channel',
                time_window=30,  # 30-day window
                analysis_types=['growth_rate']  # We only need growth rate for threshold checks
            )
            
            # Check for threshold violations
            if 'threshold_violations' in trend_data and trend_data['threshold_violations']:
                for violation in trend_data['threshold_violations']:
                    # Create alert object
                    alert = {
                        'entity_type': 'channel',
                        'entity_id': channel_id,
                        'entity_name': channel.get('title', channel_id),
                        'metric': metric,
                        'threshold_level': violation['threshold_level'],
                        'message': violation['message'],
                        'value': violation['current_value'],
                        'threshold': violation['threshold_value'],
                        'window_days': violation['window_days'],
                        'timestamp': datetime.now().isoformat(),
                        'trend_data': trend_data
                    }
                    
                    # Add to appropriate list
                    if violation['threshold_level'] == 'critical':
                        alerts['critical'].append(alert)
                    else:
                        alerts['warning'].append(alert)
    
    # Store in session state for future reference
    st.session_state['current_alerts'] = alerts
    
    return alerts
    
def _display_alerts(alerts: Dict[str, List[Dict[str, Any]]], 
                  metrics_service: MetricsTrackingService) -> None:
    """
    Display alerts in a user-friendly format.
    
    Args:
        alerts: Dictionary of alerts grouped by severity
        metrics_service: MetricsTrackingService instance
    """
    critical_alerts = alerts.get('critical', [])
    warning_alerts = alerts.get('warning', [])
    
    # Display summary counts
    col1, col2 = st.columns(2)
    
    with col1:
        if critical_alerts:
            st.error(f"🔴 {len(critical_alerts)} Critical Alerts")
        else:
            st.success("✅ No Critical Alerts")
            
    with col2:
        if warning_alerts:
            st.warning(f"🟡 {len(warning_alerts)} Warning Alerts")
        else:
            st.success("✅ No Warning Alerts")
    
    # Display any critical alerts first
    if critical_alerts:
        st.subheader("Critical Alerts")
        
        for i, alert in enumerate(critical_alerts):
            with st.expander(f"{alert['entity_name']} - {alert['metric'].replace('_', ' ').title()} - {alert['threshold_level'].upper()}", expanded=True):
                st.error(alert['message'])
                
                # Display key metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Current Value",
                        value=f"{alert['value']:.1f}%"
                    )
                    
                with col2:
                    st.metric(
                        label="Threshold",
                        value=f"{alert['threshold']:.1f}%"
                    )
                    
                with col3:
                    st.metric(
                        label="Time Window",
                        value=f"{alert['window_days']} days"
                    )
                    
                # Button to view detailed trend
                if st.button(f"View {alert['metric'].replace('_', ' ').title()} Trend", key=f"critical_{i}"):
                    # Get historical data for visualization
                    historical_data = metrics_service._get_historical_data(
                        entity_id=alert['entity_id'],
                        metric_name=alert['metric'],
                        entity_type=alert['entity_type'],
                        time_window=max(alert['window_days'] * 2, 30)  # Look back at least 30 days
                    )
                    
                    # Render visualization
                    render_trend_visualization(
                        trend_data=alert['trend_data'],
                        historical_data=historical_data,
                        include_forecast=True,
                        show_thresholds=True
                    )
    
    # Display warning alerts
    if warning_alerts:
        st.subheader("Warning Alerts")
        
        for i, alert in enumerate(warning_alerts):
            with st.expander(f"{alert['entity_name']} - {alert['metric'].replace('_', ' ').title()} - {alert['threshold_level'].upper()}"):
                st.warning(alert['message'])
                
                # Display key metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Current Value",
                        value=f"{alert['value']:.1f}%"
                    )
                    
                with col2:
                    st.metric(
                        label="Threshold",
                        value=f"{alert['threshold']:.1f}%"
                    )
                    
                with col3:
                    st.metric(
                        label="Time Window",
                        value=f"{alert['window_days']} days"
                    )
                    
                # Button to view detailed trend
                if st.button(f"View {alert['metric'].replace('_', ' ').title()} Trend", key=f"warning_{i}"):
                    # Get historical data for visualization
                    historical_data = metrics_service._get_historical_data(
                        entity_id=alert['entity_id'],
                        metric_name=alert['metric'],
                        entity_type=alert['entity_type'],
                        time_window=max(alert['window_days'] * 2, 30)  # Look back at least 30 days
                    )
                    
                    # Render visualization
                    render_trend_visualization(
                        trend_data=alert['trend_data'],
                        historical_data=historical_data,
                        include_forecast=True,
                        show_thresholds=True
                    )
                    
    # If no alerts, show a happy message
    if not critical_alerts and not warning_alerts:
        st.success("All metrics are currently within their threshold ranges! 🎉")
        st.info("The alert system will notify you when metrics exceed the defined thresholds.")
        
def _display_alert_settings(metrics_service: MetricsTrackingService) -> None:
    """
    Display current alert threshold settings.
    
    Args:
        metrics_service: MetricsTrackingService instance
    """
    # Get current thresholds
    thresholds = metrics_service.alert_config.get_all_thresholds()
    
    # Display thresholds in tables
    st.subheader("Current Alert Thresholds")
    
    # Create tabs for different entity types
    tab1, tab2, tab3 = st.tabs(["Channel Thresholds", "Video Thresholds", "Comment Thresholds"])
    
    with tab1:
        _display_entity_thresholds('channel', thresholds.get('channel', {}))
        
    with tab2:
        _display_entity_thresholds('video', thresholds.get('video', {}))
        
    with tab3:
        _display_entity_thresholds('comment', thresholds.get('comment', {}))
        
def _display_entity_thresholds(entity_type: str, thresholds: Dict[str, Any]) -> None:
    """
    Display thresholds for a specific entity type.
    
    Args:
        entity_type: Type of entity ('channel', 'video', 'comment')
        thresholds: Threshold configuration for this entity type
    """
    if not thresholds:
        st.info(f"No thresholds configured for {entity_type} metrics.")
        return
        
    # Create a DataFrame to display thresholds
    threshold_rows = []
    
    for metric_name, config in thresholds.items():
        warning = config.get('warning', {})
        critical = config.get('critical', {})
        window = config.get('comparison_window', 7)
        direction = config.get('direction', 'both')
        
        threshold_rows.append({
            'Metric': metric_name.replace('_', ' ').title(),
            'Warning': f"{warning.get('value', 'N/A')} ({warning.get('type', 'N/A')})",
            'Critical': f"{critical.get('value', 'N/A')} ({critical.get('type', 'N/A')})",
            'Window': f"{window} days",
            'Direction': direction.title()
        })
        
    if threshold_rows:
        df = pd.DataFrame(threshold_rows)
        st.dataframe(df, hide_index=True)
    else:
        st.info(f"No thresholds configured for {entity_type} metrics.")
        
def _get_available_channels(metrics_service: MetricsTrackingService) -> List[Dict[str, Any]]:
    """
    Get a list of available channels for analysis.
    
    Args:
        metrics_service: MetricsTrackingService instance
        
    Returns:
        List of channel dictionaries with channel_id and title
    """
    # In a real implementation, this would query the database
    # For now, return a dummy list
    try:
        # Try to query the database if available
        if metrics_service and metrics_service.db:
            channels = metrics_service.db.get_channel_list()
            if channels:
                return channels
    except Exception as e:
        st.error(f"Error retrieving channel list: {str(e)}")
        
    # Fallback to dummy data
    return [
        {'channel_id': 'UC123', 'title': 'Example Channel 1'},
        {'channel_id': 'UC456', 'title': 'Example Channel 2'},
    ]
