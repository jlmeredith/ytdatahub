"""
Alert threshold configuration module for YTDataHub metrics tracking.
"""
import logging
import json
import os
from typing import Dict, Any, Optional

class AlertThresholdConfig:
    """
    Configuration manager for metric alert thresholds.
    Handles threshold definitions, validation, and persistence.
    """
    
    def __init__(self):
        """Initialize alert threshold configuration."""
        self._thresholds = {
            'channel': {},
            'video': {},
            'comment': {},
        }
        
        # Define valid threshold types
        self.valid_threshold_types = ['percentage', 'absolute', 'statistical']
        
        # Define valid threshold directions
        self.valid_directions = ['increase', 'decrease', 'both']
        
        # Default config path
        self._config_file_path = os.path.join(os.path.dirname(__file__), 'alert_thresholds.json')
        
        # Set up default thresholds
        self._initialize_default_thresholds()
        
    def _initialize_default_thresholds(self) -> None:
        """Set up default thresholds for common metrics."""
        # Channel metrics
        self.set_threshold('channel', 'subscribers', {
            'warning': {'type': 'percentage', 'value': 10},
            'critical': {'type': 'percentage', 'value': 20},
            'comparison_window': 7,
            'direction': 'both'
        })
        
        self.set_threshold('channel', 'views', {
            'warning': {'type': 'percentage', 'value': 15},
            'critical': {'type': 'percentage', 'value': 30},
            'comparison_window': 7,
            'direction': 'both'
        })
        
        # Video metrics
        self.set_threshold('video', 'views', {
            'warning': {'type': 'percentage', 'value': 20},
            'critical': {'type': 'percentage', 'value': 50},
            'comparison_window': 2,
            'direction': 'both'
        })
        
        self.set_threshold('video', 'likes', {
            'warning': {'type': 'percentage', 'value': 25},
            'critical': {'type': 'percentage', 'value': 50},
            'comparison_window': 2,
            'direction': 'both'
        })
        
        # Comment metrics
        self.set_threshold('comment', 'likes', {
            'warning': {'type': 'percentage', 'value': 50},
            'critical': {'type': 'percentage', 'value': 100},
            'comparison_window': 2,
            'direction': 'both'
        })
        
    def get_threshold(self, entity_type: str, metric_name: str) -> Optional[Dict[str, Any]]:
        """
        Get threshold configuration for a specific entity type and metric.
        
        Args:
            entity_type: The type of entity ('channel', 'video', 'comment')
            metric_name: The name of the metric
            
        Returns:
            Threshold configuration dict or None if not found
        """
        if entity_type not in self._thresholds:
            return None
            
        return self._thresholds[entity_type].get(metric_name)
        
    def set_threshold(self, entity_type: str, metric_name: str, threshold_config: Dict[str, Any]) -> bool:
        """
        Set threshold configuration for a specific entity type and metric.
        
        Args:
            entity_type: The type of entity ('channel', 'video', 'comment')
            metric_name: The name of the metric
            threshold_config: Threshold configuration dict
            
        Returns:
            Boolean indicating success or failure
        """
        if entity_type not in self._thresholds:
            logging.error(f"Invalid entity type: {entity_type}")
            return False
            
        # Validate threshold configuration
        if not self._validate_threshold_config(threshold_config):
            logging.error(f"Invalid threshold configuration for {entity_type}.{metric_name}")
            return False
            
        # Store the threshold configuration
        self._thresholds[entity_type][metric_name] = threshold_config
        return True
        
    def get_all_thresholds(self) -> Dict[str, Any]:
        """
        Get all threshold configurations.
        
        Returns:
            Dictionary of all threshold configurations
        """
        return self._thresholds
        
    def set_all_thresholds(self, thresholds: Dict[str, Any]) -> bool:
        """
        Set all threshold configurations.
        
        Args:
            thresholds: Dictionary of all threshold configurations
            
        Returns:
            Boolean indicating success or failure
        """
        # Validate each entity type and threshold
        for entity_type, entity_thresholds in thresholds.items():
            if entity_type not in self._thresholds:
                logging.error(f"Invalid entity type: {entity_type}")
                return False
                
            for metric_name, threshold_config in entity_thresholds.items():
                if not self._validate_threshold_config(threshold_config):
                    logging.error(f"Invalid threshold configuration for {entity_type}.{metric_name}")
                    return False
                    
        # All configurations are valid, update all thresholds
        self._thresholds = thresholds
        return True
        
    def delete_threshold(self, entity_type: str, metric_name: str) -> bool:
        """
        Delete a threshold configuration.
        
        Args:
            entity_type: The type of entity ('channel', 'video', 'comment')
            metric_name: The name of the metric
            
        Returns:
            Boolean indicating success or failure
        """
        if entity_type not in self._thresholds:
            logging.error(f"Invalid entity type: {entity_type}")
            return False
            
        if metric_name not in self._thresholds[entity_type]:
            logging.warning(f"No threshold configuration found for {entity_type}.{metric_name}")
            return False
            
        del self._thresholds[entity_type][metric_name]
        return True
        
    def _validate_threshold_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate a threshold configuration.
        
        Args:
            config: Threshold configuration to validate
            
        Returns:
            Boolean indicating validity
        """
        # Check for required threshold levels
        required_levels = ['warning', 'critical']
        if not any(level in config for level in required_levels):
            logging.error(f"Threshold configuration must include at least one of {', '.join(required_levels)}")
            return False
            
        # Validate each threshold level
        for level in [l for l in required_levels if l in config]:
            level_config = config[level]
            
            if not isinstance(level_config, dict):
                logging.error(f"Threshold level {level} must be a dictionary")
                return False
                
            if 'type' not in level_config or 'value' not in level_config:
                logging.error(f"Threshold level {level} must include 'type' and 'value'")
                return False
                
            if level_config['type'] not in self.valid_threshold_types:
                logging.error(f"Invalid threshold type: {level_config['type']}")
                return False
                
            if not isinstance(level_config['value'], (int, float)):
                logging.error(f"Threshold value must be a number")
                return False
                
        # Validate comparison window if present
        if 'comparison_window' in config:
            if not isinstance(config['comparison_window'], int) or config['comparison_window'] <= 0:
                logging.error(f"Comparison window must be a positive integer")
                return False
                
        # Validate direction if present
        if 'direction' in config:
            if config['direction'] not in self.valid_directions:
                logging.error(f"Invalid direction: {config['direction']}")
                return False
                
        return True
    
    @property
    def config_file_path(self) -> str:
        """Get the path to the configuration file."""
        return self._config_file_path
        
    @config_file_path.setter
    def config_file_path(self, path: str) -> None:
        """Set the path to the configuration file."""
        self._config_file_path = path
        
    def save_threshold_config(self) -> bool:
        """
        Save threshold configuration to a file.
        
        Returns:
            Boolean indicating success or failure
        """
        try:
            with open(self.config_file_path, 'w') as f:
                json.dump(self.get_all_thresholds(), f, indent=2)
            logging.info(f"Threshold configuration saved to {self.config_file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save threshold configuration: {e}")
            return False
            
    def load_threshold_config(self) -> bool:
        """
        Load threshold configuration from a file.
        
        Returns:
            Boolean indicating success or failure
        """
        try:
            with open(self.config_file_path, 'r') as f:
                thresholds = json.load(f)
                
            if not self.set_all_thresholds(thresholds):
                logging.error("Failed to apply loaded threshold configuration")
                return False
                
            logging.info(f"Threshold configuration loaded from {self.config_file_path}")
            return True
        except FileNotFoundError:
            logging.warning(f"Threshold configuration file not found: {self.config_file_path}")
            return False
        except Exception as e:
            logging.error(f"Failed to load threshold configuration: {e}")
            return False
