"""
UI module for YTDataHub application.
This package contains all UI-related modules.
"""

# Export the UI rendering functions for use in the application
# Import directly from the modern implementations instead of legacy wrappers
from src.ui.data_collection.main import render_data_collection_tab
from src.ui.data_analysis.main import render_data_analysis_tab
from src.ui.utilities import render_utilities_tab
from src.ui.bulk_import.render import render_bulk_import_tab