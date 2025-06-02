"""
Factory module for creating appropriate workflow instances.
"""
import streamlit as st
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from src.utils.debug_utils import debug_log

# Import workflow implementations
from src.ui.data_collection.new_channel_workflow import NewChannelWorkflow
from src.ui.data_collection.refresh_channel_workflow import RefreshChannelWorkflow
from src.ui.data_collection.unified_workflow import UnifiedWorkflow

def create_workflow(youtube_service, mode="unified"):
    """
    Create a workflow instance based on the specified mode.
    
    Args:
        youtube_service: YouTube service instance to pass to the workflow
        mode (str): The collection mode, either "unified", "new_channel", or "refresh_channel"
        
    Returns:
        BaseCollectionWorkflow: An instance of the appropriate workflow class
    """
    if mode == "unified":
        # Create unified workflow (default and recommended)
        debug_log("Creating unified workflow")
        return UnifiedWorkflow(youtube_service)
    elif mode == "refresh_channel":
        # Create refresh channel workflow (legacy)
        debug_log("Creating refresh channel workflow")
        return RefreshChannelWorkflow(youtube_service)
    else:
        # Create new channel workflow (legacy)
        debug_log("Creating new channel workflow")
        return NewChannelWorkflow(youtube_service)
