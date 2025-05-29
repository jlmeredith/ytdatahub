#!/usr/bin/env python3
"""
Debug script to examine database structure and data
"""
import sqlite3
import json
from src.config import SQLITE_DB_PATH

def examine_database():
    print(f'Database path: {SQLITE_DB_PATH}')
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('\nTables in database:')
    for table in tables:
        print(f'  - {table[0]}')

    # Check channels table schema
    if ('channels',) in tables:
        print('\nChannels table schema:')
        cursor.execute('PRAGMA table_info(channels);')
        channels_schema = cursor.fetchall()
        for col in channels_schema:
            print(f'  {col[1]} ({col[2]})')

        # Check if we have any channel data
        print('\nChannel data count:')
        cursor.execute('SELECT COUNT(*) FROM channels;')
        count = cursor.fetchone()[0]
        print(f'  Total channels: {count}')

        # Check a sample channel record to see timestamp fields
        if count > 0:
            print('\nSample channel record:')
            cursor.execute('SELECT * FROM channels LIMIT 1;')
            sample = cursor.fetchone()
            cursor.execute('PRAGMA table_info(channels);')
            schema = cursor.fetchall()
            for i, col in enumerate(schema):
                if i < len(sample):
                    value = sample[i]
                    if col[1] in ['created_at', 'updated_at', 'last_updated', 'fetched_at'] and value:
                        print(f'  {col[1]}: {value} ⭐')
                    else:
                        print(f'  {col[1]}: {value}')

    # Check channels_history table if it exists
    if ('channels_history',) in tables:
        print('\nChannels_history table schema:')
        cursor.execute('PRAGMA table_info(channels_history);')
        history_schema = cursor.fetchall()
        for col in history_schema:
            print(f'  {col[1]} ({col[2]})')

        cursor.execute('SELECT COUNT(*) FROM channels_history;')
        history_count = cursor.fetchone()[0]
        print(f'  Total history records: {history_count}')

    conn.close()

if __name__ == '__main__':
    examine_database()
