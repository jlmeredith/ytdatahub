"""
Integration tests for the data collection and update workflow.
Tests the complete end-to-end flow from API to storage.

NOTE: This file has been refactored into smaller components:
- Base test case: ../fixtures/base_youtube_test_case.py
- Data collection workflow: test_data_collection_workflow_steps.py
- Slider and quota management: test_slider_quota_management.py
- Queue management: test_queue_management.py
- Delta reporting: test_delta_reporting.py
- End-to-end workflow: test_end_to_end_workflow.py
- API vs DB comparison: test_api_db_comparison_view.py

This file now serves as a pointer and aggregator for backward compatibility.
"""
import pytest
import os
from unittest.mock import MagicMock, patch
import logging

# Import the necessary resources from the service
from src.services.youtube_service import YouTubeService
from src.storage.factory import StorageFactory
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from src.utils.queue_tracker import add_to_queue, remove_from_queue, set_test_mode
from src.utils.queue_tracker import set_queue_hooks, clear_queue_hooks
from src.utils.helpers import debug_log

# Import the base test case and test classes from their new locations
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase
from tests.integration.test_data_collection_workflow_steps import TestDataCollectionWorkflow
from tests.integration.test_slider_quota_management import TestSliderAndQuotaManagement
from tests.integration.test_queue_management import TestQueueManagement 
from tests.integration.test_delta_reporting import TestDeltaReporting
from tests.integration.test_end_to_end_workflow import TestEndToEndWorkflow
from tests.integration.test_api_db_comparison_view import TestApiDbComparisonView

# This file is now just a stub that imports all the tests from their new locations
# The actual test classes are maintained in their respective files

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
