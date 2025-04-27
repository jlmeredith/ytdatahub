"""
Analytics dashboard component for the data analysis UI.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.analysis.youtube_analysis import YouTubeAnalysis
from src.analysis.visualization.trend_line import add_trend_line
from src.analysis.visualization.chart_helpers import (
    configure_time_series_layout,
    configure_bar_chart_layout,
    add_percentage_annotations,
    get_plotly_config
)
from src.ui.components.ui_utils import render_template_as_markdown, render_template

def render_analytics_dashboard(channel_data):
    """
    Render the analytics dashboard component.
    
    Args:
        channel_data: Dictionary containing channel data
    """
    # Initialize analysis
    analysis = YouTubeAnalysis()
    
    # Get video statistics for charts
    video_stats = analysis.get_video_statistics(channel_data)
    
    # Load analytics dashboard styles
    render_template_as_markdown("analytics_dashboard_styles.html")
    
    # Set up template context
    template_context = {
        'no_data': False,
        'show_duration_chart': st.session_state.show_duration_chart
    }
    
    # Check if we have video data
    if video_stats['df'] is None or video_stats['df'].empty:
        template_context['no_data'] = True
        render_template_as_markdown("analytics_dashboard.html", template_context)
        return
        
    df = video_stats['df']
    
    # Generate content for each section
    if 'Published' in df.columns:
        try:
            # Generate engagement timeline chart
            engagement_timeline_html = create_engagement_timeline_chart(df)
            template_context['engagement_timeline_chart'] = engagement_timeline_html
            
            # Generate engagement metrics HTML
            engagement_metrics_html = create_engagement_metrics_html(df)
            template_context['engagement_metrics_html'] = engagement_metrics_html
            
        except Exception as e:
            st.error(f"Error generating timeline charts: {str(e)}")
            
    # Video duration analysis
    if st.session_state.show_duration_chart:
        # Get duration analysis
        duration_analysis = analysis.get_duration_analysis(channel_data)
        
        if duration_analysis['category_df'] is not None:
            try:
                # Generate duration chart
                duration_chart_html = create_duration_chart_html(duration_analysis)
                template_context['duration_chart'] = duration_chart_html
                
                # Generate duration metrics HTML
                duration_metrics_html = create_duration_metrics_html(duration_analysis)
                template_context['duration_metrics_html'] = duration_metrics_html
                
            except Exception as e:
                st.error(f"Error generating duration analysis: {str(e)}")
    
    # Render the main dashboard template with all the content
    render_template_as_markdown("analytics_dashboard.html", template_context)

def create_engagement_timeline_chart(df):
    """
    Create the engagement timeline chart HTML.
    
    Args:
        df: DataFrame with video data
        
    Returns:
        str: HTML representation of the chart
    """
    # Make sure Published is in datetime format and sorted
    df['Published'] = pd.to_datetime(df['Published'])
    df_sorted = df.sort_values('Published')
    
    # Determine whether to use rolling average based on number of videos
    use_rolling_avg = len(df) > 25
    
    # Create a multi-chart figure with auto-sized height based on window width
    fig = go.Figure()
    
    # Create charts based on user preferences
    if st.session_state.show_views_chart:
        view_color = "rgba(0, 150, 255, 0.7)"  # Blue for views
        # Add the main views scatter plot
        fig.add_trace(
            go.Scatter(
                x=df_sorted['Published'], 
                y=df_sorted['Views'],
                mode='markers',
                marker=dict(color=view_color, size=10),
                opacity=0.7,
                name="Views"
            )
        )
    
    if st.session_state.show_likes_chart:
        like_color = "rgba(255, 50, 50, 0.7)"  # Red for likes
        
        # Add likes scatter plot
        fig.add_trace(
            go.Scatter(
                x=df_sorted['Published'], 
                y=df_sorted['Likes'],
                mode='markers',
                marker=dict(color=like_color, size=10),
                opacity=0.7,
                name="Likes",
                visible='legendonly'  # Hide by default
            )
        )
        
        # Add rolling average for likes if there are enough videos
        if use_rolling_avg:
            window = min(7, max(3, len(df_sorted) // 10))
            df_sorted['Likes_Rolling'] = df_sorted['Likes'].rolling(window=window).mean()
            fig.add_trace(
                go.Scatter(
                    x=df_sorted['Published'],
                    y=df_sorted['Likes_Rolling'],
                    mode='lines',
                    line=dict(color="rgba(200, 50, 50, 1)", width=3),
                    name=f"{window}-Video Rolling Avg (Likes)",
                    visible='legendonly'  # Hide by default
                )
            )
        
        # Add trend line with statsmodels
        if len(df_sorted) > 1:
            fig = add_trend_line(
                fig, 
                df_sorted['Published'], 
                df_sorted['Likes'], 
                color="rgba(150, 50, 50, 0.8)", 
                width=2, 
                dash="dash", 
                name="Likes Trend",
                visible='legendonly'  # Hide by default
            )
    
    if st.session_state.show_comments_chart:
        comment_color = "rgba(100, 255, 100, 0.7)"  # Green for comments
        # Add comments scatter plot
        fig.add_trace(
            go.Scatter(
                x=df_sorted['Published'], 
                y=df_sorted['Comments'],
                mode='markers',
                marker=dict(color=comment_color, size=10),
                opacity=0.7,
                name="Comments",
                visible='legendonly'  # Hide by default
            )
        )
        
        # Add rolling average for comments if there are enough videos
        if use_rolling_avg:
            window = min(7, max(3, len(df_sorted) // 10))
            df_sorted['Comments_Rolling'] = df_sorted['Comments'].rolling(window=window).mean()
            fig.add_trace(
                go.Scatter(
                    x=df_sorted['Published'],
                    y=df_sorted['Comments_Rolling'],
                    mode='lines',
                    line=dict(color="rgba(50, 200, 50, 1)", width=3),
                    name=f"{window}-Video Rolling Avg (Comments)",
                    visible='legendonly'  # Hide by default
                )
            )
        
        # Add trend line with statsmodels
        if len(df_sorted) > 1:
            fig = add_trend_line(
                fig, 
                df_sorted['Published'], 
                df_sorted['Comments'], 
                color="rgba(50, 150, 50, 0.8)", 
                width=2, 
                dash="dash", 
                name="Comments Trend",
                visible='legendonly'  # Hide by default
            )
    
    # Update layout with better styling and responsiveness
    fig = configure_time_series_layout(fig, "Views, Likes and Comments Over Time")
    
    # Generate chart HTML
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn', config=get_plotly_config())
    
    # Generate note based on data
    video_count = len(df)
    date_range = f"{df_sorted['Published'].min().strftime('%b %Y')} to {df_sorted['Published'].max().strftime('%b %Y')}"
    chart_note = f"Analysis based on {video_count} videos from {date_range}."
    
    # Render using the template
    return render_template("engagement_timeline_chart.html", {
        'chart_html': chart_html,
        'chart_note': chart_note
    })

def create_engagement_metrics_html(df):
    """
    Create the HTML for engagement metrics.
    
    Args:
        df: DataFrame with video data
        
    Returns:
        str: HTML content for the engagement metrics
    """
    # Calculate metrics
    avg_views = int(df['Views'].mean())
    avg_likes = int(df['Likes'].mean())
    avg_comments = int(df['Comments'].mean())
    
    # Calculate ratios
    like_view_ratio = avg_likes / avg_views * 100 if avg_views > 0 else 0
    comment_view_ratio = avg_comments / avg_views * 100 if avg_views > 0 else 0
    
    # Format values for template
    template_context = {
        'avg_views_formatted': f"{avg_views:,}",
        'avg_likes_formatted': f"{avg_likes:,}",
        'avg_comments_formatted': f"{avg_comments:,}",
        'like_view_ratio': f"{like_view_ratio:.2f}",
        'comment_view_ratio': f"{comment_view_ratio:.2f}"
    }
    
    # Render and return the metrics HTML using the template
    return render_template("engagement_metrics.html", template_context)

def create_duration_chart_html(df):
    """
    Create the video duration distribution chart HTML.
    
    Args:
        df: DataFrame with video data
        
    Returns:
        str: HTML representation of the chart
    """
    # Calculate duration in minutes
    df['Duration_Minutes'] = df['Duration'].apply(
        lambda x: x.total_seconds() / 60 if isinstance(x, timedelta) else 0
    )
    
    # Create histogram data
    fig = go.Figure()
    
    fig.add_trace(
        go.Histogram(
            x=df['Duration_Minutes'],
            autobinx=False,
            xbins=dict(
                start=0,
                end=df['Duration_Minutes'].max() + 5,  # Add padding for readability
                size=2  # 2-minute bins
            ),
            marker_color='rgba(0, 150, 255, 0.7)',
            opacity=0.9,
            hovertemplate="Duration: %{x:.1f} minutes<br>Count: %{y} videos<extra></extra>"
        )
    )
    
    # Add a line for the average duration
    avg_duration = df['Duration_Minutes'].mean()
    fig.add_vline(
        x=avg_duration,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Average: {avg_duration:.1f} min",
        annotation_position="top right"
    )
    
    # Configure layout
    fig.update_layout(
        title={
            'text': "Video Duration Distribution",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, color="#333")
        },
        xaxis_title="Duration (minutes)",
        yaxis_title="Number of Videos",
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='rgba(245, 245, 245, 0.95)',
        height=400,
        bargap=0.05
    )
    
    # Generate chart HTML
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn', config=get_plotly_config())
    
    # Generate note based on data
    min_duration = df['Duration_Minutes'].min()
    max_duration = df['Duration_Minutes'].max()
    chart_note = f"Video durations range from {min_duration:.1f} minutes to {max_duration:.1f} minutes."
    
    # Render using the template
    return render_template("duration_chart.html", {
        'chart_html': chart_html,
        'chart_note': chart_note
    })

def create_duration_metrics_html(duration_analysis):
    """
    Create the HTML for duration metrics.
    
    Args:
        duration_analysis: Dictionary with duration analysis data
        
    Returns:
        str: HTML content for the duration metrics
    """
    # Duration stats
    stats = duration_analysis['stats']
    
    if not stats:
        return ""
        
    # Get duration metrics for template
    min_duration = stats.get('min_duration_human', 'N/A')
    avg_duration = stats.get('avg_duration_human', 'N/A')
    max_duration = stats.get('max_duration_human', 'N/A')
    
    # Format template context
    template_context = {
        'min_duration': min_duration,
        'avg_duration': avg_duration,
        'max_duration': max_duration
    }
    
    # Render and return the metrics HTML
    return render_template("duration_metrics.html", template_context)