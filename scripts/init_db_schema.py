"""
CLI script to initialize the SQLite database schema for YouTube data collection.
Creates the 'channels', 'playlists', and any other required tables.
"""
import os
import sqlite3
import sys

DB_PATH = os.getenv('YOUTUBE_DB_PATH', 'data/youtube_data.db')

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT UNIQUE NOT NULL,
    channel_title TEXT,
    uploads_playlist_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS playlists (
    playlist_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    type TEXT DEFAULT 'uploads',
    title TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
);
-- Add other tables as needed
"""

def main():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
        print(f"Database schema initialized at {DB_PATH}.")
    except Exception as e:
        print(f"Failed to initialize DB schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 