"""
Comprehensive display component for channel data.
Provides collapsible, hierarchical view of all API fields.
"""
import streamlit as st
import pandas as pd
import json
from typing import Dict, Any, List, Optional, Union
from ..utils.data_conversion import format_number

def render_collapsible_field_explorer(data: Dict[str, Any], title: str = "All Channel Fields", no_expander: bool = False) -> None:
    """
    Renders a collapsible explorer for all API fields with hierarchical navigation.
    
    Args:
        data: Dictionary containing all the API fields
        title: Title for the collapsible section
        no_expander: If True, renders without wrapping in an expander (for use in existing expanders)
    """
    if not data:
        st.info("No data available to display.")
        return
    
    # Remove internal fields from display
    display_data = {k: v for k, v in data.items() if not k.startswith('_') and k != 'delta'}
    
    # Conditional expander creation based on no_expander flag
    if no_expander:
        # Add filtering option directly without expander
        st.subheader(title)
        filter_term = st.text_input("Filter fields:", key=f"filter_{title.replace(' ', '_').lower()}")
        
        # Continue with the rest of the function
        # Group fields by category
        categories = {
            "Basic Info": ["channel_id", "channel_name", "description", "country", "published_at"],
            "Statistics": ["subscribers", "views", "total_videos", "total_playlists"],
            "Engagement": ["likes", "comments", "shares"],
            "Metadata": ["tags", "category", "language", "custom_url"],
            "Other": []  # Will hold all other fields
        }
        
        categorized_data = {cat: {} for cat in categories}
        
        # Categorize each field
        for field, value in display_data.items():
            placed = False
            for cat, fields in categories.items():
                if field in fields:
                    categorized_data[cat][field] = value
                    placed = True
                    break
            
            if not placed:
                categorized_data["Other"][field] = value
        
        # Display each category
        for category, fields in categorized_data.items():
            if not fields:
                continue
                
            # Skip this category if it doesn't match the filter
            if filter_term and filter_term.lower() not in category.lower() and not any(
                filter_term.lower() in str(field).lower() or 
                (isinstance(value, (str, int, float)) and filter_term.lower() in str(value).lower())
                for field, value in fields.items()
            ):
                continue
                
            st.subheader(category)
            
            # Format fields for display
            for field, value in fields.items():
                # Skip this field if it doesn't match the filter
                if filter_term and filter_term.lower() not in field.lower() and not (
                    isinstance(value, (str, int, float)) and filter_term.lower() in str(value).lower()
                ):
                    continue
                    
                # Format value for display - avoid nested expanders
                if isinstance(value, dict):
                    # Use columns instead of nested expanders
                    st.markdown(f"**{field.capitalize()}**:")
                    st.json(value)
                elif isinstance(value, list):
                    # Use columns instead of nested expanders
                    st.markdown(f"**{field.capitalize()}** ({len(value)} items):")
                    st.write(value)
                else:
                    st.metric(label=field.capitalize(), value=value)
    else:
        # Create collapsible section
        with st.expander(title, expanded=False):
            # Add filtering option
            filter_term = st.text_input("Filter fields:", key=f"filter_{title.replace(' ', '_').lower()}")
            
            # Group fields by category
            categories = {
                "Basic Info": ["channel_id", "channel_name", "description", "country", "published_at"],
                "Statistics": ["subscribers", "views", "total_videos", "total_playlists"],
                "Engagement": ["likes", "comments", "shares"],
                "Metadata": ["tags", "category", "language", "custom_url"],
                "Other": []  # Will hold all other fields
            }
        
        categorized_data = {cat: {} for cat in categories}
        
        # Categorize each field
        for field, value in display_data.items():
            placed = False
            for cat, fields in categories.items():
                if field in fields:
                    categorized_data[cat][field] = value
                    placed = True
                    break
            
            if not placed:
                categorized_data["Other"][field] = value
        
        # Display each category
        for category, fields in categorized_data.items():
            if not fields:
                continue
                
            # Skip this category if it doesn't match the filter
            if filter_term and filter_term.lower() not in category.lower() and not any(
                filter_term.lower() in str(field).lower() or 
                (isinstance(value, (str, int, float)) and filter_term.lower() in str(value).lower())
                for field, value in fields.items()
            ):
                continue
                
            st.subheader(category)
            
            # Format fields for display
            for field, value in fields.items():
                # Skip this field if it doesn't match the filter
                if filter_term and filter_term.lower() not in field.lower() and not (
                    isinstance(value, (str, int, float)) and filter_term.lower() in str(value).lower()
                ):
                    continue
                    
                # Format value for display - avoid nested expanders
                if isinstance(value, dict):
                    # Use columns instead of nested expanders
                    st.markdown(f"**{field.capitalize()}**:")
                    st.json(value)
                elif isinstance(value, list):
                    # Use columns instead of nested expanders
                    st.markdown(f"**{field.capitalize()}** ({len(value)} items):")
                    st.write(value)
                else:
                    st.metric(label=field.capitalize(), value=value)

def render_channel_overview_card(channel_data: Dict[str, Any], delta_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Renders an enhanced channel overview card with all important metrics.
    
    Args:
        channel_data: Dictionary containing channel data
        delta_data: Optional dictionary containing change information
    """
    if not channel_data:
        st.info("No channel data available to display.")
        return
    
    # Display channel name and ID
    st.subheader(channel_data.get("channel_name", "Unknown Channel"))
    st.caption(f"Channel ID: {channel_data.get('channel_id', 'Unknown')}")
    
    # Format published date if available
    if "published_at" in channel_data:
        published = channel_data["published_at"]
        if isinstance(published, str):
            # Try to format as date if it's an ISO date string
            try:
                from datetime import datetime
                parsed_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                published = parsed_date.strftime('%B %d, %Y')
            except:
                pass  # Keep original if parsing fails
        st.caption(f"Published: {published}")
    
    # Display main metrics
    col1, col2, col3 = st.columns(3)
    
    # Function to get delta value for a metric
    def get_delta(metric):
        if not delta_data or metric not in delta_data:
            return None
        delta_info = delta_data[metric]
        if isinstance(delta_info, dict) and "old" in delta_info and "new" in delta_info:
            return delta_info["new"] - delta_info["old"]
        return None
    
    with col1:
        subscribers = channel_data.get("subscribers", 0)
        delta_subs = get_delta("subscribers")
        st.metric(
            label="Subscribers",
            value=format_number(subscribers),
            delta=format_number(delta_subs) if delta_subs is not None else None
        )
    
    with col2:
        views = channel_data.get("views", 0)
        delta_views = get_delta("views")
        st.metric(
            label="Views",
            value=format_number(views),
            delta=format_number(delta_views) if delta_views is not None else None
        )
    
    with col3:
        videos = channel_data.get("total_videos", 0)
        delta_videos = get_delta("total_videos")
        st.metric(
            label="Videos",
            value=format_number(videos),
            delta=format_number(delta_videos) if delta_videos is not None else None
        )
    
    # Display description if available
    if "description" in channel_data and channel_data["description"]:
        with st.expander("Channel Description"):
            st.write(channel_data["description"])
    
    # Show additional metrics (country, category, etc)
    if any(key in channel_data for key in ["country", "category", "language"]):
        st.subheader("Additional Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if "country" in channel_data:
                st.metric("Country", channel_data["country"])
        
        with col2:
            if "category" in channel_data:
                st.metric("Category", channel_data["category"])
        
        with col3:
            if "language" in channel_data:
                st.metric("Language", channel_data["language"])

def render_detailed_change_dashboard(api_data: Dict[str, Any]) -> None:
    """
    Renders a comprehensive delta view with all changes organized by significance.
    
    Args:
        api_data: Dictionary containing API data with delta information
    """
    if not api_data or "delta" not in api_data:
        st.info("No change information available.")
        return
    
    delta = api_data["delta"]
    
    st.subheader("Change Dashboard")
    
    # Display comparison level if available
    comparison_options = api_data.get("_comparison_options", {})
    comparison_level = comparison_options.get("comparison_level", "standard")
    st.caption(f"Comparison level: {comparison_level.upper()}")
    
    # Check for significant changes
    if "significant_changes" in delta and delta["significant_changes"]:
        st.error("⚠️ Significant Changes Detected")
        
        # Group by significance level
        changes_by_significance = {}
        for change in delta["significant_changes"]:
            significance = change.get("significance", "medium")
            if significance not in changes_by_significance:
                changes_by_significance[significance] = []
            changes_by_significance[significance].append(change)
        
        # Display each significance group
        for significance in ["critical", "high", "medium", "low"]:
            if significance in changes_by_significance:
                items = changes_by_significance[significance]
                
                # Format for display
                with st.expander(f"{significance.upper()} significance changes ({len(items)})", expanded=(significance == "critical")):
                    # Create a dataframe for better display
                    formatted = []
                    for item in items:
                        formatted.append({
                            "Metric": item.get("metric", ""),
                            "Old Value": item.get("old", ""),
                            "New Value": item.get("new", ""),
                            "Change": f"{item.get('change', '')} ({item.get('percentage', '')}%)" if "percentage" in item else "",
                            "Details": item.get("message", "")
                        })
                    
                    st.table(pd.DataFrame(formatted))
    else:
        st.success("No significant changes detected.")
    
    # Display all changes by category
    st.subheader("All Changes")
    
    # Categorize changes
    categorized_changes = {
        "Metrics": {},
        "Content": {},
        "Settings": {},
        "Other": {}
    }
    
    # Define which fields go in which category
    metric_fields = ["subscribers", "views", "videos", "likes", "comments", "videoCount"]
    content_fields = ["title", "channel_name", "description", "tags", "thumbnails"]
    settings_fields = ["country", "language", "privacy", "status", "category"]
    
    # Categorize the changes
    for field, change in delta.items():
        # Skip internal fields and special fields
        if field.startswith("_") or field == "significant_changes":
            continue
            
        # Determine category
        category = "Other"
        for metric in metric_fields:
            if metric in field:
                category = "Metrics"
                break
        
        if category == "Other":
            for content in content_fields:
                if content in field:
                    category = "Content"
                    break
        
        if category == "Other":
            for setting in settings_fields:
                if setting in field:
                    category = "Settings"
                    break
        
        # Add to appropriate category
        categorized_changes[category][field] = change
    
    # Display each category
    for category, changes in categorized_changes.items():
        if not changes:
            continue
            
        with st.expander(f"{category} Changes ({len(changes)})", expanded=(category == "Metrics")):
            # Format for display
            formatted = []
            for field, change in changes.items():
                if isinstance(change, dict) and "old" in change and "new" in change:
                    # Standard change format
                    # Convert complex types to strings to prevent Arrow conversion issues
                    old_val = str(change["old"]) if isinstance(change["old"], (list, dict)) else change["old"]
                    new_val = str(change["new"]) if isinstance(change["new"], (list, dict)) else change["new"]
                    
                    formatted.append({
                        "Field": field,
                        "Previous Value": old_val,
                        "New Value": new_val,
                        "Difference": _format_difference(change["old"], change["new"])
                    })
                elif isinstance(change, dict) and "value" in change:
                    # New field format (comprehensive mode)
                    # Convert complex types to strings to prevent Arrow conversion issues
                    new_val = str(change["value"]) if isinstance(change["value"], (list, dict)) else change["value"]
                    
                    formatted.append({
                        "Field": field,
                        "Previous Value": "-",
                        "New Value": new_val,
                        "Difference": "New Field"
                    })
            
            if formatted:
                st.table(pd.DataFrame(formatted))

def _format_difference(old_value, new_value):
    """Helper to format difference between values."""
    try:
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            diff = new_value - old_value
            if old_value != 0:
                percentage = (diff / old_value) * 100
                return f"{diff:+} ({percentage:.1f}%)"
            else:
                return f"{diff:+}"
        else:
            return "Changed"
    except:
        return "Changed"

# Add render_explorer as an alias for backward compatibility
render_explorer = render_collapsible_field_explorer