"""
CLI script to check and fix the schema of the 'channels' and 'playlists' tables in the SQLite DB.
If the schema is incorrect, drops and recreates the tables.
"""
import sqlite3
import os

DB_PATH = os.getenv('YOUTUBE_DB_PATH', 'data/youtube_data.db')

EXPECTED_CHANNELS = [
    ('id', 'INTEGER'),
    ('channel_id', 'TEXT'),
    ('channel_title', 'TEXT'),
    ('uploads_playlist_id', 'TEXT'),
    ('created_at', 'TIMESTAMP'),
    ('updated_at', 'TIMESTAMP'),
]
EXPECTED_PLAYLISTS = [
    ('playlist_id', 'TEXT'),
    ('channel_id', 'TEXT'),
    ('type', 'TEXT'),
    ('title', 'TEXT'),
    ('description', 'TEXT'),
    ('created_at', 'TIMESTAMP'),
    ('updated_at', 'TIMESTAMP'),
]

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
"""

def get_table_info(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return [(row[1], row[2]) for row in cur.fetchall()]

def print_schema(conn, table):
    print(f"Schema for {table}:")
    for col, typ in get_table_info(conn, table):
        print(f"  {col} ({typ})")

def schema_matches(actual, expected):
    return all(any(a[0] == e[0] and a[1].startswith(e[1]) for a in actual) for e in expected)

def main():
    conn = sqlite3.connect(DB_PATH)
    print(f"Checking schema in {DB_PATH}...\n")
    for table, expected in [('channels', EXPECTED_CHANNELS), ('playlists', EXPECTED_PLAYLISTS)]:
        try:
            actual = get_table_info(conn, table)
            print_schema(conn, table)
            if not schema_matches(actual, expected):
                print(f"\n[WARNING] {table} schema does not match expected. Dropping and recreating...")
                conn.execute(f"DROP TABLE IF EXISTS {table};")
                conn.commit()
            else:
                print(f"[OK] {table} schema matches expected.\n")
        except Exception as e:
            print(f"[ERROR] Could not check {table}: {e}")
    # Recreate tables if missing
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    print("\nSchema after fix:")
    for table in ['channels', 'playlists']:
        print_schema(conn, table)
    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main() 