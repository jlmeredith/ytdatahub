"""
UI components for the Bulk Import tab.
This module handles CSV imports of channel IDs and API data fetching.
"""

# Re-export the render_bulk_import_tab function from the render module
from src.ui.bulk_import.render import render_bulk_import_tab

# Global variables to control the import process - retained for backward compatibility
IMPORT_RUNNING = False
IMPORT_SHOULD_STOP = False
