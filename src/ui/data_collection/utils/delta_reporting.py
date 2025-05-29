"""
Delta reporting functionality for data collection UI.
Provides utilities to show differences between data sets.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from ..utils.data_conversion import format_number
from src.utils.debug_utils import debug_log
import json

def render_delta_report(previous_data, updated_data, data_type="channel"):
    """
    Display a comprehensive report showing differences between previous and updated data.
    
    Args:
        previous_data (dict): Previous channel data
        updated_data (dict): New channel data after update
        data_type (str): Type of data being compared ("channel", "video", or "comment")
    """
    # Add timestamp for debugging
    comparison_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    debug_log(f"[DELTA] Starting delta comparison at {comparison_timestamp} for {data_type}")
    
    # Better handling for empty or None data
    if previous_data is None and updated_data is None:
        st.info("No data available for comparison.")
        _render_debug_info(None, None, data_type, comparison_timestamp, "No data available")
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
        _render_debug_info(None, updated_data, data_type, comparison_timestamp, "New data only")
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
        _render_debug_info(previous_data, None, data_type, comparison_timestamp, "Previous data only")
        return
    
    # Check for error objects in the data
    if isinstance(previous_data, dict) and "ERROR" in previous_data:
        st.error(f"Error in previous data: {previous_data.get('ERROR', {}).get('message', 'Unknown error')}")
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Error in previous data")
        return
    
    if isinstance(updated_data, dict) and "ERROR" in updated_data:
        st.error(f"Error in updated data: {updated_data.get('ERROR', {}).get('message', 'Unknown error')}")
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Error in updated data")
        return
    
    # Validate data before comparison
    if not isinstance(previous_data, dict) or not isinstance(updated_data, dict):
        st.error(f"Invalid data format for comparison. Previous data type: {type(previous_data)}, Updated data type: {type(updated_data)}")
        if st.session_state.get('debug_mode', False):
            st.write("Previous data preview:")
            st.text(str(previous_data)[:500])
            st.write("Updated data preview:")
            st.text(str(updated_data)[:500])
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Invalid data format")
        return
    
    # Handle empty dictionaries
    if isinstance(previous_data, dict) and not previous_data:
        if isinstance(updated_data, dict) and not updated_data:
            st.info("Both previous and updated data sets are empty.")
            _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Both datasets empty")
            return
        st.info("Previous data is empty. Showing only updated data.")
        if st.session_state.get('debug_mode', False):
            try:
                st.json(updated_data)
            except Exception as e:
                st.error(f"Error displaying updated data: {str(e)}")
                st.text(str(updated_data)[:1000])
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Previous data empty")
        return
    elif isinstance(updated_data, dict) and not updated_data:
        st.info("Updated data is empty. Showing only previous data.")
        if st.session_state.get('debug_mode', False):
            try:
                st.json(previous_data)
            except Exception as e:
                st.error(f"Error displaying previous data: {str(e)}")
                st.text(str(previous_data)[:1000])
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Updated data empty")
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
        
        debug_log(f"[DELTA] Sanitized data for comparison. Previous keys: {list(previous_data_clean.keys()) if previous_data_clean else []}, Updated keys: {list(updated_data_clean.keys()) if updated_data_clean else []}")
        
        # Generate the diff
        diff = DeepDiff(previous_data_clean, updated_data_clean, exclude_paths=exclude_paths)
        
        debug_log(f"[DELTA] DeepDiff result: {bool(diff)} - {list(diff.keys()) if diff else 'No changes'}")
        
        if not diff:
            st.success("✅ No changes detected between the datasets.")
            _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "No changes detected", diff_result=diff)
            return
        
        # Render enhanced changes summary table
        _render_enhanced_changes_summary(diff, previous_data_clean, updated_data_clean, data_type)
        
        # Render debug information
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Changes detected", diff_result=diff)
                
    except ImportError:
        # Fallback if DeepDiff is not available
        st.warning("DeepDiff library not found. Using basic comparison.")
        debug_log(f"[DELTA] DeepDiff not available, using fallback comparison")
        
        _render_basic_comparison(previous_data, updated_data)
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, "Basic comparison (DeepDiff unavailable)")
        
    except Exception as e:
        # Handle other exceptions during comparison
        st.error(f"Error comparing data: {str(e)}")
        debug_log(f"[DELTA] Delta comparison error: {str(e)}")
        
        # In debug mode, show more detailed error information
        if st.session_state.get('debug_mode', False):
            st.write("Error occurred during comparison. Raw data preview:")
            st.write("Previous data sample:")
            st.text(str(previous_data)[:500])
            st.write("Updated data sample:")
            st.text(str(updated_data)[:500])
        
        _render_debug_info(previous_data, updated_data, data_type, comparison_timestamp, f"Error during comparison: {str(e)}")

def _render_basic_comparison(previous_data, updated_data):
    """Render basic comparison when DeepDiff is not available."""
    if st.session_state.get('debug_mode', False):
        st.write("Previous data (Debug):")
        st.json(previous_data)
        st.write("Updated data (Debug):")
        st.json(updated_data)
    else:
        # Basic comparison for non-debug mode
        st.write("Basic comparison (DeepDiff library not available):")
        if isinstance(previous_data, dict) and isinstance(updated_data, dict):
            changes_data = []
            
            for key in set(list(previous_data.keys()) + list(updated_data.keys())):
                if key in previous_data and key in updated_data:
                    if previous_data[key] != updated_data[key]:
                        changes_data.append({
                            'Field': key,
                            'Change Type': 'Modified',
                            'Previous Value': str(previous_data[key]),
                            'New Value': str(updated_data[key])
                        })
                elif key in updated_data:
                    changes_data.append({
                        'Field': key,
                        'Change Type': 'Added',
                        'Previous Value': '—',
                        'New Value': str(updated_data[key])
                    })
                elif key in previous_data:
                    changes_data.append({
                        'Field': key,
                        'Change Type': 'Removed',
                        'Previous Value': str(previous_data[key]),
                        'New Value': '—'
                    })
            
            if changes_data:
                st.write("### Changes Detected")
                df = pd.DataFrame(changes_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.success("✅ No changes detected between the datasets.")

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

def _render_enhanced_changes_summary(diff, previous_data, updated_data, data_type):
    """
    Render an enhanced changes summary with structured tables and better formatting.
    
    Args:
        diff (dict): DeepDiff result
        previous_data (dict): Previous data (sanitized)
        updated_data (dict): Updated data (sanitized)
        data_type (str): Type of data being compared
    """
    # Create a comprehensive changes table
    changes_data = []
    
    # Process added items
    if 'dictionary_item_added' in diff:
        for item in diff['dictionary_item_added']:
            clean_path = _clean_diff_path(item)
            value = _extract_value_from_path(item, updated_data)
            formatted_value = _format_display_value(value)
            
            changes_data.append({
                'Field': clean_path,
                'Change Type': '➕ Added',
                'Previous Value': '—',
                'New Value': formatted_value,
                'Impact': _calculate_change_impact('added', None, value)
            })
    
    # Process removed items
    if 'dictionary_item_removed' in diff:
        for item in diff['dictionary_item_removed']:
            clean_path = _clean_diff_path(item)
            value = _extract_value_from_path(item, previous_data)
            formatted_value = _format_display_value(value)
            
            changes_data.append({
                'Field': clean_path,
                'Change Type': '➖ Removed',
                'Previous Value': formatted_value,
                'New Value': '—',
                'Impact': _calculate_change_impact('removed', value, None)
            })
    
    # Process changed values
    if 'values_changed' in diff:
        for path, change in diff['values_changed'].items():
            clean_path = _clean_diff_path(path)
            old_val = change['old_value']
            new_val = change['new_value']
            
            formatted_old = _format_display_value(old_val)
            formatted_new = _format_display_value(new_val)
            
            # Calculate percentage change for numerical values
            pct_change = None
            change_indicator = '🔄 Modified'
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)) and old_val != 0:
                pct_change = ((new_val - old_val) / old_val) * 100
                if pct_change > 0:
                    change_indicator = f'📈 Increased (+{pct_change:.1f}%)'
                elif pct_change < 0:
                    change_indicator = f'📉 Decreased ({pct_change:.1f}%)'
                else:
                    change_indicator = '➡️ No Change'
            
            changes_data.append({
                'Field': clean_path,
                'Change Type': change_indicator,
                'Previous Value': formatted_old,
                'New Value': formatted_new,
                'Impact': _calculate_change_impact('modified', old_val, new_val, pct_change)
            })
    
    # Display the changes summary
    if changes_data:
        st.markdown("### 📊 Changes Summary")
        
        # Sort by impact level and then by field name
        changes_data.sort(key=lambda x: (_get_impact_priority(x['Impact']), x['Field']))
        
        # Create DataFrame for better display
        df = pd.DataFrame(changes_data)
        
        # Add color coding based on impact
        def style_impact(val):
            if 'High' in val:
                return 'background-color: #ffebee; color: #c62828'
            elif 'Medium' in val:
                return 'background-color: #fff3e0; color: #ef6c00'
            elif 'Low' in val:
                return 'background-color: #e8f5e8; color: #2e7d32'
            return ''
        
        # Display styled table
        styled_df = df.style.applymap(style_impact, subset=['Impact'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            added_count = len([c for c in changes_data if 'Added' in c['Change Type']])
            st.metric("Added Fields", added_count)
        with col2:
            removed_count = len([c for c in changes_data if 'Removed' in c['Change Type']])
            st.metric("Removed Fields", removed_count)
        with col3:
            modified_count = len([c for c in changes_data if 'Modified' in c['Change Type'] or 'Increased' in c['Change Type'] or 'Decreased' in c['Change Type']])
            st.metric("Modified Fields", modified_count)
        with col4:
            high_impact_count = len([c for c in changes_data if 'High' in c['Impact']])
            st.metric("High Impact Changes", high_impact_count)
    else:
        st.success("✅ No changes detected between the datasets.")

def _render_debug_info(previous_data, updated_data, data_type, timestamp, status, diff_result=None):
    """
    Render comprehensive debug information with timestamps and context.
    
    Args:
        previous_data (dict): Previous data
        updated_data (dict): Updated data  
        data_type (str): Type of data being compared
        timestamp (str): Comparison timestamp
        status (str): Status message
        diff_result (dict): DeepDiff result (optional)
    """
    if not st.session_state.get('debug_mode', False):
        return
    
    with st.expander("🔍 Debug Information", expanded=False):
        st.markdown("### Debug Details")
        
        # Basic information
        debug_info = {
            'Comparison Timestamp': timestamp,
            'Data Type': data_type,
            'Status': status,
            'Previous Data Available': previous_data is not None,
            'Updated Data Available': updated_data is not None,
            'Previous Data Size': len(previous_data) if isinstance(previous_data, dict) else 0,
            'Updated Data Size': len(updated_data) if isinstance(updated_data, dict) else 0
        }
        
        # Display debug info table
        debug_df = pd.DataFrame([debug_info]).T
        debug_df.columns = ['Value']
        st.table(debug_df)
        
        # Show data structure analysis
        if previous_data or updated_data:
            st.markdown("### Data Structure Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Previous Data Structure**")
                if previous_data:
                    prev_structure = _analyze_data_structure(previous_data)
                    st.json(prev_structure)
                else:
                    st.write("No previous data")
            
            with col2:
                st.markdown("**Updated Data Structure**")
                if updated_data:
                    updated_structure = _analyze_data_structure(updated_data)
                    st.json(updated_structure)
                else:
                    st.write("No updated data")
        
        # Show diff details if available
        if diff_result:
            st.markdown("### Raw Diff Results")
            st.json(dict(diff_result))
        
        # Show raw data samples
        if st.checkbox("Show Raw Data Samples", value=False):
            if previous_data:
                st.markdown("**Previous Data Sample (First 10 Keys)**")
                sample_prev = {k: v for i, (k, v) in enumerate(previous_data.items()) if i < 10}
                st.json(sample_prev)
            
            if updated_data:
                st.markdown("**Updated Data Sample (First 10 Keys)**")
                sample_updated = {k: v for i, (k, v) in enumerate(updated_data.items()) if i < 10}
                st.json(sample_updated)

def _clean_diff_path(path):
    """Clean up DeepDiff path for human-readable display."""
    import re
    # Remove root[''] wrapper and clean up the path
    clean_path = path.replace("root['", "").replace("']", "")
    # Handle nested paths
    clean_path = re.sub(r"\[(\d+)\]", r"[\1]", clean_path)
    return clean_path

def _extract_value_from_path(path, data):
    """Extract value from data using DeepDiff path."""
    import re
    if not isinstance(data, dict):
        return "Unable to extract value"
    
    try:
        keys = re.findall(r"\['([^']+)'\]", path)
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return "Unable to extract value"
        return value
    except:
        return "Unable to extract value"

def _format_display_value(value):
    """Format value for display with appropriate formatting."""
    if value is None:
        return "None"
    elif isinstance(value, (int, float)):
        return format_number(value)
    elif isinstance(value, str) and len(value) > 100:
        return f"{value[:100]}..."
    elif isinstance(value, (list, dict)):
        return f"{type(value).__name__} ({len(value)} items)"
    else:
        return str(value)

def _calculate_change_impact(change_type, old_value, new_value, pct_change=None):
    """Calculate the impact level of a change."""
    if change_type == 'added':
        if isinstance(new_value, (int, float)) and new_value > 1000:
            return "Medium Impact"
        return "Low Impact"
    
    elif change_type == 'removed':
        if isinstance(old_value, (int, float)) and old_value > 1000:
            return "Medium Impact"
        return "Low Impact"
    
    elif change_type == 'modified':
        if pct_change is not None:
            abs_pct = abs(pct_change)
            if abs_pct > 20:
                return "High Impact"
            elif abs_pct > 5:
                return "Medium Impact"
            else:
                return "Low Impact"
        
        # For non-numeric changes, consider string length changes
        if isinstance(old_value, str) and isinstance(new_value, str):
            len_diff = abs(len(new_value) - len(old_value))
            if len_diff > 100:
                return "Medium Impact"
        
        return "Low Impact"
    
    return "Unknown Impact"

def _get_impact_priority(impact):
    """Get priority number for sorting by impact."""
    if 'High' in impact:
        return 1
    elif 'Medium' in impact:
        return 2
    elif 'Low' in impact:
        return 3
    else:
        return 4

def _analyze_data_structure(data):
    """Analyze the structure of data for debugging."""
    if not isinstance(data, dict):
        return {"type": type(data).__name__, "value": str(data)[:100]}
    
    structure = {
        "type": "dict",
        "keys_count": len(data),
        "keys": list(data.keys())[:10],  # First 10 keys
        "key_types": {}
    }
    
    # Analyze value types for each key
    for key, value in list(data.items())[:10]:  # Only analyze first 10 for performance
        structure["key_types"][key] = {
            "type": type(value).__name__,
            "size": len(value) if isinstance(value, (dict, list, str)) else None
        }
    
    return structure