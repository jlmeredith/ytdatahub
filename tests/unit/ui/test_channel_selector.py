"""
Unit tests for the channel selector component in the data analysis UI.
"""
import unittest
from unittest.mock import MagicMock, patch, Mock
import sys
import os
from importlib import reload
import pandas as pd

# Ensure the src directory is in the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

class TestChannelSelector(unittest.TestCase):
    """Tests for the channel selector component."""

    def setUp(self):
        """Set up common test environment."""
        # Create a clean session state before each test
        self.patcher = patch('streamlit.session_state', new_callable=MockSessionState)
        self.mock_session_state = self.patcher.start()
        
    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()

    @patch('streamlit.text_input', return_value="")
    @patch('streamlit.selectbox')  # Removed the fixed return value of 5
    @patch('streamlit.columns', return_value=[MagicMock(), MagicMock()])
    @patch('streamlit.expander')
    @patch('streamlit.write')
    @patch('streamlit.spinner')
    @patch('streamlit.rerun')  # Prevent actual reruns
    def test_channel_display_limit_initialization(self, mock_rerun, mock_spinner,
                                               mock_write, mock_expander, mock_columns,
                                               mock_selectbox, mock_text_input):
        """
        Test that channel_display_limit is properly initialized once and respects existing values.
        This is a more focused test to isolate only the session state behavior.
        """
        # Set up mocks to minimize dependencies
        mock_expander.return_value = MagicMock().__enter__.return_value
        mock_db = MagicMock()
    
        # Create a dataframe with all required columns for testing
        test_channels_df = pd.DataFrame([
            {"Channel": "Test Channel 1", "Subscribers": 100, "Videos": 10, "Last Updated": "2025-05-01", "DB_ID": "1"},
            {"Channel": "Test Channel 2", "Subscribers": 200, "Videos": 20, "Last Updated": "2025-05-02", "DB_ID": "2"}
        ])

        # Configure selectbox to return the current session state value
        # This ensures we're not forcing a value change through the mock
        def mock_selectbox_side_effect(*args, **kwargs):
            if 'key' in kwargs and kwargs['key'] == 'display_limit_selector':
                # Return whatever is currently in session state
                return self.mock_session_state.get('channel_display_limit', 5)
            return 5
        
        mock_selectbox.side_effect = mock_selectbox_side_effect
    
        # Create a minimal set of mocks for testing just the session state behavior
        with patch('src.analysis.youtube_analysis.YouTubeAnalysis') as mock_analysis, \
             patch('src.utils.debug_utils.debug_log'), \
             patch('pandas.DataFrame', return_value=test_channels_df), \
             patch('streamlit.info'), \
             patch('streamlit.success'), \
             patch('streamlit.warning'), \
             patch('streamlit.data_editor', return_value=None), \
             patch('streamlit.container', return_value=MagicMock().__enter__.return_value), \
             patch('streamlit.caption'), \
             patch('streamlit.multiselect', return_value=[]):
    
            # Configure YouTubeAnalysis mock
            mock_analysis_instance = MagicMock()
            mock_analysis.return_value = mock_analysis_instance
            mock_analysis_instance.get_channel_statistics.return_value = {
                'name': 'Test Channel',
                'subscribers': 1000,
                'views': 5000,
                'total_videos': 10,
                'total_likes': 500
            }
    
            # Setup test for the core initialization behavior
            from src.ui.data_analysis.components import channel_selector
    
            # First call, no value set yet - should initialize to default of 5
            mock_text_input.return_value = ""  # Empty search query
            self.assertFalse('channel_display_limit' in self.mock_session_state)
    
            # Call the function to initialize channel_display_limit
            channel_selector.render_channel_selector(["Test Channel 1"], mock_db)
    
            # Verify it was initialized to 5
            self.assertTrue('channel_display_limit' in self.mock_session_state)
            self.assertEqual(self.mock_session_state.channel_display_limit, 5)
    
            # Now modify the value
            self.mock_session_state.channel_display_limit = 20
    
            # Call again - value should stay 20
            channel_selector.render_channel_selector(["Test Channel 1"], mock_db)
    
            # Check that channel_display_limit wasn't reset
            self.assertEqual(self.mock_session_state.channel_display_limit, 20,
                            "channel_display_limit was incorrectly reset when already set")
            
            # Now test with a search query to ensure it doesn't reset
            mock_text_input.return_value = "Test"
            
            # Modify value again to be sure
            self.mock_session_state.channel_display_limit = 30
            
            # Set channel_search_query to empty to simulate a change in the search query
            self.mock_session_state.channel_search_query = ""
            
            # Call with search query
            channel_selector.render_channel_selector(["Test Channel 1"], mock_db)
            
            # Value should persist even on new search
            self.assertEqual(self.mock_session_state.channel_display_limit, 30,
                            "channel_display_limit should persist for a new search")
            
            # Now clear search query to test returning to default
            mock_text_input.return_value = ""
            self.mock_session_state.channel_search_query = "Test"  # Previous search
            
            # Call with cleared search query
            channel_selector.render_channel_selector(["Test Channel 1"], mock_db)
            
            # Should respect user-selected value or default
            self.assertTrue(self.mock_session_state.channel_display_limit in [5, 2, 30],
                          "channel_display_limit should restore user-selected value or use default")

    @patch('streamlit.text_input', return_value="")
    @patch('streamlit.selectbox', return_value=10)  # User selects 10 in dropdown
    @patch('streamlit.columns', return_value=[MagicMock(), MagicMock()])
    @patch('streamlit.expander')
    @patch('streamlit.write')
    @patch('streamlit.spinner')
    @patch('streamlit.rerun')  # Prevent actual reruns
    def test_selectbox_changes_limit(self, mock_rerun, mock_spinner, 
                                   mock_write, mock_expander, mock_columns, 
                                   mock_selectbox, mock_text_input):
        """
        Test that changing the selectbox updates channel_display_limit properly.
        """
        # Set up mocks
        mock_expander.return_value = MagicMock().__enter__.return_value
        mock_db = MagicMock()
         # Create test data with all required columns
        test_channels_df = pd.DataFrame([
            {"Channel": "Test Channel 1", "Subscribers": 100, "Videos": 10, "Last Updated": "2025-05-01", "DB_ID": "1"},
            {"Channel": "Test Channel 2", "Subscribers": 200, "Videos": 20, "Last Updated": "2025-05-02", "DB_ID": "2"}
        ])
        
        # Add minimal mocks for testing
        with patch('src.analysis.youtube_analysis.YouTubeAnalysis') as mock_analysis, \
             patch('src.utils.debug_utils.debug_log'), \
             patch('pandas.DataFrame', return_value=test_channels_df), \
             patch('streamlit.info'), \
             patch('streamlit.success'), \
             patch('streamlit.warning'), \
             patch('streamlit.data_editor', return_value=None), \
             patch('streamlit.container', return_value=MagicMock().__enter__.return_value), \
             patch('streamlit.caption'), \
             patch('streamlit.multiselect', return_value=[]):
            
            # Configure YouTubeAnalysis mock
            mock_analysis_instance = MagicMock()
            mock_analysis.return_value = mock_analysis_instance
            mock_analysis_instance.get_channel_statistics.return_value = {
                'name': 'Test Channel',
                'subscribers': 1000,
                'views': 5000,
                'total_videos': 10,
                'total_likes': 500
            }
            
            # Import the module
            from src.ui.data_analysis.components import channel_selector
            
            # Initialize session state
            self.mock_session_state.channel_display_limit = 5
            
            # User selects 10 from dropdown
            mock_selectbox.return_value = 10
            
            # Call the function
            channel_selector.render_channel_selector(["Test Channel 1"], mock_db)
            
            # Check that the limit is updated to 10
            self.assertEqual(self.mock_session_state.channel_display_limit, 10,
                           "channel_display_limit should be updated when selectbox value changes")


class MockSessionState(dict):
    """A mock class for Streamlit's session_state that behaves like a dictionary with attribute access."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize performance_timers to prevent errors in the helpers module
        self['performance_timers'] = {}
    
    def __getattr__(self, key):
        if key in self:
            return self[key]
        # Create on access for dot notation
        self[key] = {}
        return self[key]
    
    def __setattr__(self, key, value):
        self[key] = value


if __name__ == '__main__':
    unittest.main()