"""
Queue Tracker Module - Tracks items in the database operation queue

This module provides functionality to monitor what data is pending
to be saved to the database at any given time.
"""
import streamlit as st
from datetime import datetime
import logging

# Flag for test mode - allows bypassing streamlit session state when testing
_TEST_MODE = False
_test_queue = {
    'channels': [],
    'videos': [],
    'comments': [],
    'analytics': []
}
_test_queue_stats = {
    'last_updated': None,
    'total_items': 0,
    'channels_count': 0,
    'videos_count': 0,
    'comments_count': 0,
    'analytics_count': 0
}

# Add hooks for testing
_add_to_queue_hook = None
_remove_from_queue_hook = None

def set_test_mode(enabled=True):
    """
    Enable or disable test mode for queue tracking
    
    Args:
        enabled (bool): Whether to enable test mode
    """
    global _TEST_MODE
    _TEST_MODE = enabled
    
    if _TEST_MODE:
        # Reset the test queues
        global _test_queue, _test_queue_stats
        _test_queue = {
            'channels': [],
            'videos': [],
            'comments': [],
            'analytics': []
        }
        _test_queue_stats = {
            'last_updated': None,
            'total_items': 0,
            'channels_count': 0,
            'videos_count': 0,
            'comments_count': 0,
            'analytics_count': 0
        }
        logging.debug("Queue tracker test mode enabled and queues reset")

def set_queue_hooks(add_hook=None, remove_hook=None):
    """
    Set hooks for testing queue operations
    
    Args:
        add_hook (callable): Function to call when add_to_queue is called
        remove_hook (callable): Function to call when remove_from_queue is called
    """
    global _add_to_queue_hook, _remove_from_queue_hook
    _add_to_queue_hook = add_hook
    _remove_from_queue_hook = remove_hook
    logging.debug(f"Queue hooks set: add_hook={add_hook is not None}, remove_hook={remove_hook is not None}")

def clear_queue_hooks():
    """Clear any test hooks"""
    global _add_to_queue_hook, _remove_from_queue_hook
    _add_to_queue_hook = None
    _remove_from_queue_hook = None
    logging.debug("Queue hooks cleared")

class QueueTracker:
    """
    Class for tracking items in the queue and providing status updates
    """
    
    def __init__(self):
        """Initialize the QueueTracker"""
        initialize_queue_state()
        
    def add_item(self, item_type, item_data, identifier=None):
        """Add an item to the queue"""
        add_to_queue(item_type, item_data, identifier)
        
    def remove_item(self, item_type, identifier):
        """Remove an item from the queue"""
        remove_from_queue(item_type, identifier)
        
    def clear_items(self, item_type=None):
        """Clear items from the queue"""
        clear_queue(item_type)
        
    def get_stats(self):
        """Get current queue statistics"""
        if _TEST_MODE:
            return _test_queue_stats
        return st.session_state.queue_stats if 'queue_stats' in st.session_state else {}
        
    def get_queue_items(self, item_type=None):
        """Get items in the queue by type"""
        if _TEST_MODE:
            if item_type:
                return _test_queue.get(item_type, [])
            else:
                # Return all items
                all_items = []
                for queue_type in _test_queue:
                    all_items.extend(_test_queue[queue_type])
                return all_items
                
        if 'db_queue' not in st.session_state:
            return []
            
        if item_type:
            return st.session_state.db_queue.get(item_type, [])
        else:
            # Return all items
            all_items = []
            for queue_type in st.session_state.db_queue:
                all_items.extend(st.session_state.db_queue[queue_type])
            return all_items

def initialize_queue_state():
    """
    Initialize the session state variables for queue tracking
    """
    if _TEST_MODE:
        return
        
    if 'db_queue' not in st.session_state:
        st.session_state.db_queue = {
            'channels': [],
            'videos': [],
            'comments': [],
            'analytics': []
        }
        
    if 'queue_stats' not in st.session_state:
        st.session_state.queue_stats = {
            'last_updated': None,
            'total_items': 0,
            'channels_count': 0,
            'videos_count': 0,
            'comments_count': 0,
            'analytics_count': 0
        }

def add_to_queue(item_type, item_data, identifier=None):
    """
    Add an item to the tracked queue
    
    Args:
        item_type (str): Type of item ('channels', 'videos', 'comments', 'analytics')
        item_data (dict): The data being queued
        identifier (str, optional): Unique identifier for the item (e.g., video_id)
    """
    # Call test hook if set
    if _add_to_queue_hook is not None:
        _add_to_queue_hook(item_type, item_data, identifier)
    
    if _TEST_MODE:
        # Add the timestamp
        queue_item = {
            'data': item_data,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'id': identifier or f"{item_type}_{len(_test_queue[item_type])}"
        }
        
        # Add to the appropriate queue
        if item_type in _test_queue:
            _test_queue[item_type].append(queue_item)
            
        # Update stats
        update_queue_stats()
        return
    
    initialize_queue_state()
    
    # Add the timestamp
    queue_item = {
        'data': item_data,
        'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'id': identifier or f"{item_type}_{len(st.session_state.db_queue[item_type])}"
    }
    
    # Add to the appropriate queue
    if item_type in st.session_state.db_queue:
        st.session_state.db_queue[item_type].append(queue_item)
        
    # Update stats
    update_queue_stats()
    
def remove_from_queue(item_type, identifier):
    """
    Remove an item from the tracked queue
    
    Args:
        item_type (str): Type of item ('channels', 'videos', 'comments', 'analytics')
        identifier (str): Identifier of the item to remove
    """
    # Call test hook if set
    if _remove_from_queue_hook is not None:
        _remove_from_queue_hook(item_type, identifier)
    
    if _TEST_MODE:
        if item_type in _test_queue:
            _test_queue[item_type] = [
                item for item in _test_queue[item_type] 
                if item['id'] != identifier
            ]
        
        # Update stats
        update_queue_stats()
        return
    
    initialize_queue_state()
    
    if item_type in st.session_state.db_queue:
        st.session_state.db_queue[item_type] = [
            item for item in st.session_state.db_queue[item_type] 
            if item['id'] != identifier
        ]
    
    # Update stats
    update_queue_stats()

def clear_queue(item_type=None):
    """
    Clear the queue, either a specific type or all queues
    
    Args:
        item_type (str, optional): Type to clear, or None for all types
    """
    if _TEST_MODE:
        if item_type:
            if item_type in _test_queue:
                _test_queue[item_type] = []
        else:
            for key in _test_queue:
                _test_queue[key] = []
        
        # Update stats
        update_queue_stats()
        return
    
    initialize_queue_state()
    
    if item_type:
        if item_type in st.session_state.db_queue:
            st.session_state.db_queue[item_type] = []
    else:
        for key in st.session_state.db_queue:
            st.session_state.db_queue[key] = []
    
    # Update stats
    update_queue_stats()

def update_queue_stats():
    """
    Update the queue statistics
    """
    if _TEST_MODE:
        _test_queue_stats['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _test_queue_stats['channels_count'] = len(_test_queue['channels'])
        _test_queue_stats['videos_count'] = len(_test_queue['videos'])
        _test_queue_stats['comments_count'] = len(_test_queue['comments'])
        _test_queue_stats['analytics_count'] = len(_test_queue['analytics'])
        _test_queue_stats['total_items'] = (
            _test_queue_stats['channels_count'] +
            _test_queue_stats['videos_count'] +
            _test_queue_stats['comments_count'] +
            _test_queue_stats['analytics_count']
        )
        return
        
    initialize_queue_state()
    
    st.session_state.queue_stats['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.session_state.queue_stats['channels_count'] = len(st.session_state.db_queue['channels'])
    st.session_state.queue_stats['videos_count'] = len(st.session_state.db_queue['videos'])
    st.session_state.queue_stats['comments_count'] = len(st.session_state.db_queue['comments'])
    st.session_state.queue_stats['analytics_count'] = len(st.session_state.db_queue['analytics'])
    st.session_state.queue_stats['total_items'] = (
        st.session_state.queue_stats['channels_count'] +
        st.session_state.queue_stats['videos_count'] +
        st.session_state.queue_stats['comments_count'] +
        st.session_state.queue_stats['analytics_count']
    )

def get_queue_stats():
    """
    Get current queue statistics
    
    Returns:
        dict: The current queue statistics
    """
    if _TEST_MODE:
        return _test_queue_stats
        
    initialize_queue_state()
    return st.session_state.queue_stats

def render_queue_status_sidebar():
    """
    Render the queue status in the sidebar
    """
    if _TEST_MODE:
        return
        
    stats = get_queue_stats()
    
    st.sidebar.markdown("### Queue Status")
    
    # Display metrics
    if stats['total_items'] > 0:
        st.sidebar.info(f"Total items in queue: {stats['total_items']}")
        
        # Show breakdown by type
        if stats['channels_count'] > 0:
            st.sidebar.metric("Channels", stats['channels_count'])
        if stats['videos_count'] > 0:
            st.sidebar.metric("Videos", stats['videos_count'])
        if stats['comments_count'] > 0:
            st.sidebar.metric("Comments", stats['comments_count'])
        if stats['analytics_count'] > 0:
            st.sidebar.metric("Analytics", stats['analytics_count'])
            
        # Last updated timestamp
        if stats['last_updated']:
            st.sidebar.caption(f"Last updated: {stats['last_updated']}")
    else:
        st.sidebar.success("Queue is empty")