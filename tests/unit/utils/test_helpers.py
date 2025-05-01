"""
Unit tests for utility functions related to data collection.
"""
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
import logging
from src.utils.helpers import (
    format_number, format_duration, duration_to_seconds, estimate_quota_usage,
    debug_log, get_ui_freeze_report
)


class TestDataHelperFunctions:
    """Tests for helper functions used in data collection and analysis"""
    
    def test_format_number(self):
        """Test number formatting function"""
        assert format_number(1000) == "1K"
        assert format_number(1500) == "1.5K"
        assert format_number(1000000) == "1M"
        assert format_number(1500000) == "1.5M"
        assert format_number(1000000000) == "1B"
        assert format_number(0) == "0"
        assert format_number(None) == "0"
        assert format_number("50000") == "50K"  # String input
    
    def test_format_duration(self):
        """Test YouTube duration formatting"""
        assert format_duration("PT1H30M20S") == "1:30:20"
        assert format_duration("PT30M20S") == "30:20"
        assert format_duration("PT20S") == "0:20"
        assert format_duration("PT1H") == "1:00:00"
        assert format_duration("PT1H20S") == "1:00:20"
        assert format_duration("") == "0:00"
        assert format_duration(None) == "0:00"
    
    def test_duration_to_seconds(self):
        """Test conversion of YouTube duration to seconds"""
        assert duration_to_seconds("PT1H30M20S") == 5420  # 1h 30m 20s = 5420s
        assert duration_to_seconds("PT30M20S") == 1820    # 30m 20s = 1820s
        assert duration_to_seconds("PT20S") == 20         # 20s = 20s
        assert duration_to_seconds("PT1H") == 3600        # 1h = 3600s
        assert duration_to_seconds("") == 0
        assert duration_to_seconds(None) == 0
    
    def test_estimate_quota_usage(self):
        """Test YouTube API quota usage estimation"""
        # Test base cases
        assert estimate_quota_usage(fetch_channel=True, fetch_videos=False, fetch_comments=False, video_count=0, comments_count=0) == 1
        
        # Test video-only quota
        assert estimate_quota_usage(fetch_channel=False, fetch_videos=True, fetch_comments=False, video_count=10, comments_count=0) >= 10
        
        # Test comment quota
        assert estimate_quota_usage(fetch_channel=False, fetch_videos=False, fetch_comments=True, video_count=5, comments_count=10) >= 5
        
        # Test combined quota
        full_quota = estimate_quota_usage(fetch_channel=True, fetch_videos=True, fetch_comments=True, 
                                          video_count=50, comments_count=10)
        assert full_quota > 50  # Should be significantly more than just video count


class TestQueueManagement:
    """Tests for background task queue management"""
    
    @patch('src.utils.background_tasks.st.session_state.background_task_queue.put')
    @patch('src.utils.background_tasks.ensure_worker_thread_running')
    def test_queue_data_collection_task(self, mock_ensure_worker, mock_queue_put):
        """Test queuing a data collection task"""
        from src.utils.background_tasks import queue_data_collection_task
        
        # Test queueing a task
        channel_id = 'UC_test_channel'
        api_key = 'test_api_key'
        options = {
            'max_videos': 50,
            'max_comments_per_video': 10
        }
        
        task_id = queue_data_collection_task(channel_id, api_key, options)
        
        # Verify task was properly queued
        assert task_id is not None
        mock_queue_put.assert_called_once()
        mock_ensure_worker.assert_called_once()
        
        # Check correct data was added to the queue
        call_args = mock_queue_put.call_args[0][0]
        assert call_args['channel_id'] == channel_id
        assert call_args['api_key'] == api_key
        assert call_args['options'] == options


class TestDebugLogging:
    """Tests for debug logging functionality"""
    
    @patch('src.utils.helpers.st.session_state')
    @patch('src.utils.helpers.logging.debug')
    def test_debug_log_basic(self, mock_logging_debug, mock_session_state):
        """Test basic debug log function behavior"""
        # Setup session state with debug mode enabled
        mock_session_state.debug_mode = True
        mock_session_state.log_level = logging.DEBUG
        
        # Test simple debug log
        debug_log("Test debug message")
        mock_logging_debug.assert_called_once()
    
    @patch('src.utils.helpers.st.session_state')
    @patch('src.utils.helpers.logging.debug')
    def test_debug_log_disabled(self, mock_logging_debug, mock_session_state):
        """Test debug log function when debug mode is disabled"""
        # Setup session state with debug mode disabled
        mock_session_state.debug_mode = False
        mock_session_state.log_level = logging.WARNING
        
        # Test debug log won't output with debug mode off
        debug_log("Test debug message")
        mock_logging_debug.assert_not_called()
    
    @patch('src.utils.helpers.st.session_state')
    @patch('src.utils.helpers.logging.debug')
    @patch('src.utils.helpers.logging.warning')
    def test_performance_timing_start(self, mock_logging_warning, mock_logging_debug, mock_session_state):
        """Test performance timing start"""
        # Setup session state
        mock_session_state.debug_mode = True
        mock_session_state.log_level = logging.DEBUG
        mock_session_state.performance_timers = {}
        
        # Start a performance timer
        debug_log("Starting operation", performance_tag="start_test_operation")
        
        # Verify timer was started
        assert "test_operation" in mock_session_state.performance_timers
        mock_logging_debug.assert_called_once()
    
    @patch('src.utils.helpers.st.session_state')
    @patch('src.utils.helpers.logging.debug')
    @patch('src.utils.helpers.logging.warning')
    @patch('src.utils.helpers.time.time')
    def test_performance_timing_end(self, mock_time, mock_logging_warning, mock_logging_debug, mock_session_state):
        """Test performance timing end"""
        # Setup session state
        mock_session_state.debug_mode = True
        mock_session_state.log_level = logging.DEBUG
        mock_session_state.performance_timers = {"test_operation": 1000.0}  # Start time
        mock_session_state.performance_metrics = {}
        mock_session_state.ui_freeze_thresholds = {
            'warning': 1.0,
            'critical': 3.0,
            'ui_blocking': 0.5
        }
        
        # Setup time mock to simulate 2 seconds elapsed
        mock_time.return_value = 1002.0
        
        # End the timer
        debug_log("Completed operation", performance_tag="end_test_operation")
        
        # Verify performance metrics were recorded
        assert len(mock_session_state.performance_metrics) == 1
        
        # Check the timer was removed after use
        assert "test_operation" not in mock_session_state.performance_timers
        
        # Verify warning was logged for operations that exceed warning threshold
        mock_logging_warning.assert_called_once()
    
    @patch('src.utils.helpers.st.session_state')
    def test_get_ui_freeze_report(self, mock_session_state):
        """Test UI freeze report generation"""
        # Setup mock data
        mock_session_state.ui_timing_metrics = [
            {
                'operation': 'test_operation_1',
                'duration': 2.5,
                'timestamp': 1000.0,
                'severity': 'warning'
            },
            {
                'operation': 'test_operation_2',
                'duration': 4.2,
                'timestamp': 1010.0,
                'severity': 'critical'
            }
        ]
        
        # Get the report
        report = get_ui_freeze_report()
        
        # Verify report has expected content
        assert report is not None
        assert len(report) == 2
        assert 'Operation' in report.columns
        assert 'Duration' in report.columns
        assert 'Severity' in report.columns


if __name__ == '__main__':
    pytest.main()