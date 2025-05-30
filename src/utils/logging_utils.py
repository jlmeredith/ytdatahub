"""
Logging and debugging utilities for the YouTube Data Hub application.
"""
import re
import os
import sys
import json
import logging
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
import time
from datetime import datetime
from typing import Any, Dict, Optional, List, Union
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
from src.utils.log_level_helper import get_log_level_int

# ANSI Color codes for terminal output
COLORS = {
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
    'BLACK': '\033[30m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
    'GRAY': '\033[90m',
    'BRIGHT_RED': '\033[91m',
    'BRIGHT_GREEN': '\033[92m',
    'BRIGHT_YELLOW': '\033[93m',
    'BRIGHT_BLUE': '\033[94m',
    'BRIGHT_MAGENTA': '\033[95m',
    'BRIGHT_CYAN': '\033[96m',
    'BRIGHT_WHITE': '\033[97m',
    'BG_BLACK': '\033[40m',
    'BG_RED': '\033[41m',
    'BG_GREEN': '\033[42m',
    'BG_YELLOW': '\033[43m',
    'BG_BLUE': '\033[44m',
    'BG_MAGENTA': '\033[45m',
    'BG_CYAN': '\033[46m',
    'BG_WHITE': '\033[47m',
}

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter to add colors to log messages based on level
    """
    FORMATS = {
        logging.DEBUG: COLORS['GRAY'] + '%(asctime)s ' + COLORS['BRIGHT_CYAN'] + '[%(levelname)s]' + COLORS['RESET'] + COLORS['GRAY'] + ' [%(filename)s:%(lineno)d]' + COLORS['RESET'] + ' %(message)s',
        logging.INFO: COLORS['GRAY'] + '%(asctime)s ' + COLORS['BRIGHT_GREEN'] + '[%(levelname)s]' + COLORS['RESET'] + COLORS['GRAY'] + ' [%(filename)s:%(lineno)d]' + COLORS['RESET'] + ' %(message)s',
        logging.WARNING: COLORS['GRAY'] + '%(asctime)s ' + COLORS['BRIGHT_YELLOW'] + '[%(levelname)s]' + COLORS['RESET'] + COLORS['GRAY'] + ' [%(filename)s:%(lineno)d]' + COLORS['RESET'] + ' %(message)s',
        logging.ERROR: COLORS['GRAY'] + '%(asctime)s ' + COLORS['BRIGHT_RED'] + '[%(levelname)s]' + COLORS['RESET'] + COLORS['GRAY'] + ' [%(filename)s:%(lineno)d]' + COLORS['RESET'] + ' %(message)s',
        logging.CRITICAL: COLORS['GRAY'] + '%(asctime)s ' + COLORS['BOLD'] + COLORS['BG_RED'] + '[%(levelname)s]' + COLORS['RESET'] + COLORS['GRAY'] + ' [%(filename)s:%(lineno)d]' + COLORS['RESET'] + ' %(message)s',
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

# Create colored formatter for console
colored_formatter = ColoredFormatter()

# Configure logging with colored format and set to DEBUG level to show all logs
handler = logging.StreamHandler()
handler.setFormatter(colored_formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
# Remove any existing handlers
for hdlr in root_logger.handlers[:]:
    root_logger.removeHandler(hdlr)
root_logger.addHandler(handler)

def initialize_performance_tracking():
    """Initialize performance tracking variables in session state."""
    if 'performance_timers' not in st.session_state:
        st.session_state.performance_timers = {}

    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {}

    # Add UI freeze detection
    if 'ui_freeze_thresholds' not in st.session_state:
        st.session_state.ui_freeze_thresholds = {
            'warning': 1.0,  # Operations taking longer than 1 second get a warning
            'critical': 3.0,  # Operations taking longer than 3 seconds are critical
            'ui_blocking': 0.5  # Operations that may block UI if longer than this
        }

def debug_log(message: str, data: Any = None, performance_tag: str = None):
    """
    Log debug messages to server console if debug mode is enabled
    
    Args:
        message: The message to log
        data: Optional data to include with the log
        performance_tag: Optional tag for performance tracking
    """
    # In test environments, st.session_state might not be available, so we need fallbacks
    if 'pytest' in sys.modules:
        # We're running in a test - respect debug mode from mock session_state if available
        # This allows tests to verify that debug mode is working correctly
        mock_session_state = getattr(st, 'session_state', None)
        debug_mode = getattr(mock_session_state, 'debug_mode', True) if mock_session_state else True
        log_level = getattr(mock_session_state, 'log_level', logging.DEBUG) if mock_session_state else logging.DEBUG
        
        # Handle timers for tests so we can test performance timing
        if performance_tag and performance_tag.startswith('start_'):
            tag = performance_tag[6:]  # Remove 'start_' prefix
            # Make sure performance_timers exists in mock session state
            if mock_session_state and not hasattr(mock_session_state, 'performance_timers'):
                mock_session_state.performance_timers = {}
            
            # Store the timer in the mock session state
            if mock_session_state:
                mock_session_state.performance_timers[tag] = time.time()
            
            # Convert log_level to integer using the helper
            log_level_int = get_log_level_int(log_level)
            
            # Only log if debug mode is on
            if debug_mode and log_level_int <= logging.DEBUG:
                logging.debug(f"{COLORS['BRIGHT_CYAN']}⏱️ START TIMER [{tag}]{COLORS['RESET']}: {message}")
            return
        elif performance_tag and performance_tag.startswith('end_'):
            tag = performance_tag[4:]  # Remove 'end_' prefix
            # Check if we have a timer in the mock session state
            if mock_session_state and hasattr(mock_session_state, 'performance_timers'):
                if tag in mock_session_state.performance_timers:
                    elapsed = time.time() - mock_session_state.performance_timers[tag]
                    
                    # Initialize performance_metrics if it doesn't exist
                    if not hasattr(mock_session_state, 'performance_metrics'):
                        mock_session_state.performance_metrics = {}
                    
                    # Store metrics
                    mock_session_state.performance_metrics[f"{tag}_{time.time()}"] = {
                        'tag': tag,
                        'duration': elapsed,
                        'timestamp': time.time(),
                        'message': message,
                        'severity': 'warning' if elapsed >= 1.0 else 'good'
                    }
                    
                    # Remove the timer
                    del mock_session_state.performance_timers[tag]
                    
                    # Log with appropriate severity based on elapsed time
                    if elapsed >= 3.0:  # Critical
                        logging.warning(f"{COLORS['BOLD']}{COLORS['BRIGHT_RED']}⏱️ END TIMER [{tag}]{COLORS['RESET']}: {message} {COLORS['BRIGHT_RED']}(took {elapsed:.2f}s) - CRITICAL PERFORMANCE ISSUE{COLORS['RESET']}")
                    elif elapsed >= 1.0:  # Warning
                        logging.warning(f"{COLORS['BRIGHT_YELLOW']}⏱️ END TIMER [{tag}]{COLORS['RESET']}: {message} {COLORS['BRIGHT_YELLOW']}(took {elapsed:.2f}s) - PERFORMANCE WARNING{COLORS['RESET']}")
                    elif debug_mode and get_log_level_int(log_level) <= logging.DEBUG:  # Normal
                        logging.debug(f"{COLORS['BRIGHT_GREEN']}⏱️ END TIMER [{tag}]{COLORS['RESET']}: {message} {COLORS['GRAY']}(took {elapsed:.2f}s){COLORS['RESET']}")
            
            return
        
        # Standard logging for tests
        log_level_int = get_log_level_int(log_level)
        if debug_mode and log_level_int <= logging.DEBUG:
            if data is not None:
                logging.debug(f"{message}: {data}")
            else:
                logging.debug(message)
        return
    
    # Not in test environment, use normal logging with st.session_state
    if not hasattr(st, 'session_state'):
        return  # Can't proceed without session state (likely in docs build or non-streamlit context)
    
    # Initialize debug mode if not set
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    # Initialize log level if not set
    if 'log_level' not in st.session_state:
        st.session_state.log_level = logging.WARNING
    
    debug_mode = st.session_state.debug_mode
    log_level = st.session_state.log_level
    
    # Check if this is a performance timing call
    if performance_tag and performance_tag.startswith('start_'):
        tag = performance_tag[6:]  # Remove 'start_' prefix
        
        # Record the start time for this tag
        if 'performance_timers' not in st.session_state:
            st.session_state.performance_timers = {}
            
        st.session_state.performance_timers[tag] = time.time()
        
        # Only log if debug mode is on
        if debug_mode and log_level <= logging.DEBUG:
            logging.debug(f"{COLORS['BRIGHT_CYAN']}⏱️ START TIMER [{tag}]{COLORS['RESET']}: {message}")
        return
        
    elif performance_tag and performance_tag.startswith('end_'):
        tag = performance_tag[4:]  # Remove 'end_' prefix
        
        # Make sure we have the performance timer for this tag
        if 'performance_timers' in st.session_state and tag in st.session_state.performance_timers:
            # Calculate elapsed time
            elapsed = time.time() - st.session_state.performance_timers[tag]
            
            # Get threshold values from session state or use defaults
            warning_threshold = st.session_state.ui_freeze_thresholds.get('warning', 1.0)
            critical_threshold = st.session_state.ui_freeze_thresholds.get('critical', 3.0)
            ui_blocking = st.session_state.ui_freeze_thresholds.get('ui_blocking', 0.5)
            
            # Set indicator based on elapsed time
            if elapsed >= critical_threshold:
                indicator = "🔴"  # Red circle for critical
                severity_bar = "█████"  # Full bar for critical
                severity_color = COLORS['BRIGHT_RED']
                logging.warning(f"{severity_color}{indicator} END TIMER [{tag}]{COLORS['RESET']}: {message} {severity_color}(took {elapsed:.2f}s){COLORS['RESET']} {severity_color}{severity_bar} CRITICAL PERFORMANCE ISSUE{COLORS['RESET']}")
            elif elapsed >= warning_threshold:
                indicator = "🟠"  # Orange circle for warning
                severity_bar = "███▒▒"  # Partial bar for warning
                severity_color = COLORS['BRIGHT_YELLOW']
                logging.warning(f"{severity_color}{indicator} END TIMER [{tag}]{COLORS['RESET']}: {message} {severity_color}(took {elapsed:.2f}s){COLORS['RESET']} {severity_color}{severity_bar} PERFORMANCE WARNING{COLORS['RESET']}")
            else:
                indicator = "🟢"  # Green circle for good
                severity_bar = "█▒▒▒▒"  # Low bar for good
                severity_color = COLORS['BRIGHT_GREEN']
                # Only log in debug mode and if log level allows it
                log_level_int = get_log_level_int(st.session_state.log_level)
                if st.session_state.debug_mode and log_level_int <= logging.DEBUG:
                    logging.debug(f"{severity_color}{indicator} END TIMER [{tag}]{COLORS['RESET']}: {message} {COLORS['GRAY']}(took {elapsed:.2f}s){COLORS['RESET']} {severity_color}{severity_bar}{COLORS['RESET']}")
            
            # Add UI blocking analysis
            ui_impact = ""
            if elapsed >= ui_blocking:
                ui_impact = f" [UI FREEZE RISK: {elapsed:.2f}s]"
            
            # Store the performance metric for analysis with enhanced data
            if 'performance_metrics' not in st.session_state:
                st.session_state.performance_metrics = {}
            
            # Store with timestamp, duration and performance classification
            st.session_state.performance_metrics[f"{tag}_{time.time()}"] = {
                'tag': tag,
                'duration': elapsed,
                'timestamp': time.time(),
                'message': message,
                'indicator': indicator,
                'ui_impact': ui_impact != "",
                'severity': 'critical' if elapsed >= critical_threshold else 
                           'warning' if elapsed >= warning_threshold else 'good'
            }
            
            # Clean up the timer
            del st.session_state.performance_timers[tag]
            return
        else:
            # Timer not found, just log as a regular message if in debug mode
            log_level_int = get_log_level_int(st.session_state.log_level)
            if st.session_state.debug_mode and log_level_int <= logging.DEBUG:
                logging.debug(f"⚠️ TIMER [{tag}] not found: {message}")
            return
            
    # Skip normal logging if debug mode is off
    if not debug_mode and not performance_tag:
        return
    
    # Standard log - only if debug mode is on
    log_level_int = get_log_level_int(log_level)
    if debug_mode and log_level_int <= logging.DEBUG:
        if data is not None:
            # Format data for display
            if isinstance(data, dict) or isinstance(data, list):
                try:
                    # Use a more readable format for JSON data with indentation and color
                    data_str = json.dumps(data, indent=2, sort_keys=True)
                    
                    # Add ANSI colors for values based on type (works in terminals with color support)
                    if 'pytest' not in sys.modules:  # Only in non-test mode
                        # Add colors for strings, numbers, and booleans
                        data_str = re.sub(r'(".*?"):', f'{COLORS["CYAN"]}\\1{COLORS["RESET"]}:', data_str)  # Keys
                        data_str = re.sub(r': (".*?")(,?)$', f': {COLORS["GREEN"]}\\1{COLORS["RESET"]}\\2', data_str, flags=re.MULTILINE)  # String values
                        data_str = re.sub(r': (true|false)(,?)$', f': {COLORS["YELLOW"]}\\1{COLORS["RESET"]}\\2', data_str, flags=re.MULTILINE)  # Booleans
                        data_str = re.sub(r': ([-+]?\d*\.?\d+)(,?)$', f': {COLORS["MAGENTA"]}\\1{COLORS["RESET"]}\\2', data_str, flags=re.MULTILINE)  # Numbers
                        data_str = re.sub(r': (null)(,?)$', f': {COLORS["RED"]}\\1{COLORS["RESET"]}\\2', data_str, flags=re.MULTILINE)  # Null
                except:
                    data_str = str(data)
            else:
                data_str = str(data)
            
            # Truncate if too long
            if len(data_str) > 1000:
                data_str = data_str[:997] + "..."
                
            # Determine log prefix - include caller information in log message
            log_prefix = ""
            try:
                # Get caller frame info
                frame = sys._getframe(1)
                func_name = frame.f_code.co_name
                file_name = os.path.basename(frame.f_code.co_filename)
                line_no = frame.f_lineno
                log_prefix = f"[{file_name}:{line_no} in {func_name}]"
            except:
                # In case frame info extraction fails
                log_prefix = "[unknown location]"
                
            logging.debug(f"{log_prefix} {message}:\n{data_str}")
        else:
            logging.debug(f"{log_prefix} {message}")

# Only define pandas-dependent functions if pandas is available
if PANDAS_AVAILABLE:
    def get_ui_freeze_report() -> pd.DataFrame:
        """
        Generate a report of performance metrics that might cause UI freezing
        
        Returns:
            DataFrame containing operations that may freeze the UI
        """
        # Default to empty DataFrame
        df = pd.DataFrame(columns=['operation', 'Duration', 'Time', 'severity'])
        
        # Get metrics from session state
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}
        
        metrics = st.session_state.performance_metrics
        if not metrics:
            return df
        
        # Convert metrics to DataFrame
        rows = []
        for key, data in metrics.items():
            # Only include metrics with potential UI impact
            if data.get('ui_impact', False) or data.get('severity') != 'good':
                rows.append({
                    'operation': data['tag'],
                    'Duration': round(data['duration'], 2),
                    'Time': datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S'),
                    'severity': data['severity']
                })
        
        # Create DataFrame if we have rows
        if rows:
            df = pd.DataFrame(rows)
            df = df.sort_values(by='Duration', ascending=False)
        
        # Return formatted DataFrame
        display_df = df[['operation', 'Duration', 'Time', 'severity']].copy()
        display_df.columns = ['Operation', 'Duration', 'Time', 'Severity']
        
        return display_df

def log_error(error, component=None, additional_info=None):
    """
    Log error with traceback and contextual information
    
    Args:
        error: The exception object
        component: Optional name of the component where the error occurred
        additional_info: Optional additional information about the context
    """
    import traceback
    
    # Format the error message
    error_message = f"ERROR: {str(error)}"
    if component:
        error_message = f"[{component}] {error_message}"
        
    # Get the stack trace
    stack_trace = traceback.format_exc()
    
    # Log the error
    logging.error(error_message)
    logging.error(f"Stack trace:\n{stack_trace}")
    
    # Log additional info if provided
    if additional_info:
        logging.error(f"Additional info: {additional_info}")
        
    # In debug mode, also output to debug log for test access
    debug_log(error_message, {'stack_trace': stack_trace, 'additional_info': additional_info})
