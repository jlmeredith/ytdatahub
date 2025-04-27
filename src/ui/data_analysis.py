"""
UI components for the Data Analysis tab.
"""
import streamlit as st
from src.ui.data_analysis.main import render_data_analysis_tab

# Backward compatibility wrapper that maintains the original API
def render_data_analysis_tab_legacy():
    """Render the data analysis tab."""
    return render_data_analysis_tab()