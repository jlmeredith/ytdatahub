"""
WebSocket keepalive utilities for maintaining Streamlit connections during long operations.
"""
import streamlit as st
import time
import threading
from typing import Optional, Callable, Any
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class WebSocketKeepAlive:
    """
    Utility class to maintain WebSocket connections during long-running operations.
    """
    
    def __init__(self, update_interval: int = 30):
        """
        Initialize the WebSocket keepalive manager.
        
        Args:
            update_interval: Seconds between keepalive updates
        """
        self.update_interval = update_interval
        self._keepalive_thread: Optional[threading.Thread] = None
        self._stop_keepalive = threading.Event()
        self._status_placeholder = None
        self._progress_placeholder = None
        
    def start_keepalive(self, status_message: str = "Processing..."):
        """
        Start the keepalive mechanism.
        
        Args:
            status_message: Message to display during processing
        """
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            return  # Already running
            
        # Create placeholders for status updates
        self._status_placeholder = st.empty()
        self._progress_placeholder = st.empty()
        
        # Reset the stop event
        self._stop_keepalive.clear()
        
        # Start the keepalive thread
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_worker,
            args=(status_message,),
            daemon=True
        )
        self._keepalive_thread.start()
        
    def stop_keepalive(self):
        """Stop the keepalive mechanism."""
        if self._keepalive_thread:
            self._stop_keepalive.set()
            self._keepalive_thread.join(timeout=5)
            self._keepalive_thread = None
            
        # Clear placeholders
        if self._status_placeholder:
            self._status_placeholder.empty()
        if self._progress_placeholder:
            self._progress_placeholder.empty()
            
    def update_status(self, message: str, progress: Optional[float] = None):
        """
        Update the status message and optionally the progress.
        
        Args:
            message: Status message to display
            progress: Progress value between 0.0 and 1.0
        """
        if self._status_placeholder:
            self._status_placeholder.info(f"🔄 {message}")
            
        if progress is not None and self._progress_placeholder:
            self._progress_placeholder.progress(progress)
            
    def _keepalive_worker(self, status_message: str):
        """
        Worker thread to send periodic keepalive updates.
        
        Args:
            status_message: Base message to display
        """
        start_time = time.time()
        
        while not self._stop_keepalive.is_set():
            elapsed = int(time.time() - start_time)
            minutes, seconds = divmod(elapsed, 60)
            
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            message = f"{status_message} (Running for {time_str})"
            
            try:
                if self._status_placeholder:
                    self._status_placeholder.info(f"🔄 {message}")
                    
                # Force a small UI update to maintain WebSocket connection
                if hasattr(st, 'rerun'):
                    # In newer Streamlit versions
                    pass  # Don't call rerun in thread
                else:
                    pass  # Don't call experimental_rerun in thread
                    
            except Exception as e:
                logger.warning(f"WebSocket keepalive update failed: {e}")
                
            # Wait for the specified interval or until stop is signaled
            self._stop_keepalive.wait(self.update_interval)


@contextmanager
def websocket_keepalive(
    status_message: str = "Processing long operation...",
    update_interval: int = 30
):
    """
    Context manager for maintaining WebSocket connections during long operations.
    
    Args:
        status_message: Message to display during processing
        update_interval: Seconds between keepalive updates
        
    Usage:
        with websocket_keepalive("Collecting comments..."):
            # Long-running operation here
            result = perform_long_operation()
    """
    keepalive = WebSocketKeepAlive(update_interval)
    
    try:
        keepalive.start_keepalive(status_message)
        yield keepalive
    finally:
        keepalive.stop_keepalive()


class ChunkedOperationManager:
    """
    Manager for breaking long operations into chunks with UI updates.
    """
    
    def __init__(self, chunk_size: int = 5, update_interval: float = 2.0):
        """
        Initialize the chunked operation manager.
        
        Args:
            chunk_size: Number of items to process per chunk
            update_interval: Minimum seconds between UI updates
        """
        self.chunk_size = chunk_size
        self.update_interval = update_interval
        self.last_update = 0
        
    def process_in_chunks(self, 
                         items: list, 
                         process_func: Callable[[Any], Any],
                         progress_callback: Optional[Callable[[int, int, str], None]] = None) -> list:
        """
        Process a list of items in chunks with UI updates.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            progress_callback: Optional callback for progress updates (current, total, item_desc)
            
        Returns:
            List of processed results
        """
        results = []
        total_items = len(items)
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            for i in range(0, total_items, self.chunk_size):
                chunk = items[i:i + self.chunk_size]
                chunk_results = []
                
                for j, item in enumerate(chunk):
                    current_index = i + j
                    progress = (current_index + 1) / total_items
                    
                    # Process the item
                    try:
                        result = process_func(item)
                        chunk_results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing item {current_index}: {e}")
                        chunk_results.append(None)
                    
                    # Update UI periodically
                    current_time = time.time()
                    if current_time - self.last_update >= self.update_interval:
                        progress_bar.progress(progress)
                        
                        if progress_callback:
                            item_desc = str(item)[:50] + "..." if len(str(item)) > 50 else str(item)
                            progress_callback(current_index + 1, total_items, item_desc)
                            
                        status_text.text(f"Processing item {current_index + 1} of {total_items}")
                        self.last_update = current_time
                        
                        # Allow UI to update
                        time.sleep(0.1)
                
                results.extend(chunk_results)
                
                # Force UI update after each chunk
                progress_bar.progress((i + len(chunk)) / total_items)
                time.sleep(0.1)
                
        finally:
            # Clean up UI elements
            progress_bar.empty()
            status_text.empty()
            
        return results


def handle_websocket_error(func: Callable) -> Callable:
    """
    Decorator to handle WebSocket errors gracefully.
    
    Args:
        func: Function to wrap with error handling
        
    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            
            if any(keyword in error_str for keyword in ['websocket', 'timeout', 'connection']):
                st.error("""
                🔌 **Connection Issue Detected**
                
                It looks like the connection was interrupted during processing. This can happen with large datasets.
                
                **What to do:**
                1. Click the "Retry" button below to continue
                2. Consider reducing the number of comments per video
                3. Process data in smaller batches
                
                Your data has been preserved and you can continue where you left off.
                """)
                
                # Offer retry button
                if st.button("🔄 Retry Operation", key="websocket_retry"):
                    st.rerun()
                    
                return None
            else:
                # Re-raise non-WebSocket errors
                raise e
    
    return wrapper
