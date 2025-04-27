"""
Commenter analysis tab for comment explorer.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from src.analysis.visualization.chart_helpers import (
    configure_bar_chart_layout,
    get_plotly_config
)

def render_commenter_tab(comment_analysis, total_comments):
    """
    Render the commenter analysis tab for comment explorer.
    
    Args:
        comment_analysis: Dictionary with comment analysis data
        total_comments: Total number of comments
    """
    st.subheader("Top Commenters Analysis")
    
    if 'author_stats' in comment_analysis and comment_analysis['author_stats'] is not None:
        try:
            author_stats = comment_analysis['author_stats']
            
            # Display basic stats
            render_commenter_metrics(author_stats, total_comments)
            
            # Show top commenters chart
            if 'top_authors' in author_stats and not author_stats['top_authors'].empty:
                render_top_commenters_chart(author_stats['top_authors'])
                
        except Exception as e:
            st.error(f"Error generating commenter analysis: {str(e)}")
    else:
        st.info("Commenter analysis not available for this channel.")

def render_commenter_metrics(author_stats, total_comments):
    """
    Render commenter metrics section.
    
    Args:
        author_stats: Dictionary with author statistics
        total_comments: Total number of comments
    """
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        unique_authors = author_stats.get('unique_authors', 0)
        st.metric("Unique Commenters", f"{unique_authors:,}")
    
    with metric_cols[1]:
        comments_per_author = total_comments / unique_authors if unique_authors > 0 else 0
        st.metric("Avg Comments per Author", f"{comments_per_author:.2f}")
    
    with metric_cols[2]:
        top10_percent = author_stats.get('top10_percent', 0)
        st.metric("Top Author Concentration", f"{top10_percent:.1f}% make 10% of comments")
        
def render_top_commenters_chart(top_authors_df):
    """
    Render top commenters chart.
    
    Args:
        top_authors_df: DataFrame with top authors data
    """
    st.subheader("Top Commenters")
    
    # Get top 20 authors max for better visualization
    display_df = top_authors_df.head(20).copy()
    
    # Create a horizontal bar chart
    fig = px.bar(
        display_df,
        y='Author',
        x='Comment Count',
        orientation='h',
        color='Comment Count',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={'Comment Count': 'Number of Comments', 'Author': 'Commenter'},
        title=f"Top {len(display_df)} Commenters"
    )
    
    # Customize chart
    fig = configure_bar_chart_layout(
        fig,
        f"Top {len(display_df)} Commenters",
        "Number of Comments",
        "Commenter",
        height=min(400, 100 + 20 * len(display_df))  # Dynamic height based on number of commenters
    )
    
    # Sort bars from highest to lowest
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config=get_plotly_config())
    
    # Show top commenters as a table
    with st.expander("View Top Commenters Data"):
        st.dataframe(display_df, use_container_width=True)