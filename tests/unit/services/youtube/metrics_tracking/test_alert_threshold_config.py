"""
Unit tests for AlertThresholdConfig.
Tests the configuration management for metric alert thresholds.
"""
import pytest
import json
from unittest.mock import patch, mock_open
from src.services.youtube.metrics_tracking.alert_threshold_config import AlertThresholdConfig


class TestAlertThresholdConfig:
    """Tests for the AlertThresholdConfig class."""
    
    def test_initialization(self):
        """Test that AlertThresholdConfig initializes with default thresholds."""
        config = AlertThresholdConfig()
        
        # Verify default thresholds for major metrics are set
        assert 'subscribers' in config._thresholds['channel']
        assert 'views' in config._thresholds['channel']
        assert 'views' in config._thresholds['video']
        assert 'likes' in config._thresholds['video']
        assert 'likes' in config._thresholds['comment']
        
        # Verify default threshold structure
        subscribers_config = config._thresholds['channel']['subscribers']
        assert 'warning' in subscribers_config
        assert 'critical' in subscribers_config
        assert subscribers_config['warning']['type'] == 'percentage'
        assert subscribers_config['critical']['type'] == 'percentage'
        
    def test_get_threshold(self):
        """Test retrieving threshold configurations."""
        config = AlertThresholdConfig()
        
        # Test retrieving existing threshold
        threshold = config.get_threshold('channel', 'subscribers')
        assert threshold is not None
        assert 'warning' in threshold
        assert 'critical' in threshold
        
        # Test retrieving non-existent threshold
        non_existent = config.get_threshold('channel', 'non_existent')
        assert non_existent is None
        
        # Test retrieving threshold for invalid entity type
        invalid = config.get_threshold('invalid_entity', 'subscribers')
        assert invalid is None
        
    def test_set_threshold(self):
        """Test setting threshold configurations."""
        config = AlertThresholdConfig()
        
        # Valid threshold configuration
        valid_config = {
            'warning': {'type': 'percentage', 'value': 15},
            'critical': {'type': 'percentage', 'value': 30},
            'comparison_window': 7,
            'direction': 'both'
        }
        
        # Test setting valid threshold
        result = config.set_threshold('channel', 'new_metric', valid_config)
        assert result is True
        
        # Verify the threshold was set correctly
        threshold = config.get_threshold('channel', 'new_metric')
        assert threshold is not None
        assert threshold['warning']['value'] == 15
        assert threshold['critical']['value'] == 30
        
        # Test setting threshold for invalid entity type
        result = config.set_threshold('invalid_entity', 'metric', valid_config)
        assert result is False
        
        # Test setting threshold with invalid configuration
        invalid_config = {
            'warning': {'type': 'invalid_type', 'value': 15}
        }
        result = config.set_threshold('channel', 'invalid_metric', invalid_config)
        assert result is False
        
        # Test setting threshold without required fields
        incomplete_config = {
            'warning': {'value': 15}  # missing 'type'
        }
        result = config.set_threshold('channel', 'incomplete_metric', incomplete_config)
        assert result is False
        
    def test_set_all_thresholds(self):
        """Test setting all threshold configurations at once."""
        config = AlertThresholdConfig()
        
        # Valid full configuration
        valid_full_config = {
            'channel': {
                'test_metric': {
                    'warning': {'type': 'percentage', 'value': 10},
                    'critical': {'type': 'percentage', 'value': 20},
                    'comparison_window': 7,
                    'direction': 'both'
                }
            },
            'video': {},
            'comment': {}
        }
        
        # Test setting valid configuration
        result = config.set_all_thresholds(valid_full_config)
        assert result is True
        
        # Verify configuration was set
        threshold = config.get_threshold('channel', 'test_metric')
        assert threshold is not None
        assert threshold['warning']['value'] == 10
        
        # Test setting configuration with invalid entity type
        invalid_config = {
            'channel': {},
            'invalid_entity': {}
        }
        result = config.set_all_thresholds(invalid_config)
        assert result is False
        
        # Test setting configuration with invalid threshold
        invalid_threshold_config = {
            'channel': {
                'test_metric': {
                    'warning': {'type': 'invalid_type', 'value': 10}
                }
            },
            'video': {},
            'comment': {}
        }
        result = config.set_all_thresholds(invalid_threshold_config)
        assert result is False
        
    def test_delete_threshold(self):
        """Test deleting a threshold configuration."""
        config = AlertThresholdConfig()
        
        # Test deleting existing threshold
        result = config.delete_threshold('channel', 'subscribers')
        assert result is True
        
        # Verify threshold was deleted
        threshold = config.get_threshold('channel', 'subscribers')
        assert threshold is None
        
        # Test deleting non-existent threshold
        result = config.delete_threshold('channel', 'non_existent')
        assert result is False
        
        # Test deleting threshold for invalid entity type
        result = config.delete_threshold('invalid_entity', 'subscribers')
        assert result is False
        
    def test_validate_threshold_config(self):
        """Test threshold configuration validation."""
        config = AlertThresholdConfig()
        
        # Valid configuration with warning only
        valid_warning = {
            'warning': {'type': 'percentage', 'value': 10},
            'comparison_window': 7
        }
        assert config._validate_threshold_config(valid_warning) is True
        
        # Valid configuration with critical only
        valid_critical = {
            'critical': {'type': 'absolute', 'value': 1000},
            'comparison_window': 7
        }
        assert config._validate_threshold_config(valid_critical) is True
        
        # Valid configuration with both levels
        valid_both = {
            'warning': {'type': 'percentage', 'value': 10},
            'critical': {'type': 'percentage', 'value': 20},
            'comparison_window': 7
        }
        assert config._validate_threshold_config(valid_both) is True
        
        # Invalid configuration - no threshold levels
        invalid_no_levels = {'comparison_window': 7}
        assert config._validate_threshold_config(invalid_no_levels) is False
        
        # Invalid configuration - warning is not a dict
        invalid_warning_type = {
            'warning': 'not_a_dict',
            'comparison_window': 7
        }
        assert config._validate_threshold_config(invalid_warning_type) is False
        
        # Invalid configuration - missing type
        invalid_missing_type = {
            'warning': {'value': 10},
            'comparison_window': 7
        }
        assert config._validate_threshold_config(invalid_missing_type) is False
        
        # Invalid configuration - missing value
        invalid_missing_value = {
            'warning': {'type': 'percentage'},
            'comparison_window': 7
        }
        assert config._validate_threshold_config(invalid_missing_value) is False
        
        # Invalid configuration - invalid threshold type
        invalid_threshold_type = {
            'warning': {'type': 'invalid', 'value': 10},
            'comparison_window': 7
        }
        assert config._validate_threshold_config(invalid_threshold_type) is False
        
        # Invalid configuration - value not a number
        invalid_value_type = {
            'warning': {'type': 'percentage', 'value': 'not_a_number'},
            'comparison_window': 7
        }
        assert config._validate_threshold_config(invalid_value_type) is False
        
    def test_save_threshold_config(self):
        """Test saving threshold configuration to file."""
        config = AlertThresholdConfig()
        
        # Mock the open function
        mock_json = json.dumps(config.get_all_thresholds(), indent=2)
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            result = config.save_threshold_config()
            assert result is True
            mock_file.assert_called_once_with(config.config_file_path, 'w')
            mock_json_dump.assert_called_once()
            
    def test_save_threshold_config_exception(self):
        """Test error handling when saving configuration."""
        config = AlertThresholdConfig()
        
        # Test exception when opening file
        with patch('builtins.open', side_effect=Exception("File error")):
            result = config.save_threshold_config()
            assert result is False
            
    def test_load_threshold_config(self):
        """Test loading threshold configuration from file."""
        config = AlertThresholdConfig()
        
        # Create a sample config to load
        sample_config = {
            'channel': {
                'test_metric': {
                    'warning': {'type': 'percentage', 'value': 10},
                    'critical': {'type': 'percentage', 'value': 20},
                    'comparison_window': 7,
                    'direction': 'both'
                }
            },
            'video': {},
            'comment': {}
        }
        
        # Mock the open function and json.load
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))), \
             patch('json.load', return_value=sample_config):
            result = config.load_threshold_config()
            assert result is True
            
            # Verify configuration was loaded
            threshold = config.get_threshold('channel', 'test_metric')
            assert threshold is not None
            assert threshold['warning']['value'] == 10
            
    def test_load_threshold_config_file_not_found(self):
        """Test handling of missing configuration file."""
        config = AlertThresholdConfig()
        
        # Test FileNotFoundError
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = config.load_threshold_config()
            assert result is False
            
    def test_load_threshold_config_exception(self):
        """Test error handling when loading configuration."""
        config = AlertThresholdConfig()
        
        # Test general exception
        with patch('builtins.open', mock_open()), \
             patch('json.load', side_effect=Exception("JSON error")):
            result = config.load_threshold_config()
            assert result is False


if __name__ == '__main__':
    pytest.main()
