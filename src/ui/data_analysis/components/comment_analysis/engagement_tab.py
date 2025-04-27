"""
Engagement analysis tab for comment explorer.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from src.analysis.visualization.chart_helpers import (
    configure_bar_chart_layout,
    add_percentage_annotations,
    get_plotly_config
)

def render_engagement_tab(comment_analysis, total_comments):
    """
    Render the engagement analysis tab for comment explorer.
    
    Args:
        comment_analysis: Dictionary with comment analysis data
        total_comments: Total number of comments
    """
    st.subheader("Comment Engagement Analysis")
    
    # Get basic comment stats
    if 'stats' in comment_analysis and comment_analysis['stats'] is not None:
        try:
            # Display the main comment metrics
            render_engagement_metrics(comment_analysis['stats'])
            
            # Show comment length distribution if available
            if 'length_distribution' in comment_analysis['stats']:
                render_length_distribution(comment_analysis['stats'])
                
        except Exception as e:
            st.error(f"Error generating engagement analysis: {str(e)}")
    else:
        st.info("Engagement analysis not available for this channel.")

def render_engagement_metrics(stats):
    """
    Render engagement metrics section.
    
    Args:
        stats: Dictionary with comment statistics
    """
    # First row of metrics
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        comments_per_video = stats.get('comments_per_video', 0)
        st.metric("Avg Comments per Video", f"{comments_per_video:.1f}")
    
    with metric_cols[1]:
        avg_comment_length = stats.get('avg_comment_length', 0)
        st.metric("Avg Comment Length", f"{avg_comment_length:.1f} chars")
    
    with metric_cols[2]:
        reply_percentage = stats.get('reply_percentage', 0)
        st.metric("Replies", f"{reply_percentage:.1f}% of comments")
    
    # Second row of metrics
    metric_cols2 = st.columns(3)
    
    with metric_cols2[0]:
        avg_likes_per_comment = stats.get('avg_likes_per_comment', 0)
        st.metric("Avg Likes per Comment", f"{avg_likes_per_comment:.1f}")
    
    with metric_cols2[1]:
        most_liked_value = stats.get('most_liked_count', 0)
        st.metric("Most Liked Comment", f"{most_liked_value:,} likes")
    
    with metric_cols2[2]:
        creator_comments = stats.get('creator_comments', 0)
        total_comments = stats.get('total_comments', 1)  # Avoid division by zero
        creator_comments_pct = creator_comments / total_comments * 100
        st.metric("Creator Comments", f"{creator_comments:,} ({creator_comments_pct:.1f}%)")

def render_length_distribution(stats):
    """
    Render comment length distribution chart.
    
    Args:
        stats: Dictionary with comment statistics
    """
    length_dist = stats['length_distribution']
    
    if length_dist and isinstance(length_dist, dict):
        # Convert to dataframe for easier plotting
        length_df = pd.DataFrame({
            'Length Range': list(length_dist.keys()),
            'Count': list(length_dist.values())
        })
        
        # Ensure proper order
        length_ranges = [
            'Very Short (<50 chars)',
            'Short (50-100 chars)',
            'Medium (100-200 chars)',
            'Long (200-500 chars)',
            'Very Long (>500 chars)'
        ]
        
        length_df['Range_Ordered'] = pd.Categorical(
            length_df['Length Range'], 
            categories=length_ranges, 
            ordered=True
        )
        
        # Sort by the ordered range
        length_df = length_df.sort_values('Range_Ordered')
        
        # Create chart
        st.subheader("Comment Length Distribution")
        
        fig = px.bar(
            length_df,
            x='Range_Ordered',
            y='Count',
            labels={'Range_Ordered': 'Comment Length', 'Count': 'Number of Comments'},
            color='Count',
            color_continuous_scale=px.colors.sequential.Teal,
            text='Count'
        )
        
        # Configure layout
        fig = configure_bar_chart_layout(
            fig,
            "",
            "Comment Length",
            "Number of Comments",
            height=400
        )
        
        # Add percentage annotations
        total = length_df['Count'].sum()
        fig = add_percentage_annotations(fig, length_df, 'Range_Ordered', 'Count', total)
        
        # Show chart
        st.plotly_chart(fig, use_container_width=True, config=get_plotly_config())