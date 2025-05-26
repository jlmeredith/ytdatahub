"""
Unit tests for MetricsTrackingService.
Tests the metrics tracking, trend analysis, and alert functionality.
"""
import pytest
import json
import pandas as pd
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta

from src.services.youtube.metrics_tracking.metrics_tracking_service import MetricsTrackingService
from src.services.youtube.metrics_tracking.alert_threshold_config import AlertThresholdConfig
from src.services.youtube.metrics_tracking.trend_analysis import TrendAnalyzer


class TestMetricsTrackingService:
    """Tests for the MetricsTrackingService class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database for testing."""
        mock = MagicMock()
        
        # Setup mock responses for get_metric_history
        mock.get_metric_history.return_value = [
            {'timestamp': (datetime.now() - timedelta(days=9)).isoformat(), 'value': 100},
            {'timestamp': (datetime.now() - timedelta(days=8)).isoformat(), 'value': 110},
            {'timestamp': (datetime.now() - timedelta(days=7)).isoformat(), 'value': 120},
            {'timestamp': (datetime.now() - timedelta(days=6)).isoformat(), 'value': 130},
            {'timestamp': (datetime.now() - timedelta(days=5)).isoformat(), 'value': 140},
            {'timestamp': (datetime.now() - timedelta(days=4)).isoformat(), 'value': 150},
            {'timestamp': (datetime.now() - timedelta(days=3)).isoformat(), 'value': 160},
            {'timestamp': (datetime.now() - timedelta(days=2)).isoformat(), 'value': 170},
            {'timestamp': (datetime.now() - timedelta(days=1)).isoformat(), 'value': 180},
            {'timestamp': datetime.now().isoformat(), 'value': 190}
        ]
        
        return mock
        
    @pytest.fixture
    def mock_trend_analyzer(self):
        """Create a mock TrendAnalyzer for testing."""
        mock = MagicMock(spec=TrendAnalyzer)
        
        # Setup mock responses for different analysis types
        mock.calculate_linear_trend.return_value = {
            'slope': 10.0,
            'direction': 'increasing',
            'r_squared': 0.95,
            'significance': 'high',
            'forecast': [
                {'date': (datetime.now() + timedelta(days=1)).isoformat(), 'value': 200},
                {'date': (datetime.now() + timedelta(days=2)).isoformat(), 'value': 210}
            ]
        }
        
        mock.calculate_moving_averages.return_value = {
            'short': {
                'window_size': 3,
                'latest_value': 180.0,
                'window_values': [170, 180, 190],
                'window_dates': [
                    (datetime.now() - timedelta(days=2)).isoformat(),
                    (datetime.now() - timedelta(days=1)).isoformat(),
                    datetime.now().isoformat()
                ]
            }
        }
        
        mock.calculate_growth_rates.return_value = {
            '7day': {
                'absolute': 70,
                'percentage': 58.33,  # (190-120)/120 * 100
                'start_value': 120,
                'end_value': 190
            },
            '30day': {
                'absolute': 90,
                'percentage': 90.0,  # Assuming 100 as starting value
                'start_value': 100,
                'end_value': 190
            }
        }
        
        return mock
        
    @pytest.fixture
    def mock_alert_config(self):
        """Create a mock AlertThresholdConfig for testing."""
        mock = MagicMock(spec=AlertThresholdConfig)
        
        # Setup mock responses for get_threshold
        mock.get_threshold.return_value = {
            'warning': {'type': 'percentage', 'value': 20},
            'critical': {'type': 'percentage', 'value': 50},
            'comparison_window': 7,
            'direction': 'both'
        }
        
        return mock
    
    def test_initialization(self, mock_db):
        """Test that MetricsTrackingService initializes correctly."""
        service = MetricsTrackingService(db=mock_db)
        
        # Verify service attributes
        assert service.db == mock_db
        assert isinstance(service.alert_config, AlertThresholdConfig)
        assert isinstance(service.trend_analyzer, TrendAnalyzer)
        assert len(service.default_time_windows) == 4  # short_term, medium_term, long_term, year
        
    def test_analyze_historical_trends_successful(self, mock_db, mock_trend_analyzer):
        """Test analyzing historical trends with successful data retrieval."""
        service = MetricsTrackingService(db=mock_db)
        service.trend_analyzer = mock_trend_analyzer
        
        # Test with all analysis types
        result = service.analyze_historical_trends(
            entity_id='UC_test_channel',
            metric_name='subscribers',
            entity_type='channel',
            time_window=90,
            analysis_types=['linear_trend', 'moving_average', 'growth_rate']
        )
        
        # Verify method was called with correct data
        mock_db.get_metric_history.assert_called_once()
        assert mock_db.get_metric_history.call_args[0][0] == 'subscribers'
        assert mock_db.get_metric_history.call_args[0][1] == 'UC_test_channel'
        
        # Verify the response structure
        assert result['entity_id'] == 'UC_test_channel'
        assert result['entity_type'] == 'channel'
        assert result['metric_name'] == 'subscribers'
        assert result['status'] == 'success'
        assert result['data_points'] == 10
        assert 'linear_trend' in result
        assert 'moving_average' in result
        assert 'growth_rate' in result
        
        # Verify analysis methods were called
        mock_trend_analyzer.calculate_linear_trend.assert_called_once()
        mock_trend_analyzer.calculate_moving_averages.assert_called_once()
        mock_trend_analyzer.calculate_growth_rates.assert_called_once()
        
    def test_analyze_historical_trends_insufficient_data(self, mock_db):
        """Test analyzing historical trends with insufficient data."""
        service = MetricsTrackingService(db=mock_db)
        
        # Set mock to return insufficient data
        mock_db.get_metric_history.return_value = [
            {'timestamp': datetime.now().isoformat(), 'value': 100}
        ]
        
        result = service.analyze_historical_trends(
            entity_id='UC_test_channel',
            metric_name='subscribers',
            entity_type='channel'
        )
        
        # Verify the response indicates insufficient data
        assert result['status'] == 'insufficient_data'
        assert 'Not enough historical data' in result['message']
        
    def test_analyze_historical_trends_no_db(self):
        """Test analyzing historical trends without a DB connection."""
        service = MetricsTrackingService(db=None)
        
        result = service.analyze_historical_trends(
            entity_id='UC_test_channel',
            metric_name='subscribers',
            entity_type='channel'
        )
        
        # Verify the response indicates insufficient data
        assert result['status'] == 'insufficient_data'
        
    def test_set_alert_threshold(self):
        """Test setting alert thresholds."""
        service = MetricsTrackingService()
        
        # Mock the alert_config.set_threshold method
        service.alert_config.set_threshold = MagicMock(return_value=True)
        service.save_threshold_config = MagicMock(return_value=True)
        
        threshold_config = {
            'warning': {'type': 'percentage', 'value': 15},
            'critical': {'type': 'percentage', 'value': 30},
            'comparison_window': 7,
            'direction': 'both'
        }
        
        result = service.set_alert_threshold(
            entity_type='channel',
            metric_name='subscribers',
            threshold_config=threshold_config
        )
        
        # Verify the methods were called correctly
        service.alert_config.set_threshold.assert_called_once_with(
            'channel', 'subscribers', threshold_config
        )
        service.save_threshold_config.assert_called_once()
        assert result is True
        
    def test_set_alert_threshold_failure(self):
        """Test handling of threshold setting failure."""
        service = MetricsTrackingService()
        
        # Mock the alert_config.set_threshold method to fail
        service.alert_config.set_threshold = MagicMock(return_value=False)
        service.save_threshold_config = MagicMock()
        
        threshold_config = {
            'warning': {'type': 'invalid', 'value': 15}
        }
        
        result = service.set_alert_threshold(
            entity_type='channel',
            metric_name='subscribers',
            threshold_config=threshold_config
        )
        
        # Verify save_threshold_config was not called and result is False
        service.save_threshold_config.assert_not_called()
        assert result is False
        
    def test_check_threshold_violations_with_violations(self, mock_alert_config):
        """Test threshold violation checking with violations."""
        service = MetricsTrackingService()
        service.alert_config = mock_alert_config
        
        # Create analysis results with growth rate exceeding warning threshold
        analysis_results = {
            'growth_rate': {
                '7day': {
                    'percentage': 25.0,  # Above warning threshold of 20%
                    'absolute': 250,
                    'start_value': 1000,
                    'end_value': 1250
                }
            }
        }
        
        # Set up a custom _check_single_threshold to return a violation only for warning level
        def mock_check_threshold(level, threshold_type, threshold_value, actual_value, direction, metric_name, entity_id, entity_type, window):
            if level == 'warning':
                return {
                    'threshold_level': 'warning',
                    'threshold_value': 20,
                    'threshold_type': 'percentage',
                    'current_value': 25.0,
                    'direction': 'both',
                    'window_days': 7,
                    'message': '[WARNING] subscribers for channel UC_test_channel has increased by 25.00% in the last 7 days, exceeding the warning threshold of 20%'
                }
            return None  # No violation for critical level
        
        service._check_single_threshold = MagicMock(side_effect=mock_check_threshold)
        
        violations = service.check_threshold_violations(
            entity_id='UC_test_channel',
            entity_type='channel',
            metric_name='subscribers',
            analysis_results=analysis_results
        )
        
        # Verify threshold was checked and violation was returned
        assert len(violations) == 1
        assert violations[0]['threshold_level'] == 'warning'
        assert violations[0]['current_value'] == 25.0
        
    def test_check_threshold_violations_no_violations(self, mock_alert_config):
        """Test threshold violation checking with no violations."""
        service = MetricsTrackingService()
        service.alert_config = mock_alert_config
        
        # Create analysis results with growth rate below threshold
        analysis_results = {
            'growth_rate': {
                '7day': {
                    'percentage': 15.0,  # Below warning threshold of 20%
                    'absolute': 150,
                    'start_value': 1000,
                    'end_value': 1150
                }
            }
        }
        
        # Set up a custom _check_single_threshold to return None (no violation)
        service._check_single_threshold = MagicMock(return_value=None)
        
        violations = service.check_threshold_violations(
            entity_id='UC_test_channel',
            entity_type='channel',
            metric_name='subscribers',
            analysis_results=analysis_results
        )
        
        # Verify threshold was checked but no violations were returned
        assert len(violations) == 0
        
    def test_check_threshold_violations_no_thresholds(self):
        """Test threshold violation checking with no configured thresholds."""
        service = MetricsTrackingService()
        service.alert_config.get_threshold = MagicMock(return_value=None)
        
        analysis_results = {
            'growth_rate': {
                '7day': {
                    'percentage': 25.0,
                    'absolute': 250,
                    'start_value': 1000,
                    'end_value': 1250
                }
            }
        }
        
        violations = service.check_threshold_violations(
            entity_id='UC_test_channel',
            entity_type='channel',
            metric_name='subscribers',
            analysis_results=analysis_results
        )
        
        # No thresholds configured, so no violations
        assert len(violations) == 0
        
    def test_generate_trend_report(self, mock_db, mock_trend_analyzer):
        """Test generating a comprehensive trend report."""
        service = MetricsTrackingService(db=mock_db)
        service.trend_analyzer = mock_trend_analyzer
        
        # Mock analyze_historical_trends to return analysis results
        service.analyze_historical_trends = MagicMock(return_value={
            'status': 'success',
            'linear_trend': mock_trend_analyzer.calculate_linear_trend.return_value,
            'growth_rate': mock_trend_analyzer.calculate_growth_rates.return_value
        })
        
        # Generate report for subscribers and views
        report = service.generate_trend_report(
            entity_id='UC_test_channel',
            entity_type='channel',
            metrics=['subscribers', 'views'],
            time_windows=[30, 90]
        )
        
        # Verify the report structure
        assert report['entity_id'] == 'UC_test_channel'
        assert report['entity_type'] == 'channel'
        assert 'timestamp' in report
        
        # Check that each requested metric is included
        assert 'subscribers' in report['metrics']
        assert 'views' in report['metrics']
        
        # Check that each time window is included
        assert 'window_30days' in report['metrics']['subscribers']
        assert 'window_90days' in report['metrics']['subscribers']
        
        # Verify analyze_historical_trends was called for each metric and window
        assert service.analyze_historical_trends.call_count == 4  # 2 metrics * 2 windows
        
    def test_generate_trend_report_default_metrics(self, mock_db, mock_trend_analyzer):
        """Test generating a trend report with default metrics."""
        service = MetricsTrackingService(db=mock_db)
        service.trend_analyzer = mock_trend_analyzer
        
        # Mock analyze_historical_trends to return analysis results
        service.analyze_historical_trends = MagicMock(return_value={
            'status': 'success',
            'linear_trend': mock_trend_analyzer.calculate_linear_trend.return_value
        })
        
        # Generate report with default metrics for channel
        report = service.generate_trend_report(
            entity_id='UC_test_channel',
            entity_type='channel'
        )
        
        # Verify default metrics for channel were used
        assert 'subscribers' in report['metrics']
        assert 'views' in report['metrics']
        assert 'total_videos' in report['metrics']
        
    def test_generate_trend_report_default_time_windows(self, mock_db, mock_trend_analyzer):
        """Test generating a trend report with default time window."""
        service = MetricsTrackingService(db=mock_db)
        service.trend_analyzer = mock_trend_analyzer
        
        # Mock analyze_historical_trends to return analysis results
        service.analyze_historical_trends = MagicMock(return_value={
            'status': 'success',
            'linear_trend': mock_trend_analyzer.calculate_linear_trend.return_value
        })
        
        # Generate report with default time window
        report = service.generate_trend_report(
            entity_id='UC_test_channel',
            entity_type='channel',
            metrics=['subscribers']
        )
        
        # Verify default time window was used (long_term = 90 days)
        window_key = f"window_{service.default_time_windows['long_term']}days"
        assert window_key in report['metrics']['subscribers']
        
    def test_save_threshold_config(self):
        """Test saving threshold configuration to file."""
        service = MetricsTrackingService()
        
        # Mock the open function and json.dump
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            result = service.save_threshold_config()
            
            # Verify file was opened and json was dumped
            assert result is True
            mock_file.assert_called_once_with(service.config_file_path, 'w')
            mock_json_dump.assert_called_once()
            
    def test_save_threshold_config_exception(self):
        """Test error handling when saving threshold configuration."""
        service = MetricsTrackingService()
        
        # Mock the open function to raise an exception
        with patch('builtins.open', side_effect=Exception("File error")):
            result = service.save_threshold_config()
            assert result is False
            
    def test_load_threshold_config(self):
        """Test loading threshold configuration from file."""
        service = MetricsTrackingService()
        
        # Mock the alert_config.set_all_thresholds method
        service.alert_config.set_all_thresholds = MagicMock(return_value=True)
        
        # Create a sample config to load
        sample_config = {
            'channel': {'subscribers': {'warning': {'type': 'percentage', 'value': 10}}},
            'video': {},
            'comment': {}
        }
        
        # Mock the open function and json.load
        with patch('builtins.open', mock_open()), \
             patch('json.load', return_value=sample_config):
            result = service.load_threshold_config()
            
            # Verify thresholds were loaded
            assert result is True
            service.alert_config.set_all_thresholds.assert_called_once_with(sample_config)
            
    def test_load_threshold_config_file_not_found(self):
        """Test handling of missing configuration file."""
        service = MetricsTrackingService()
        
        # Mock the open function to raise FileNotFoundError
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = service.load_threshold_config()
            assert result is False
            
    def test_load_threshold_config_exception(self):
        """Test error handling when loading configuration."""
        service = MetricsTrackingService()
        
        # Mock the open function and json.load to raise an exception
        with patch('builtins.open', mock_open()), \
             patch('json.load', side_effect=Exception("JSON error")):
            result = service.load_threshold_config()
            assert result is False
            
    def test_get_historical_data(self, mock_db):
        """Test retrieval of historical data."""
        service = MetricsTrackingService(db=mock_db)
        
        data = service._get_historical_data(
            entity_id='UC_test_channel',
            metric_name='subscribers',
            entity_type='channel',
            time_window=90
        )
        
        # Verify the database was queried correctly
        mock_db.get_metric_history.assert_called_once()
        args = mock_db.get_metric_history.call_args[0]
        assert args[0] == 'subscribers'
        assert args[1] == 'UC_test_channel'
        
        # Check that a start_time was provided in the call
        kwargs = mock_db.get_metric_history.call_args[1]
        assert 'start_time' in kwargs
        
        # Verify the returned data
        assert len(data) == 10
        assert isinstance(data[0], dict)
        assert 'timestamp' in data[0]
        assert 'value' in data[0]
        
    def test_get_historical_data_no_db(self):
        """Test handling of missing DB connection."""
        service = MetricsTrackingService(db=None)
        
        data = service._get_historical_data(
            entity_id='UC_test_channel',
            metric_name='subscribers',
            entity_type='channel',
            time_window=90
        )
        
        # Should return empty list when no DB is available
        assert data == []
        
    def test_get_historical_data_exception(self, mock_db):
        """Test error handling during data retrieval."""
        service = MetricsTrackingService(db=mock_db)
        
        # Make the DB raise an exception
        mock_db.get_metric_history.side_effect = Exception("Database error")
        
        data = service._get_historical_data(
            entity_id='UC_test_channel',
            metric_name='subscribers',
            entity_type='channel',
            time_window=90
        )
        
        # Should handle the exception and return an empty list
        assert data == []
        
    def test_check_single_threshold_percentage_increase(self):
        """Test threshold checking for percentage increase."""
        service = MetricsTrackingService()
        
        # Test with value exceeding threshold
        violation = service._check_single_threshold(
            level='warning',
            threshold_type='percentage',
            threshold_value=10.0,
            actual_value=15.0,
            direction='increase',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should detect a violation
        assert violation is not None
        assert violation['threshold_level'] == 'warning'
        assert violation['threshold_value'] == 10.0
        assert violation['current_value'] == 15.0
        assert 'increased by 15.00%' in violation['message']
        
        # Test with value below threshold
        no_violation = service._check_single_threshold(
            level='warning',
            threshold_type='percentage',
            threshold_value=10.0,
            actual_value=5.0,
            direction='increase',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should not detect a violation
        assert no_violation is None
        
    def test_check_single_threshold_percentage_decrease(self):
        """Test threshold checking for percentage decrease."""
        service = MetricsTrackingService()
        
        # Test with value exceeding threshold
        violation = service._check_single_threshold(
            level='warning',
            threshold_type='percentage',
            threshold_value=10.0,
            actual_value=-15.0,
            direction='decrease',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should detect a violation
        assert violation is not None
        assert violation['threshold_level'] == 'warning'
        assert violation['threshold_value'] == 10.0
        assert violation['current_value'] == -15.0
        assert 'decreased by 15.00%' in violation['message']
        
        # Test with value below threshold
        no_violation = service._check_single_threshold(
            level='warning',
            threshold_type='percentage',
            threshold_value=10.0,
            actual_value=-5.0,
            direction='decrease',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should not detect a violation
        assert no_violation is None
        
    def test_check_single_threshold_percentage_both(self):
        """Test threshold checking for percentage in both directions."""
        service = MetricsTrackingService()
        
        # Test with positive value exceeding threshold
        pos_violation = service._check_single_threshold(
            level='warning',
            threshold_type='percentage',
            threshold_value=10.0,
            actual_value=15.0,
            direction='both',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should detect a violation
        assert pos_violation is not None
        assert pos_violation['threshold_level'] == 'warning'
        assert 'increased by 15.00%' in pos_violation['message']
        
        # Test with negative value exceeding threshold
        neg_violation = service._check_single_threshold(
            level='warning',
            threshold_type='percentage',
            threshold_value=10.0,
            actual_value=-15.0,
            direction='both',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should detect a violation
        assert neg_violation is not None
        assert neg_violation['threshold_level'] == 'warning'
        assert 'decreased by 15.00%' in neg_violation['message']
        
        # Test with value below threshold in both directions
        no_violation = service._check_single_threshold(
            level='warning',
            threshold_type='percentage',
            threshold_value=10.0,
            actual_value=5.0,
            direction='both',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should not detect a violation
        assert no_violation is None
        
    def test_check_single_threshold_absolute(self):
        """Test threshold checking for absolute values."""
        service = MetricsTrackingService()
        
        # Test absolute threshold with increasing direction
        abs_violation = service._check_single_threshold(
            level='warning',
            threshold_type='absolute',
            threshold_value=1000,
            actual_value=1500,
            direction='increase',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should detect a violation
        assert abs_violation is not None
        assert abs_violation['threshold_level'] == 'warning'
        assert abs_violation['threshold_value'] == 1000
        assert abs_violation['current_value'] == 1500
        
        # Test absolute threshold with decreasing direction
        abs_decrease_violation = service._check_single_threshold(
            level='warning',
            threshold_type='absolute',
            threshold_value=-500,
            actual_value=-700,
            direction='decrease',
            metric_name='subscribers',
            entity_id='UC_test_channel',
            entity_type='channel',
            window=7
        )
        
        # Should detect a violation
        assert abs_decrease_violation is not None
        assert abs_decrease_violation['threshold_level'] == 'warning'
        assert abs_decrease_violation['threshold_value'] == -500
        assert abs_decrease_violation['current_value'] == -700


if __name__ == '__main__':
    pytest.main()
