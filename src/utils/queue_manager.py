"""
Queue management utilities for tracking database operations.
This module helps track what data is being held in memory before being saved to the database.
"""
import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List, Optional


class QueueManager:
    """
    Class to manage queues for database operations.
    Keeps track of what data is being processed before being saved to the database.
    """
    
    @staticmethod
    def initialize():
        """Initialize the database queue manager in session state"""
        if 'queue_status' not in st.session_state:
            st.session_state.queue_status = {
                'channels': 0,
                'videos': 0, 
                'comments': 0,
                'last_updated': None
            }
        
        if 'queue_items' not in st.session_state:
            st.session_state.queue_items = {
                'channels': [],
                'videos': [],
                'comments': []
            }
        
        if 'flush_queue_requested' not in st.session_state:
            st.session_state.flush_queue_requested = False
    
    @staticmethod
    def add_to_queue(queue_type: str, item_id: str, item_data: Any):
        """
        Add an item to the database queue.
        
        Args:
            queue_type: Type of item ('channels', 'videos', or 'comments')
            item_id: Unique identifier for the item
            item_data: The actual data to be saved
        """
        # Make sure the queue manager is initialized
        QueueManager.initialize()
        
        # Add to the appropriate queue
        if queue_type not in st.session_state.queue_items:
            st.session_state.queue_items[queue_type] = []
        
        # Check if the item is already in the queue
        existing_ids = [item['id'] for item in st.session_state.queue_items[queue_type]]
        if item_id not in existing_ids:
            # Add the item to the queue
            st.session_state.queue_items[queue_type].append({
                'id': item_id,
                'data': item_data,
                'added_at': datetime.now()
            })
            
            # Update the queue status counts
            st.session_state.queue_status[queue_type] = len(st.session_state.queue_items[queue_type])
            st.session_state.queue_status['last_updated'] = datetime.now()
    
    @staticmethod
    def remove_from_queue(queue_type: str, item_id: str):
        """
        Remove an item from the database queue.
        
        Args:
            queue_type: Type of item ('channels', 'videos', or 'comments')
            item_id: Unique identifier for the item to remove
        """
        # Make sure the queue manager is initialized
        QueueManager.initialize()
        
        # Remove from the appropriate queue if it exists
        if queue_type in st.session_state.queue_items:
            st.session_state.queue_items[queue_type] = [
                item for item in st.session_state.queue_items[queue_type] 
                if item['id'] != item_id
            ]
            
            # Update the queue status counts
            st.session_state.queue_status[queue_type] = len(st.session_state.queue_items[queue_type])
            st.session_state.queue_status['last_updated'] = datetime.now()
    
    @staticmethod
    def clear_queue(queue_type: Optional[str] = None):
        """
        Clear the database queue.
        
        Args:
            queue_type: Type of queue to clear, or None to clear all queues
        """
        # Make sure the queue manager is initialized
        QueueManager.initialize()
        
        if queue_type is None:
            # Clear all queues
            st.session_state.queue_items = {
                'channels': [],
                'videos': [],
                'comments': []
            }
            st.session_state.queue_status = {
                'channels': 0,
                'videos': 0,
                'comments': 0,
                'last_updated': datetime.now()
            }
        elif queue_type in st.session_state.queue_items:
            # Clear only the specified queue
            st.session_state.queue_items[queue_type] = []
            st.session_state.queue_status[queue_type] = 0
            st.session_state.queue_status['last_updated'] = datetime.now()


# Keep the original functions for backward compatibility
def initialize_queue_manager():
    """Initialize the database queue manager in session state"""
    QueueManager.initialize()

def add_to_queue(queue_type: str, item_id: str, item_data: Any):
    """
    Add an item to the database queue.
    
    Args:
        queue_type: Type of item ('channels', 'videos', or 'comments')
        item_id: Unique identifier for the item
        item_data: The actual data to be saved
    """
    QueueManager.add_to_queue(queue_type, item_id, item_data)

def remove_from_queue(queue_type: str, item_id: str):
    """
    Remove an item from the database queue.
    
    Args:
        queue_type: Type of item ('channels', 'videos', or 'comments')
        item_id: Unique identifier for the item to remove
    """
    QueueManager.remove_from_queue(queue_type, item_id)

def clear_queue(queue_type: Optional[str] = None):
    """
    Clear the database queue.
    
    Args:
        queue_type: Type of queue to clear, or None to clear all queues
    """
    QueueManager.clear_queue(queue_type)

def get_queue_items(queue_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get items in the database queue.
    
    Args:
        queue_type: Type of queue to get items from, or None to get all queues
        
    Returns:
        Dict containing queue items
    """
    # Make sure the queue manager is initialized
    QueueManager.initialize()
    
    if queue_type is None:
        # Return all queues
        return st.session_state.queue_items
    elif queue_type in st.session_state.queue_items:
        # Return only the specified queue
        return {queue_type: st.session_state.queue_items[queue_type]}
    else:
        return {}

def get_queue_status() -> Dict[str, Any]:
    """
    Get the current status of all database queues.
    
    Returns:
        Dict containing queue status information
    """
    # Make sure the queue manager is initialized
    QueueManager.initialize()
    
    return st.session_state.queue_status

def request_queue_flush():
    """Request that the queue be flushed to the database on the next processing cycle"""
    st.session_state.flush_queue_requested = True
    
def check_and_reset_flush_request() -> bool:
    """
    Check if a flush has been requested and reset the flag.
    
    Returns:
        bool: True if flush was requested, False otherwise
    """
    if st.session_state.get('flush_queue_requested', False):
        st.session_state.flush_queue_requested = False
        return True
    return False