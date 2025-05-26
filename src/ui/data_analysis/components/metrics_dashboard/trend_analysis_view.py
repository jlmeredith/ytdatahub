"""
Metrics dashboard components for YTDataHub analytics.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union, Optional

from src.services.youtube.metrics_tracking import MetricsTrackingService
from src.ui.data_collection.utils.trend_visualization import (
    render_trend_visualization, 
    configure_alert_thresholds
)

def render_metrics_dashboard(metrics_service: MetricsTrackingService = None) -> None:
    """
    Render the metrics dashboard.
    
    Args:
        metrics_service: MetricsTrackingService instance
    """
    st.title("Metrics Dashboard")
    
    # Check if metrics service is available
    if not metrics_service:
        st.warning("Metrics tracking service not available. Please initialize it first.")
        return
        
    # Setup tabs for different dashboard sections
    tab1, tab2, tab3 = st.tabs([
        "Trend Analysis", 
        "Alert Configuration", 
        "Historical Metrics"
    ])
    
    with tab1:
        render_trend_analysis_tab(metrics_service)
        
    with tab2:
        render_alert_configuration_tab(metrics_service)
        
    with tab3:
        render_historical_metrics_tab(metrics_service)

def render_trend_analysis_tab(metrics_service: MetricsTrackingService) -> None:
    """
    Render the trend analysis tab.
    
    Args:
        metrics_service: MetricsTrackingService instance
    """
    st.header("Trend Analysis")
    
    # Channel selector
    channels = _get_available_channels(metrics_service)
    selected_channel = st.selectbox(
        "Select Channel",
        options=channels,
        format_func=lambda x: x.get('title', x.get('channel_id', 'Unknown'))
    )
    
    if not selected_channel:
        st.warning("No channels available for analysis.")
        return
        
    # Get channel ID
    channel_id = selected_channel.get('channel_id')
    
    # Metric selector
    metrics = [
        {"name": "Subscribers", "value": "subscribers"},
        {"name": "Views", "value": "views"}, 
        {"name": "Videos", "value": "total_videos"}
    ]
    
    selected_metric = st.selectbox(
        "Select Metric",
        options=metrics,
        format_func=lambda x: x['name']
    )
    
    # Time window selector
    time_windows = [
        {"name": "Last 7 days", "value": 7},
        {"name": "Last 30 days", "value": 30},
        {"name": "Last 90 days", "value": 90},
        {"name": "Last year", "value": 365}
    ]
    
    selected_window = st.selectbox(
        "Select Time Window",
        options=time_windows,
        index=2,  # Default to 90 days
        format_func=lambda x: x['name']
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    with col1:
        include_forecast = st.checkbox("Include Forecast", value=True)
    with col2:
        show_thresholds = st.checkbox("Show Alert Thresholds", value=True)
    
    # Analyze button
    if st.button("Analyze Trend"):
        with st.spinner("Analyzing trend data..."):
            # Perform trend analysis
            trend_data = metrics_service.analyze_historical_trends(
                entity_id=channel_id,
                metric_name=selected_metric['value'],
                entity_type='channel',
                time_window=selected_window['value'],
                analysis_types=['linear_trend', 'moving_average', 'growth_rate', 
                               'seasonality', 'anomaly_detection']
            )
            
            # Get historical data for visualization
            historical_data = metrics_service._get_historical_data(
                entity_id=channel_id,
                metric_name=selected_metric['value'],
                entity_type='channel',
                time_window=selected_window['value']
            )
            
            # Render visualization
            render_trend_visualization(
                trend_data=trend_data,
                historical_data=historical_data,
                include_forecast=include_forecast,
                show_thresholds=show_thresholds
            )
            
            # Show download buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Export Analysis Report"):
                    st.session_state['export_data'] = trend_data
                    st.success("Report ready for export")
                    
            with col2:
                if st.button("Export Raw Data"):
                    st.session_state['export_raw_data'] = historical_data
                    st.success("Raw data ready for export")
                    
            # Add additional metrics
            if 'export_data' in st.session_state:
                st.download_button(
                    label="Download Analysis Report (JSON)",
                    data=pd.DataFrame([st.session_state['export_data']]).to_json(orient="records"),
                    file_name=f"{channel_id}_{selected_metric['value']}_analysis.json",
                    mime="application/json"
                )
                
            if 'export_raw_data' in st.session_state:
                st.download_button(
                    label="Download Raw Data (CSV)",
                    data=pd.DataFrame(st.session_state['export_raw_data']).to_csv(index=False),
                    file_name=f"{channel_id}_{selected_metric['value']}_data.csv",
                    mime="text/csv"
                )
    
def render_alert_configuration_tab(metrics_service: MetricsTrackingService) -> None:
    """
    Render the alert configuration tab.
    
    Args:
        metrics_service: MetricsTrackingService instance
    """
    st.header("Alert Configuration")
    
    # Get current thresholds from service
    current_thresholds = metrics_service.alert_config.get_all_thresholds()
    
    # Configure thresholds
    new_thresholds = configure_alert_thresholds(current_thresholds)
    
    # Save button
    if st.button("Save Threshold Configuration"):
        with st.spinner("Saving threshold configuration..."):
            # Update each entity type and metric
            success = True
            
            for entity_type, metrics in new_thresholds.items():
                for metric_name, threshold_config in metrics.items():
                    result = metrics_service.set_alert_threshold(
                        entity_type, metric_name, threshold_config
                    )
                    if not result:
                        st.error(f"Failed to set threshold for {entity_type}.{metric_name}")
                        success = False
            
            # Save to disk
            if success and metrics_service.save_threshold_config():
                st.success("Alert thresholds saved successfully!")
            else:
                st.error("Failed to save some thresholds")
                
    # Reset button
    if st.button("Reset to Default Thresholds"):
        metrics_service.alert_config._initialize_default_thresholds()
        if metrics_service.save_threshold_config():
            st.success("Alert thresholds reset to defaults!")
        else:
            st.error("Failed to reset thresholds")
            
    # Explanation of threshold types
    with st.expander("About Alert Thresholds"):
        st.markdown("""
        ### Alert Threshold Types
        
        - **Percentage**: Triggers when the metric changes by the specified percentage
        - **Absolute**: Triggers when the metric changes by the specified absolute value
        - **Statistical**: Triggers when the metric deviates from expected values by the specified number of standard deviations
        
        ### Alert Levels
        
        - **Warning**: First level of alert for moderate changes
        - **Critical**: Highest level of alert for significant changes
        
        ### Comparison Window
        
        The number of days to look back when comparing current values to historical values.
        
        ### Alert Direction
        
        - **Both**: Alert triggers for both increases and decreases
        - **Increase**: Alert triggers only for increases
        - **Decrease**: Alert triggers only for decreases
        """)

def render_historical_metrics_tab(metrics_service: MetricsTrackingService) -> None:
    """
    Render the historical metrics tab.
    
    Args:
        metrics_service: MetricsTrackingService instance
    """
    st.header("Historical Metrics")
    
    # Channel selector
    channels = _get_available_channels(metrics_service)
    selected_channel = st.selectbox(
        "Select Channel",
        options=channels,
        key="hist_channel",
        format_func=lambda x: x.get('title', x.get('channel_id', 'Unknown'))
    )
    
    if not selected_channel:
        st.warning("No channels available for analysis.")
        return
        
    # Get channel ID
    channel_id = selected_channel.get('channel_id')
    
    # Multi-metric selector
    metrics = [
        {"name": "Subscribers", "value": "subscribers"},
        {"name": "Views", "value": "views"}, 
        {"name": "Videos", "value": "total_videos"}
    ]
    
    selected_metrics = st.multiselect(
        "Select Metrics to Compare",
        options=metrics,
        default=[metrics[0], metrics[1]],
        format_func=lambda x: x['name']
    )
    
    # Time window selector
    time_window = st.slider(
        "Historical Data Period (days)",
        min_value=7,
        max_value=365,
        value=90
    )
    
    # Analysis button
    if st.button("Generate Historical Report", key="hist_analyze"):
        if not selected_metrics:
            st.warning("Please select at least one metric to analyze.")
            return
            
        with st.spinner("Generating historical report..."):
            # List of metric names
            metric_names = [m['value'] for m in selected_metrics]
            
            # Generate trend report
            report = metrics_service.generate_trend_report(
                entity_id=channel_id,
                entity_type='channel',
                metrics=metric_names,
                time_windows=[time_window]
            )
            
            # Display report summary
            st.subheader("Historical Metrics Report")
            st.caption(f"Channel: {selected_channel.get('title', channel_id)}")
            st.caption(f"Generated: {datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Create metric comparison charts
            _display_metric_comparison_chart(metrics_service, channel_id, metric_names, time_window)
            
            # Display detailed metrics
            for metric_name in metric_names:
                with st.expander(f"{metric_name.replace('_', ' ').title()} Details"):
                    if 'metrics' in report and metric_name in report['metrics']:
                        metric_data = report['metrics'][metric_name].get(f'window_{time_window}days')
                        
                        if metric_data and metric_data['status'] == 'success':
                            # Show key metrics
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric(
                                    label="Current Value",
                                    value=f"{int(metric_data['current_value']):,}" if metric_data['current_value'] >= 10 else f"{metric_data['current_value']:.2f}"
                                )
                                
                            with col2:
                                if 'growth_rate' in metric_data and '30day' in metric_data['growth_rate']:
                                    growth_30d = metric_data['growth_rate']['30day']['percentage']
                                    st.metric(
                                        label="30-Day Growth",
                                        value=f"{growth_30d:.1f}%",
                                        delta=f"{growth_30d:.1f}%"
                                    )
                                    
                            with col3:
                                if 'linear_trend' in metric_data:
                                    direction = metric_data['linear_trend']['direction']
                                    st.metric(
                                        label="Trend Direction",
                                        value=direction.title()
                                    )
                                    
                            # Check for anomalies
                            if 'anomalies' in metric_data and metric_data['anomalies']['total_anomalies'] > 0:
                                st.warning(f"⚠️ {metric_data['anomalies']['total_anomalies']} anomalies detected")
                                
                            # Check for threshold violations
                            if 'threshold_violations' in metric_data and metric_data['threshold_violations']:
                                violations = len(metric_data['threshold_violations'])
                                st.error(f"⚠️ {violations} threshold violations detected")
                        else:
                            st.info(f"No trend data available for {metric_name}")
                    else:
                        st.info(f"No trend data available for {metric_name}")
            
            # Export options
            st.download_button(
                label="Export Full Report (JSON)",
                data=pd.DataFrame([report]).to_json(orient="records"),
                file_name=f"{channel_id}_metrics_report.json",
                mime="application/json"
            )

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

def _display_metric_comparison_chart(metrics_service: MetricsTrackingService, 
                                   channel_id: str, 
                                   metric_names: List[str], 
                                   time_window: int) -> None:
    """
    Display a comparison chart for multiple metrics.
    
    Args:
        metrics_service: MetricsTrackingService instance
        channel_id: Channel ID
        metric_names: List of metric names
        time_window: Time window in days
    """
    # Create a figure for comparison
    fig = go.Figure()
    
    # Get historical data for each metric
    for metric_name in metric_names:
        historical_data = metrics_service._get_historical_data(
            entity_id=channel_id,
            metric_name=metric_name,
            entity_type='channel',
            time_window=time_window
        )
        
        if not historical_data:
            continue
            
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Normalize values for comparison (0-100% scale)
        if len(df) > 0:
            min_val = df['value'].min()
            max_val = df['value'].max()
            
            if max_val > min_val:
                df['normalized'] = ((df['value'] - min_val) / (max_val - min_val)) * 100
            else:
                df['normalized'] = 100
                
            # Add trace for this metric
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['normalized'],
                    mode='lines',
                    name=metric_name.replace('_', ' ').title()
                )
            )
            
    # Update layout
    fig.update_layout(
        title="Normalized Metric Comparison",
        xaxis_title="Date",
        yaxis_title="Normalized Value (%)",
        yaxis=dict(range=[0, 100]),
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified"
    )
    
    # Add range selector
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=30, label="1m", step="day", stepmode="backward"),
                dict(count=90, label="3m", step="day", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
