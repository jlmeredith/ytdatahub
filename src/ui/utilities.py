"""
UI components for the Utilities tab.
"""
import streamlit as st
from src.utils.helpers import clear_cache

def render_utilities_tab():
    """
    Render the Utilities tab UI.
    """
    st.header("Utilities")
    
    # Cache Management Section
    st.subheader("Cache Management")
    st.write("Clear different types of caches in the application.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        clear_api = st.checkbox("Clear API Cache", value=True, 
                               help="Clears the YouTube API response cache")
    with col2:
        clear_python = st.checkbox("Clear Python Cache", value=True, 
                                  help="Removes __pycache__ directories")
    with col3:
        clear_db = st.checkbox("Clear DB Cache", value=True, 
                              help="Clears database caches and optimizes storage")
    
    verbose_logging = st.checkbox("Verbose Logging", value=True,
                                 help="Show detailed information about what was cleared")
    
    if st.button("Clear Caches", type="primary"):
        with st.spinner("Clearing caches..."):
            # Use the clear_cache function from helpers.py
            results = clear_cache(
                clear_api_cache=clear_api,
                clear_python_cache=clear_python,
                clear_db_cache=clear_db,
                verbose=verbose_logging
            )
            
            # Show the results
            st.success(f"Cache clearing complete! Total items cleared: {results['total_items_cleared']}")
            
            if verbose_logging:
                with st.expander("Cache Clearing Details"):
                    if results["api_cache_cleared"]:
                        st.write("✅ API cache cleared")
                    
                    if results["python_cache_cleared"]:
                        st.write("✅ Python cache directories removed:")
                        for cache_dir in results["python_cache_dirs_removed"]:
                            st.write(f"  - {cache_dir}")
                    
                    if results["db_cache_cleared"]:
                        st.write("✅ Database cache cleared")