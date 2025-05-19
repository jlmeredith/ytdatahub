"""
Channel comparison functionality for the analytics dashboard.
"""
import streamlit as st
import pandas as pd
import time
from src.utils.helpers import debug_log

def render_channel_comparison(aggregated_metrics, channel_colors):
    """
    Render the channel comparison table and related visualizations.
    
    Args:
        aggregated_metrics: List of dictionaries containing channel metrics
        channel_colors: Dictionary mapping channel names to colors
    """
    chart_start_time = time.time()
    st.subheader("Channel Comparison")
    metrics_df = pd.DataFrame(aggregated_metrics)
    
    # Format the metrics for display
    for col in ['Avg Views', 'Avg Likes', 'Avg Comments', 'Total Videos']:
        if col in metrics_df.columns:
            metrics_df[col] = metrics_df[col].apply(lambda x: f"{int(x):,}")
            
    for col in ['Like/View Ratio', 'Comment/View Ratio', 'Engagement Rate']:
        if col in metrics_df.columns:
            metrics_df[col] = metrics_df[col].apply(lambda x: f"{x:.2f}%")
    
    # Display the comparison table
    st.dataframe(
        metrics_df,
        column_config={
            "Channel": st.column_config.TextColumn(
                    "Channel",
                    help="Click on a channel name to analyze it"
                ),
            "Total Videos": st.column_config.TextColumn("Videos", width="small"),
            "Avg Views": st.column_config.TextColumn("Avg Views", width="small"),
            "Avg Likes": st.column_config.TextColumn("Avg Likes", width="small"),
            "Avg Comments": st.column_config.TextColumn("Avg Comments", width="small"),
            "Like/View Ratio": st.column_config.TextColumn("Like Rate", width="small"),
            "Comment/View Ratio": st.column_config.TextColumn("Comment Rate", width="small"),
            "Engagement Rate": st.column_config.TextColumn("Engagement", width="small"),
            "Date Range": st.column_config.TextColumn("Date Range", width="medium")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Add clickable channel names with JavaScript interactivity
    st.markdown("""
    <style>
    .channel-link {
        text-decoration: none;
        color: #1E88E5;
        font-weight: 500;
        cursor: pointer;
    }
    .channel-link:hover {
        text-decoration: underline;
        color: #0D47A1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create links for each channel
    for _, row in metrics_df.iterrows():
        channel_name = row['Channel']
        st.markdown(f"""
        <p><a class="channel-link" href="javascript:void(0);" 
        onclick="document.dispatchEvent(new CustomEvent('streamlit:selectChannel', {{detail: '{channel_name}'}}))">
        {channel_name}</a></p>
        """, unsafe_allow_html=True)
        
    # JavaScript to handle the custom event
    st.markdown("""
    <script>
    document.addEventListener('streamlit:selectChannel', function(e) {
        const channelName = e.detail;
        window.parent.postMessage({
            type: 'streamlit:setSessionState', 
            session_state: {
                selected_channel: channelName,
                active_analysis_section: 'dashboard'
            }
        }, '*');
        // Force reload to apply the change
        setTimeout(() => window.parent.postMessage({type: 'streamlit:forceRerun'}, '*'), 100);
    });
    </script>
    """, unsafe_allow_html=True)
    
    debug_log(f"Channel comparison table rendered in {time.time() - chart_start_time:.2f} seconds",
             performance_tag="end_comparison_table")
