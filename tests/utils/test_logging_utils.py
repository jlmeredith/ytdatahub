import pytest
import logging
import time
import streamlit as st
import pandas as pd
from src.utils.logging_utils import (
    initialize_performance_tracking,
    debug_log,
    get_ui_freeze_report
)

@pytest.fixture
def mock_session_state():
    """Fixture to provide a mock session state for testing"""
    class MockSessionState:
        def __init__(self):
            self.debug_mode = False
            self.log_level = logging.WARNING
            self.performance_timers = {}
            self.performance_metrics = {}
            self.ui_freeze_thresholds = {
                'warning': 1.0,
                'critical': 3.0,
                'ui_blocking': 0.5
            }
    
    # Create mock session state
    mock_state = MockSessionState()
    # Set it as the session state
    st.session_state = mock_state
    return mock_state

def test_initialize_performance_tracking(mock_session_state):
    """Test initialization of performance tracking"""
    # Clear existing state
    mock_session_state.performance_timers = None
    mock_session_state.performance_metrics = None
    mock_session_state.ui_freeze_thresholds = None
    
    # Initialize
    initialize_performance_tracking()
    
    # Check that all required attributes are initialized
    assert isinstance(mock_session_state.performance_timers, dict)
    assert isinstance(mock_session_state.performance_metrics, dict)
    assert isinstance(mock_session_state.ui_freeze_thresholds, dict)
    assert mock_session_state.ui_freeze_thresholds['warning'] == 1.0
    assert mock_session_state.ui_freeze_thresholds['critical'] == 3.0
    assert mock_session_state.ui_freeze_thresholds['ui_blocking'] == 0.5

def test_debug_log_basic(mock_session_state, caplog):
    """Test basic debug logging functionality"""
    # Test with debug mode off
    debug_log("Test message")
    assert "Test message" not in caplog.text
    
    # Test with debug mode on
    mock_session_state.debug_mode = True
    mock_session_state.log_level = logging.DEBUG
    debug_log("Debug message")
    assert "Debug message" in caplog.text

def test_debug_log_with_data(mock_session_state, caplog):
    """Test debug logging with data"""
    mock_session_state.debug_mode = True
    mock_session_state.log_level = logging.DEBUG
    
    # Test with dictionary data
    test_data = {"key": "value"}
    debug_log("Test with dict", data=test_data)
    assert "Test with dict" in caplog.text
    assert "value" in caplog.text
    
    # Test with list data
    test_list = [1, 2, 3]
    debug_log("Test with list", data=test_list)
    assert "Test with list" in caplog.text
    assert "1" in caplog.text
    assert "2" in caplog.text
    assert "3" in caplog.text

def test_debug_log_performance_tracking(mock_session_state, caplog):
    """Test performance tracking functionality"""
    mock_session_state.debug_mode = True
    mock_session_state.log_level = logging.DEBUG
    
    # Start timer
    debug_log("Starting operation", performance_tag="start_test_op")
    assert "START TIMER [test_op]" in caplog.text
    
    # End timer
    time.sleep(0.1)  # Small delay to ensure measurable time
    debug_log("Ending operation", performance_tag="end_test_op")
    assert "END TIMER [test_op]" in caplog.text
    assert "took" in caplog.text

def test_debug_log_performance_severity(mock_session_state, caplog):
    """Test performance severity levels"""
    mock_session_state.debug_mode = True
    mock_session_state.log_level = logging.DEBUG
    
    # Test critical performance
    debug_log("Start critical", performance_tag="start_critical")
    time.sleep(3.1)  # Exceed critical threshold
    debug_log("End critical", performance_tag="end_critical")
    assert "CRITICAL PERFORMANCE ISSUE" in caplog.text
    
    # Test warning performance
    debug_log("Start warning", performance_tag="start_warning")
    time.sleep(1.1)  # Exceed warning threshold
    debug_log("End warning", performance_tag="end_warning")
    assert "PERFORMANCE WARNING" in caplog.text
    
    # Test good performance
    debug_log("Start good", performance_tag="start_good")
    time.sleep(0.1)  # Below warning threshold
    debug_log("End good", performance_tag="end_good")
    assert "CRITICAL" not in caplog.text
    assert "WARNING" not in caplog.text

def test_get_ui_freeze_report_empty(mock_session_state):
    """Test UI freeze report with no freezes"""
    report = get_ui_freeze_report()
    assert isinstance(report, pd.DataFrame)
    assert len(report) == 0

def test_get_ui_freeze_report_with_metrics(mock_session_state):
    """Test UI freeze report with performance metrics"""
    # Add some performance metrics
    mock_session_state.performance_metrics = {
        "test_op_1": {
            "tag": "test_op",
            "duration": 2.5,
            "timestamp": time.time(),
            "message": "Test operation",
            "indicator": "🟠",
            "ui_impact": True,
            "severity": "warning"
        },
        "test_op_2": {
            "tag": "test_op",
            "duration": 0.5,  # Should not be included (below threshold)
            "timestamp": time.time(),
            "message": "Test operation",
            "indicator": "🟢",
            "ui_impact": False,
            "severity": "good"
        }
    }
    
    report = get_ui_freeze_report()
    assert isinstance(report, pd.DataFrame)
    assert len(report) == 1
    assert report.iloc[0]['operation'] == "test_op"
    assert report.iloc[0]['Duration'] == 2.5
    assert report.iloc[0]['severity'] == "warning"

def test_get_ui_freeze_report_severity_levels(mock_session_state):
    """Test UI freeze report severity levels"""
    # Add metrics with different durations
    mock_session_state.performance_metrics = {
        "low_severity": {
            "tag": "low",
            "duration": 1.5,
            "timestamp": time.time(),
            "message": "Low severity",
            "indicator": "🟠",
            "ui_impact": True,
            "severity": "warning"
        },
        "medium_severity": {
            "tag": "medium",
            "duration": 2.5,
            "timestamp": time.time(),
            "message": "Medium severity",
            "indicator": "🟠",
            "ui_impact": True,
            "severity": "warning"
        },
        "high_severity": {
            "tag": "high",
            "duration": 3.5,
            "timestamp": time.time(),
            "message": "High severity",
            "indicator": "🔴",
            "ui_impact": True,
            "severity": "critical"
        }
    }
    
    report = get_ui_freeze_report()
    assert len(report) == 3
    
    # Check severity levels
    severities = dict(zip(report['operation'], report['severity']))
    assert severities["low"] == "warning"
    assert severities["medium"] == "warning"
    assert severities["high"] == "critical"
    
    # Check sorting (should be sorted by duration, descending)
    assert report.iloc[0]['Duration'] == 3.5
    assert report.iloc[1]['Duration'] == 2.5
    assert report.iloc[2]['Duration'] == 1.5 