"""
Service for tracking, analyzing and visualizing metrics over time.
"""
import logging
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from src.services.youtube.base_service import BaseService
from src.utils.helpers import debug_log
from .alert_threshold_config import AlertThresholdConfig
from .trend_analysis import TrendAnalyzer

class MetricsTrackingService(BaseService):
    """
    Service for tracking, analyzing and visualizing metrics over time.
    Provides advanced historical trend analysis and customizable alert thresholds.
    """
    
    def __init__(self, db=None, **kwargs):
        """Initialize the metrics tracking service.
        
        Args:
            db: Database service for historical data retrieval
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.db = db
        self.config_file_path = kwargs.get('config_path', 'metrics_thresholds.json')
        self.alert_config = AlertThresholdConfig()
        self.trend_analyzer = TrendAnalyzer()
        
        # Load saved thresholds configuration
        self.load_threshold_config()
        
        # Default time windows for analysis
        self.default_time_windows = {
            'short_term': 7,     # 7 days
            'medium_term': 30,   # 30 days
            'long_term': 90,     # 90 days
            'year': 365,         # 365 days
        }
        
    def analyze_historical_trends(self, entity_id: str, metric_name: str, 
                                 entity_type: str = 'channel', 
                                 time_window: int = 90, 
                                 analysis_types: List[str] = None) -> Dict[str, Any]:
        """
        Analyze historical data for a given metric and return trend insights.
        
        Args:
            entity_id: ID of the channel, video, or comment
            metric_name: Name of the metric to analyze (e.g., 'views', 'subscribers')
            entity_type: Type of entity ('channel', 'video', or 'comment')
            time_window: Number of days to look back for analysis
            analysis_types: List of analysis types to perform (default: all)
                Options include:
                - 'linear_trend'
                - 'moving_average'
                - 'growth_rate'
                - 'seasonality'
                - 'anomaly_detection'
                
        Returns:
            Dict containing trend analysis results
        """
        if not analysis_types:
            analysis_types = ['linear_trend', 'moving_average', 'growth_rate']
        
        # Fetch historical metric data
        history = self._get_historical_data(entity_id, metric_name, entity_type, time_window)
        
        if not history or len(history) < 2:
            debug_log(f"Not enough historical data for {entity_type} {entity_id}, metric: {metric_name}")
            return {
                'entity_id': entity_id,
                'entity_type': entity_type,
                'metric_name': metric_name, 
                'status': 'insufficient_data',
                'message': f"Not enough historical data available for trend analysis (found {len(history) if history else 0} data points)"
            }
        
        # Convert to pandas DataFrame for easier analysis
        df = pd.DataFrame(history)
        
        # Perform requested analyses
        results = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'metric_name': metric_name,
            'time_window_days': time_window,
            'data_points': len(df),
            'earliest_date': df['timestamp'].min(),
            'latest_date': df['timestamp'].max(),
            'current_value': df.iloc[-1]['value'],
            'status': 'success'
        }
        
        # Add analysis results
        for analysis_type in analysis_types:
            if analysis_type == 'linear_trend':
                results['linear_trend'] = self.trend_analyzer.calculate_linear_trend(df)
            elif analysis_type == 'moving_average':
                results['moving_average'] = self.trend_analyzer.calculate_moving_averages(df)
            elif analysis_type == 'growth_rate':
                results['growth_rate'] = self.trend_analyzer.calculate_growth_rates(df)
            elif analysis_type == 'seasonality':
                results['seasonality'] = self.trend_analyzer.analyze_seasonality(df)
            elif analysis_type == 'anomaly_detection':
                results['anomalies'] = self.trend_analyzer.detect_anomalies(df)
        
        # Check if any thresholds have been violated
        threshold_violations = self.check_threshold_violations(
            entity_id, entity_type, metric_name, results
        )
        
        if threshold_violations:
            results['threshold_violations'] = threshold_violations
            
        return results
    
    def set_alert_threshold(self, entity_type: str, metric_name: str, 
                           threshold_config: Dict[str, Any]) -> bool:
        """
        Set alert thresholds for a specific entity type and metric.
        
        Args:
            entity_type: Type of entity ('channel', 'video', or 'comment')
            metric_name: Name of the metric to set thresholds for
            threshold_config: Dictionary containing threshold configuration
                {
                    'warning': {'type': 'percentage', 'value': 10},
                    'critical': {'type': 'percentage', 'value': 20},
                    'comparison_window': 7,  # days
                    'direction': 'both',  # 'increase', 'decrease', 'both'
                }
                
        Returns:
            Boolean indicating success or failure
        """
        result = self.alert_config.set_threshold(entity_type, metric_name, threshold_config)
        
        # Save updated thresholds to disk
        if result:
            self.save_threshold_config()
            
        return result
    
    def check_threshold_violations(self, entity_id: str, entity_type: str, 
                                  metric_name: str, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check if the current metric values violate any configured thresholds.
        
        Args:
            entity_id: ID of the entity (channel, video, comment)
            entity_type: Type of entity
            metric_name: Name of the metric
            analysis_results: Dict of trend analysis results
            
        Returns:
            List of threshold violations, each containing:
            - threshold_level: 'warning' or 'critical'
            - threshold_value: The value of the threshold
            - current_value: Current value being compared
            - comparison_value: Value used for comparison (e.g., previous period)
            - message: Human-readable message about the violation
        """
        # Get threshold configuration for this metric
        thresholds = self.alert_config.get_threshold(entity_type, metric_name)
        if not thresholds:
            return []
        
        violations = []
        
        # Get growth rates from analysis results
        if 'growth_rate' in analysis_results:
            growth_data = analysis_results['growth_rate']
            
            # Check each configured threshold
            for level, config in thresholds.items():
                if level in ('warning', 'critical'):
                    # Determine comparison window
                    window = config.get('comparison_window', 7)  # Default: 7 days
                    window_key = f"{window}day"
                    
                    if window_key in growth_data:
                        growth_value = growth_data[window_key]['percentage']
                        threshold_value = config['value']
                        threshold_type = config['type']
                        direction = config.get('direction', 'both')
                        
                        violation = self._check_single_threshold(
                            level, threshold_type, threshold_value,
                            growth_value, direction, metric_name, entity_id, entity_type, window
                        )
                        
                        if violation:
                            violations.append(violation)
        
        return violations
    
    def generate_trend_report(self, entity_id: str, entity_type: str = 'channel', 
                             metrics: List[str] = None, time_windows: List[int] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive trend report for multiple metrics of an entity.
        
        Args:
            entity_id: ID of the entity
            entity_type: Type of entity
            metrics: List of metric names to analyze (None for default set)
            time_windows: List of time windows in days to analyze (None for default set)
            
        Returns:
            Dictionary containing trend reports for each metric
        """
        if not metrics:
            # Default metrics based on entity type
            if entity_type == 'channel':
                metrics = ['subscribers', 'views', 'total_videos']
            elif entity_type == 'video':
                metrics = ['views', 'likes', 'comment_count']
            elif entity_type == 'comment':
                metrics = ['likes', 'reply_count']
            else:
                metrics = ['views']
                
        if not time_windows:
            time_windows = [self.default_time_windows['long_term']]  # Default to long-term
            
        report = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }
        
        # Analyze each metric for each time window
        for metric in metrics:
            report['metrics'][metric] = {}
            for window in time_windows:
                analysis = self.analyze_historical_trends(
                    entity_id, metric, entity_type, window
                )
                report['metrics'][metric][f"window_{window}days"] = analysis
                
        return report

    def save_threshold_config(self) -> bool:
        """
        Save threshold configurations to disk.
        
        Returns:
            Boolean indicating success or failure
        """
        try:
            with open(self.config_file_path, 'w') as f:
                json.dump(self.alert_config.get_all_thresholds(), f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Failed to save threshold config: {str(e)}")
            return False
            
    def load_threshold_config(self) -> bool:
        """
        Load threshold configurations from disk.
        
        Returns:
            Boolean indicating success or failure
        """
        try:
            with open(self.config_file_path, 'r') as f:
                thresholds = json.load(f)
                self.alert_config.set_all_thresholds(thresholds)
            return True
        except FileNotFoundError:
            logging.info(f"No threshold configuration file found at {self.config_file_path}")
            return False
        except Exception as e:
            logging.error(f"Failed to load threshold config: {str(e)}")
            return False
    
    def _get_historical_data(self, entity_id: str, metric_name: str, 
                            entity_type: str, time_window: int) -> List[Dict[str, Any]]:
        """
        Retrieve historical data for the specified entity and metric.
        
        Args:
            entity_id: ID of the entity
            metric_name: Name of the metric
            entity_type: Type of entity
            time_window: Time window in days
            
        Returns:
            List of historical data points
        """
        if not self.db:
            debug_log("No database connection available for historical data retrieval")
            return []
            
        try:
            # Convert time_window to datetime for database query
            start_date = datetime.now() - timedelta(days=time_window)
            
            # Query the database for historical data
            history = self.db.get_metric_history(
                metric_name, entity_id, 
                start_time=start_date.isoformat(),
                limit=1000  # Set a high limit to get all data
            )
            
            # Sort by timestamp
            if history:
                history = sorted(history, key=lambda x: x['timestamp'])
                
            return history
        except Exception as e:
            logging.error(f"Error retrieving historical data: {str(e)}")
            return []
            
    def _check_single_threshold(self, level, threshold_type, threshold_value,
                               actual_value, direction, metric_name, entity_id, 
                               entity_type, window) -> Dict[str, Any]:
        """
        Check if a single threshold has been violated.
        
        Args:
            level: Threshold level ('warning' or 'critical')
            threshold_type: Type of threshold ('percentage', 'absolute', etc.)
            threshold_value: Value of the threshold
            actual_value: Actual value to compare
            direction: Direction to check ('increase', 'decrease', 'both')
            metric_name: Name of the metric
            entity_id: ID of the entity
            entity_type: Type of entity
            window: Time window in days
            
        Returns:
            Dictionary with violation details if threshold is violated, None otherwise
        """
        is_violated = False
        
        # For percentage thresholds
        if threshold_type == 'percentage':
            if direction == 'increase' and actual_value >= threshold_value:
                is_violated = True
            elif direction == 'decrease' and actual_value <= -threshold_value:
                is_violated = True
            elif direction == 'both' and abs(actual_value) >= threshold_value:
                is_violated = True
                
        # For absolute thresholds
        elif threshold_type == 'absolute':
            if direction == 'increase' and actual_value >= threshold_value:
                is_violated = True
            elif direction == 'decrease' and actual_value <= threshold_value:
                is_violated = True
            elif direction == 'both' and abs(actual_value) >= abs(threshold_value):
                is_violated = True
        
        if is_violated:
            # Format a descriptive message
            if actual_value > 0:
                change_description = f"increased by {actual_value:.2f}%"
            else:
                change_description = f"decreased by {abs(actual_value):.2f}%"
                
            return {
                'threshold_level': level,
                'threshold_value': threshold_value,
                'threshold_type': threshold_type,
                'current_value': actual_value,
                'direction': direction,
                'window_days': window,
                'message': f"[{level.upper()}] {metric_name} for {entity_type} {entity_id} has {change_description} in the last {window} days, exceeding the {level} threshold of {threshold_value}%"
            }
            
        return None
