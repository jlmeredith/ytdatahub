"""
Save operation manager component.
Provides standardized UI feedback for save operations.
"""
import streamlit as st
import datetime
import json
from typing import Dict, Any, List, Optional, Union
import time

class SaveOperationManager:
    """
    Manages save operations and provides standardized UI feedback.
    """
    
    def __init__(self):
        """Initialize the save operation manager."""
        # Initialize session state for save operations if needed
        if 'save_operations' not in st.session_state:
            st.session_state.save_operations = []
        
        if 'last_save_time' not in st.session_state:
            st.session_state.last_save_time = None
        
        if 'save_summary' not in st.session_state:
            st.session_state.save_summary = {}
    
    def perform_save_operation(self, youtube_service, api_data: Dict[str, Any],
                              total_videos: int = 0, total_comments: int = 0) -> bool:
        """
        Perform a save operation with UI feedback and logging.
        
        Args:
            youtube_service: YouTube service instance to use for saving
            api_data: API data to save
            total_videos: Number of videos being saved
            total_comments: Number of comments being saved
            
        Returns:
            bool: Whether the save was successful
        """
        if not api_data:
            st.error("No data to save.")
            return False
        
        # Show progress indicator first
        with st.spinner("Saving data to database..."):
            # Track start time
            start_time = time.time()
            
            # Perform the save operation
            try:
                success = youtube_service.save_channel_data(api_data, "SQLite Database")
                
                # Calculate duration
                duration = time.time() - start_time
                
                if success:
                    # Update session state
                    st.session_state.last_save_time = datetime.datetime.now().isoformat()
                    
                    # Create save summary
                    save_summary = {
                        "Channel": api_data.get('channel_name', 'Unknown'),
                        "Channel ID": api_data.get('channel_id', 'Unknown'),
                        "Timestamp": st.session_state.last_save_time,
                        "Data Fields": len([k for k in api_data.keys() if not k.startswith('_') and k != 'delta']),
                        "Videos Saved": total_videos,
                        "Comments Saved": total_comments,
                        "Comparison Level": api_data.get('_comparison_options', {}).get('comparison_level', 'standard'),
                        "Duration": f"{duration:.2f} seconds"
                    }
                    
                    # Add significant changes to summary if available
                    delta = api_data.get('delta', {})
                    if 'significant_changes' in delta and delta['significant_changes']:
                        save_summary["Significant Changes"] = len(delta['significant_changes'])
                    
                    st.session_state.save_summary = save_summary
                    
                    # Log the operation
                    self._log_save_operation(save_summary)
                    
                    # Show success message
                    self._show_save_success_feedback()
                    
                    return True
                else:
                    st.error("Failed to save data to database.")
                    return False
            
            except Exception as e:
                st.error(f"Error during save operation: {str(e)}")
                return False
    
    def _show_save_success_feedback(self) -> None:
        """Display success feedback with operation details."""
        # Display success toast
        st.success("Data saved successfully!")
        
        # Get save summary
        save_summary = st.session_state.save_summary
        
        # Show expandable details
        with st.expander("Complete Save Operation Details", expanded=True):
            # Format the details for display
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Channel Information**")
                st.write(f"Channel: {save_summary.get('Channel', 'Unknown')}")
                st.write(f"Channel ID: {save_summary.get('Channel ID', 'Unknown')}")
                
                # Format the timestamp for better display
                timestamp = save_summary.get('Timestamp', '')
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_time = timestamp
                
                st.write(f"Saved at: {formatted_time}")
                
                # Show details about significant changes if present
                if 'Significant Changes' in save_summary:
                    st.error(f"⚠️ {save_summary['Significant Changes']} significant changes detected!")
            
            with col2:
                st.write("**Data Overview**")
                st.write(f"Fields Saved: {save_summary.get('Data Fields', 0)}")
                st.write(f"Videos: {save_summary.get('Videos Saved', 0)}")
                st.write(f"Comments: {save_summary.get('Comments Saved', 0)}")
                st.write(f"Comparison Level: {save_summary.get('Comparison Level', 'standard').upper()}")
                st.write(f"Operation Time: {save_summary.get('Duration', '')}")
            
            # Add a divider
            st.divider()
            
            # Show previous save operations if available
            if st.session_state.save_operations:
                st.write("**Previous Save Operations**")
                
                # Format for display
                previous_saves = []
                for op in st.session_state.save_operations[-5:]:  # Show last 5
                    try:
                        dt = datetime.datetime.fromisoformat(op.get('Timestamp', ''))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        formatted_time = op.get('Timestamp', '')
                    
                    previous_saves.append({
                        "Channel": op.get('Channel', 'Unknown'),
                        "Timestamp": formatted_time,
                        "Videos": op.get('Videos Saved', 0),
                        "Comments": op.get('Comments Saved', 0)
                    })
                
                # Display as a table
                import pandas as pd
                st.table(pd.DataFrame(previous_saves).sort_values(by="Timestamp", ascending=False))
    
    def _log_save_operation(self, save_summary: Dict[str, Any]) -> None:
        """
        Log a save operation to session state.
        
        Args:
            save_summary: Summary of the save operation
        """
        # Append to save operations
        st.session_state.save_operations.append(save_summary.copy())
        
        # Keep only the last 20 operations
        if len(st.session_state.save_operations) > 20:
            st.session_state.save_operations = st.session_state.save_operations[-20:]

def show_save_confirmation_dialog(message: str) -> bool:
    """
    Show a save confirmation dialog.
    
    Args:
        message: Message to display in the confirmation dialog
        
    Returns:
        bool: Whether the user confirmed the save operation
    """
    # Create a unique key for each confirmation dialog
    import random
    key = f"save_confirm_{random.randint(1000, 9999)}"
    
    # Show the confirmation dialog
    st.info(message)
    
    col1, col2 = st.columns(2)
    
    with col1:
        confirm = st.button("Save Data", key=f"{key}_confirm", type="primary")
    
    with col2:
        cancel = st.button("Cancel", key=f"{key}_cancel")
    
    # Return the result
    if cancel:
        return False
    
    return confirm

def display_save_progress(progress: float, message: str) -> None:
    """
    Display save progress.
    
    Args:
        progress: Progress value (0-1)
        message: Progress message to display
    """
    # Create progress bar
    progress_bar = st.progress(0)
    
    # Update progress
    progress_bar.progress(progress)
    
    # Show message
    st.caption(message)

def render_save_metadata_panel() -> None:
    """Render a panel showing save metadata."""
    # Get save operations from session state
    save_operations = st.session_state.get('save_operations', [])
    
    if not save_operations:
        st.info("No save operations recorded yet.")
        return
    
    # Show the last save time
    last_save = save_operations[-1]
    try:
        timestamp = last_save.get('Timestamp', '')
        dt = datetime.datetime.fromisoformat(timestamp)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        formatted_time = timestamp
    
    st.caption(f"Last saved: {formatted_time}")
    
    # Show save history in expander
    with st.expander("Save History", expanded=False):
        # Create a table of save operations
        import pandas as pd
        
        # Format data for display
        formatted_ops = []
        for op in save_operations:
            try:
                dt = datetime.datetime.fromisoformat(op.get('Timestamp', ''))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = op.get('Timestamp', '')
            
            formatted_ops.append({
                "Channel": op.get('Channel', 'Unknown'),
                "Time": formatted_time,
                "Videos": op.get('Videos Saved', 0),
                "Comments": op.get('Comments Saved', 0),
                "Comparison": op.get('Comparison Level', 'standard').upper()
            })
        
        # Create and display the table
        if formatted_ops:
            df = pd.DataFrame(formatted_ops)
            st.table(df.sort_values(by="Time", ascending=False))