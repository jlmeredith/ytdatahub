import os
import sqlite3
import tempfile
import subprocess
import sys

def test_init_db_schema_creates_channels_table():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        db_path = tf.name
    try:
        env = os.environ.copy()
        env['YOUTUBE_DB_PATH'] = db_path
        subprocess.run([sys.executable, 'scripts/init_db_schema.py'], check=True, env=env)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='channels';")
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "channels table should exist after init script runs"
    finally:
        os.remove(db_path)

def test_clear_and_reset_db_script_clears_and_recreates_schema():
    import subprocess
    import sys
    import sqlite3
    import tempfile
    import os
    # Create a temp DB and add a row
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        db_path = tf.name
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE channels (id INTEGER PRIMARY KEY, name TEXT)")
        cur.execute("INSERT INTO channels (name) VALUES ('test')")
        conn.commit()
        conn.close()
        # Run the clear_and_reset_db script
        env = os.environ.copy()
        env['YOUTUBE_DB_PATH'] = db_path
        subprocess.run([sys.executable, 'scripts/clear_and_reset_db.py'], check=True, env=env)
        # Check that the schema exists and is empty
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='channels'")
        assert cur.fetchone() is not None, "channels table should exist after reset"
        cur.execute("SELECT COUNT(*) FROM channels")
        assert cur.fetchone()[0] == 0, "channels table should be empty after reset"
        conn.close()
    finally:
        os.remove(db_path) 