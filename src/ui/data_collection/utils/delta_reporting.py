"""
Delta reporting functionality for data collection UI.
Provides utilities to show differences between data sets.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from ..utils.data_conversion import format_number
from src.utils.helpers import debug_log

def render_delta_report(previous_data, updated_data, data_type="channel"):
    """
    Display a report showing differences between previous and updated data.
    
    Args:
        previous_data (dict): Previous channel data
        updated_data (dict): New channel data after update
        data_type (str): Type of data being compared ("channel", "video", or "comment")
    """
    if not previous_data or not updated_data:
        st.info("No previous data available for comparison.")
        return
    
    try:
        # Attempt to use DeepDiff for more detailed comparison
        from deepdiff import DeepDiff
        
        # For video and comment comparisons, only look at specific fields
        if data_type == "video":
            exclude_paths = ["root['data_source']", "root['channel_id']", "root['channel_name']", 
                            "root['subscribers']", "root['views']", "root['total_videos']"]
        elif data_type == "comment":
            exclude_paths = ["root['data_source']", "root['channel_id']", "root['channel_name']", 
                            "root['subscribers']", "root['views']", "root['total_videos']",
                            "root['video_id'][*]['video_id']", "root['video_id'][*]['title']"]
        else:
            exclude_paths = ["root['data_source']"]
            
        # Perform the deep comparison
        diff = DeepDiff(previous_data, updated_data, exclude_paths=exclude_paths)
        
        if not diff:
            # No differences found
            st.info("No changes detected in the data.")
            
            # Show summary of what was checked
            if data_type == "channel":
                st.write("Channel data remains unchanged.")
                st.caption(f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # For video data, show a summary of the videos that were checked
            elif data_type == "video":
                video_count = len(updated_data.get('video_id', []))
                if video_count > 0:
                    st.write(f"All {video_count} videos remain unchanged.")
                    
                    # Show a sample of video titles
                    sample_size = min(5, video_count)
                    if sample_size > 0:
                        st.write(f"Sample videos checked:")
                        for i in range(sample_size):
                            video = updated_data['video_id'][i]
                            st.write(f"- {video.get('title', 'Unknown')}")
                        
                        if video_count > sample_size:
                            st.write(f"...and {video_count - sample_size} more videos")
            
            # For comments data, show a summary of the comments that were checked
            elif data_type == "comment":
                comment_count = sum(len(v.get('comments', [])) for v in updated_data.get('video_id', []))
                if comment_count > 0:
                    st.write(f"All {comment_count} comments remain unchanged.")
                    
        else:
            # For channel data, display key channel metrics
            if data_type == "channel":
                # Display key channel metrics that have been updated
                metrics_to_show = []
                if 'channel_name' in updated_data:
                    metrics_to_show.append(("Channel Name", updated_data.get('channel_name', 'Unknown')))
                if 'subscribers' in updated_data:
                    metrics_to_show.append(("Subscribers", format_number(int(updated_data.get('subscribers', 0)))))
                if 'views' in updated_data:
                    metrics_to_show.append(("Views", format_number(int(updated_data.get('views', 0)))))
                if 'total_videos' in updated_data:
                    metrics_to_show.append(("Videos", format_number(int(updated_data.get('total_videos', 0)))))
                
                # Display metrics in a clear format
                if metrics_to_show:
                    # Use columns to display metrics nicely
                    cols = st.columns(min(4, len(metrics_to_show)))
                    for i, (label, value) in enumerate(metrics_to_show):
                        with cols[i % len(cols)]:
                            st.metric(label, value)
                
                # Add timestamp info for last check
                st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Show added items
            if 'dictionary_item_added' in diff:
                added_items = [item.replace("root['", "").replace("']", "").replace(".", " > ") 
                              for item in diff['dictionary_item_added']]
                
                if data_type == "video":
                    new_videos_count = len([item for item in added_items if "video_id" in item])
                    if new_videos_count > 0:
                        st.success(f"✅ {new_videos_count} new videos found")
                elif data_type == "comment":
                    new_comments_count = len([item for item in added_items if "comments" in item])
                    if new_comments_count > 0:
                        st.success(f"✅ {new_comments_count} new comments found")
                else:
                    if added_items:
                        st.success(f"✅ New data added: {', '.join(added_items[:5])}")
                        if len(added_items) > 5:
                            st.info(f"...and {len(added_items)-5} more items")
            
            # Show removed items
            if 'dictionary_item_removed' in diff:
                removed_items = [item.replace("root['", "").replace("']", "").replace(".", " > ") 
                                for item in diff['dictionary_item_removed']]
                
                if removed_items:
                    st.warning(f"⚠️ Items no longer present: {', '.join(removed_items[:5])}")
                    if len(removed_items) > 5:
                        st.info(f"...and {len(removed_items)-5} more items")
            
            # Show changed values
            if 'values_changed' in diff:
                changed_items = diff['values_changed']
                
                # For nicer display, group changes by type
                view_changes = []
                like_changes = []
                comment_changes = []
                other_changes = []
                
                for path, change in changed_items.items():
                    if 'views' in path:
                        view_changes.append(f"{change['old_value']} → {change['new_value']}")
                    elif 'likes' in path:
                        like_changes.append(f"{change['old_value']} → {change['new_value']}")
                    elif 'comment_count' in path:
                        comment_changes.append(f"{change['old_value']} → {change['new_value']}")
                    else:
                        other_changes.append(f"{path}: {change['old_value']} → {change['new_value']}")
                
                # Display view changes
                if view_changes and len(view_changes) <= 5:
                    st.info(f"📈 Views updated: {', '.join(view_changes)}")
                elif view_changes:
                    st.info(f"📈 Views updated for {len(view_changes)} items")
                
                # Display like changes
                if like_changes and len(like_changes) <= 5:
                    st.info(f"👍 Likes updated: {', '.join(like_changes)}")
                elif like_changes:
                    st.info(f"👍 Likes updated for {len(like_changes)} items")
                
                # Display comment count changes
                if comment_changes and len(comment_changes) <= 5:
                    st.info(f"💬 Comment counts updated: {', '.join(comment_changes)}")
                elif comment_changes:
                    st.info(f"💬 Comment counts updated for {len(comment_changes)} items")
                
                # Display other changes
                if other_changes and len(other_changes) <= 5:
                    st.info(f"Other changes: {', '.join(other_changes)}")
                elif other_changes:
                    st.info(f"Other changes in {len(other_changes)} items")
                    
    except ImportError:
        # Fallback if DeepDiff is not available
        st.info("Data has been updated. Install DeepDiff for detailed change reports.")
        
    except Exception as e:
        debug_log(f"Error generating delta report: {str(e)}", e)
        st.error(f"Error generating comparison report: {str(e)}")
        
        # Fallback to basic comparison
        if data_type == "channel":
            # Show basic metrics
            if 'subscribers' in updated_data and 'subscribers' in previous_data:
                old_subs = int(previous_data.get('subscribers', 0))
                new_subs = int(updated_data.get('subscribers', 0))
                st.metric("Subscribers", format_number(new_subs), format_number(new_subs - old_subs))
            
            if 'views' in updated_data and 'views' in previous_data:
                old_views = int(previous_data.get('views', 0))
                new_views = int(updated_data.get('views', 0))
                st.metric("Total Views", format_number(new_views), format_number(new_views - old_views))
            
            if 'total_videos' in updated_data and 'total_videos' in previous_data:
                old_videos = int(previous_data.get('total_videos', 0))
                new_videos = int(updated_data.get('total_videos', 0))
                st.metric("Videos", format_number(new_videos), format_number(new_videos - old_videos))