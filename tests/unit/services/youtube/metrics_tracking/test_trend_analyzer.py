"""
Unit tests for TrendAnalyzer.
Tests the trend analysis functionality for time-series metrics data.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.services.youtube.metrics_tracking.trend_analysis import TrendAnalyzer


class TestTrendAnalyzer:
    """Tests for the TrendAnalyzer class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample time-series data for testing."""
        dates = [datetime.now() - timedelta(days=i) for i in range(10, 0, -1)]
        values = [100, 110, 115, 125, 130, 140, 145, 155, 160, 170]  # Steadily increasing values
        
        df = pd.DataFrame({
            'timestamp': dates,
            'value': values
        })
        return df
        
    @pytest.fixture
    def flat_data(self):
        """Create sample time-series data with flat trend."""
        dates = [datetime.now() - timedelta(days=i) for i in range(10, 0, -1)]
        values = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]  # Flat values
        
        df = pd.DataFrame({
            'timestamp': dates,
            'value': values
        })
        return df
        
    @pytest.fixture
    def decreasing_data(self):
        """Create sample time-series data with decreasing trend."""
        dates = [datetime.now() - timedelta(days=i) for i in range(10, 0, -1)]
        values = [200, 190, 185, 175, 170, 160, 155, 145, 140, 130]  # Steadily decreasing values
        
        df = pd.DataFrame({
            'timestamp': dates,
            'value': values
        })
        return df
        
    @pytest.fixture
    def volatile_data(self):
        """Create sample time-series data with high volatility."""
        dates = [datetime.now() - timedelta(days=i) for i in range(10, 0, -1)]
        # Make volatility even more extreme to ensure anomaly detection
        values = [100, 150, 80, 190, 90, 200, 100, 220, 110, 250]  # Extremely volatile values
        
        df = pd.DataFrame({
            'timestamp': dates,
            'value': values
        })
        return df
    
    def test_initialization(self):
        """Test that TrendAnalyzer initializes correctly with default values."""
        analyzer = TrendAnalyzer()
        
        # Verify default window sizes
        assert 'short' in analyzer.default_window_sizes
        assert 'medium' in analyzer.default_window_sizes
        assert 'long' in analyzer.default_window_sizes
        
        # Verify default growth periods
        assert len(analyzer.default_growth_periods) > 0
        assert 7 in analyzer.default_growth_periods
        assert 30 in analyzer.default_growth_periods
        
    def test_calculate_linear_trend_increasing(self, sample_data):
        """Test calculating linear trend for increasing data."""
        analyzer = TrendAnalyzer()
        result = analyzer.calculate_linear_trend(sample_data)
        
        # Verify the basic structure of the result
        assert 'slope' in result
        assert 'direction' in result
        assert 'r_squared' in result
        assert 'significance' in result
        assert 'forecast' in result
        
        # Verify the trend direction is correct
        assert result['direction'] == 'increasing'
        assert result['slope'] > 0
        
        # Verify R-squared is meaningful
        assert result['r_squared'] > 0.9  # Should be very high for this linear data
        
        # Verify forecast exists and has reasonable values
        assert len(result['forecast']) == 7
        assert all(forecast['value'] >= 170 for forecast in result['forecast'])  # Should be >= last value
        
    def test_calculate_linear_trend_flat(self, flat_data):
        """Test calculating linear trend for flat data."""
        analyzer = TrendAnalyzer()
        result = analyzer.calculate_linear_trend(flat_data)
        
        # Verify the trend direction is stable
        assert result['direction'] == 'stable'
        assert abs(result['slope']) < 0.001
        
    def test_calculate_linear_trend_decreasing(self, decreasing_data):
        """Test calculating linear trend for decreasing data."""
        analyzer = TrendAnalyzer()
        result = analyzer.calculate_linear_trend(decreasing_data)
        
        # Verify the trend direction is correct
        assert result['direction'] == 'decreasing'
        assert result['slope'] < 0
        
        # Verify R-squared is meaningful
        assert result['r_squared'] > 0.9  # Should be very high for this linear data
        
        # Verify forecast exists and has reasonable values
        assert len(result['forecast']) == 7
        assert all(forecast['value'] <= 130 for forecast in result['forecast'])  # Should be <= last value
        
    def test_calculate_linear_trend_insufficient_data(self):
        """Test calculating linear trend with insufficient data."""
        analyzer = TrendAnalyzer()
        
        # Create data with only 2 points
        dates = [datetime.now() - timedelta(days=i) for i in range(2, 0, -1)]
        values = [100, 110]
        df = pd.DataFrame({'timestamp': dates, 'value': values})
        
        # Calculate trend
        result = analyzer.calculate_linear_trend(df)
        
        # Verify default values are returned
        assert result['slope'] == 0.0
        assert result['direction'] == 'stable'
        assert result['r_squared'] == 0.0
        assert result['significance'] == 'none'
        assert len(result['forecast']) == 0
        
    def test_calculate_linear_trend_statsmodels_import_error(self, sample_data):
        """Test fallback behavior when statsmodels is not available."""
        analyzer = TrendAnalyzer()
        
        # Use a module level patch to simulate statsmodels import error
        with patch.dict('sys.modules', {'statsmodels': None}):
            # This will cause import statements for statsmodels in the method to fail
            result = analyzer.calculate_linear_trend(sample_data)
            
            # Verify the trend was still calculated using numpy fallback
            assert result['slope'] > 0
            assert result['direction'] == 'increasing'
            assert result['r_squared'] > 0.9
            assert len(result['forecast']) == 7
            
    def test_calculate_moving_averages(self, sample_data):
        """Test calculating moving averages."""
        analyzer = TrendAnalyzer()
        result = analyzer.calculate_moving_averages(sample_data)
        
        # Verify the basic structure of the result
        assert 'short' in result
        assert 'medium' in result
        
        # Verify the window sizes are correct
        assert result['short']['window_size'] == analyzer.default_window_sizes['short']
        assert result['medium']['window_size'] == analyzer.default_window_sizes['medium']
        
        # Verify the latest moving averages make sense (should be close to recent values)
        assert 150 < result['short']['latest_value'] < 190
        
    def test_calculate_moving_averages_custom_windows(self, sample_data):
        """Test calculating moving averages with custom window sizes."""
        analyzer = TrendAnalyzer()
        custom_windows = {'tiny': 2, 'huge': 8}
        result = analyzer.calculate_moving_averages(sample_data, window_sizes=custom_windows)
        
        # Verify the custom windows were used
        assert 'tiny' in result
        assert 'huge' in result
        assert 'short' not in result  # Default window should not be present
        assert result['tiny']['window_size'] == 2
        assert result['huge']['window_size'] == 8
        
    def test_calculate_moving_averages_insufficient_data(self):
        """Test calculating moving averages with insufficient data."""
        analyzer = TrendAnalyzer()
        
        # Create data with only 1 point
        dates = [datetime.now()]
        values = [100]
        df = pd.DataFrame({'timestamp': dates, 'value': values})
        
        result = analyzer.calculate_moving_averages(df)
        assert result == {}  # Should return empty dict when insufficient data
        
    def test_calculate_growth_rates(self, sample_data):
        """Test calculating growth rates."""
        analyzer = TrendAnalyzer()
        result = analyzer.calculate_growth_rates(sample_data)
        
        # Verify the basic structure of the result
        for period in analyzer.default_growth_periods:
            period_key = f"{period}day"
            if period_key in result:  # Only check if we have enough data for this period
                assert 'absolute' in result[period_key]
                assert 'percentage' in result[period_key]
                
                # For our sample data (steadily increasing), growth should be positive
                assert result[period_key]['absolute'] > 0
                assert result[period_key]['percentage'] > 0
                
    def test_calculate_growth_rates_insufficient_data(self):
        """Test calculating growth rates with insufficient data."""
        analyzer = TrendAnalyzer()
        
        # Create data with only 1 point
        dates = [datetime.now()]
        values = [100]
        df = pd.DataFrame({'timestamp': dates, 'value': values})
        
        result = analyzer.calculate_growth_rates(df)
        assert result == {}  # Should return empty dict when insufficient data
        
    def test_analyze_seasonality(self, sample_data):
        """Test analyzing seasonality patterns."""
        analyzer = TrendAnalyzer()
        
        # Patch the seasonal_decompose function since we need more data for actual seasonality detection
        with patch('statsmodels.tsa.seasonal.seasonal_decompose', 
                  return_value=MagicMock(seasonal=pd.Series([5, -5, 5, -5, 5, -5, 5, -5, 5, -5]))):
            result = analyzer.analyze_seasonality(sample_data)
            
            # Verify the basic structure
            assert 'has_seasonality' in result
            assert 'strength' in result
            assert 'period' in result
            assert 'pattern' in result
            
    def test_analyze_seasonality_insufficient_data(self):
        """Test analyzing seasonality with insufficient data."""
        analyzer = TrendAnalyzer()
        
        # Create data with only 5 points (not enough for seasonality)
        dates = [datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
        values = [100, 110, 100, 110, 100]
        df = pd.DataFrame({'timestamp': dates, 'value': values})
        
        result = analyzer.analyze_seasonality(df)
        assert result['has_seasonality'] is False
        assert result['strength'] == 0.0
        
    def test_detect_anomalies(self, volatile_data):
        """Test detecting anomalies in time-series data."""
        analyzer = TrendAnalyzer()
        result = analyzer.detect_anomalies(volatile_data)
        
        # Verify the basic structure
        assert 'anomalies_detected' in result
        assert 'method' in result
        assert 'threshold' in result
        assert 'data_points' in result
        
        # With our volatile data, we should detect some anomalies
        assert result['anomalies_detected'] > 0
        
        # Check that each anomaly has the required fields
        if result['anomalies_detected'] > 0 and 'points' in result:
            for point in result['points']:
                assert 'timestamp' in point
                assert 'value' in point
                assert 'deviation' in point
                
    def test_detect_anomalies_insufficient_data(self):
        """Test detecting anomalies with insufficient data."""
        analyzer = TrendAnalyzer()
        
        # Create data with only 2 points
        dates = [datetime.now() - timedelta(days=i) for i in range(2, 0, -1)]
        values = [100, 110]
        df = pd.DataFrame({'timestamp': dates, 'value': values})
        
        result = analyzer.detect_anomalies(df)
        assert result['anomalies_detected'] == 0
        assert 'points' not in result
        

if __name__ == '__main__':
    pytest.main()
