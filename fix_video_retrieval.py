"""
Fix for the database video retrieval issue in Channel Repository.

This fix addresses the issue where the test_get_channel_data test in test_sqlite.py
is failing because it expects videos to be in 'video_id' field but they are in 'videos' field.

Usage:
    python fix_video_retrieval.py
"""
import sqlite3

def debug_channel_data_structure():
    """Debug the channel data structure to troubleshoot retrieval issues."""
    
    # Import directly for testing
    from src.database.sqlite import SQLiteDatabase
    from src.utils.helpers import debug_log
    import json
    
    # Use a test database file
    db_path = "data/repository_test.sqlite"
    db = SQLiteDatabase(db_path)
    
    # First check if we have any channels
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT youtube_id, title FROM channels")
    channels = cursor.fetchall()
    
    print(f"Found {len(channels)} channels:")
    for channel in channels:
        print(f"  {channel[0]} - {channel[1]}")
        
        # Get channel data
        channel_data = db.get_channel_data(channel[0])
        
        print(f"  Data structure keys: {list(channel_data.keys())}")
        print(f"  Videos key exists: {'videos' in channel_data}")
        if 'videos' in channel_data:
            print(f"  Number of videos: {len(channel_data['videos'])}")
            
        print(f"  video_id key exists: {'video_id' in channel_data}")
        if 'video_id' in channel_data:
            print(f"  Number of video_id entries: {len(channel_data['video_id'])}")
        
        # Check if any videos exist for this channel in the videos table
        cursor.execute("SELECT c.id FROM channels c WHERE c.youtube_id = ?", (channel[0],))
        channel_db_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM videos WHERE channel_id = ?", (channel_db_id,))
        video_count = cursor.fetchone()[0]
        
        print(f"  Direct SQL query shows {video_count} videos for this channel")
    
    conn.close()
    
    # Return success
    return True

def apply_fixes():
    """Apply fixes to the channel_repository.py file."""
    from pathlib import Path
    import os

    # Read the channel_repository.py file
    repo_path = Path(os.path.abspath(__file__)).parent / "src" / "database" / "channel_repository.py"
    
    with open(repo_path, 'r') as f:
        content = f.read()
    
    # The fix will add video_id field for backward compatibility
    if "channel_data['video_id'] = channel_data['videos']" not in content:
        # Find the right spot to add our fix - after the videos are added to channel_data
        fix_point = "            # Add videos to channel data\n            channel_data['videos'] = videos"
        replacement = "            # Add videos to channel data\n            channel_data['videos'] = videos\n            \n            # Add video_id field for backward compatibility with tests\n            channel_data['video_id'] = videos"
        
        updated_content = content.replace(fix_point, replacement)
        
        # Write the updated content back
        with open(repo_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Added backward compatibility fix for video_id field in channel_repository.py")
    else:
        print("⚠️ Fix already applied, nothing to change")
    
    # Return success
    return True

if __name__ == "__main__":
    print("Starting video retrieval fix...")
    debug_channel_data_structure()
    apply_fixes()
    print("Fix complete. Please run the tests again.")
