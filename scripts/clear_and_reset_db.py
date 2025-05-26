"""
CLI script to clear and reset the SQLite database for YTDataHub.
Creates a backup, drops all tables, and recreates the schema.
Usage: venv/bin/python scripts/clear_and_reset_db.py
"""
import os
import sys
from src.database.sqlite import SQLiteDatabase
from src.config import SQLITE_DB_PATH

def main():
    db_path = os.getenv('YOUTUBE_DB_PATH', SQLITE_DB_PATH)
    db = SQLiteDatabase(db_path)
    print(f"Clearing and resetting database at {db_path}...")
    success = db.clear_all_data()
    if success:
        print("Database cleared, schema recreated, and backup created.")
    else:
        print("Failed to clear and reset the database. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 