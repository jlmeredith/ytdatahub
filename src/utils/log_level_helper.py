"""
Helper utility for handling different log level formats.
"""
import logging

def get_log_level_int(log_level):
    """
    Convert a log level (string or int) to the corresponding integer value.
    
    Args:
        log_level: The log level as a string name ('DEBUG', 'INFO', etc.) or integer
        
    Returns:
        The integer value corresponding to the log level
    """
    if isinstance(log_level, int):
        return log_level
        
    if isinstance(log_level, str):
        # Convert string log level to integer
        level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_mapping.get(log_level.upper(), logging.WARNING)
    
    # Default to WARNING for unknown types
    return logging.WARNING
