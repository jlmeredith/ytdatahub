"""
Trend visualization components for YTDataHub.
Provides UI components for displaying metric trends and threshold alerts.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union

def render_trend_visualization(trend_data: Dict[str, Any], 
                             historical_data: List[Dict[str, Any]] = None,
                             include_forecast: bool = True,
                             show_thresholds: bool = True) -> None:
    """
    Render trend visualization for metric data.
    
    Args:
        trend_data: Dictionary containing trend analysis results
        historical_data: List of historical data points
        include_forecast: Whether to include forecast data in the visualization
        show_thresholds: Whether to show threshold indicators
    """
    if not trend_data or 'status' not in trend_data or trend_data['status'] != 'success':
        st.warning("No trend data available for visualization.")
        return
        
    # Extract key information
    entity_id = trend_data.get('entity_id', 'Unknown')
    entity_type = trend_data.get('entity_type', 'Unknown')
    metric_name = trend_data.get('metric_name', 'Unknown')
    time_window = trend_data.get('time_window_days', 90)
    current_value = trend_data.get('current_value', 0)
    
    # Display header
    st.subheader(f"{metric_name.title()} Trend Analysis")
    st.caption(f"Entity: {entity_type} {entity_id} | Time Window: {time_window} days")
    
    # Create a two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display main trend visualization
        fig = _create_trend_chart(trend_data, historical_data, include_forecast)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Display trend summary metrics
        _display_trend_summary(trend_data)
        
    # Display growth rates
    if 'growth_rate' in trend_data:
        _display_growth_rates(trend_data['growth_rate'])
    
    # Show anomalies if available
    if 'anomalies' in trend_data and trend_data['anomalies']['total_anomalies'] > 0:
        _display_anomalies(trend_data['anomalies'])
    
    # Show threshold violations if available
    if show_thresholds and 'threshold_violations' in trend_data and trend_data['threshold_violations']:
        _display_threshold_violations(trend_data['threshold_violations'])
        
    # Show seasonality analysis if available
    if 'seasonality' in trend_data and trend_data['seasonality']['has_seasonality']:
        _display_seasonality_analysis(trend_data['seasonality'])
        
def _create_trend_chart(trend_data: Dict[str, Any], 
                       historical_data: List[Dict[str, Any]] = None,
                       include_forecast: bool = True) -> go.Figure:
    """
    Create a trend chart using Plotly.
    
    Args:
        trend_data: Dictionary containing trend analysis results
        historical_data: List of historical data points
        include_forecast: Whether to include forecast data
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Process historical data for the chart
    if historical_data:
        # Convert list of dicts to DataFrame
        history_df = pd.DataFrame(historical_data)
        
        # Ensure timestamp is in datetime format
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        
        # Sort by timestamp
        history_df = history_df.sort_values('timestamp')
        
        # Historical data trace
        fig.add_trace(
            go.Scatter(
                x=history_df['timestamp'],
                y=history_df['value'],
                mode='lines+markers',
                name='Historical Data',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6)
            )
        )
        
    # Add moving averages if available
    if 'moving_average' in trend_data:
        for window_name, ma_data in trend_data['moving_average'].items():
            # Check if we have dates and values
            if 'window_dates' in ma_data and 'window_values' in ma_data:
                # Convert dates to datetime objects
                dates = [datetime.fromisoformat(d) for d in ma_data['window_dates']]
                
                # Add moving average trace
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=ma_data['window_values'],
                        mode='lines',
                        name=f"{window_name.title()} MA ({ma_data['window_size']} days)",
                        line=dict(
                            width=3, 
                            dash='dash',
                            color='#ff7f0e' if window_name == 'short' else 
                                  '#2ca02c' if window_name == 'medium' else '#d62728'
                        )
                    )
                )
                
    # Add linear trend if available
    if 'linear_trend' in trend_data:
        linear_trend = trend_data['linear_trend']
        
        # Add trend line annotation
        slope = linear_trend.get('slope', 0)
        direction = linear_trend.get('direction', 'stable')
        significance = linear_trend.get('significance', 'none')
        r_squared = linear_trend.get('r_squared', 0)
        
        if direction == 'increasing':
            trend_color = '#00cc44'  # Green for increasing
            trend_icon = "📈"
        elif direction == 'decreasing':
            trend_color = '#ff4444'  # Red for decreasing
            trend_icon = "📉"
        else:
            trend_color = '#cccccc'  # Gray for stable
            trend_icon = "➡️"
            
        # Add annotation for trend
        significance_text = {
            'high': 'High Significance',
            'medium': 'Medium Significance',
            'low': 'Low Significance',
            'none': 'Not Significant'
        }.get(significance, 'Unknown Significance')
        
        # Add forecast if available and requested
        if include_forecast and 'forecast' in linear_trend and linear_trend['forecast']:
            forecast_data = linear_trend['forecast']
            
            # Extract dates and values
            forecast_dates = [datetime.fromisoformat(point['date']) for point in forecast_data]
            forecast_values = [point['value'] for point in forecast_data]
            
            # Add forecast trace
            fig.add_trace(
                go.Scatter(
                    x=forecast_dates,
                    y=forecast_values,
                    mode='lines+markers',
                    name='Forecast (7 days)',
                    line=dict(color='rgba(128, 0, 128, 0.7)', width=2, dash='dot'),
                    marker=dict(size=5),
                )
            )
            
            # Add shaded area for forecast confidence interval
            # This is a simple confidence interval based on the R-squared value
            confidence = min(0.3, 0.1 + (1 - r_squared) * 0.2)  # Scale confidence by R-squared
            
            upper_bounds = [v * (1 + confidence) for v in forecast_values]
            lower_bounds = [max(0, v * (1 - confidence)) for v in forecast_values]
            
            # Add confidence interval as a filled area
            fig.add_trace(
                go.Scatter(
                    x=forecast_dates + forecast_dates[::-1],
                    y=upper_bounds + lower_bounds[::-1],
                    fill='toself',
                    fillcolor='rgba(128, 0, 128, 0.1)',
                    line=dict(color='rgba(255, 255, 255, 0)'),
                    hoverinfo='skip',
                    showlegend=False,
                    name='Forecast Range'
                )
            )
        
    # Check for threshold violations to add markers
    if 'threshold_violations' in trend_data:
        # We'll mark the latest data point if there are violations
        if historical_data and trend_data['threshold_violations']:
            latest_point = max(historical_data, key=lambda x: pd.to_datetime(x['timestamp']))
            
            fig.add_trace(
                go.Scatter(
                    x=[pd.to_datetime(latest_point['timestamp'])],
                    y=[latest_point['value']],
                    mode='markers',
                    name='Threshold Violation',
                    marker=dict(
                        symbol='circle',
                        size=12,
                        color='red',
                        line=dict(width=2, color='darkred')
                    )
                )
            )
            
    # Update layout
    fig.update_layout(
        title=f"{trend_data.get('metric_name', 'Metric').title()} Trend Analysis",
        xaxis_title="Date",
        yaxis_title=f"{trend_data.get('metric_name', 'Value').title()}",
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
    
    return fig

def _display_trend_summary(trend_data: Dict[str, Any]) -> None:
    """
    Display trend summary metrics.
    
    Args:
        trend_data: Dictionary containing trend analysis results
    """
    st.markdown("### Trend Summary")
    
    # Format current value with commas
    current_value_str = f"{int(trend_data['current_value']):,}" if trend_data['current_value'] >= 10 else f"{trend_data['current_value']:.2f}"
    
    # Display current value
    st.metric(
        label="Current Value", 
        value=current_value_str
    )
    
    # Display linear trend information if available
    if 'linear_trend' in trend_data:
        linear_trend = trend_data['linear_trend']
        direction = linear_trend.get('direction', 'stable')
        slope = linear_trend.get('slope', 0)
        
        # Format direction indicator
        if direction == 'increasing':
            direction_color = 'green'
            direction_icon = "📈"
        elif direction == 'decreasing':
            direction_color = 'red'
            direction_icon = "📉"
        else:
            direction_color = 'gray'
            direction_icon = "➡️"
            
        # Display direction with icon
        st.markdown(
            f"<h4 style='color:{direction_color};margin-bottom:0'>"
            f"{direction_icon} {direction.title()}</h4>", 
            unsafe_allow_html=True
        )
        
        # Display daily change rate
        daily_change = abs(slope)
        daily_change_str = f"{daily_change:.2f}" if daily_change < 10 else f"{int(daily_change):,}"
        
        st.metric(
            label="Daily Change Rate", 
            value=daily_change_str,
            delta=f"{slope:.2f}" if abs(slope) < 10 else f"{int(slope):,}"
        )
        
        # Display significance
        significance = linear_trend.get('significance', 'none')
        significance_map = {
            'high': 'High Significance (99%)',
            'medium': 'Medium Significance (95%)',
            'low': 'Low Significance (90%)',
            'none': 'Not Statistically Significant'
        }
        
        st.caption(significance_map.get(significance, 'Unknown Significance'))
        
    # Display data range information
    earliest_date = datetime.fromisoformat(str(trend_data['earliest_date']))
    latest_date = datetime.fromisoformat(str(trend_data['latest_date']))
    
    st.caption(
        f"Based on {trend_data['data_points']} data points from "
        f"{earliest_date.strftime('%b %d, %Y')} to {latest_date.strftime('%b %d, %Y')}"
    )
    
def _display_growth_rates(growth_rate_data: Dict[str, Dict[str, Any]]) -> None:
    """
    Display growth rate information.
    
    Args:
        growth_rate_data: Dictionary containing growth rate information
    """
    st.markdown("### Growth Rates")
    
    # Sort periods by number of days
    periods = sorted(growth_rate_data.keys(), key=lambda x: int(x.replace('day', '')))
    
    # Create a table for growth rates
    data = []
    cols = ["Period", "Change", "Percentage", "Direction"]
    
    for period in periods:
        rate = growth_rate_data[period]
        days = int(period.replace('day', ''))
        
        if days == 7:
            period_name = "Last 7 days"
        elif days == 30:
            period_name = "Last 30 days"
        elif days == 90:
            period_name = "Last 90 days"
        else:
            period_name = f"Last {days} days"
            
        # Format the change value
        change_value = rate['absolute_change']
        if abs(change_value) >= 1000000:
            change_str = f"{change_value / 1000000:.1f}M"
        elif abs(change_value) >= 1000:
            change_str = f"{change_value / 1000:.1f}K"
        else:
            change_str = f"{change_value:.1f}"
            
        # Format the percentage
        percentage = rate['percentage']
        if percentage == float('inf'):
            percentage_str = "∞"
        else:
            percentage_str = f"{percentage:.1f}%"
            
        # Direction indicator
        if rate['direction'] == 'increasing':
            direction = "📈"
        elif rate['direction'] == 'decreasing':
            direction = "📉"
        else:
            direction = "➡️"
            
        data.append([period_name, change_str, percentage_str, direction])
        
    # Create a pandas DataFrame
    df = pd.DataFrame(data, columns=cols)
    
    # Display as a styled table
    st.dataframe(df, hide_index=True)
    
def _display_anomalies(anomaly_data: Dict[str, Any]) -> None:
    """
    Display anomaly information.
    
    Args:
        anomaly_data: Dictionary containing anomaly information
    """
    total = anomaly_data['total_anomalies']
    anomalies = anomaly_data.get('anomalies', [])
    
    with st.expander(f"Anomalies Detected ({total})"):
        st.markdown(f"Found {total} anomalies in the data")
        
        if anomaly_data.get('latest_is_anomaly', False):
            st.warning("⚠️ The most recent data point is an anomaly!")
            
        if anomalies:
            # Create a table of anomalies
            anomaly_dicts = []
            
            for anomaly in anomalies:
                timestamp = datetime.fromisoformat(anomaly['timestamp']).strftime('%Y-%m-%d')
                
                anomaly_dicts.append({
                    'Date': timestamp,
                    'Value': anomaly['value'],
                    'Expected': f"{anomaly['expected_value']:.2f}",
                    'Deviation': f"{anomaly['deviation']:.2f}",
                    'Z-Score': f"{anomaly['z_score']:.2f}",
                    'Severity': anomaly['severity'].title(),
                    'Direction': anomaly['direction'].title()
                })
                
            # Convert to DataFrame and display
            anomaly_df = pd.DataFrame(anomaly_dicts)
            st.dataframe(anomaly_df, hide_index=True)
            
def _display_threshold_violations(violations: List[Dict[str, Any]]) -> None:
    """
    Display threshold violation information.
    
    Args:
        violations: List of threshold violations
    """
    # Count warning and critical violations
    warning_count = sum(1 for v in violations if v['threshold_level'] == 'warning')
    critical_count = sum(1 for v in violations if v['threshold_level'] == 'critical')
    
    if critical_count > 0:
        title = f"⚠️ Critical Threshold Violations ({critical_count})"
        st.error(title)
    elif warning_count > 0:
        title = f"⚠️ Warning Threshold Violations ({warning_count})"
        st.warning(title)
    else:
        title = "Threshold Violations (0)"
        st.info(title)
        
    # Display violation details
    for violation in violations:
        level = violation['threshold_level']
        message = violation['message']
        
        if level == 'critical':
            st.error(message)
        else:
            st.warning(message)
            
def _display_seasonality_analysis(seasonality_data: Dict[str, Any]) -> None:
    """
    Display seasonality analysis information.
    
    Args:
        seasonality_data: Dictionary containing seasonality information
    """
    with st.expander(f"Seasonality Analysis ({seasonality_data['detected_period_name']})"):
        period = seasonality_data['period']
        confidence = seasonality_data['confidence']
        
        st.markdown(f"### {seasonality_data['detected_period_name'].title()} Pattern Detected")
        
        confidence_emoji = "🟢" if confidence == 'high' else "🟡" if confidence == 'medium' else "🟠"
        st.markdown(f"**Confidence Level**: {confidence_emoji} {confidence.title()}")
        
        # Display patterns if available
        if seasonality_data.get('patterns'):
            patterns = seasonality_data['patterns']
            
            # Convert to DataFrame
            pattern_dicts = []
            for pattern in patterns:
                pattern_dicts.append({
                    'Day': pattern['day'],
                    'Average': f"{pattern['average']:.2f}",
                    'Variation': f"{pattern['variation']:+.1f}%"
                })
                
            pattern_df = pd.DataFrame(pattern_dicts)
            st.dataframe(pattern_df, hide_index=True)
            
            # Determine top and bottom days
            top_day = max(patterns, key=lambda x: x['variation'])
            bottom_day = min(patterns, key=lambda x: x['variation'])
            
            st.markdown(f"**Peak Day**: {top_day['day']} (+{top_day['variation']:.1f}%)")
            st.markdown(f"**Low Day**: {bottom_day['day']} ({bottom_day['variation']:.1f}%)")
            
        else:
            st.markdown(f"Detected a {period}-day seasonal pattern")
            
def configure_alert_thresholds(default_thresholds=None):
    """
    UI component for configuring alert thresholds.
    
    Args:
        default_thresholds: Dictionary of default thresholds
        
    Returns:
        Dictionary of configured thresholds
    """
    st.subheader("Configure Alert Thresholds")
    
    # Initialize with defaults if provided
    if default_thresholds is None:
        default_thresholds = {
            'channel': {
                'subscribers': {
                    'warning': {'type': 'percentage', 'value': 10},
                    'critical': {'type': 'percentage', 'value': 20},
                    'comparison_window': 7,
                    'direction': 'both'
                },
                'views': {
                    'warning': {'type': 'percentage', 'value': 15},
                    'critical': {'type': 'percentage', 'value': 30},
                    'comparison_window': 7,
                    'direction': 'both'
                }
            },
            'video': {
                'views': {
                    'warning': {'type': 'percentage', 'value': 20},
                    'critical': {'type': 'percentage', 'value': 50},
                    'comparison_window': 2,
                    'direction': 'both'
                }
            }
        }
    
    # Create tabs for different entity types
    tab1, tab2, tab3 = st.tabs(["Channel Metrics", "Video Metrics", "Comment Metrics"])
    
    with tab1:
        channel_thresholds = _configure_entity_thresholds(
            'channel',
            ['subscribers', 'views', 'total_videos'],
            default_thresholds.get('channel', {})
        )
        
    with tab2:
        video_thresholds = _configure_entity_thresholds(
            'video',
            ['views', 'likes', 'comment_count'],
            default_thresholds.get('video', {})
        )
        
    with tab3:
        comment_thresholds = _configure_entity_thresholds(
            'comment',
            ['likes', 'reply_count'],
            default_thresholds.get('comment', {})
        )
        
    # Combine all thresholds
    return {
        'channel': channel_thresholds,
        'video': video_thresholds,
        'comment': comment_thresholds
    }
        
def _configure_entity_thresholds(entity_type, metrics, defaults):
    """
    Configure thresholds for a specific entity type.
    
    Args:
        entity_type: Type of entity ('channel', 'video', 'comment')
        metrics: List of metric names
        defaults: Default threshold values
        
    Returns:
        Dictionary of configured thresholds
    """
    st.subheader(f"{entity_type.title()} Metrics")
    thresholds = {}
    
    for metric in metrics:
        with st.expander(f"{metric.replace('_', ' ').title()} Thresholds"):
            default = defaults.get(metric, {
                'warning': {'type': 'percentage', 'value': 10},
                'critical': {'type': 'percentage', 'value': 20},
                'comparison_window': 7,
                'direction': 'both'
            })
            
            # Select threshold type
            threshold_type = st.selectbox(
                f"{metric} Threshold Type",
                options=["percentage", "absolute", "statistical"],
                index=0 if default.get('warning', {}).get('type') == 'percentage' else 
                      1 if default.get('warning', {}).get('type') == 'absolute' else 2,
                key=f"{entity_type}_{metric}_type"
            )
            
            # Configure warning threshold
            warning_value = st.number_input(
                f"{metric} Warning Threshold",
                min_value=0.0,
                max_value=1000.0,
                value=float(default.get('warning', {}).get('value', 10)),
                key=f"{entity_type}_{metric}_warning"
            )
            
            # Configure critical threshold
            critical_value = st.number_input(
                f"{metric} Critical Threshold",
                min_value=0.0,
                max_value=1000.0,
                value=float(default.get('critical', {}).get('value', 20)),
                key=f"{entity_type}_{metric}_critical"
            )
            
            # Configure comparison window
            comparison_window = st.slider(
                f"{metric} Comparison Window (days)",
                min_value=1,
                max_value=90,
                value=int(default.get('comparison_window', 7)),
                key=f"{entity_type}_{metric}_window"
            )
            
            # Configure direction
            direction = st.selectbox(
                f"{metric} Alert Direction",
                options=["both", "increase", "decrease"],
                index=0 if default.get('direction') == 'both' else 
                      1 if default.get('direction') == 'increase' else 2,
                key=f"{entity_type}_{metric}_direction"
            )
            
            # Store the configuration
            thresholds[metric] = {
                'warning': {'type': threshold_type, 'value': warning_value},
                'critical': {'type': threshold_type, 'value': critical_value},
                'comparison_window': comparison_window,
                'direction': direction
            }
            
    return thresholds
