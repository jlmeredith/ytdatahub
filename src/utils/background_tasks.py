"""
Background task management for YouTube data collection.
This module allows for queued data collection tasks to run in the background
while users are analyzing existing data.
"""
import threading
import queue
import time
from datetime import datetime
import streamlit as st
from src.utils.helpers import debug_log
from src.services.youtube_service import YouTubeService

# Global queue for background tasks
if 'background_task_queue' not in st.session_state:
    st.session_state.background_task_queue = queue.Queue()

# Track running tasks
if 'background_tasks_running' not in st.session_state:
    st.session_state.background_tasks_running = False

# Store task results
if 'background_task_results' not in st.session_state:
    st.session_state.background_task_results = {}

# Store task status
if 'background_tasks_status' not in st.session_state:
    st.session_state.background_tasks_status = {}

# Worker thread reference
if 'worker_thread' not in st.session_state:
    st.session_state.worker_thread = None

def queue_data_collection_task(channel_id, api_key, options, task_id=None):
    """
    Queue a data collection task to run in the background.
    
    Args:
        channel_id: YouTube channel ID or URL
        api_key: YouTube API key
        options: Dictionary of collection options
        task_id: Optional task ID, will be generated if not provided
        
    Returns:
        task_id: Unique ID for the queued task
    """
    if task_id is None:
        # Generate a unique task ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_id = f"task_{timestamp}_{channel_id.replace('@', '').replace('-', '_')}"
    
    # Create task data
    task = {
        'id': task_id,
        'channel_id': channel_id,
        'api_key': api_key,
        'options': options,
        'status': 'queued',
        'queued_at': datetime.now().isoformat(),
        'started_at': None,
        'completed_at': None,
        'result': None,
        'error': None
    }
    
    # Add to queue
    st.session_state.background_task_queue.put(task)
    
    # Update task status
    st.session_state.background_tasks_status[task_id] = task
    
    # Start worker thread if not already running
    ensure_worker_thread_running()
    
    debug_log(f"Queued background task {task_id} for channel {channel_id}")
    return task_id

def ensure_worker_thread_running():
    """Ensure the worker thread is running to process the task queue."""
    if (st.session_state.worker_thread is None or 
        not st.session_state.worker_thread.is_alive()):
        # Start new worker thread
        st.session_state.worker_thread = threading.Thread(
            target=background_worker_thread,
            daemon=True
        )
        st.session_state.worker_thread.start()
        st.session_state.background_tasks_running = True
        debug_log("Started background worker thread")

def background_worker_thread():
    """Worker thread function to process background tasks."""
    debug_log("Background worker thread started")
    
    while True:
        try:
            # Get task from queue with timeout
            try:
                task = st.session_state.background_task_queue.get(timeout=1.0)
            except queue.Empty:
                # No tasks in queue, check if we should exit
                if not st.session_state.background_tasks_running:
                    debug_log("Background worker thread exiting (tasks stopped)")
                    break
                continue
            
            # Process the task
            task_id = task['id']
            debug_log(f"Processing background task {task_id}")
            
            # Update task status
            task['status'] = 'running'
            task['started_at'] = datetime.now().isoformat()
            st.session_state.background_tasks_status[task_id] = task
            
            try:
                # Execute the data collection
                youtube_service = YouTubeService(task['api_key'])
                result = youtube_service.collect_channel_data(
                    task['channel_id'], 
                    task['options']
                )
                
                # Save the result
                task['result'] = result
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                
                # Check if we need to save to storage
                if task['options'].get('save_to_storage', False):
                    storage_type = task['options'].get('storage_type', 'SQLite Database')
                    from src.config import Settings
                    success = youtube_service.save_channel_data(result, storage_type, Settings())
                    task['saved_to_storage'] = success
                
                debug_log(f"Completed background task {task_id}")
                
            except Exception as e:
                # Handle errors
                debug_log(f"Error in background task {task_id}: {str(e)}")
                task['status'] = 'error'
                task['error'] = str(e)
                task['completed_at'] = datetime.now().isoformat()
            
            # Update status in session state
            st.session_state.background_tasks_status[task_id] = task
            st.session_state.background_task_results[task_id] = task
            
            # Mark task as done in queue
            st.session_state.background_task_queue.task_done()
            
        except Exception as e:
            # Handle unexpected errors in the worker thread
            debug_log(f"Unexpected error in background worker thread: {str(e)}")
            time.sleep(1)  # Avoid tight loop if there's a persistent error

def stop_background_tasks():
    """Stop all background tasks and the worker thread."""
    st.session_state.background_tasks_running = False
    debug_log("Stopping background tasks")

def get_task_status(task_id):
    """
    Get the status of a background task.
    
    Args:
        task_id: The task ID
        
    Returns:
        dict: Task status information
    """
    if task_id in st.session_state.background_tasks_status:
        return st.session_state.background_tasks_status[task_id]
    return None

def get_all_task_statuses():
    """
    Get the status of all background tasks.
    
    Returns:
        dict: Dictionary of task statuses
    """
    return st.session_state.background_tasks_status

def clear_completed_tasks():
    """Clear completed tasks from the status dictionary."""
    # Create a copy to avoid modifying during iteration
    completed_tasks = []
    for task_id, task in st.session_state.background_tasks_status.items():
        if task['status'] in ['completed', 'error']:
            completed_tasks.append(task_id)
    
    # Remove completed tasks
    for task_id in completed_tasks:
        if task_id in st.session_state.background_tasks_status:
            del st.session_state.background_tasks_status[task_id]
    
    debug_log(f"Cleared {len(completed_tasks)} completed background tasks")