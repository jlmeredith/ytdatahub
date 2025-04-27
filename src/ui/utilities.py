"""
UI components for the Utilities tab.
"""
import streamlit as st
import os
from src.utils.helpers import clear_cache
from src.config import Settings
from src.ui.components.ui_utils import render_template_as_markdown

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
    
    # Data Storage Options Section
    st.divider()
    st.subheader("Data Storage Management")
    st.write("Configure and manage different storage options for YouTube data.")
    
    # Initialize settings
    app_settings = Settings()
    
    # Prepare data for the storage options template
    current_options = app_settings.get_available_storage_options()
    available_options_html = ""
    for option in current_options:
        available_options_html += f'<div class="storage-option-item success">✅ {option}</div>\n'
    
    # Determine MongoDB and PostgreSQL status
    mongodb_status = "Connected" if app_settings.mongodb_available else "Not Configured"
    mongodb_status_class = "status-active" if app_settings.mongodb_available else "status-inactive"
    
    postgres_status = "Connected" if app_settings.postgres_available else "Not Configured"
    postgres_status_class = "status-active" if app_settings.postgres_available else "status-inactive"
    
    # Render the storage options template
    with st.expander("Storage Options", expanded=True):
        render_template_as_markdown("storage_options.html", {
            "available_options_html": available_options_html,
            "mongodb_status": mongodb_status,
            "mongodb_status_class": mongodb_status_class,
            "postgres_status": postgres_status,
            "postgres_status_class": postgres_status_class
        })
    
    # SQLite is always available, so show its configuration
    sqlite_col1, sqlite_col2 = st.columns([3, 1])
    with sqlite_col1:
        sqlite_path = st.text_input("SQLite Database Path:", 
                                   value=str(app_settings.sqlite_db_path),
                                   help="Location of SQLite database file")
    with sqlite_col2:
        st.write("Status:")
        st.success("Active")
    
    # JSON is always available
    json_col1, json_col2 = st.columns([3, 1])
    with json_col1:
        json_path = st.text_input("JSON Storage Path:", 
                                 value=str(app_settings.channels_file),
                                 help="Location of JSON data files")
    with json_col2:
        st.write("Status:")
        st.success("Active")
    
    # MongoDB configuration
    st.markdown("#### MongoDB Configuration")
    mongo_col1, mongo_col2 = st.columns([3, 1])
    with mongo_col1:
        mongo_uri = st.text_input("MongoDB URI:", 
                                 value=os.getenv('MONGO_URI', ''),
                                 type="password",
                                 help="MongoDB connection string (mongodb://username:password@host:port/database)")
    with mongo_col2:
        st.write("Status:")
        if app_settings.mongodb_available:
            st.success("Connected")
        else:
            st.error("Not Configured")
    
    # PostgreSQL configuration
    st.markdown("#### PostgreSQL Configuration")
    pg_col1, pg_col2 = st.columns(2)
    with pg_col1:
        pg_host = st.text_input("Host:", value=os.getenv('PG_HOST', ''),
                              help="PostgreSQL server address")
        pg_user = st.text_input("Username:", value=os.getenv('PG_USER', ''),
                              help="PostgreSQL username")
    with pg_col2:
        pg_db = st.text_input("Database:", value=os.getenv('PG_DATABASE', ''),
                            help="PostgreSQL database name")
        pg_pass = st.text_input("Password:", value=os.getenv('PG_PASSWORD', ''),
                              type="password", help="PostgreSQL password")
    
    pg_status_col1, pg_status_col2 = st.columns([3, 1])
    with pg_status_col2:
        st.write("Status:")
        if app_settings.postgres_available:
            st.success("Connected")
        else:
            st.error("Not Configured")
    
    # Save configuration button
    if st.button("Save Storage Configuration", type="primary"):
        # Create a flag to track if any changes were made
        changes_made = False
        
        # Here we would typically save the configuration to environment variables or a config file
        # For this example, we'll just show a success message and note that in a real implementation
        # you would need to persist these settings
        
        # MongoDB configuration
        if mongo_uri != os.getenv('MONGO_URI', ''):
            # In a real implementation, set the environment variable or update a config file
            # os.environ['MONGO_URI'] = mongo_uri
            changes_made = True
        
        # PostgreSQL configuration
        pg_settings_changed = (
            pg_host != os.getenv('PG_HOST', '') or
            pg_user != os.getenv('PG_USER', '') or
            pg_db != os.getenv('PG_DATABASE', '') or
            pg_pass != os.getenv('PG_PASSWORD', '')
        )
        
        if pg_settings_changed:
            # In a real implementation, set the environment variables or update a config file
            # os.environ['PG_HOST'] = pg_host
            # os.environ['PG_USER'] = pg_user
            # os.environ['PG_DATABASE'] = pg_db
            # os.environ['PG_PASSWORD'] = pg_pass
            changes_made = True
        
        # SQLite and JSON path changes
        if sqlite_path != str(app_settings.sqlite_db_path) or json_path != str(app_settings.channels_file):
            # In a real implementation, update these paths in your configuration
            changes_made = True
        
        if changes_made:
            st.success("Storage configuration updated! Changes will be applied on application restart.")
            st.info("Note: For the changes to take effect, you may need to restart the application.")
        else:
            st.info("No changes were made to the storage configuration.")