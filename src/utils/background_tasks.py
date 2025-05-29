"""
Background task management for YouTube data collection.
This module previously allowed for queued data collection tasks to run in the background.
The queue system has been fully removed. All data is now saved immediately.
"""

# All queue/background task functionality has been removed.
# If any function from this module is called, raise NotImplementedError.

def queue_data_collection_task(*args, **kwargs):
    raise NotImplementedError("Background queue system has been removed. Data is saved immediately.")

def ensure_worker_thread_running(*args, **kwargs):
    raise NotImplementedError("Background queue system has been removed.")

def background_worker_thread(*args, **kwargs):
    raise NotImplementedError("Background queue system has been removed.")

def stop_background_tasks(*args, **kwargs):
    raise NotImplementedError("Background queue system has been removed.")

def get_task_status(*args, **kwargs):
    raise NotImplementedError("Background queue system has been removed.")

def get_all_task_statuses(*args, **kwargs):
    raise NotImplementedError("Background queue system has been removed.")

def clear_completed_tasks(*args, **kwargs):
    raise NotImplementedError("Background queue system has been removed.")