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
    # Better handling for empty or None data
    if previous_data is None and updated_data is None:
        st.info("No data available for comparison.")
        return
    elif previous_data is None:
        st.info("No previous data available. This appears to be new data.")
        if updated_data:
            st.write("New data:")
            st.json(updated_data)
        return
    elif updated_data is None:
        st.info("No updated data available for comparison.")
        if previous_data:
            st.write("Previous data:")
            st.json(previous_data)
        return
    
    # Handle empty dictionaries
    if isinstance(previous_data, dict) and not previous_data:
        if isinstance(updated_data, dict) and not updated_data:
            st.info("Both previous and updated data sets are empty.")
            return
        st.info("Previous data is empty. Showing only updated data.")
        st.json(updated_data)
        return
    elif isinstance(updated_data, dict) and not updated_data:
        st.info("Updated data is empty. Showing only previous data.")
        st.json(previous_data)
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
                            st.write(f"... and {video_count - sample_size} more videos.")
            
            return
            
        # Display differences in a readable format
        st.subheader("Changes Detected")
        
        # Display added items
        if 'dictionary_item_added' in diff:
            st.markdown("#### Added Items")
            for item in diff['dictionary_item_added']:
                item_path = item.replace("root['", "").replace("']", "")
                st.write(f"- Added: {item_path}")
                
        # Display removed items
        if 'dictionary_item_removed' in diff:
            st.markdown("#### Removed Items")
            for item in diff['dictionary_item_removed']:
                item_path = item.replace("root['", "").replace("']", "")
                st.write(f"- Removed: {item_path}")
                
        # Display changed values
        if 'values_changed' in diff:
            st.markdown("#### Changed Values")
            for path, change in diff['values_changed'].items():
                # Clean up the path for display
                clean_path = path.replace("root['", "").replace("']", "")
                
                # Format numbers with commas for readability
                old_val = format_number(change['old_value']) if isinstance(change['old_value'], (int, float)) else change['old_value']
                new_val = format_number(change['new_value']) if isinstance(change['new_value'], (int, float)) else change['new_value']
                
                # Calculate and display percentage change for numerical values
                if isinstance(change['old_value'], (int, float)) and isinstance(change['new_value'], (int, float)) and change['old_value'] != 0:
                    pct_change = ((change['new_value'] - change['old_value']) / change['old_value']) * 100
                    if pct_change > 0:
                        change_str = f"(+{pct_change:.2f}%)"
                        st.write(f"- {clean_path}: {old_val} → {new_val} {change_str} 📈")
                    elif pct_change < 0:
                        change_str = f"({pct_change:.2f}%)"
                        st.write(f"- {clean_path}: {old_val} → {new_val} {change_str} 📉")
                    else:
                        st.write(f"- {clean_path}: {old_val} → {new_val}")
                else:
                    st.write(f"- {clean_path}: {old_val} → {new_val}")
                
    except ImportError:
        # Fallback if DeepDiff is not available
        st.warning("DeepDiff library not found. Using basic comparison.")
        st.write("Previous data:")
        st.json(previous_data)
        st.write("Updated data:")
        st.json(updated_data)
    except Exception as e:
        # Handle other errors
        debug_log(f"Error in delta report: {str(e)}")
        st.error(f"Error generating delta report: {str(e)}")
        st.write("Previous data:")
        st.json(previous_data)
        st.write("Updated data:")
        st.json(updated_data)