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
        if updated_data and st.session_state.get('debug_mode', False):
            st.write("New data (Debug):")
            # Safely display JSON data
            try:
                if isinstance(updated_data, dict) and "ERROR" in updated_data:
                    st.error(f"Error in updated data: {updated_data.get('ERROR', {}).get('message', 'Unknown error')}")
                else:
                    st.json(updated_data)
            except Exception as e:
                st.error(f"Error displaying updated data: {str(e)}")
                st.text(str(updated_data)[:1000])
        return
    elif updated_data is None:
        st.info("No updated data available for comparison.")
        if previous_data and st.session_state.get('debug_mode', False):
            st.write("Previous data (Debug):")
            # Safely display JSON data
            try:
                if isinstance(previous_data, dict) and "ERROR" in previous_data:
                    st.error(f"Error in previous data: {previous_data.get('ERROR', {}).get('message', 'Unknown error')}")
                else:
                    st.json(previous_data)
            except Exception as e:
                st.error(f"Error displaying previous data: {str(e)}")
                st.text(str(previous_data)[:1000])
        return
    
    # Check for error objects in the data
    if isinstance(previous_data, dict) and "ERROR" in previous_data:
        st.error(f"Error in previous data: {previous_data.get('ERROR', {}).get('message', 'Unknown error')}")
        return
    
    if isinstance(updated_data, dict) and "ERROR" in updated_data:
        st.error(f"Error in updated data: {updated_data.get('ERROR', {}).get('message', 'Unknown error')}")
        return
    
    # Validate data before comparison
    if not isinstance(previous_data, dict) or not isinstance(updated_data, dict):
        st.error(f"Invalid data format for comparison. Previous data type: {type(previous_data)}, Updated data type: {type(updated_data)}")
        if st.session_state.get('debug_mode', False):
            st.write("Previous data preview:")
            st.text(str(previous_data)[:500])
            st.write("Updated data preview:")
            st.text(str(updated_data)[:500])
        return
    
    # Handle empty dictionaries
    if isinstance(previous_data, dict) and not previous_data:
        if isinstance(updated_data, dict) and not updated_data:
            st.info("Both previous and updated data sets are empty.")
            return
        st.info("Previous data is empty. Showing only updated data.")
        if st.session_state.get('debug_mode', False):
            try:
                st.json(updated_data)
            except Exception as e:
                st.error(f"Error displaying updated data: {str(e)}")
                st.text(str(updated_data)[:1000])
        return
    elif isinstance(updated_data, dict) and not updated_data:
        st.info("Updated data is empty. Showing only previous data.")
        if st.session_state.get('debug_mode', False):
            try:
                st.json(previous_data)
            except Exception as e:
                st.error(f"Error displaying previous data: {str(e)}")
                st.text(str(previous_data)[:1000])
        return
    
    # Try to use DeepDiff for comparison
    try:
        from deepdiff import DeepDiff
        
        # Set appropriate exclusion paths based on data type
        exclude_paths = []
        if data_type == "channel":
            exclude_paths = ["root['raw_channel_info']", "root['data_source']", "root['video_id']"]
        elif data_type == "video":
            exclude_paths = ["root['comments']", "root['data_source']"]
        elif data_type == "comment":
            exclude_paths = ["root['data_source']"]
        
        # Sanitize data before comparison to avoid "src property" errors
        previous_data_clean = _sanitize_for_deepdiff(previous_data)
        updated_data_clean = _sanitize_for_deepdiff(updated_data)
        
        # Generate the diff
        diff = DeepDiff(previous_data_clean, updated_data_clean, exclude_paths=exclude_paths)
        
        if not diff:
            st.success("✅ No changes detected between the datasets.")
            return
        
        # Show a summary of changes
        categories = []
        if 'dictionary_item_added' in diff:
            categories.append(f"**{len(diff['dictionary_item_added'])}** new items added")
        if 'dictionary_item_removed' in diff:
            categories.append(f"**{len(diff['dictionary_item_removed'])}** items removed")
        if 'values_changed' in diff:
            categories.append(f"**{len(diff['values_changed'])}** values changed")
        
        if categories:
            st.write("### Changes Summary")
            st.write(", ".join(categories))
        
        # Display added values
        if 'dictionary_item_added' in diff:
            st.markdown("#### New Fields")
            for item in diff['dictionary_item_added']:
                # Clean up the path for display
                clean_path = item.replace("root['", "").replace("']", "")
                
                # Get the value from the updated data
                import re
                keys = re.findall(r"\['([^']+)'\]", item)
                value = updated_data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = "Unable to extract value"
                        break
                
                # Format value for display
                if isinstance(value, (int, float)):
                    value = format_number(value)
                
                st.write(f"- {clean_path}: {value}")
        
        # Display removed values
        if 'dictionary_item_removed' in diff:
            st.markdown("#### Removed Fields")
            for item in diff['dictionary_item_removed']:
                # Clean up the path for display
                clean_path = item.replace("root['", "").replace("']", "")
                st.write(f"- {clean_path}")
        
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
        if st.session_state.get('debug_mode', False):
            st.write("Previous data (Debug):")
            st.json(previous_data)
            st.write("Updated data (Debug):")
            st.json(updated_data)
        else:
            # Basic comparison for non-debug mode
            st.write("Basic comparison (DeepDiff library not available):")
            if isinstance(previous_data, dict) and isinstance(updated_data, dict):
                for key in set(list(previous_data.keys()) + list(updated_data.keys())):
                    if key in previous_data and key in updated_data:
                        if previous_data[key] != updated_data[key]:
                            st.write(f"- {key}: {previous_data[key]} → {updated_data[key]}")
                    elif key in updated_data:
                        st.write(f"- {key}: (added) {updated_data[key]}")
                    elif key in previous_data:
                        st.write(f"- {key}: (removed) {previous_data[key]}")
    except Exception as e:
        # Handle other exceptions during comparison
        st.error(f"Error comparing data: {str(e)}")
        debug_log(f"Delta comparison error: {str(e)}")
        
        # In debug mode, show more detailed error information
        if st.session_state.get('debug_mode', False):
            st.write("Error occurred during comparison. Raw data preview:")
            st.write("Previous data sample:")
            st.text(str(previous_data)[:500])
            st.write("Updated data sample:")
            st.text(str(updated_data)[:500])

def _sanitize_for_deepdiff(data):
    """
    Sanitize data structure to avoid common DeepDiff errors
    like "src property must be a valid json object"
    
    Args:
        data (dict): Data structure to sanitize
        
    Returns:
        dict: Sanitized copy of the data
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        # Skip problematic keys that might cause JSON serialization issues
        if key in ['src', 'source', 'raw_data']:
            if isinstance(value, (dict, list)):
                # Try to convert to string to avoid serialization errors
                try:
                    import json
                    result[key] = json.dumps(value)
                except:
                    result[key] = str(value)
            else:
                result[key] = str(value)
        # Recursively sanitize nested dictionaries
        elif isinstance(value, dict):
            result[key] = _sanitize_for_deepdiff(value)
        # Handle lists with dictionaries inside
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                result[key] = [_sanitize_for_deepdiff(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        # Keep other values as is
        else:
            result[key] = value
            
    return result