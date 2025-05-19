"""
Utility helper functions for the YouTube scraper application.
This module re-exports utility functions from specialized modules for backward compatibility.

NOTE: This module is deprecated and will be removed in a future version.
Please import directly from the specialized modules instead.
"""
from typing import Any, Dict, Optional, List, Union

# Re-export utility functions from specialized modules
from src.utils.debug_utils import (
    debug_log,
    log_error,
    get_ui_freeze_report
)

from src.utils.performance_tracking import initialize_performance_tracking

from src.utils.formatters import (
    format_number,
    format_duration,
    duration_to_seconds,
    format_timedelta,
    get_thumbnail_url,
    get_location_display
)

from src.utils.duration_utils import (
    format_duration_human_friendly
)

from src.utils.validation import (
    validate_api_key,
    validate_channel_id,
    validate_channel_id_old
)

from src.utils.quota_estimation import estimate_quota_usage

from src.utils.cache_utils import clear_cache

from src.utils.ui_helpers import (
    paginate_dataframe,
    render_pagination_controls,
    initialize_pagination_state,
    get_pagination_state,
    update_pagination_state
)

from src.utils.ui_performance import (
    report_ui_timing,
    get_performance_summary
)

# Initialize performance tracking
initialize_performance_tracking()

# Function has been moved to src.utils.debug_utils
# This placeholder is kept for backward compatibility
def debug_log(message: str, data: Any = None, performance_tag: str = None):
    """
    Log debug messages to server console if debug mode is enabled
    
    This function has been moved to src.utils.debug_utils.
    This placeholder is kept for backward compatibility.
    
    Args:
        message: The message to log
        data: Optional data to include with the log
        performance_tag: Optional tag for performance tracking
    """
    from src.utils.debug_utils import debug_log as _debug_log
    return _debug_log(message, data, performance_tag)

# Function has been moved to src.utils.ui_performance
# This placeholder is kept for backward compatibility
def report_ui_timing(operation_name: str, start_time: float, show_spinner: bool = False):
    """
    Report the timing of a UI operation
    
    This function has been moved to src.utils.ui_performance.
    This placeholder is kept for backward compatibility.
    
    Args:
        operation_name: Descriptive name of the operation
        start_time: The starting timestamp (from time.time())
        show_spinner: Whether to show a spinner for operations that exceed the UI blocking threshold
        
    Returns:
        elapsed_time: Time taken for the operation in seconds
    """
    from src.utils.ui_performance import report_ui_timing as _report_ui_timing
    return _report_ui_timing(operation_name, start_time, show_spinner)

# Function has been moved to src.utils.ui_performance
# This placeholder is kept for backward compatibility
def get_performance_summary():
    """
    Get a summary of tracked performance metrics.
    
    This function has been moved to src.utils.ui_performance.
    This placeholder is kept for backward compatibility.
    
    Returns:
        A DataFrame with performance statistics
    """
    from src.utils.ui_performance import get_performance_summary as _get_performance_summary
    return _get_performance_summary()

# Function has been moved to src.utils.ui_performance
# This placeholder is kept for backward compatibility
def get_ui_freeze_report():
    """
    Get a report of potential UI freezes detected during the session.
    
    This function has been moved to src.utils.debug_utils.
    This placeholder is kept for backward compatibility.
    
    Returns:
        A DataFrame with UI freeze information or None if no UI metrics available
    """
    from src.utils.debug_utils import get_ui_freeze_report as _get_ui_freeze_report
    return _get_ui_freeze_report()

# Function has been moved to src.utils.quota_estimation
# This placeholder is kept for backward compatibility
def estimate_quota_usage(fetch_channel=None, fetch_videos=None, fetch_comments=None, 
                         video_count=None, comments_count=None):
    """
    Estimates YouTube API quota points that will be used with current settings
    
    This function has been moved to src.utils.quota_estimation.
    This placeholder is kept for backward compatibility.
    
    Args:
        fetch_channel: Whether to fetch channel data (defaults to session state if None)
        fetch_videos: Whether to fetch videos (defaults to session state if None)
        fetch_comments: Whether to fetch comments (defaults to session state if None)
        video_count: Number of videos to fetch (defaults to session state if None)
        comments_count: Number of comments per video (default 10 if None)
    
    Returns:
        int: Estimated quota usage
    """
    from src.utils.quota_estimation import estimate_quota_usage as _estimate_quota_usage
    return _estimate_quota_usage(fetch_channel, fetch_videos, fetch_comments, video_count, comments_count)
