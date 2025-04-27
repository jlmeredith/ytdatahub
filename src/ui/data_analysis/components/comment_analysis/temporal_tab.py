"""
Temporal analysis tab for comment explorer.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.analysis.visualization.trend_line import add_trend_line
from src.analysis.visualization.chart_helpers import (
    configure_time_series_layout,
    configure_bar_chart_layout,
    get_plotly_config
)

def render_temporal_tab(comment_analysis):
    """
    Render the temporal analysis tab for comment explorer.
    
    Args:
        comment_analysis: Dictionary with comment analysis data
    """
    if comment_analysis['temporal_data'] is not None:
        st.subheader("Comment Trends Over Time")
        
        # Get temporal data
        temporal_data = comment_analysis['temporal_data']
        
        # Show daily comment trend if we have enough data
        if 'daily' in temporal_data and len(temporal_data['daily']) > 5:
            try:
                render_daily_trend(temporal_data)
            except Exception as e:
                st.error(f"Error generating temporal analysis: {str(e)}")
        else:
            st.info("Not enough temporal data to display daily comment trends.")
            
        # Show hourly distribution if available
        if 'hourly' in temporal_data and len(temporal_data['hourly']) > 0:
            try:
                render_hourly_distribution(temporal_data)
            except Exception as e:
                st.error(f"Error generating hourly distribution: {str(e)}")
        else:
            st.info("Hourly distribution data not available.")
        
        # Show day of week distribution if available
        if 'day_of_week' in temporal_data and len(temporal_data['day_of_week']) > 0:
            try:
                render_day_of_week_distribution(temporal_data)
            except Exception as e:
                st.error(f"Error generating day of week distribution: {str(e)}")
        else:
            st.info("Day of week distribution data not available.")
    else:
        st.info("Temporal data not available for this channel.")

def render_daily_trend(temporal_data):
    """
    Render the daily comment trend chart.
    
    Args:
        temporal_data: Dictionary with temporal analysis data
    """
    daily_df = temporal_data['daily']
    
    # Create a container for better layout
    with st.container():
        # Create figure for daily comments
        fig = go.Figure()
        
        # Add bar chart for daily comments
        fig.add_trace(
            go.Bar(
                x=daily_df['Date'],
                y=daily_df['Count'],
                name="Comments",
                marker_color="rgba(58, 71, 180, 0.6)"
            )
        )
        
        # Add a 7-day moving average if we have enough data
        if len(daily_df) > 7:
            # Create a copy and sort by date
            df_sorted = daily_df.sort_values('Date')
            
            # Calculate the 7-day moving average
            df_sorted['MovingAvg'] = df_sorted['Count'].rolling(window=7).mean()
            
            # Add the moving average line to the chart
            fig.add_trace(
                go.Scatter(
                    x=df_sorted['Date'],
                    y=df_sorted['MovingAvg'],
                    mode='lines',
                    name="7-day Avg",
                    line=dict(color="red", width=2)
                )
            )
        
        # Add trendline using statsmodels if we have more than 3 points
        if len(daily_df) > 3:
            fig = add_trend_line(
                fig, 
                daily_df['Date'], 
                daily_df['Count'], 
                color="rgba(255, 0, 0, 0.7)", 
                width=3, 
                dash="dash", 
                name="Overall Trend"
            )
        
        # Configure layout
        fig = configure_time_series_layout(
            fig,
            "Daily Comment Activity",
            height=450
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True, config=get_plotly_config())
        
        # Add summary statistics
        summary_cols = st.columns(3)
        with summary_cols[0]:
            avg_comments = daily_df['Count'].mean()
            st.metric("Avg Comments/Day", f"{avg_comments:.1f}")
        
        with summary_cols[1]:
            max_comments = daily_df['Count'].max()
            max_day = daily_df.loc[daily_df['Count'].idxmax(), 'Date']
            max_day_str = max_day.strftime('%b %d, %Y') if hasattr(max_day, 'strftime') else str(max_day)
            st.metric("Max Comments", f"{max_comments}", f"on {max_day_str}")
        
        with summary_cols[2]:
            recent_avg = daily_df.sort_values('Date', ascending=False).head(7)['Count'].mean()
            recent_vs_overall = recent_avg - avg_comments
            delta = f"{recent_vs_overall:+.1f} vs overall"
            st.metric("Recent 7-day Avg", f"{recent_avg:.1f}", delta)

def render_hourly_distribution(temporal_data):
    """
    Render the hourly comment distribution chart.
    
    Args:
        temporal_data: Dictionary with temporal analysis data
    """
    hourly_df = temporal_data['hourly']
    
    # Create hourly distribution chart
    st.subheader("Comment Activity by Hour of Day")
    
    # Create figure
    fig = px.bar(
        hourly_df, 
        x='Hour', 
        y='Count',
        labels={'Hour': 'Hour of Day (UTC)', 'Count': 'Number of Comments'},
        color='Count',
        color_continuous_scale=px.colors.sequential.Blues
    )
    
    # Configure layout
    fig = configure_bar_chart_layout(
        fig,
        "",
        "Hour of Day (UTC)",
        "Number of Comments",
        height=350
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config=get_plotly_config())
    
    # Show peak hours
    top_hours = hourly_df.sort_values('Count', ascending=False).head(3)
    st.write("Peak commenting hours (UTC):")
    for _, row in top_hours.iterrows():
        st.write(f"- {int(row['Hour']):02d}:00 - {int(row['Hour']):02d}:59: {int(row['Count'])} comments ({row['Count']/hourly_df['Count'].sum()*100:.1f}%)")

def render_day_of_week_distribution(temporal_data):
    """
    Render the day of week comment distribution chart.
    
    Args:
        temporal_data: Dictionary with temporal analysis data
    """
    dow_df = temporal_data['day_of_week']
    
    # Create day of week distribution chart
    st.subheader("Comment Activity by Day of Week")
    
    # Create figure
    fig = px.bar(
        dow_df, 
        x='Day', 
        y='Count',
        labels={'Day': 'Day of Week', 'Count': 'Number of Comments'},
        color='Count',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Configure layout
    fig = configure_bar_chart_layout(
        fig,
        "",
        "Day of Week",
        "Number of Comments",
        height=350
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config=get_plotly_config())