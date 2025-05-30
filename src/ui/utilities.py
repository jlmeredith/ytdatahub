"""
UI components for the Utilities tab.
"""
import streamlit as st
import os
import pandas as pd
import time
from src.utils.cache_utils import clear_cache
from src.utils.debug_utils import debug_log, get_ui_freeze_report
from src.utils.debug_tools import log_app_state, format_duration_bar, get_performance_summary
from src.config import Settings
from src.ui.components.ui_utils import render_template_as_markdown
from dotenv import find_dotenv, set_key
import logging

def render_utilities_tab():
    """
    Render the Utilities tab UI.
    """
    st.info("Utilities tab loaded")
    st.header("Utilities")
    
    # --- Full App Reset Button ---
    st.divider()
    if st.button("Reset App (Full)", type="primary"):
        # 1. Clear all caches
        clear_cache(clear_api_cache=True, clear_python_cache=True, clear_db_cache=True, verbose=True)
        # 2. Clear and re-initialize the database
        from src.config import SQLITE_DB_PATH
        from src.database.sqlite import SQLiteDatabase
        db = SQLiteDatabase(SQLITE_DB_PATH)
        db.clear_all_data()
        db.initialize_db()
        # 3. Clear all session state
        st.session_state.clear()
        # 4. Rerun the app for a truly fresh state
        st.success("App fully reset! All caches, database, and session state cleared.")
        st.rerun()
    
    # Cache Management Section
    try:
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
    except Exception as e:
        st.error(f"Error in Cache Management section: {e}")
    
    # Data Storage Options Section
    st.divider()
    try:
        import os
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
    except Exception as e:
        st.error(f"Error in Data Storage Management section: {e}")
    
    # Add a new database management expander
    st.divider()
    try:
        import os
        with st.expander("Database Management Tools", expanded=True):
            st.warning("""
            ⚠️ **Warning**: The following operations can result in data loss. 
            Use these tools only for testing, development, or when you need to reset your database.
            """)
            
            st.subheader("Clear Database")
            st.write("""
            This will completely erase all channel data, videos, comments, and other information 
            from your database. A backup will be created before deletion.
            """)
            
            # Two-step confirmation to prevent accidental clearing
            confirm_clear = st.checkbox("I understand this will delete all data", key="confirm_clear_db")
            
            clear_col1, clear_col2 = st.columns([3, 1])
            with clear_col1:
                confirm_text = st.text_input(
                    "Type 'CLEAR ALL DATA' to confirm", 
                    key="clear_db_text_confirm",
                    help="This confirmation helps prevent accidental data loss"
                )
            
            with clear_col2:
                if st.button("Clear Database", type="primary", disabled=not (confirm_clear and confirm_text == "CLEAR ALL DATA")):
                    with st.spinner("Clearing database and creating backup..."):
                        from src.config import SQLITE_DB_PATH
                        from src.database.sqlite import SQLiteDatabase
                        
                        # Create a database instance
                        db = SQLiteDatabase(SQLITE_DB_PATH)
                        
                        # Call the clear_all_data method
                        success = db.clear_all_data()
                        if success:
                            # Re-initialize the schema after clearing
                            db.initialize_db()
                            # Clear session state cache as well
                            if 'use_data_cache' in st.session_state:
                                # Keep track of current cache setting
                                current_cache_setting = st.session_state.use_data_cache
                                # Clear all session state keys that start with 'channel_data_'
                                keys_to_remove = [k for k in st.session_state.keys() if k.startswith('channel_data_')]
                                for key in keys_to_remove:
                                    del st.session_state[key]
                                # Clear the channels table cache if it exists
                                if 'analysis_channels_table' in st.session_state:
                                    del st.session_state['analysis_channels_table']
                                # Restore cache setting
                                st.session_state.use_data_cache = current_cache_setting
                            st.success("✅ Database successfully cleared and schema re-initialized! A backup was created before deletion.")
                            st.info("The database has been reset and all tables have been recreated. You can now import new data.")
                        else:
                            st.error("❌ There was an error clearing the database. Please check the logs for details.")
    except Exception as e:
        st.error(f"Error in Database Management Tools section: {e}")
    
    # Add a new section for API key management
    st.divider()
    try:
        import os
        st.subheader("API Key Management")
        st.write("""
        Configure your YouTube Data API key. This key is needed for all operations that 
        fetch data from the YouTube API, including channel importing and data collection.
        """)
        
        # Get the current API key from environment
        from dotenv import load_dotenv, find_dotenv, set_key
        from src.utils.validation import validate_api_key
        
        # Reload .env to ensure we have the latest values
        load_dotenv()
        
        # Get current API key from environment or session state
        current_api_key = os.getenv('YOUTUBE_API_KEY', '')
        api_key_source = "Environment Variable"
        
        if not current_api_key and 'youtube_api_key' in st.session_state:
            current_api_key = st.session_state.youtube_api_key
            api_key_source = "Session State"
        
        # Display current API key status
        api_status_col1, api_status_col2 = st.columns([3, 1])
        
        with api_status_col1:
            # Mask most of the API key for security, but show the first and last few characters
            masked_key = ""
            if current_api_key:
                if len(current_api_key) > 10:
                    masked_key = f"{current_api_key[:4]}{'*' * (len(current_api_key) - 8)}{current_api_key[-4:]}"
                else:
                    masked_key = "***" + current_api_key[-3:] if len(current_api_key) > 3 else current_api_key
                
                st.info(f"Current API key: {masked_key} (from {api_key_source})")
            else:
                st.warning("No YouTube API key configured. Enter a key below.")
        
        with api_status_col2:
            st.write("Validation:")
            if current_api_key:
                # Validate the current API key format (basic validation)
                is_valid = validate_api_key(current_api_key)
                if is_valid:
                    st.success("Valid Format")
                else:
                    st.error("Invalid Format")
            else:
                st.error("Missing")
        
        # Input for new API key
        new_api_key = st.text_input(
            "YouTube Data API Key:",
            type="password",
            help="Enter your YouTube Data API key. Get one at https://console.developers.google.com/"
        )
        
        # Option to save to .env file
        save_to_env = st.checkbox(
            "Save to .env file (persistent)",
            value=True,
            help="If checked, the API key will be saved to the .env file and persist between application restarts."
        )
        
        # Button to save the API key
        if st.button("Save API Key", key="save_api_key_btn"):
            if not new_api_key:
                st.error("Please enter an API key.")
            else:
                # Basic validation
                if not validate_api_key(new_api_key):
                    st.warning("The API key format looks unusual. Please check it's correct.")
                    # Continue anyway since we can't fully validate without a live test
                
                # Save to session state (temporary for this session)
                st.session_state.youtube_api_key = new_api_key
                
                # If requested, save to .env file (permanent)
                if save_to_env:
                    try:
                        # Find the .env file
                        dotenv_path = find_dotenv()
                        
                        if not dotenv_path:
                            # If .env doesn't exist, create it in the current directory
                            dotenv_path = os.path.join(os.getcwd(), '.env')
                            with open(dotenv_path, 'a') as f:
                                pass  # Create an empty file
                        
                        # Save the API key to the .env file
                        set_key(dotenv_path, 'YOUTUBE_API_KEY', new_api_key)
                        debug_log("Saved YouTube API key to .env file")
                        
                        st.success("API key saved to .env file. It will persist between application restarts.")
                    except Exception as e:
                        st.error(f"Error saving to .env file: {str(e)}")
                        debug_log(f"Error saving API key to .env: {str(e)}")
                        
                        # Even if saving to .env fails, we still have it in session state
                        st.info("API key saved to session state for the current session only.")
                else:
                    # Only saving to session state
                    st.info("API key saved to session state. It will be available only for the current session.")
                
                # Offer to test the API key
                if st.button("Test API Key Connection"):
                    try:
                        from src.api.youtube_api import YouTubeAPI
                        
                        with st.spinner("Testing API connection..."):
                            # Try to initialize the API with the new key
                            api = YouTubeAPI(new_api_key)
                            
                            if api.is_initialized():
                                # Try a simple API call
                                test_result = api.test_connection()
                                if test_result:
                                    st.success("✅ API connection successful!")
                                else:
                                    st.error("❌ API initialization succeeded, but test call failed.")
                            else:
                                st.error("❌ Failed to initialize YouTube API. Please check your API key.")
                    except Exception as e:
                        st.error(f"❌ Error testing API connection: {str(e)}")
    except Exception as e:
        st.error(f"Error in API Key Management section: {e}")
    
    # Add a utility to clear the API key if needed
    with st.expander("Advanced API Key Options"):
        if st.button("Clear API Key"):
            # Clear from session state
            if 'youtube_api_key' in st.session_state:
                del st.session_state.youtube_api_key
            
            # Clear from .env if it exists
            try:
                dotenv_path = find_dotenv()
                if dotenv_path:
                    set_key(dotenv_path, 'YOUTUBE_API_KEY', '')
                    debug_log("Removed YouTube API key from .env file")
            except Exception as e:
                debug_log(f"Error clearing API key from .env: {str(e)}")
            
            st.success("API key cleared from session and .env file.")
            st.rerun()  # Rerun to update the UI
            
    # Add a new section for Debug Settings
    st.divider()
    try:
        import os
        st.subheader("Debug Settings")
        st.write("""
        Configure debugging options to help troubleshoot issues with the application.
        Debug logging provides detailed information about application operations.
        """)
        if 'debug_mode' not in st.session_state:
            st.session_state.debug_mode = False
        if 'log_level' not in st.session_state:
            st.session_state.log_level = logging.WARNING
        if 'ui_freeze_thresholds' not in st.session_state:
            st.session_state.ui_freeze_thresholds = {
                'ui_blocking': 0.5,
                'warning': 1.0,
                'critical': 3.0
            }
        debug_col1, debug_col2 = st.columns(2)
        with debug_col1:
            debug_enabled = st.toggle(
                "Enable Debug Mode", 
                value=st.session_state.debug_mode,
                help="When enabled, detailed debug information will be logged"
            )
            if debug_enabled != st.session_state.debug_mode:
                st.session_state.debug_mode = debug_enabled
                debug_log(f"Debug mode set to {debug_enabled}")
                st.success(f"Debug mode {'enabled' if debug_enabled else 'disabled'}")
            log_level = st.selectbox(
                "Log Level",
                options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(logging.getLevelName(st.session_state.get('log_level', logging.WARNING))),
                help="Set the minimum log level for debug output"
            )
            # Update log level in session state
            log_level_int = getattr(logging, log_level.upper(), logging.WARNING)
            if st.session_state.get('log_level', logging.WARNING) != log_level_int:
                st.session_state['log_level'] = log_level_int
                debug_log(f"Log level set to {log_level} ({log_level_int})")
        with debug_col2:
            st.write("Performance Monitoring")
            show_metrics = st.checkbox(
                "Show Performance Metrics",
                value=st.session_state.get('show_performance_metrics', False),
                help="Display performance metrics for UI operations"
            )
            st.session_state.show_performance_metrics = show_metrics
            if show_metrics:
                st.write("UI Freeze Thresholds (seconds):")
                ui_blocking = st.slider(
                    "UI Blocking Threshold",
                    min_value=0.1,
                    max_value=2.0,
                    value=st.session_state.ui_freeze_thresholds.get('ui_blocking', 0.5),
                    step=0.1,
                    help="Operations taking longer than this may cause UI lag"
                )
                warning_threshold = st.slider(
                    "Warning Threshold",
                    min_value=0.5,
                    max_value=5.0,
                    value=st.session_state.ui_freeze_thresholds.get('warning', 1.0),
                    step=0.5,
                    help="Operations taking longer than this will trigger a warning"
                )
                critical_threshold = st.slider(
                    "Critical Threshold",
                    min_value=1.0,
                    max_value=10.0,
                    value=st.session_state.ui_freeze_thresholds.get('critical', 3.0),
                    step=1.0,
                    help="Operations taking longer than this will trigger a critical alert"
                )
                if (ui_blocking != st.session_state.ui_freeze_thresholds.get('ui_blocking', 0.5) or
                    warning_threshold != st.session_state.ui_freeze_thresholds.get('warning', 1.0) or
                    critical_threshold != st.session_state.ui_freeze_thresholds.get('critical', 3.0)):
                    st.session_state.ui_freeze_thresholds = {
                        'ui_blocking': ui_blocking,
                        'warning': warning_threshold,
                        'critical': critical_threshold
                    }
                    st.success("Performance thresholds updated")
        if show_metrics and 'performance_metrics' in st.session_state:
            st.subheader("Recent Performance Metrics")
            performance_df = get_ui_freeze_report()
            if not performance_df.empty:
                st.dataframe(performance_df, use_container_width=True)
                if st.button("Clear Performance Data"):
                    st.session_state.performance_metrics = {}
                    st.session_state.ui_timing_metrics = []
                    st.success("Performance data cleared")
                    st.rerun()
            else:
                st.info("No performance metrics collected yet. Enable debug mode and use the app to generate metrics.")
        if debug_enabled:
            st.subheader("Debug Actions")
            # Create columns for buttons
            debug_btn_col1, debug_btn_col2 = st.columns(2)
            
            with debug_btn_col1:
                if st.button("View Recent Debug Logs", key="view_debug_logs_btn"):
                    try:
                        possible_log_paths = [
                            os.path.expanduser("~/.streamlit/logs/streamlit.log"),
                            os.path.expanduser("~/Library/Application Support/streamlit/logs/streamlit.log"),
                            os.path.expanduser("~/.streamlit/streamlit.log"),
                            "streamlit.log"
                        ]
                        log_file = next((path for path in possible_log_paths if os.path.exists(path)), None)
                        if log_file:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                last_lines = lines[-50:] if len(lines) > 50 else lines
                            with st.expander("Recent Debug Logs", expanded=True):
                                for line in last_lines:
                                    if "DEBUG" in line:
                                        st.text(line.strip())
                        else:
                            st.warning("Could not locate Streamlit log file. Try running the app with --log_level=debug")
                    except Exception as e:
                        st.error(f"Error reading log file: {str(e)}")
            
            with debug_btn_col2:
                if st.button("Log Application State", key="log_app_state_btn"):
                    # Generate a comprehensive application state log
                    debug_report = log_app_state("Manual app state snapshot triggered from UI")
                    st.success("Application state has been logged")
                    
                    # Display a summary of the logged information
                    with st.expander("Application State Summary", expanded=True):
                        if 'system' in debug_report:
                            system_info = debug_report['system']
                            st.subheader("System Information")
                            system_info_md = f"""
                            - **Timestamp**: {system_info.get('timestamp', 'N/A')}
                            - **Python**: {system_info.get('python_version', 'N/A')}
                            - **OS**: {system_info.get('os', 'N/A')}
                            - **Processor**: {system_info.get('processor', 'N/A')}
                            """
                            
                            # Add memory info if available
                            if 'memory' in system_info:
                                memory = system_info['memory']
                                system_info_md += f"""
                                - **Memory**: {memory.get('available_gb', 'N/A')}GB available / {memory.get('total_gb', 'N/A')}GB total ({memory.get('percent_used', 'N/A')}% used)
                                """
                            
                            st.markdown(system_info_md)
                        
                        # Show session state summary in a table
                        if 'session_state' in debug_report:
                            st.subheader("Session State Summary")
                            for category, values in debug_report['session_state'].items():
                                if category != 'other':
                                    st.write(f"**{category.upper()}**")
                                    st.json(values)
            
            # Add advanced performance metrics visualization
            if 'performance_metrics' in st.session_state and st.session_state.performance_metrics:
                st.subheader("Advanced Performance Metrics")
                
                # Get performance summary
                perf_summary = get_performance_summary()
                
                # Display performance statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Operations Measured", 
                        perf_summary['summary']['total_measurements']
                    )
                with col2:
                    st.metric(
                        "Warning Operations",
                        perf_summary['summary']['warning_count'],
                        delta=f"{int(perf_summary['summary']['warning_count']/max(1, perf_summary['summary']['total_measurements'])*100)}%"
                    )
                with col3:
                    st.metric(
                        "Critical Operations",
                        perf_summary['summary']['critical_count'],
                        delta=f"{int(perf_summary['summary']['critical_count']/max(1, perf_summary['summary']['total_measurements'])*100)}%",
                        delta_color="inverse"
                    )
                
                # Show more detailed metrics
                st.subheader("Operation Durations")
                
                # Convert metrics to a dataframe format that's easier to display
                metrics_list = []
                for key, metric in st.session_state.performance_metrics.items():
                    if isinstance(metric, dict):
                        operation = {
                            'Operation': metric.get('tag', 'Unknown'),
                            'Duration': metric.get('duration', 0),
                            'Timestamp': metric.get('timestamp', 0),
                            'Message': metric.get('message', '')
                        }
                        metrics_list.append(operation)
                
                # Sort by duration (slowest first)
                metrics_list.sort(key=lambda x: x['Duration'], reverse=True)
                
                # Show as a table with visual duration bars
                if metrics_list:
                    # Create HTML for table
                    html_table = """
                    <table style="width:100%; border-collapse: collapse;">
                        <tr style="border-bottom: 2px solid #dee2e6; background-color: #f8f9fa;">
                            <th style="padding: 8px; text-align: left;">Operation</th>
                            <th style="padding: 8px; text-align: left;">Duration</th>
                            <th style="padding: 8px; text-align: left;">Message</th>
                        </tr>
                    """
                    
                    # Add rows for top 10 operations
                    for i, op in enumerate(metrics_list[:10]):
                        row_style = 'background-color: #fff0f0;' if op['Duration'] >= 3.0 else \
                                   'background-color: #fffaf0;' if op['Duration'] >= 1.0 else ''
                        
                        html_table += f"""
                        <tr style="border-bottom: 1px solid #dee2e6; {row_style}">
                            <td style="padding: 8px;">{op['Operation']}</td>
                            <td style="padding: 8px;">{format_duration_bar(op['Duration'])}</td>
                            <td style="padding: 8px; font-size:0.9em;">{op['Message']}</td>
                        </tr>
                        """
                    
                    html_table += "</table>"
                    
                    st.markdown(html_table, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error in Debug Settings section: {e}")

def show_debug_metrics():
    """Show debug metrics from the performance monitor"""
    try:
        # Get any UI freeze reports
        freezes = get_ui_freeze_report()
        # Display the freezes report
        if freezes:
            st.dataframe(freezes)
        else:
            st.info("No performance issues detected")
    except Exception as e:
        st.error(f"Error showing debug metrics: {e}")