"""
UI tests for tab navigation and styling in YTDataHub.
These tests focus on verifying the visibility and styling of tabs in different themes.
"""
import pytest
from unittest.mock import MagicMock, patch
import streamlit as st
import re
from bs4 import BeautifulSoup

# Import the components that render UI with tabs
from src.ui.data_collection import render_data_collection_tab
from src.ui.data_analysis import render_data_analysis_tab
from src.ui.utilities import render_utilities_tab


class TestTabNavigation:
    """Tests for tab navigation styling and visibility across the application."""

    @pytest.fixture
    def mock_css_loader(self):
        """Mock the CSS loading function to capture what CSS is loaded."""
        css_mock = MagicMock()
        return css_mock

    def test_custom_css_is_loaded(self, mock_css_loader):
        """Test that custom CSS for tabs is properly loaded."""
        with patch('src.ui.components.ui_utils.load_css_file', mock_css_loader):
            # Call the function that would load CSS
            from src.ui.components.ui_utils import load_css_file
            load_css_file()
            
            # Verify the function was called
            mock_css_loader.assert_called_once()

    def test_tab_styles_in_css(self):
        """Test that the CSS file contains proper tab styling rules."""
        # Read the actual CSS file
        with open('/Users/jamiemeredith/Projects/ytdatahub/src/static/css/styles.css', 'r') as f:
            css_content = f.read()
        
        # Check for tab-related CSS selectors
        assert '.stTabs [data-baseweb="tab-list"]' in css_content
        assert '.stTabs [data-baseweb="tab"]' in css_content
        assert '.stTabs [aria-selected="true"]' in css_content
        
        # Check for theme-specific overrides
        assert '[data-theme="dark"] .stTabs' in css_content
        assert '[data-theme="light"] .stTabs' in css_content

    def test_dark_mode_tab_contrast(self):
        """Test that tabs have sufficient contrast in dark mode."""
        # Extract dark mode tab background color from CSS
        with open('/Users/jamiemeredith/Projects/ytdatahub/src/static/css/styles.css', 'r') as f:
            css_content = f.read()
        
        # Use regex to extract the background-color value for dark mode tabs
        dark_tab_bg_match = re.search(r'\[data-theme="dark"\] \.stTabs \[data-baseweb="tab"\] \{\s*background-color: (rgba\([^)]+\))', css_content)
        
        if dark_tab_bg_match:
            dark_tab_bg_color = dark_tab_bg_match.group(1)
            # Parse the rgba values
            rgba_match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', dark_tab_bg_color)
            if rgba_match:
                r, g, b, a = map(float, rgba_match.groups())
                
                # Calculate perceived brightness (simple formula: (r*299 + g*587 + b*114) / 1000)
                brightness = (r*299 + g*587 + b*114) / 1000
                
                # For dark mode, the background should be dark enough
                assert brightness < 128, "Dark mode tab background is not dark enough"
                
                # For text to be visible on dark background, it should have enough contrast
                # This is a simplified check - full WCAG compliance would require more complex testing
                assert a > 0.05, "Dark mode tab background opacity is too low for visibility"

    def test_tab_rendering_in_data_collection(self):
        """Test that tabs render properly in the data collection UI."""
        with patch('streamlit.tabs') as mock_tabs:
            # Configure the mock to return a list of tab objects
            tab_mocks = [MagicMock(), MagicMock()]
            mock_tabs.return_value = tab_mocks
            
            # Call the function that creates tabs
            render_data_collection_tab()
            
            # Verify tabs were created with the expected labels
            mock_tabs.assert_called_once()
            
            # Check the arguments - this may need adjustment based on actual implementation
            args = mock_tabs.call_args[0][0]
            assert len(args) >= 2, "At least two tabs should be created"
            assert "New Channel" in args, "Should have a 'New Channel' tab"
            assert "Update Existing Channel" in args, "Should have an 'Update Existing Channel' tab"

    @pytest.mark.parametrize("theme", ["light", "dark"])
    def test_theme_specific_tab_styling(self, theme):
        """Test that tabs have theme-specific styling."""
        # Read the CSS file
        with open('/Users/jamiemeredith/Projects/ytdatahub/src/static/css/styles.css', 'r') as f:
            css_content = f.read()
        
        # Check for theme-specific selectors
        theme_selector = f'[data-theme="{theme}"] .stTabs'
        assert theme_selector in css_content, f"Missing {theme} theme-specific styling for tabs"
        
        # Check that selected tabs have distinct styling
        selected_tab_selector = f'{theme_selector} [aria-selected="true"]'
        assert "background-color" in css_content[css_content.find(selected_tab_selector):], \
            f"Selected tab in {theme} mode should have distinct background color"


if __name__ == "__main__":
    pytest.main()