"""
Integration tests for edge cases in the data collection process.
Tests handling of unusual channel data, empty channels, and other edge cases.

This file re-exports test classes that have been refactored into separate modules
for better maintainability and organization.
"""
# Import and re-export all test classes from the edge_cases package
from tests.integration.workflow.edge_cases import (
    TestChannelEdgeCases,
    TestVideoEdgeCases,
    TestCommentEdgeCases,
    TestMetadataEdgeCases
)

__all__ = [
    'TestChannelEdgeCases',
    'TestVideoEdgeCases',
    'TestCommentEdgeCases',
    'TestMetadataEdgeCases'
]
