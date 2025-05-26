"""
Main test file for running all metrics tracking service tests.
"""
import pytest

# Import all tests
from tests.unit.services.youtube.metrics_tracking.test_alert_threshold_config import TestAlertThresholdConfig
from tests.unit.services.youtube.metrics_tracking.test_trend_analyzer import TestTrendAnalyzer
from tests.unit.services.youtube.metrics_tracking.test_metrics_tracking_service import TestMetricsTrackingService
from tests.unit.services.youtube.metrics_tracking.test_metrics_delta_integration import TestMetricsDeltaIntegration

if __name__ == '__main__':
    pytest.main(['-v'])
