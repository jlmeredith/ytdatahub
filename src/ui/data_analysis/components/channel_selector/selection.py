"""
Selection handling functionality for the channel selector component.
"""
import streamlit as st
from src.utils.helpers import debug_log

def handle_channel_selection(selected_channels):
    """
    Handle the user's channel selection.
    
    Args:
        selected_channels: List of selected channel names
        
    Returns:
        Boolean indicating if the selection should be processed
    """
    # Validate selection
    if not selected_channels:
        st.warning("Please select at least one channel to analyze.")
        return False
    
    # Use a button to confirm selection instead of automatic processing
    proceed = st.button("Analyze Selected Channels", type="primary")
    
    if not proceed:
        # Provide option to clear selection
        if st.button("Clear Selection"):
            st.session_state.selected_channels = []
            st.rerun()
        
        # Option to save comparison set
        if len(selected_channels) > 1:
            save_name = st.text_input("Save comparison set as:", key="save_comparison_name")
            if st.button("Save Comparison Set") and save_name:
                if 'saved_comparisons' not in st.session_state:
                    st.session_state.saved_comparisons = {}
                
                st.session_state.saved_comparisons[save_name] = selected_channels.copy()
                st.success(f"Saved comparison set '{save_name}' with {len(selected_channels)} channels")
        
        # Show saved comparisons if any
        if 'saved_comparisons' in st.session_state and st.session_state.saved_comparisons:
            st.write("Saved comparison sets:")
            
            for name, channels in st.session_state.saved_comparisons.items():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{name}**: {', '.join(channels[:2])}{' ...' if len(channels) > 2 else ''}")
                
                with col2:
                    if st.button(f"Load", key=f"load_{name}"):
                        st.session_state.selected_channels = channels.copy()
                        st.rerun()
                
                with col3:
                    if st.button(f"Delete", key=f"delete_{name}"):
                        del st.session_state.saved_comparisons[name]
                        st.rerun()
    
    return proceed

def apply_selection_action(selected_channels, db):
    """
    Apply the selection action by loading channel data.
    
    Args:
        selected_channels: List of selected channel names
        db: Database connection
        
    Returns:
        Dictionary of channel data, keyed by channel name
    """
    # Process the selection if user clicked "Analyze"
    if not handle_channel_selection(selected_channels):
        return None
    
    debug_log(f"Loading data for selected channels: {selected_channels}")
    
    # Load data for the selected channels
    channel_data_dict = {}
    
    with st.spinner(f"Loading data for {len(selected_channels)} channels..."):
        for channel in selected_channels:
            try:
                channel_data = db.get_channel_data(channel)
                if channel_data:
                    channel_data_dict[channel] = channel_data
            except Exception as e:
                debug_log(f"Error loading data for {channel}: {str(e)}")
                st.error(f"Failed to load data for {channel}: {str(e)}")
    
    if channel_data_dict:
        return channel_data_dict
    
    st.error("Failed to load data for the selected channels.")
    return None
