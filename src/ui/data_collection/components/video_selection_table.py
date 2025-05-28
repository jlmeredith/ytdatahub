import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import pandas as pd


def render_video_selection_table(videos, selected_ids=None, key="video_selection_table"):
    """
    Render a sortable, filterable, paginated video selection table using AgGrid.
    Args:
        videos (list of dict): List of video data dicts
        selected_ids (list): List of video_ids that are currently selected
        key (str): Streamlit key for component state
    Returns:
        dict: {"selected_ids": list of selected video_ids, "action": str}
    """
    if not videos:
        st.info("No videos available for selection.")
        return {"selected_ids": [], "action": "none"}
    
    # Filter out videos missing video_id field
    valid_videos = []
    invalid_count = 0
    for video in videos:
        if not isinstance(video, dict):
            invalid_count += 1
            continue
        video_id = video.get('video_id')
        if not video_id:
            invalid_count += 1
            continue
        valid_videos.append(video)
    
    if invalid_count > 0:
        st.warning(f"⚠️ {invalid_count} videos were filtered out due to missing video_id fields.")
    
    if not valid_videos:
        st.error("No valid videos found with video_id fields.")
        return {"selected_ids": [], "action": "none"}
    
    # Initialize selected_ids if not provided
    if selected_ids is None:
        selected_ids = []

    # Flatten and prepare data for DataFrame
    df = pd.DataFrame(valid_videos)
    if 'video_id' not in df.columns:
        st.error("Video data missing 'video_id' field.")
        return {"selected_ids": [], "action": "none"}
    
    # Ensure we have basic required columns
    if 'title' not in df.columns:
        df['title'] = df.get('snippet', [{}]).apply(lambda s: s.get('title', '') if isinstance(s, dict) else '')
    if 'views' not in df.columns:
        df['views'] = df.get('statistics', [{}]).apply(lambda s: s.get('viewCount', 0) if isinstance(s, dict) else 0)
    if 'likes' not in df.columns:
        df['likes'] = df.get('statistics', [{}]).apply(lambda s: s.get('likeCount', 0) if isinstance(s, dict) else 0)
    if 'comment_count' not in df.columns:
        df['comment_count'] = df.get('statistics', [{}]).apply(lambda s: s.get('commentCount', 0) if isinstance(s, dict) else 0)
    if 'published_at' not in df.columns:
        df['published_at'] = df.get('snippet', [{}]).apply(lambda s: s.get('publishedAt', '') if isinstance(s, dict) else '')

    # Columns to display (simplified - no thumbnails for now)
    display_cols = [
        'video_id', 'title', 'views', 'likes', 'comment_count', 'published_at'
    ]
    df_display = df[display_cols].rename(columns={
        'video_id': 'Video ID',
        'title': 'Title',
        'views': 'Views',
        'likes': 'Likes',
        'comment_count': 'Comments',
        'published_at': 'Published'
    })

    # Convert numeric columns to ensure they're properly formatted
    for col in ['Views', 'Likes', 'Comments']:
        df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0).astype(int)

    gb = GridOptionsBuilder.from_dataframe(df_display)
    
    # Fix pre-selection logic to handle the actual DataFrame structure
    pre_selected_indices = []
    if selected_ids:
        for i, video_id in enumerate(df['video_id']):
            if video_id in selected_ids:
                pre_selected_indices.append(i)
    
    gb.configure_selection('multiple', use_checkbox=True, pre_selected_rows=pre_selected_indices)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
    gb.configure_column('Title', sortable=True, filter=True, width=400)
    gb.configure_column('Views', type=['numericColumn'], sortable=True, filter=True)
    gb.configure_column('Likes', type=['numericColumn'], sortable=True, filter=True)
    gb.configure_column('Comments', type=['numericColumn'], sortable=True, filter=True)
    gb.configure_column('Published', sortable=True, filter=True)
    gb.configure_column('Video ID', hide=True)
    grid_options = gb.build()

    # Remove custom HTML renderer registration
    response = AgGrid(
        df_display,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        key=key
    )

    # Safely handle the response
    selected_rows = response.get('selected_rows', []) if response else []
    if selected_rows is None:
        selected_rows = []
    
    selected_video_ids = []
    try:
        # Debug: log what we're getting from AgGrid
        st.write(f"Debug: Selected rows type: {type(selected_rows)}")
        
        # Handle pandas DataFrame (which AgGrid often returns)
        if hasattr(selected_rows, 'to_dict'):
            # Convert DataFrame to list of dictionaries
            selected_rows = selected_rows.to_dict('records')
            st.write(f"Debug: Converted DataFrame to {len(selected_rows)} records")
        
        if selected_rows:
            st.write(f"Debug: First selected row type: {type(selected_rows[0])}")
            st.write(f"Debug: First selected row content: {selected_rows[0]}")
        
        # Handle different possible formats
        for row in selected_rows:
            if isinstance(row, dict):
                # Standard dictionary format
                if 'Video ID' in row:
                    selected_video_ids.append(row['Video ID'])
            elif isinstance(row, str):
                # If it's a string, it might be the video ID directly
                selected_video_ids.append(row)
            elif hasattr(row, 'get'):
                # Object with get method
                video_id = row.get('Video ID')
                if video_id:
                    selected_video_ids.append(video_id)
                    
    except Exception as e:
        st.error(f"Error processing selected rows: {e}")
        st.write(f"Debug: Selected rows content: {selected_rows}")
        selected_video_ids = []
    
    st.caption(f"{len(selected_video_ids)} of {len(df)} videos selected.")
    return {"selected_ids": selected_video_ids, "action": "none"} 