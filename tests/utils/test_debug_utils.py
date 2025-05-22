import pytest
import logging
import time
import streamlit as st
from src.utils.debug_utils import debug_log, log_error, get_ui_freeze_report

@pytest.fixture
def mock_session_state():
    """Fixture to provide a mock session state for testing"""
    class MockSessionState:
        def __init__(self):
            self.debug_mode = False
            self.log_level = logging.WARNING
            self.performance_timers = {}
            self.performance_metrics = {}
            self.ui_freeze_thresholds = {'warning': 1.0}
    
    # Create mock session state
    mock_state = MockSessionState()
    # Set it as the session state
    st.session_state = mock_state
    return mock_state

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
    
    test_data = {"key": "value"}
    debug_log("Test with data", data=test_data)
    assert "Test with data" in caplog.text
    assert "value" in caplog.text

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

def test_log_error_basic(caplog):
    """Test basic error logging"""
    log_error("Test error")
    assert "Test error" in caplog.text

def test_log_error_with_exception(caplog):
    """Test error logging with exception"""
    test_exception = ValueError("Test exception")
    log_error("Test error", error=test_exception)
    assert "Test error" in caplog.text
    assert "Test exception" in caplog.text

def test_get_ui_freeze_report_empty(mock_session_state):
    """Test UI freeze report with no freezes"""
    report = get_ui_freeze_report()
    assert isinstance(report, list)
    assert len(report) == 0

def test_get_ui_freeze_report_with_metrics(mock_session_state):
    """Test UI freeze report with performance metrics"""
    # Add some performance metrics
    mock_session_state.performance_metrics = {
        "test_op_1": {
            "tag": "test_op",
            "duration": 2.5,
            "timestamp": time.time()
        },
        "test_op_2": {
            "tag": "test_op",
            "duration": 0.5,  # Should not be included (below threshold)
            "timestamp": time.time()
        }
    }
    
    report = get_ui_freeze_report()
    assert len(report) == 1
    assert report[0]["tag"] == "test_op"
    assert report[0]["duration"] == 2.5
    assert report[0]["severity"] == "medium"

def test_get_ui_freeze_report_severity_levels(mock_session_state):
    """Test UI freeze report severity levels"""
    # Add metrics with different durations
    mock_session_state.performance_metrics = {
        "low_severity": {
            "tag": "low",
            "duration": 1.5,
            "timestamp": time.time()
        },
        "medium_severity": {
            "tag": "medium",
            "duration": 2.5,
            "timestamp": time.time()
        },
        "high_severity": {
            "tag": "high",
            "duration": 3.5,
            "timestamp": time.time()
        }
    }
    
    report = get_ui_freeze_report()
    assert len(report) == 3
    
    # Check severity levels
    severities = {item["tag"]: item["severity"] for item in report}
    assert severities["low"] == "low"
    assert severities["medium"] == "medium"
    assert severities["high"] == "high"
    
    # Check sorting (should be sorted by duration, descending)
    assert report[0]["duration"] == 3.5
    assert report[1]["duration"] == 2.5
    assert report[2]["duration"] == 1.5 