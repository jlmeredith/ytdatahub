"""
Integration tests for YouTube API quota optimization.
Tests the application's ability to efficiently use the YouTube API quota.

NOTE: This file has been refactored into smaller components:
- Quota Estimation: test_quota_estimation.py
- Optimization Techniques: test_optimization_techniques.py
- Quota Optimization Strategies: test_quota_optimization_strategies.py
"""
import pytest
from unittest.mock import MagicMock, patch, call
import logging
import time
import googleapiclient.errors

from src.services.youtube_service import YouTubeService
from src.api.youtube_api import YouTubeAPI
from src.database.sqlite import SQLiteDatabase
from tests.fixtures.base_youtube_test_case import BaseYouTubeTestCase
from tests.integration.services.test_quota_estimation import TestQuotaEstimation
from tests.integration.workflow.test_optimization_techniques import TestOptimizationTechniques
from tests.integration.services.test_quota_optimization_strategies import BaseQuotaOptimizationTest


# The TestQuotaEstimation class has been moved to test_quota_estimation.py
# The TestOptimizationTechniques class has been moved to test_optimization_techniques.py
# The TestQuotaOptimizationStrategies class has been moved to test_quota_optimization_strategies.py


if __name__ == '__main__':
    pytest.main()
