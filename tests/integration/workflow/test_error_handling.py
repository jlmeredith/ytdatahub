"""
Integration tests focusing on error handling and recovery during data collection.
Tests how the application handles API failures, partial collections, and quota issues.

This file re-exports test classes that have been refactored into separate modules
for better maintainability and organization.
"""
# Import and re-export all test classes from the error_handling package
from .error_handling import (
    TestApiErrorHandling,
    TestConnectionErrorHandling,
    TestQuotaErrorHandling,
    TestDataIntegrityErrorHandling,
    TestRetryMechanisms,
    TestRecoveryStrategies
)

__all__ = [
    'TestApiErrorHandling',
    'TestConnectionErrorHandling',
    'TestQuotaErrorHandling',
    'TestDataIntegrityErrorHandling',
    'TestRetryMechanisms',
    'TestRecoveryStrategies'
]
