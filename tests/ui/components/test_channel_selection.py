"""
Tests for channel selection and data loading workflow in the data collection UI.
This file has been refactored into multiple smaller files:
- test_data_conversion.py: Tests for data conversion functionality
- test_channel_selection_ui.py: Tests for channel selection UI
- test_channel_refresh.py: Tests for channel refresh functionality
- test_comparison_view.py: Tests for comparison view functionality

This file now re-exports the tests from the new files for backward compatibility.
"""

# Import pytest for backward compatibility
import pytest
from unittest.mock import MagicMock

# Import all the classes from the refactored files
from tests.ui.pages.test_data_conversion import TestDataConversion
from tests.ui.pages.test_channel_selection_ui import TestChannelSelectionUI
from tests.ui.pages.test_channel_refresh import TestChannelRefresh
from tests.ui.pages.test_comparison_view import TestComparisonView

# For backward compatibility, also define the original class name
class TestChannelSelectionWorkflow(TestChannelSelectionUI):
    """
    For backward compatibility - points to TestChannelSelectionUI
    See the refactored files for the implementation details.
    """
    pass

