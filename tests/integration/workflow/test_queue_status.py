import pytest
from src.utils.queue_tracker import render_queue_status_sidebar, set_test_mode, clear_queue_hooks, add_to_queue, get_queue_stats

def test_queue_status_implementation():
    """
    Test that queue tracker stats update as items are added.
    """
    # Set up test mode
    set_test_mode(True)
    clear_queue_hooks()
    
    # Add some test items
    add_to_queue('channels', {'id': 'test1'})
    add_to_queue('videos', {'id': 'test2'})
    
    # Get stats
    stats = get_queue_stats()
    
    # Verify stats
    assert stats['channels_count'] == 1
    assert stats['videos_count'] == 1
    assert stats['total_items'] == 2
    
    # Clean up
    set_test_mode(False) 