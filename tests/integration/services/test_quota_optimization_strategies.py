# filepath: /Users/jamiemeredith/Projects/ytdatahub/tests/integration/services/test_quota_optimization_strategies.py
"""
Integration tests for YouTube API quota optimization strategies.
Tests the application's ability to implement various quota optimization strategies
such as batch requests, prioritization, caching, adaptive polling and quota budgeting.

This file re-exports test classes that have been refactored into separate modules
for better maintainability and organization.
"""
# Import and re-export all test classes from the quota_optimization package
from .quota_optimization import (
    BaseQuotaOptimizationTest,
    TestBatchRequestStrategy,
    TestResourcePrioritization,
    TestCachingStrategy,
    TestAdaptivePollingStrategy,
    TestQuotaBudgetingStrategy
)

__all__ = [
    'BaseQuotaOptimizationTest',
    'TestBatchRequestStrategy',
    'TestResourcePrioritization',
    'TestCachingStrategy',
    'TestAdaptivePollingStrategy',
    'TestQuotaBudgetingStrategy'
]
