"""
Advanced debugging tools for YTDataHub.
"""
import sys
import os
import platform
import json
import datetime
import logging
from typing import Dict, Any, List, Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.utils.debug_utils import debug_log


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging.
    
    Returns:
        Dict containing system information
    """
    info = {
        'timestamp': datetime.datetime.now().isoformat(),
        'python_version': platform.python_version(),
        'os': platform.platform(),
        'processor': platform.processor(),
        'interpreter_path': sys.executable,
    }
    
    # Add memory information if psutil is available
    if PSUTIL_AVAILABLE:
        mem = psutil.virtual_memory()
        info['memory'] = {
            'total_gb': round(mem.total / (1024 ** 3), 2),
            'available_gb': round(mem.available / (1024 ** 3), 2),
            'percent_used': mem.percent
        }
    
    return info


def get_session_state_summary() -> Dict[str, Any]:
    """
    Get a summary of the streamlit session state.
    
    Returns:
        Dict containing session state summary
    """
    if not STREAMLIT_AVAILABLE or not hasattr(st, 'session_state'):
        return {'error': 'Streamlit session state not available'}
    
    # Categories of session state variables
    categories = {
        'api': ['api_initialized', 'api_client_initialized', 'youtube_api_key', 'last_api_call', 'api_last_error'],
        'ui': ['debug_mode', 'active_tab', 'theme'],
        'collection': ['collection_step', 'collection_mode', 'channel_input', 'channel_data_fetched', 'videos_fetched'],
        'performance': ['performance_metrics', 'performance_timers', 'ui_timing_metrics'],
    }
    
    result = {}
    
    # Get variables by category
    for category, var_names in categories.items():
        result[category] = {}
        for var in var_names:
            if var in st.session_state:
                # Skip large data structures
                value = st.session_state[var]
                if isinstance(value, dict) and len(str(value)) > 1000:
                    result[category][var] = f"<dict with {len(value)} items>"
                elif isinstance(value, list) and len(str(value)) > 1000:
                    result[category][var] = f"<list with {len(value)} items>"
                else:
                    result[category][var] = value
            else:
                result[category][var] = None
    
    # Count other variables
    other_vars = []
    for var in st.session_state:
        if not any(var in category_vars for category_vars in categories.values()):
            other_vars.append(var)
    
    result['other'] = {
        'count': len(other_vars),
        'names': other_vars[:20] + ['...'] if len(other_vars) > 20 else other_vars
    }
    
    return result


def log_app_state(message: str = "Application state snapshot") -> None:
    """
    Log a comprehensive snapshot of the application state for debugging.
    
    Args:
        message: Optional message to include with the log
    """
    # Collect system and app state info
    system_info = get_system_info()
    session_state = get_session_state_summary() if STREAMLIT_AVAILABLE else {}
    
    # Combine into a single report
    debug_report = {
        'message': message,
        'system': system_info,
        'session_state': session_state
    }
    
    # Log using debug_log
    debug_log(f"APPLICATION STATE: {message}", data=debug_report)
    
    return debug_report


def format_duration_bar(duration: float, thresholds: Dict[str, float] = None) -> str:
    """
    Create a visual bar representation of a duration.
    
    Args:
        duration: Time in seconds
        thresholds: Optional dict with 'warning' and 'critical' thresholds
        
    Returns:
        String with a visual bar representation
    """
    if thresholds is None:
        thresholds = {
            'warning': 1.0,
            'critical': 3.0
        }
    
    # Determine the bar character based on duration
    if duration >= thresholds.get('critical', 3.0):
        bar_char = '█'
        color = 'red'
    elif duration >= thresholds.get('warning', 1.0):
        bar_char = '▓'
        color = 'yellow'
    else:
        bar_char = '▒'
        color = 'green'
    
    # Calculate bar length (1-10)
    max_bar_length = 10
    bar_length = min(int(duration * 3) + 1, max_bar_length)
    
    # Create the bar
    bar = bar_char * bar_length
    
    # Add HTML for color in Streamlit
    if color == 'red':
        return f'<span style="color:#dc3545">{bar}</span> {duration:.2f}s'
    elif color == 'yellow':
        return f'<span style="color:#ffc107">{bar}</span> {duration:.2f}s'
    else:
        return f'<span style="color:#28a745">{bar}</span> {duration:.2f}s'


def get_performance_summary() -> Dict[str, Any]:
    """
    Get a summary of performance metrics.
    
    Returns:
        Dict containing performance summary
    """
    if not STREAMLIT_AVAILABLE or not hasattr(st, 'session_state'):
        return {'error': 'Streamlit session state not available'}
    
    result = {
        'timers': {},
        'metrics': {},
        'summary': {
            'total_measurements': 0,
            'warning_count': 0,
            'critical_count': 0,
            'avg_operation_time': 0
        }
    }
    
    # Get current timers
    if 'performance_timers' in st.session_state:
        timers = st.session_state.performance_timers
        result['timers'] = {
            'count': len(timers),
            'active_operations': list(timers.keys())
        }
    
    # Get performance metrics
    if 'performance_metrics' in st.session_state:
        metrics = st.session_state.performance_metrics
        if isinstance(metrics, dict):
            total_time = 0
            warning_count = 0
            critical_count = 0
            
            for key, metric in metrics.items():
                if isinstance(metric, dict) and 'duration' in metric:
                    duration = metric['duration']
                    total_time += duration
                    
                    if 'warning_threshold' in metric and duration >= metric['warning_threshold']:
                        warning_count += 1
                    elif duration >= 1.0:  # Default warning threshold
                        warning_count += 1
                        
                    if 'critical_threshold' in metric and duration >= metric['critical_threshold']:
                        critical_count += 1
                    elif duration >= 3.0:  # Default critical threshold
                        critical_count += 1
            
            result['metrics'] = {
                'count': len(metrics),
                'total_time': total_time,
                'warning_count': warning_count,
                'critical_count': critical_count,
                'avg_time': total_time / len(metrics) if metrics else 0
            }
            
            result['summary'] = {
                'total_measurements': len(metrics),
                'warning_count': warning_count,
                'critical_count': critical_count,
                'avg_operation_time': round(total_time / len(metrics) if metrics else 0, 3)
            }
    
    return result
