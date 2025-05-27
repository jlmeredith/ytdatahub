import os
from src.database.video_repository import VideoRepository
from src.database.comment_repository import CommentRepository
from src.config import SQLITE_DB_PATH
from src.api.youtube.comment import CommentClient
from src.utils.helpers import debug_log

# --- Load .env if present ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv is not installed, skip (assume env is set)

import sqlite3

# Known public video with comments enabled (replace with a real one if needed)
TEST_VIDEO_ID = 'dQw4w9WgXcQ'  # Rick Astley - Never Gonna Give You Up

def get_video_db_id(db_path, youtube_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def insert_test_video_if_needed(db_path, youtube_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
    # Insert minimal video record
    cursor.execute("INSERT INTO videos (youtube_id, title, fetched_at, updated_at) VALUES (?, ?, datetime('now'), datetime('now'))", (youtube_id, 'Test Video',))
    conn.commit()
    cursor.execute("SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def main():
    db_path = SQLITE_DB_PATH
    video_repo = VideoRepository(db_path)
    comment_repo = CommentRepository(db_path)
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        raise RuntimeError('YOUTUBE_API_KEY environment variable not set!')
    comment_client = CommentClient(api_key)

    # Simulate a video dict as in the workflow
    video = {
        'video_id': TEST_VIDEO_ID,
        'title': 'Test Video',
        'comments': []
    }
    channel_info = {'video_id': [video]}

    # Fetch comments for the video
    print(f"[DEBUG] Fetching comments for video: {TEST_VIDEO_ID}")
    result = comment_client.get_video_comments(channel_info, max_comments_per_video=10)
    print(f"[DEBUG] Raw API response: {result}")
    # Extract comments from the correct path
    try:
        comments = result['video_id'][0]['comments']
    except (KeyError, IndexError, TypeError):
        print("[ERROR] Could not extract comments from API response. Full response:")
        print(result)
        return
    print(f"[DEBUG] Number of comments fetched: {len(comments)}")
    print(f"[DEBUG] First comment (if any): {comments[0] if comments else 'None'}")

    # --- Ensure the test video is present in the DB ---
    video_db_id = insert_test_video_if_needed(db_path, TEST_VIDEO_ID)
    print(f"[DEBUG] Using video_db_id: {video_db_id}")
    if not video_db_id:
        print("[ERROR] Could not insert or find test video in DB!")
        return

    # --- Ensure the comment_ingestion_stats table exists ---
    comment_repo.create_comment_ingestion_stats_table()

    # Store comments in DB
    print(f"[DEBUG] Storing comments for video_db_id: {video_db_id}")
    comment_repo.store_comments(comments, video_db_id=video_db_id)
    print(f"[DEBUG] Stored {len(comments)} comments in DB for video_db_id: {video_db_id}")
    # Log analytics for this ingestion
    comment_repo.log_comment_ingestion_stats(video_db_id, len(comments), len(comments))
    print(f"[DEBUG] Logged comment ingestion stats for video_db_id: {video_db_id}")

    # Query DB to verify
    stored_comments = comment_repo.get_video_comments(video_db_id)
    print(f"DB now contains {len(stored_comments)} comments for video {TEST_VIDEO_ID}")

if __name__ == '__main__':
    main() 