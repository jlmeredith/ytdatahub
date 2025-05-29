"""
Base class for all YouTube data analyzers.
"""
from abc import ABC, abstractmethod
import pandas as pd
import logging
from typing import Dict, Any, Optional, List, Union

class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzer classes.
    Defines common methods and utilities for data analysis.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analyzer with configuration.
        
        Args:
            config (dict, optional): Configuration for the analyzer
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def analyze(self, data: Any) -> Dict[str, Any]:
        """
        Analyze the provided data.
        
        Args:
            data: The data to analyze
            
        Returns:
            dict: The analysis results
        """
        pass

    def validate_data(self, data: Any, required_keys: Optional[List[str]] = None) -> bool:
        """
        Validate if the data contains required keys.
        
        Args:
            data: Data to validate
            required_keys: List of required keys
            
        Returns:
            bool: True if valid, False otherwise
        """
        if data is None:
            return False
            
        if required_keys and isinstance(data, dict):
            return all(key in data for key in required_keys)
            
        return True
        
    def safe_int_value(self, value: Any, default: int = 0) -> int:
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
    
    def clean_dates(self, df: pd.DataFrame, date_column: str = 'Published') -> pd.DataFrame:
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
        except Exception as e:
            self.logger.warning(f"Error cleaning dates: {str(e)}")
            return df
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get analyzer metrics and statistics.
        
        Returns:
            dict: Metrics and statistics for the analyzer
        """
        return {
            'analyzer_name': self.__class__.__name__,
            'config': self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update the analyzer configuration.
        
        Args:
            new_config (dict): New configuration values to apply
        """
        self.config.update(new_config)