"""
Factory module for creating appropriate workflow instances.
"""
from src.ui.data_collection.workflow_base import BaseCollectionWorkflow
from src.ui.data_collection.new_channel_workflow import NewChannelWorkflow
from src.ui.data_collection.refresh_channel_workflow import RefreshChannelWorkflow

def create_workflow(youtube_service, mode="new_channel"):
    """
    Create a workflow instance based on the specified mode.
    
    Args:
        youtube_service: YouTube service instance to pass to the workflow
        mode (str): The collection mode, either "new_channel" or "refresh_channel"
        
    Returns:
        BaseCollectionWorkflow: An instance of the appropriate workflow class
    """
    if mode == "refresh_channel":
        return RefreshChannelWorkflow(youtube_service)
    else:
        # Default to new channel workflow
        return NewChannelWorkflow(youtube_service)
