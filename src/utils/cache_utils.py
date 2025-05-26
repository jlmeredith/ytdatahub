"""
Cache management utilities for the YouTube Data Hub application.
"""
import os
import sys
import shutil
import logging
from typing import Dict, Any, Optional
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Import utility functions
from src.utils.logging_utils import debug_log

def clear_cache(clear_api_cache: bool = True, 
                clear_python_cache: bool = True, 
                clear_db_cache: bool = True, 
                verbose: bool = True) -> Dict[str, Any]:
    """
    Clear various caches to fix issues and improve performance
    
    Args:
        clear_api_cache: Whether to clear the API response cache
        clear_python_cache: Whether to clear Python __pycache__ directories
        clear_db_cache: Whether to clear database caches
        verbose: Whether to log detailed information
        
    Returns:
        Dictionary with results of the operation
    """
    # Track results
    results = {
        "api_cache_cleared": False,
        "python_cache_cleared": False,
        "db_cache_cleared": False,
        "total_items_cleared": 0,
        "python_cache_dirs_removed": []
    }
    
    # Clear API cache if requested
    if clear_api_cache:
        # If st.session_state.api_cache exists, clear it
        cache_size = 0
        if hasattr(st, 'session_state') and 'api_cache' in st.session_state:
            cache_size = len(st.session_state.api_cache)
            st.session_state.api_cache = {}
        
        results["api_cache_cleared"] = True
        results["total_items_cleared"] += cache_size
        
        if verbose:
            debug_log(f"Cleared {cache_size} items from API cache")
    
    # Clear Python __pycache__ directories
    if clear_python_cache:
        # Get the root directory of the application
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        # Find and remove all __pycache__ directories
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if '__pycache__' in dirnames:
                pycache_path = os.path.join(dirpath, '__pycache__')
                try:
                    # Count files before removing
                    file_count = len(os.listdir(pycache_path))
                    results["total_items_cleared"] += file_count
                    
                    # Remove the directory
                    shutil.rmtree(pycache_path)
                    results["python_cache_dirs_removed"].append(pycache_path)
                    
                    if verbose:
                        debug_log(f"Removed __pycache__ directory: {pycache_path} ({file_count} files)")
                except Exception as e:
                    if verbose:
                        debug_log(f"Error removing __pycache__ directory {pycache_path}: {str(e)}")
        
        results["python_cache_cleared"] = len(results["python_cache_dirs_removed"]) > 0
    
    # Clear database cache if needed
    if clear_db_cache:
        try:
            # Import here to avoid circular imports
            from src.database.sqlite import SQLiteDatabase
            
            # Get a database instance and clear its cache
            db = SQLiteDatabase()
            db.clear_cache()
            
            results["db_cache_cleared"] = True
            
            if verbose:
                debug_log("Database cache cleared")
        except Exception as e:
            if verbose:
                debug_log(f"Error clearing database cache: {str(e)}")
    
    # Display summary if verbose
    if verbose:
        debug_log(f"Cache clearing complete. Total items cleared: {results['total_items_cleared']}")
    
    return results
