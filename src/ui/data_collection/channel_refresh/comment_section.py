"""
This module handles the comment section of the channel refresh UI.
"""
import streamlit as st
import pandas as pd
from src.utils.debug_utils import debug_log

def render_comment_section(comments_data):
    """
    Render the comment section of the channel refresh UI.
    
    Args:
        comments_data: List of comment data from the API
    """
    st.subheader("Step 4: Comment Collection Results")
    
    if not comments_data:
        st.info("No comments found or comments have not been loaded yet.")
        return
    
    st.write(f"Successfully collected {len(comments_data)} comments")
    
    # Display a sample of comments
    st.subheader("Sample Comments")
    
    # Create a dataframe for comments
    comment_data_for_display = []
    for i, comment in enumerate(comments_data[:10]):  # Show up to 10 comments
        author = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('authorDisplayName', 'Unknown')
        text = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textDisplay', 'No text')
        published = comment.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('publishedAt', 'Unknown')
        
        comment_data_for_display.append({
            "Author": author,
            "Comment": text[:100] + "..." if len(text) > 100 else text,
            "Published": published
        })
    
    if comment_data_for_display:
        comment_df = pd.DataFrame(comment_data_for_display)
        st.dataframe(comment_df)

def configure_comment_collection():
    """
    Configure comment collection options.
    
    Returns:
        dict: Options for comment collection
    """
    st.subheader("🎯 Comment Collection Strategy")
    
    # Strategic Comment Collection Options
    st.markdown("""
    **Choose your strategy based on your analysis goals:**
    - Each video costs 1 API unit regardless of comment count
    - Maximize value by choosing the right strategy for your needs
    """)
    
    # Strategy selection
    strategy_options = {
        "Speed Mode": {
            "description": "🚀 **Fast sampling** - Get quick insights from minimal comments",
            "comments": 5,
            "replies": 0,
            "benefits": "• Fastest collection (3-5x faster)\n• Minimal API usage\n• Good for sentiment overview",
            "best_for": "Quick content sampling, basic sentiment analysis"
        },
        "Balanced Mode": {
            "description": "⚖️ **Balanced approach** - Good mix of speed and data richness", 
            "comments": 20,
            "replies": 5,
            "benefits": "• Moderate collection time\n• Comprehensive conversation context\n• Good engagement insights",
            "best_for": "General analysis, audience engagement studies"
        },
        "Comprehensive Mode": {
            "description": "📊 **Maximum data** - Extract maximum value from each API call",
            "comments": 50,
            "replies": 10,
            "benefits": "• Complete conversation threads\n• Deep engagement analysis\n• Maximum ROI on API quota",
            "best_for": "In-depth research, complete conversation analysis"
        },
        "Custom": {
            "description": "⚙️ **Custom settings** - Fine-tune parameters for your specific needs",
            "comments": 20,
            "replies": 5,
            "benefits": "• Full control over parameters\n• Tailored to specific use cases\n• Flexible configuration",
            "best_for": "Specific research requirements, advanced users"
        }
    }
    
    # Strategy selection radio buttons
    selected_strategy = st.radio(
        "Select your comment collection strategy:",
        options=list(strategy_options.keys()),
        format_func=lambda x: strategy_options[x]["description"],
        help="Each strategy optimizes for different goals and API usage patterns"
    )
    
    # Show strategy details
    strategy = strategy_options[selected_strategy]
    
    # Display strategy information in columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"**✅ Benefits:**\n{strategy['benefits']}")
    
    with col2:
        st.markdown(f"**🎯 Best for:** {strategy['best_for']}")
    
    # Strategy-specific controls
    if selected_strategy == "Custom":
        st.markdown("#### Custom Parameters")
        col1, col2 = st.columns([1, 1])
        with col1:
            max_comments_per_video = st.slider(
                "Top-Level Comments Per Video",
                min_value=0,
                max_value=100,
                value=20,
                help="Set to 0 to skip comment collection entirely"
            )
        
        with col2:
            max_replies_per_comment = st.slider(
                "Replies Per Top-Level Comment",
                min_value=0,
                max_value=50, 
                value=5,
                help="Set to 0 to skip fetching replies"
            )
    else:
        # Use predefined strategy values
        max_comments_per_video = strategy["comments"]
        max_replies_per_comment = strategy["replies"]
        
        # Show the selected values
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Comments per Video", max_comments_per_video)
        with col2:
            st.metric("Replies per Comment", max_replies_per_comment)
    
    # API efficiency information
    with st.expander("📊 Collection Efficiency Details"):
        st.markdown(f"""
        **API Constraints & Optimization:**
        - YouTube API requires 1 call per video (cannot be batched)
        - Comments per video: **{max_comments_per_video}** (maximum value per API unit)
        - Replies per comment: **{max_replies_per_comment}**
        
        **Why we've optimized this:**
        - RAPID MODE processing with 0.3s delays (maximum safe speed)
        - Pre-filtering to skip videos with disabled comments
        - Exact fetch counts to eliminate over-fetching waste
        """)

    optimize_quota = st.checkbox(
        "Optimize API quota usage",
        value=True,
        help="When enabled, only videos with comments will be queried"
    )
    
    # Create options for comments
    options = {
        'fetch_channel_data': False,
        'fetch_videos': False,
        'fetch_comments': True,
        'analyze_sentiment': False,
        'max_videos': 10,  # Limit for comments collection
        'max_comments_per_video': max_comments_per_video,
        'max_replies_per_comment': max_replies_per_comment,
        'optimize_quota': optimize_quota
    }
    
    return options
