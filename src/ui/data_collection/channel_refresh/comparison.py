"""
This module handles the comparison between database and API data for channels.
"""
import streamlit as st
import pandas as pd
from src.utils.debug_utils import debug_log
from ..components.comprehensive_display import render_detailed_change_dashboard, render_collapsible_field_explorer

def _assess_change_impact(change):
    """Assess the impact of a change for display purposes."""
    try:
        significance = change.get('significance', 'low').lower()
        metric = change.get('metric', '').lower()
        
        # High priority metrics
        if metric in ['subscribers', 'views', 'videos'] or significance == 'high':
            return "High Impact - Requires Review"
        elif metric in ['title', 'description', 'keywords'] or significance == 'medium':
            return "Medium Impact - Monitor Closely"
        else:
            return "Low Impact - Informational"
    except Exception:
        return "Impact Assessment Unavailable"

def _calculate_change_magnitude(old_value, new_value):
    """Calculate the magnitude of change between two values."""
    try:
        # Handle numeric values
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            if old_value == 0:
                return "Infinite" if new_value != 0 else "No Change"
            percentage = abs((new_value - old_value) / old_value) * 100
            if percentage > 50:
                return "Major Change"
            elif percentage > 10:
                return "Moderate Change"
            elif percentage > 1:
                return "Minor Change"
            else:
                return "Minimal Change"
        
        # Handle string values
        elif isinstance(old_value, str) and isinstance(new_value, str):
            if old_value == new_value:
                return "No Change"
            elif len(old_value) == 0 or len(new_value) == 0:
                return "Major Change"
            else:
                # Simple string similarity check
                common_chars = set(old_value.lower()) & set(new_value.lower())
                total_chars = set(old_value.lower()) | set(new_value.lower())
                similarity = len(common_chars) / len(total_chars) if total_chars else 0
                if similarity < 0.3:
                    return "Major Change"
                elif similarity < 0.7:
                    return "Moderate Change"
                else:
                    return "Minor Change"
        
        # Default for other types
        return "Change Detected"
        
    except Exception:
        return "Unknown Change"

def _categorize_change(field, magnitude, old_value, new_value):
    """Categorize a change based on field type and magnitude."""
    try:
        field_lower = field.lower()
        
        # Critical fields that should always be closely monitored
        critical_fields = ['subscribers', 'views', 'videos', 'title', 'channel_name']
        if any(critical_field in field_lower for critical_field in critical_fields):
            if magnitude in ["Major Change", "Infinite"]:
                return "Critical"
            elif magnitude in ["Moderate Change"]:
                return "Important"
            else:
                return "Minor"
        
        # Important fields for content analysis
        important_fields = ['description', 'keywords', 'tags', 'category']
        if any(important_field in field_lower for important_field in important_fields):
            if magnitude in ["Major Change", "Infinite"]:
                return "Important"
            else:
                return "Minor"
        
        # Default categorization based on magnitude
        if magnitude in ["Major Change", "Infinite"]:
            return "Important"
        else:
            return "Minor"
            
    except Exception:
        return "Minor"

def _format_value_for_display(value):
    """Format a value for better display in the UI."""
    try:
        if value is None:
            return "—"
        elif isinstance(value, (int, float)):
            if isinstance(value, int) or value.is_integer():
                return f"{int(value):,}"
            else:
                return f"{value:,.2f}"
        elif isinstance(value, str):
            if len(value) > 100:
                return f"{value[:97]}..."
            return value
        elif isinstance(value, (list, tuple)):
            if len(value) == 0:
                return "Empty"
            elif len(value) <= 3:
                return ", ".join(str(item) for item in value)
            else:
                return f"{', '.join(str(item) for item in value[:3])}... (+{len(value)-3} more)"
        elif isinstance(value, dict):
            if len(value) == 0:
                return "Empty"
            else:
                return f"Dict with {len(value)} keys"
        else:
            return str(value)
    except Exception:
        return str(value) if value is not None else "—"

def _filter_persistent_fields(data):
    """Return a copy of the data with only persistent, user-facing fields (no _internal, session, or debug fields)."""
    if not isinstance(data, dict):
        return data
    # List of known non-persistent/internal fields to exclude
    exclude_prefixes = ('_',)
    exclude_fields = {
        'raw_channel_info', 'data_source', 'delta', 'video_delta', 'comment_delta',
        '_existing_data', '_delta_options', '_comparison_options',
        'last_refresh', 'last_update', 'debug', 'session', 'api_data',
    }
    return {
        k: v for k, v in data.items()
        if not k.startswith(exclude_prefixes) and k not in exclude_fields
    }

def display_comparison_results(db_data, api_data):
    """Displays a comprehensive comparison between database and API data with enhanced diagnostics."""
    st.subheader("📊 Data Comparison & Analysis")
    
    # Add timestamp and context information
    comparison_time = st.session_state.get('last_api_call', 'Unknown')
    st.caption(f"Comparison performed at: {comparison_time}")

    # Filter both data dicts for debug display and delta
    db_data_clean = _filter_persistent_fields(db_data)
    api_data_clean = _filter_persistent_fields(api_data)

    # Unified debug toggle and output (single location, only if enabled)
    debug_mode = st.session_state.get('debug_mode', False)
    if debug_mode:
        with st.expander("Debug: Raw Data Used for Comparison", expanded=False):
            st.markdown("**Database Data (Persistent Fields Only):**")
            st.json(db_data_clean)
            st.markdown("**API Data (Persistent Fields Only):**")
            st.json(api_data_clean)

    # Show detailed delta report if available
    if 'delta' in st.session_state:
        st.subheader("🔍 Detailed Change Analysis")
        delta = st.session_state['delta']
        
        # Get comparison options for display
        comparison_options = None
        if '_comparison_options' in api_data:
            comparison_options = api_data.get('_comparison_options')
        elif 'comparison_options' in st.session_state:
            comparison_options = st.session_state.get('comparison_options')
        
        # Display comparison level used for this data
        comparison_level = "standard"
        if comparison_options:
            comparison_level = comparison_options.get('comparison_level', 'standard')
        
        # Enhanced comparison info display
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Comparison Level:** {comparison_level.upper()}")
        with col2:
            if comparison_options and 'track_keywords' in comparison_options:
                keyword_count = len(comparison_options['track_keywords'])
                st.info(f"**Tracked Keywords:** {keyword_count}")
        with col3:
            if comparison_options and 'compare_all_fields' in comparison_options:
                field_mode = "All Fields" if comparison_options['compare_all_fields'] else "Key Fields Only"
                st.info(f"**Field Mode:** {field_mode}")
        
        # Process the delta report for display using the comprehensive display components
        if delta and isinstance(delta, dict):
            # Store delta information in the API data for rendering
            enhanced_api_data = api_data.copy() if api_data else {}
            enhanced_api_data['delta'] = delta
            
            # Use the comprehensive display component to render the detailed change dashboard
            render_detailed_change_dashboard(enhanced_api_data)
            
            # Enhanced significant changes display
            if 'significant_changes' in delta and delta['significant_changes']:
                st.error("⚠️ **SIGNIFICANT CHANGES DETECTED**")
                st.markdown("These changes may indicate important updates or potential data issues:")
                
                sig_changes = delta['significant_changes']
                
                # Create enhanced significant changes table
                sig_formatted = []
                for change in sig_changes:
                    change_desc = ""
                    if 'old' in change and 'new' in change:
                        change_desc = f"{change.get('old', 'N/A')} → {change.get('new', 'N/A')}"
                    elif 'change' in change:
                        change_desc = f"{change.get('change', 'N/A')}"
                        if 'percentage' in change:
                            change_desc += f" ({change.get('percentage', 'N/A')}%)"
                    else:
                        change_desc = str(change.get('keywords', change.get('value', 'Unknown change')))
                    
                    # Determine priority level
                    priority = "🔴 CRITICAL" if change.get('significance', '').lower() == 'high' else "🟡 MODERATE"
                    
                    sig_formatted.append({
                        'Priority': priority,
                        'Metric': change.get('metric', 'Unknown'),
                        'Change Details': change_desc,
                        'Impact Assessment': _assess_change_impact(change)
                    })
                
                if sig_formatted:
                    # Sort by priority (critical first)
                    sig_formatted.sort(key=lambda x: x['Priority'])
                    
                    sig_df = pd.DataFrame(sig_formatted)
                    st.dataframe(sig_df, use_container_width=True)
                    
                    # Add recommendations
                    st.markdown("**🎯 Recommended Actions:**")
                    high_impact_count = len([c for c in sig_formatted if '🔴' in c['Priority']])
                    if high_impact_count > 0:
                        st.warning(f"• Review {high_impact_count} critical changes before proceeding")
                        st.info("• Consider investigating the source of unexpected changes")
                        st.info("• Verify API data accuracy if changes seem unusual")
            
            # Enhanced changes table with better categorization
            formatted_changes = []
            change_categories = {'Critical': [], 'Important': [], 'Minor': []}
            
            for field, change in delta.items():
                # Skip internal fields and significant_changes which was already displayed
                if field.startswith('_') or field == 'significant_changes':
                    continue
                    
                change_item = None
                category = 'Minor'  # Default category
                
                if isinstance(change, dict):
                    if 'old' in change and 'new' in change:
                        # Handle standard change fields
                        change_magnitude = _calculate_change_magnitude(change['old'], change['new'])
                        category = _categorize_change(field, change_magnitude, change['old'], change['new'])
                        
                        change_item = {
                            'Field': field,
                            'Previous Value': _format_value_for_display(change['old']),
                            'New Value': _format_value_for_display(change['new']),
                            'Change Type': 'Modified',
                            'Impact': change_magnitude,
                            'Category': category
                        }
                    elif field.endswith('_keywords'):
                        # Handle keyword tracking results
                        base_field = field.replace('_keywords', '')
                        keywords_added = change.get('added', [])
                        keywords_removed = change.get('removed', [])
                        
                        if keywords_added or keywords_removed:
                            category = 'Important' if keywords_added or keywords_removed else 'Minor'
                            change_item = {
                                'Field': f"{base_field} Keywords",
                                'Previous Value': ', '.join(keywords_removed) if keywords_removed else '—',
                                'New Value': ', '.join(keywords_added) if keywords_added else '—',
                                'Change Type': 'Keywords',
                                'Impact': 'Keyword Changes Detected',
                                'Category': category
                            }
                    elif 'value' in change:
                        # Handle unchanged fields (comprehensive mode)
                        status = "Unchanged"
                        if field.endswith('_unchanged'):
                            field_clean = field.replace('_unchanged', '')
                        elif field.endswith('_new'):
                            field_clean = field.replace('_new', '')
                            status = "New Field"
                            category = 'Important'
                        else:
                            field_clean = field
                            
                        change_item = {
                            'Field': field_clean,
                            'Previous Value': str(change['value']) if status == "Unchanged" else "—",
                            'New Value': str(change['value']),
                            'Change Type': status,
                            'Impact': 'No Change' if status == "Unchanged" else 'New Data',
                            'Category': category
                        }
                elif isinstance(change, (int, float)) and field not in ('old', 'new', 'diff'):
                    # Legacy numeric difference format
                    magnitude = abs(change) if isinstance(change, (int, float)) else 0
                    category = 'Critical' if magnitude > 1000 else 'Important' if magnitude > 100 else 'Minor'
                    
                    change_item = {
                        'Field': field,
                        'Previous Value': "—",
                        'New Value': str(change),
                        'Change Type': 'Numeric Difference',
                        'Impact': f'Change: {change:+}',
                        'Category': category
                    }
                
                if change_item:
                    formatted_changes.append(change_item)
                    change_categories[category].append(change_item)
            
            # Display changes by category with enhanced formatting
            if formatted_changes:
                st.markdown("#### 📋 All Changes by Category")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Changes", len(formatted_changes))
                with col2:
                    st.metric("Critical", len(change_categories['Critical']), 
                             delta="High Priority" if change_categories['Critical'] else None)
                with col3:
                    st.metric("Important", len(change_categories['Important']))
                with col4:
                    st.metric("Minor", len(change_categories['Minor']))
                
                # Tabbed view for different categories
                tab1, tab2, tab3, tab4 = st.tabs(["🔴 Critical", "🟡 Important", "🟢 Minor", "📊 All Changes"])
                
                with tab1:
                    if change_categories['Critical']:
                        st.dataframe(pd.DataFrame(change_categories['Critical']), use_container_width=True)
                    else:
                        st.success("No critical changes detected")
                
                with tab2:
                    if change_categories['Important']:
                        st.dataframe(pd.DataFrame(change_categories['Important']), use_container_width=True)
                    else:
                        st.info("No important changes detected")
                
                with tab3:
                    if change_categories['Minor']:
                        st.dataframe(pd.DataFrame(change_categories['Minor']), use_container_width=True)
                    else:
                        st.info("No minor changes detected")
                
                with tab4:
                    # Show all changes with filtering options
                    change_types = st.multiselect(
                        "Filter by Change Type:",
                        options=['Modified', 'Keywords', 'Unchanged', 'New Field', 'Numeric Difference'],
                        default=['Modified', 'Keywords', 'New Field', 'Numeric Difference']
                    )
                    
                    filtered_changes = [c for c in formatted_changes if c['Change Type'] in change_types]
                    if filtered_changes:
                        st.dataframe(pd.DataFrame(filtered_changes), use_container_width=True)
                    else:
                        st.info("No changes match the selected filters")
            
            return
            
        st.warning("⚠️ Delta information is not available - comparison may be incomplete")
        return
    if not db_data or not api_data:
        # Skip showing the warning here since it's already shown in the workflow
        return
    
    # Extract channel info data
    db_channel = db_data.get('channel_info', {})
    api_channel = api_data
    
    # Extract basic stats for comparison
    db_stats = db_channel.get('statistics', {})
    
    # Convert values to integers for comparison
    db_subs = int(db_stats.get('subscriberCount', 0))
    db_views = int(db_stats.get('viewCount', 0))
    db_videos = int(db_stats.get('videoCount', 0))
    
    api_subs = int(api_channel.get('subscribers', 0))
    api_views = int(api_channel.get('views', 0))
    api_videos = int(api_channel.get('total_videos', 0))
    
    # Calculate deltas
    delta_subs = api_subs - db_subs
    delta_views = api_views - db_views
    delta_videos = api_videos - db_videos
    
    # Display metrics with deltas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Subscribers",
            value=f"{api_subs:,}",
            delta=f"{delta_subs:+,}",
            delta_color="normal" if delta_subs >= 0 else "inverse"
        )
    
    with col2:
        st.metric(
            label="Total Views",
            value=f"{api_views:,}",
            delta=f"{delta_views:+,}",
            delta_color="normal" if delta_views >= 0 else "inverse"
        )
    
    with col3:
        st.metric(
            label="Videos",
            value=f"{api_videos:,}",
            delta=f"{delta_videos:+,}",
            delta_color="normal" if delta_videos >= 0 else "inverse"
        )

def compare_data(db_data, api_data):
    """
    Compare database data with API data and return a delta report.
    Only persistent, user-facing fields are compared.
    """
    debug_log(f"compare_data called with db_data={repr(db_data)} api_data={repr(api_data)}")
    # Filter both data dicts
    db_data_clean = _filter_persistent_fields(db_data)
    api_data_clean = _filter_persistent_fields(api_data)
    
    # Initialize delta dictionary
    delta = {}
    
    # Extract channel info data
    db_channel = db_data_clean.get('channel_info', {})
    api_channel = api_data_clean
    
    # Compare basic channel info with robust path handling
    db_title = (
        db_channel.get('title') or
        db_channel.get('snippet', {}).get('title') or
        db_data_clean.get('channel_name') or
        db_data_clean.get('channel_title', '')
    )
    
    api_title = (
        api_channel.get('channel_name') or
        api_channel.get('title') or
        api_channel.get('snippet', {}).get('title', '')
    )
    
    # Only compare titles if they actually differ
    if db_title != api_title:
        delta['channel_name'] = {
            'old': db_title,
            'new': api_title
        }
    
    # Compare channel description with robust path handling
    db_description = (
        db_channel.get('description') or
        db_channel.get('snippet', {}).get('description') or
        db_data_clean.get('channel_description') or
        db_data_clean.get('description', '')
    )
    
    api_description = (
        api_channel.get('channel_description') or
        api_channel.get('description') or
        api_channel.get('snippet', {}).get('description', '')
    )
    
    # Only compare descriptions if they actually differ
    if db_description != api_description:
        delta['channel_description'] = {
            'old': db_description,
            'new': api_description
        }
    
    # Compare additional metadata fields with robust path handling
    
    # Compare custom URL
    db_custom_url = (
        db_channel.get('custom_url') or
        db_channel.get('snippet', {}).get('customUrl') or
        db_data_clean.get('custom_url', '')
    )
    
    api_custom_url = (
        api_channel.get('custom_url') or
        api_channel.get('snippet', {}).get('customUrl', '')
    )
    
    if db_custom_url != api_custom_url:
        delta['custom_url'] = {
            'old': db_custom_url,
            'new': api_custom_url
        }
    
    # Compare country
    db_country = (
        db_channel.get('country') or
        db_channel.get('snippet', {}).get('country') or
        db_data_clean.get('country', '')
    )
    
    api_country = (
        api_channel.get('country') or
        api_channel.get('snippet', {}).get('country', '')
    )
    
    if db_country != api_country:
        delta['country'] = {
            'old': db_country,
            'new': api_country
        }
    
    # Compare default language
    db_language = (
        db_channel.get('default_language') or
        db_channel.get('snippet', {}).get('defaultLanguage') or
        db_data_clean.get('default_language', '')
    )
    
    api_language = (
        api_channel.get('default_language') or
        api_channel.get('snippet', {}).get('defaultLanguage', '')
    )
    
    if db_language != api_language:
        delta['default_language'] = {
            'old': db_language,
            'new': api_language
        }
    
    # Compare privacy status
    db_privacy = (
        db_channel.get('privacy_status') or
        db_channel.get('status', {}).get('privacyStatus') or
        db_data_clean.get('privacy_status', '')
    )
    
    api_privacy = (
        api_channel.get('privacy_status') or
        api_channel.get('status', {}).get('privacyStatus', '')
    )
    
    if db_privacy != api_privacy:
        delta['privacy_status'] = {
            'old': db_privacy,
            'new': api_privacy
        }
    
    # Compare keywords
    db_keywords = (
        db_channel.get('keywords') or
        db_channel.get('brandingSettings', {}).get('channel', {}).get('keywords') or
        db_data_clean.get('keywords', '')
    )
    
    api_keywords = (
        api_channel.get('keywords') or
        api_channel.get('brandingSettings', {}).get('channel', {}).get('keywords', '')
    )
    
    if db_keywords != api_keywords:
        delta['keywords'] = {
            'old': db_keywords,
            'new': api_keywords
        }
    
    # Compare published_at
    db_published = (
        db_channel.get('published_at') or
        db_channel.get('snippet', {}).get('publishedAt') or
        db_data_clean.get('published_at', '')
    )
    
    api_published = (
        api_channel.get('published_at') or
        api_channel.get('snippet', {}).get('publishedAt', '')
    )
    
    if db_published != api_published:
        delta['published_at'] = {
            'old': db_published,
            'new': api_published
        }
    
    # Compare topic categories
    db_topics = (
        db_channel.get('topic_categories') or
        db_channel.get('topicDetails', {}).get('topicCategories') or
        db_data_clean.get('topic_categories', [])
    )
    
    api_topics = (
        api_channel.get('topic_categories') or
        api_channel.get('topicDetails', {}).get('topicCategories', [])
    )
    
    if db_topics != api_topics:
        delta['topic_categories'] = {
            'old': db_topics,
            'new': api_topics
        }
    
    # Compare thumbnail URLs
    db_thumbnail = (
        db_channel.get('thumbnail_high') or
        db_channel.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url') or
        db_data_clean.get('thumbnail_high', '')
    )
    
    api_thumbnail = (
        api_channel.get('thumbnail_high') or
        api_channel.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url', '')
    )
    
    if db_thumbnail != api_thumbnail:
        delta['thumbnail_high'] = {
            'old': db_thumbnail,
            'new': api_thumbnail
        }
    
    # Compare statistics
    db_stats = db_channel.get('statistics', {})
    
    # Convert values to integers for comparison
    db_subs = int(db_stats.get('subscriberCount', 0))
    db_views = int(db_stats.get('viewCount', 0))
    db_videos = int(db_stats.get('videoCount', 0))
    
    api_subs = int(api_channel.get('subscribers', 0))
    api_views = int(api_channel.get('views', 0))
    api_videos = int(api_channel.get('total_videos', 0))
    
    # Record differences in statistics
    if db_subs != api_subs:
        delta['subscribers'] = {'old': db_subs, 'new': api_subs}
    
    if db_views != api_views:
        delta['views'] = {'old': db_views, 'new': api_views}
    
    if db_videos != api_videos:
        delta['videos'] = {'old': db_videos, 'new': api_videos}
    
    debug_log(f"compare_data returning delta={repr(delta)}")
    return delta
