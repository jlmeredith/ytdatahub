"""
Unit tests for MetricsDeltaIntegration.
Tests the integration between metrics tracking and delta calculation.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.services.youtube.metrics_tracking.metrics_delta_integration import MetricsDeltaIntegration
from src.services.youtube.delta_service import DeltaService
from src.services.youtube.metrics_tracking.metrics_tracking_service import MetricsTrackingService


class TestMetricsDeltaIntegration:
    """Tests for the MetricsDeltaIntegration class."""
    
    @pytest.fixture
    def mock_delta_service(self):
        """Create a mock DeltaService for testing."""
        mock = MagicMock(spec=DeltaService)
        
        # Mock calculate_deltas method to return the channel data with deltas
        mock.calculate_deltas.return_value = {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '12000',
            'views': '5500000',
            'total_videos': '255',
            'delta': {
                'subscribers': {
                    'old': 10000,
                    'new': 12000,
                    'diff': 2000
                },
                'views': {
                    'old': 5000000,
                    'new': 5500000,
                    'diff': 500000
                },
                'total_videos': {
                    'old': 250,
                    'new': 255,
                    'diff': 5
                }
            }
        }
        
        return mock
        
    @pytest.fixture
    def mock_metrics_service(self):
        """Create a mock MetricsTrackingService for testing."""
        mock = MagicMock(spec=MetricsTrackingService)
        
        # Mock analyze_historical_trends method to return trend analysis data
        mock.analyze_historical_trends.return_value = {
            'entity_id': 'UC_test_channel',
            'entity_type': 'channel',
            'metric_name': 'subscribers',
            'status': 'success',
            'data_points': 10,
            'current_value': 12000,
            'linear_trend': {
                'slope': 200.0,
                'direction': 'increasing',
                'r_squared': 0.95,
                'significance': 'high',
                'forecast': []
            },
            'growth_rate': {
                '7day': {
                    'absolute': 1000,
                    'percentage': 10.0,
                    'start_value': 10000,
                    'end_value': 11000
                },
                '30day': {
                    'absolute': 2000,
                    'percentage': 20.0,
                    'start_value': 10000,
                    'end_value': 12000
                }
            }
        }
        
        # Mock check_threshold_violations method to return violations
        mock.check_threshold_violations.return_value = [{
            'threshold_level': 'warning',
            'threshold_value': 15,
            'threshold_type': 'percentage',
            'current_value': 20.0,
            'direction': 'increase',
            'window_days': 30,
            'message': '[WARNING] subscribers for channel UC_test_channel has increased by 20.00% in the last 30 days, exceeding the warning threshold of 15%'
        }]
        
        return mock
        
    @pytest.fixture
    def sample_channel_data(self):
        """Create sample channel data for testing."""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '12000',
            'views': '5500000',
            'total_videos': '255',
            'timestamp': datetime.now().isoformat()
        }
        
    @pytest.fixture
    def sample_original_data(self):
        """Create sample original channel data for testing."""
        return {
            'channel_id': 'UC_test_channel',
            'channel_name': 'Test Channel',
            'subscribers': '10000',
            'views': '5000000',
            'total_videos': '250',
            'timestamp': (datetime.now() - timedelta(days=30)).isoformat()
        }
    
    def test_initialization(self, mock_delta_service, mock_metrics_service):
        """Test that MetricsDeltaIntegration initializes correctly with provided services."""
        integration = MetricsDeltaIntegration(
            delta_service=mock_delta_service,
            metrics_service=mock_metrics_service
        )
        
        # Verify service attributes
        assert integration.delta_service == mock_delta_service
        assert integration.metrics_service == mock_metrics_service
        
    def test_initialization_default_services(self):
        """Test that MetricsDeltaIntegration creates services when not provided."""
        with patch('src.services.youtube.metrics_tracking.metrics_delta_integration.DeltaService') as mock_delta_class, \
             patch('src.services.youtube.metrics_tracking.metrics_delta_integration.MetricsTrackingService') as mock_metrics_class:
            
            # Create mock instances
            mock_delta_instance = MagicMock()
            mock_metrics_instance = MagicMock()
            
            # Configure mocks to return instances
            mock_delta_class.return_value = mock_delta_instance
            mock_metrics_class.return_value = mock_metrics_instance
            
            # Initialize with default services
            integration = MetricsDeltaIntegration()
            
            # Verify services were created
            assert mock_delta_class.called
            assert mock_metrics_class.called
            assert integration.delta_service == mock_delta_instance
            assert integration.metrics_service == mock_metrics_instance
            
    def test_process_delta_with_trend_analysis(self, mock_delta_service, mock_metrics_service, 
                                             sample_channel_data, sample_original_data):
        """Test processing delta with trend analysis."""
        integration = MetricsDeltaIntegration(
            delta_service=mock_delta_service,
            metrics_service=mock_metrics_service
        )
        
        # Process deltas with trend analysis
        result = integration.process_delta_with_trend_analysis(
            channel_data=sample_channel_data,
            original_data=sample_original_data,
            options={'include_trend_metrics': True, 'trend_time_window': 90}
        )
        
        # Verify delta calculation was performed
        mock_delta_service.calculate_deltas.assert_called_once_with(
            sample_channel_data, sample_original_data, {'include_trend_metrics': True, 'trend_time_window': 90}
        )
        
        # Verify trend analysis was performed for each metric
        assert mock_metrics_service.analyze_historical_trends.call_count >= 3  # For subscribers, views, total_videos
        
        # Verify result contains trend analysis
        assert 'trend_analysis' in result
        
    def test_process_delta_without_trend_metrics(self, mock_delta_service, mock_metrics_service,
                                               sample_channel_data, sample_original_data):
        """Test processing delta without trend analysis."""
        integration = MetricsDeltaIntegration(
            delta_service=mock_delta_service,
            metrics_service=mock_metrics_service
        )
        
        # Process deltas without trend analysis
        result = integration.process_delta_with_trend_analysis(
            channel_data=sample_channel_data,
            original_data=sample_original_data,
            options={'include_trend_metrics': False}
        )
        
        # Verify delta calculation was performed
        mock_delta_service.calculate_deltas.assert_called_once_with(
            sample_channel_data, sample_original_data, {'include_trend_metrics': False}
        )
        
        # Verify trend analysis was not performed
        mock_metrics_service.analyze_historical_trends.assert_not_called()
        
        # Verify result does not contain trend analysis
        assert 'trend_analysis' not in result
        
    def test_process_delta_without_channel_id(self, mock_delta_service, mock_metrics_service):
        """Test processing delta without channel ID."""
        integration = MetricsDeltaIntegration(
            delta_service=mock_delta_service,
            metrics_service=mock_metrics_service
        )
        
        # Create data without channel_id
        invalid_data = {'views': '5500000'}
        
        # Process deltas with invalid data
        result = integration.process_delta_with_trend_analysis(
            channel_data=invalid_data,
            original_data={},
            options={}
        )
        
        # Verify delta calculation was performed
        mock_delta_service.calculate_deltas.assert_called_once()
        
        # Verify trend analysis was not performed
        mock_metrics_service.analyze_historical_trends.assert_not_called()
        
    def test_process_delta_with_analysis_errors(self, mock_delta_service, mock_metrics_service,
                                              sample_channel_data, sample_original_data):
        """Test handling of analysis errors during delta processing."""
        integration = MetricsDeltaIntegration(
            delta_service=mock_delta_service,
            metrics_service=mock_metrics_service
        )
        
        # Make analyze_historical_trends raise an exception
        mock_metrics_service.analyze_historical_trends.side_effect = Exception("Analysis error")
        
        # Process deltas with trend analysis
        result = integration.process_delta_with_trend_analysis(
            channel_data=sample_channel_data,
            original_data=sample_original_data,
            options={}
        )
        
        # Verify delta calculation was performed
        mock_delta_service.calculate_deltas.assert_called_once()
        
        # Verify trend analysis was attempted
        mock_metrics_service.analyze_historical_trends.assert_called()
        
        # Verify result still has delta data but may have empty trend analysis
        assert result == mock_delta_service.calculate_deltas.return_value
        
    def test_enhance_delta_report_with_trends(self, mock_metrics_service):
        """Test enhancing an existing delta report with trend analysis."""
        integration = MetricsDeltaIntegration(
            metrics_service=mock_metrics_service
        )
        
        # Create a sample delta report
        delta_report = {
            'channel_id': 'UC_test_channel',
            'delta': {
                'subscribers': {'old': 10000, 'new': 12000, 'diff': 2000},
                'views': {'old': 5000000, 'new': 5500000, 'diff': 500000}
            }
        }
        
        # Enhance the report with trend analysis
        result = integration.enhance_delta_report_with_trends(delta_report)
        
        # Verify trend analysis was performed for each metric in delta
        assert mock_metrics_service.analyze_historical_trends.call_count >= 2  # For subscribers and views
        
        # Verify result contains trend analysis
        assert 'trend_analysis' in result
        
    def test_enhance_delta_report_with_trends_invalid_report(self, mock_metrics_service):
        """Test enhancing an invalid delta report."""
        integration = MetricsDeltaIntegration(
            metrics_service=mock_metrics_service
        )
        
        # Create an invalid delta report (no delta key)
        invalid_report = {'channel_id': 'UC_test_channel'}
        
        # Attempt to enhance the report
        result = integration.enhance_delta_report_with_trends(invalid_report)
        
        # Verify no trend analysis was performed
        mock_metrics_service.analyze_historical_trends.assert_not_called()
        
        # Verify the original report is returned unchanged
        assert result == invalid_report
        
    def test_enhance_delta_report_without_channel_id(self, mock_metrics_service):
        """Test enhancing a delta report without channel ID."""
        integration = MetricsDeltaIntegration(
            metrics_service=mock_metrics_service
        )
        
        # Create a delta report without channel_id
        invalid_report = {
            'delta': {
                'subscribers': {'old': 10000, 'new': 12000, 'diff': 2000}
            }
        }
        
        # Attempt to enhance the report
        result = integration.enhance_delta_report_with_trends(invalid_report)
        
        # Verify no trend analysis was performed
        mock_metrics_service.analyze_historical_trends.assert_not_called()
        
        # Verify the original report is returned unchanged
        assert result == invalid_report
        
    def test_enhance_delta_report_with_no_changes(self, mock_metrics_service):
        """Test enhancing a delta report with no metric changes."""
        integration = MetricsDeltaIntegration(
            metrics_service=mock_metrics_service
        )
        
        # Create a delta report without relevant metric changes
        delta_report = {
            'channel_id': 'UC_test_channel',
            'delta': {
                'channel_name': {'old': 'Old Name', 'new': 'New Name'}
            }
        }
        
        # Attempt to enhance the report
        result = integration.enhance_delta_report_with_trends(delta_report)
        
        # Verify no trend analysis was performed
        mock_metrics_service.analyze_historical_trends.assert_not_called()
        
        # Verify the original report is returned unchanged
        assert result == delta_report
        
    def test_enhance_delta_report_with_analysis_error(self, mock_metrics_service):
        """Test handling of analysis errors during delta report enhancement."""
        integration = MetricsDeltaIntegration(
            metrics_service=mock_metrics_service
        )
        
        # Create a sample delta report
        delta_report = {
            'channel_id': 'UC_test_channel',
            'delta': {
                'subscribers': {'old': 10000, 'new': 12000, 'diff': 2000}
            }
        }
        
        # Make analyze_historical_trends raise an exception
        mock_metrics_service.analyze_historical_trends.side_effect = Exception("Analysis error")
        
        # Attempt to enhance the report
        result = integration.enhance_delta_report_with_trends(delta_report)
        
        # Verify trend analysis was attempted
        mock_metrics_service.analyze_historical_trends.assert_called()
        
        # Verify the report has trend_analysis key but might be empty
        assert result['channel_id'] == 'UC_test_channel'
        assert 'trend_analysis' in result
        assert len(result['trend_analysis']) == 0  # Should be empty due to error
        
    def test_check_for_threshold_violations(self, mock_delta_service, mock_metrics_service):
        """Test checking for threshold violations in channel data."""
        integration = MetricsDeltaIntegration(
            delta_service=mock_delta_service,
            metrics_service=mock_metrics_service
        )
        
        # Create channel data with trend analysis
        channel_data = {
            'channel_id': 'UC_test_channel',
            'trend_analysis': {
                'subscribers': {
                    'entity_id': 'UC_test_channel',
                    'metric_name': 'subscribers',
                    'status': 'success'
                },
                'views': {
                    'entity_id': 'UC_test_channel',
                    'metric_name': 'views',
                    'status': 'success'
                }
            }
        }
        
        # Check for violations
        integration._check_for_threshold_violations(channel_data)
        
        # Verify check_threshold_violations was called for each metric
        assert mock_metrics_service.check_threshold_violations.call_count == 2  # For subscribers and views
        
        # Verify threshold violations were added to the channel data
        assert channel_data['has_threshold_violations'] is True
        
    def test_check_for_threshold_violations_no_trend_analysis(self, mock_metrics_service):
        """Test checking for threshold violations without trend analysis."""
        integration = MetricsDeltaIntegration(
            metrics_service=mock_metrics_service
        )
        
        # Create channel data without trend analysis
        channel_data = {
            'channel_id': 'UC_test_channel'
        }
        
        # Check for violations
        integration._check_for_threshold_violations(channel_data)
        
        # Verify check_threshold_violations was not called
        mock_metrics_service.check_threshold_violations.assert_not_called()
        
    def test_check_for_threshold_violations_no_violations(self, mock_metrics_service):
        """Test checking for threshold violations when none are found."""
        integration = MetricsDeltaIntegration(
            metrics_service=mock_metrics_service
        )
        
        # Configure mock to return no violations
        mock_metrics_service.check_threshold_violations.return_value = []
        
        # Create channel data with trend analysis
        channel_data = {
            'channel_id': 'UC_test_channel',
            'trend_analysis': {
                'subscribers': {
                    'entity_id': 'UC_test_channel',
                    'metric_name': 'subscribers',
                    'status': 'success'
                }
            }
        }
        
        # Check for violations
        integration._check_for_threshold_violations(channel_data)
        
        # Verify check_threshold_violations was called
        mock_metrics_service.check_threshold_violations.assert_called_once()
        
        # Verify no violation flag was added
        assert 'has_threshold_violations' not in channel_data


if __name__ == '__main__':
    pytest.main()
