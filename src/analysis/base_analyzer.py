"""
Base class for all YouTube data analyzers.
"""
from abc import ABC, abstractmethod
import pandas as pd

class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzer classes.
    Defines common methods and utilities for data analysis.
    """

    def __init__(self):
        """Initialize the analyzer."""
        pass

    def validate_data(self, channel_data, required_keys=None):
        """
        Validate if the channel data contains required keys.
        
        Args:
            channel_data: Dictionary with channel data
            required_keys: List of required keys
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not channel_data:
            return False
            
        if required_keys:
            return all(key in channel_data for key in required_keys)
            
        return True
        
    def safe_int_value(self, value, default=0):
        """
        Safely convert a value to integer.
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            int: Converted integer value
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def clean_dates(self, df, date_column='Published'):
        """
        Clean and convert date columns to proper datetime format.
        
        Args:
            df: DataFrame with date column
            date_column: Name of the date column
            
        Returns:
            DataFrame: DataFrame with cleaned dates
        """
        if df is None or date_column not in df.columns:
            return df
            
        try:
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])
            return df
        except Exception:
            return df