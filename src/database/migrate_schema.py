"""
Migration script to update the YouTube Data Hub database schema.

This script will:
1. Create new tables with the updated schema
2. Copy data from existing tables to the new ones
3. Drop the old tables
4. Rename the new tables to the original names

Usage:
    python -m src.database.migrate_schema
"""

import sqlite3
import os
import sys
from pathlib import Path
import datetime
import shutil

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = str(Path(__file__).parent.parent.parent)
    if project_root not in sys.path:
        sys.path.append(project_root)

from src.utils.helpers import debug_log

def backup_database(db_path):
    """Create a backup of the database before migration."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}_{timestamp}.bak"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Database backup created at: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating database backup: {str(e)}")
        return False

def migrate_schema(db_path):
    """Migrate the database schema to the latest version."""
    print(f"Starting migration of database: {db_path}")
    
    # Backup the database
    if not backup_database(db_path):
        print("Migration aborted due to backup failure.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Check if old schema tables exist
        has_old_channels = "channels" in tables
        has_old_videos = "videos" in tables
        has_old_comments = "comments" in tables
        has_old_video_locations = "video_locations" in tables
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION;")
        
        # Migrate channels table
        if has_old_channels:
            print("Migrating channels table...")
            
            # Create new channels table
            cursor.execute('''
            CREATE TABLE channels_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE NOT NULL,
                title TEXT,
                subscriber_count INTEGER,
                video_count INTEGER,
                view_count INTEGER,
                description TEXT,
                custom_url TEXT,
                published_at TEXT,
                country TEXT,
                default_language TEXT,
                privacy_status TEXT,
                is_linked BOOLEAN,
                long_uploads_status TEXT,
                made_for_kids BOOLEAN,
                hidden_subscriber_count BOOLEAN,
                thumbnail_default TEXT,
                thumbnail_medium TEXT,
                thumbnail_high TEXT,
                keywords TEXT,
                topic_categories TEXT,
                fetched_at TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploads_playlist_id TEXT,
                local_thumbnail_medium TEXT,
                local_thumbnail_default TEXT,
                local_thumbnail_high TEXT,
                updated_at TEXT
            )
            ''')
            
            # Copy data from old to new table (with appropriate mapping)
            cursor.execute('''
            INSERT INTO channels_new (
                youtube_id, title, subscriber_count, video_count, view_count, 
                description, uploads_playlist_id, fetched_at, updated_at
            )
            SELECT 
                channel_id, channel_name, subscribers, total_videos, views, 
                channel_description, playlist_id, NULL, CURRENT_TIMESTAMP
            FROM channels
            ''')
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE channels;")
            cursor.execute("ALTER TABLE channels_new RENAME TO channels;")
            
            # Create indexes for the new channels table
            cursor.execute('CREATE INDEX idx_channels_youtube_id ON channels(youtube_id)')
            cursor.execute('CREATE INDEX idx_channels_id ON channels(id)')
        
        # Migrate videos table
        if has_old_videos:
            print("Migrating videos table...")
            
            # Create new videos table
            cursor.execute('''
            CREATE TABLE videos_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                youtube_id TEXT UNIQUE NOT NULL,
                channel_id INTEGER,
                title TEXT,
                description TEXT,
                published_at TEXT,
                view_count INTEGER,
                like_count INTEGER,
                dislike_count INTEGER,
                favorite_count INTEGER,
                comment_count INTEGER,
                duration TEXT,
                dimension TEXT,
                definition TEXT,
                caption BOOLEAN,
                licensed_content BOOLEAN,
                projection TEXT,
                privacy_status TEXT,
                license TEXT,
                embeddable BOOLEAN,
                public_stats_viewable BOOLEAN,
                made_for_kids BOOLEAN,
                thumbnail_default TEXT,
                thumbnail_medium TEXT,
                thumbnail_high TEXT,
                tags TEXT,
                category_id INTEGER,
                live_broadcast_content TEXT,
                fetched_at TEXT,
                updated_at TEXT,
                local_thumbnail_default TEXT,
                local_thumbnail_medium TEXT,
                local_thumbnail_high TEXT,
                FOREIGN KEY (channel_id) REFERENCES channels (id)
            )
            ''')
            
            # Copy data from old to new table
            # First, create a temporary mapping from old channel_id to new id
            cursor.execute('''
            CREATE TEMPORARY TABLE channel_id_map AS
            SELECT c.channel_id as old_id, cn.id as new_id 
            FROM channels cn
            JOIN (SELECT DISTINCT channel_id FROM videos) c ON cn.youtube_id = c.channel_id
            ''')
            
            # Now copy the data with the mapping
            cursor.execute('''
            INSERT INTO videos_new (
                youtube_id, channel_id, title, description, published_at,
                view_count, like_count, duration, caption, 
                thumbnail_high, fetched_at, updated_at
            )
            SELECT 
                v.video_id, m.new_id, v.title, v.video_description, v.published_at,
                v.views, v.likes, v.duration, v.caption_status,
                v.thumbnails, NULL, CURRENT_TIMESTAMP
            FROM videos v
            LEFT JOIN channel_id_map m ON v.channel_id = m.old_id
            ''')
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE videos;")
            cursor.execute("ALTER TABLE videos_new RENAME TO videos;")
            
            # Create indexes for the new videos table
            cursor.execute('CREATE INDEX idx_videos_channel_id ON videos(channel_id)')
            cursor.execute('CREATE INDEX idx_videos_youtube_id ON videos(youtube_id)')
            cursor.execute('CREATE INDEX idx_videos_id ON videos(id)')
        
        # Migrate comments table
        if has_old_comments:
            print("Migrating comments table...")
            
            # Create new comments table
            cursor.execute('''
            CREATE TABLE comments_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE NOT NULL,
                video_id INTEGER NOT NULL,
                text TEXT,
                author_display_name TEXT,
                author_profile_image_url TEXT,
                author_channel_id TEXT,
                like_count INTEGER,
                published_at TEXT,
                updated_at TEXT,
                parent_id INTEGER,
                is_reply BOOLEAN DEFAULT FALSE,
                fetched_at TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES comments (id) ON DELETE CASCADE
            )
            ''')
            
            # Create a temporary mapping from old video_id to new id
            cursor.execute('''
            CREATE TEMPORARY TABLE video_id_map AS
            SELECT c.video_id as old_id, cn.id as new_id 
            FROM videos cn
            JOIN (SELECT DISTINCT video_id FROM comments) c ON cn.youtube_id = c.video_id
            ''')
            
            # Copy data from old to new table
            cursor.execute('''
            INSERT INTO comments_new (
                comment_id, video_id, text, author_display_name, published_at, updated_at
            )
            SELECT 
                c.comment_id, m.new_id, c.comment_text, c.comment_author, c.comment_published_at, CURRENT_TIMESTAMP
            FROM comments c
            LEFT JOIN video_id_map m ON c.video_id = m.old_id
            ''')
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE comments;")
            cursor.execute("ALTER TABLE comments_new RENAME TO comments;")
            
            # Create indexes for the new comments table
            cursor.execute('CREATE INDEX idx_comments_video_id ON comments(video_id)')
            cursor.execute('CREATE INDEX idx_comments_comment_id ON comments(comment_id)')
        
        # Migrate or create video_locations table
        print("Handling video_locations table...")
        
        # Check if video_locations table exists
        if has_old_video_locations:
            print("Migrating existing video_locations table...")
            
            # Create new video_locations table
            cursor.execute('''
            CREATE TABLE video_locations_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                location_type TEXT NOT NULL,
                location_name TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                source TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
            )
            ''')
            
            # Since the videos table has been migrated, we need to map old video_ids to new ids
            cursor.execute('''
            CREATE TEMPORARY TABLE IF NOT EXISTS video_id_map AS
            SELECT v.video_id as old_id, vn.id as new_id 
            FROM videos vn
            JOIN (SELECT DISTINCT video_id FROM video_locations) v ON vn.youtube_id = v.video_id
            ''')
            
            # Copy data from old to new table
            cursor.execute('''
            INSERT INTO video_locations_new (
                video_id, location_type, location_name, confidence, source, created_at
            )
            SELECT 
                m.new_id, vl.location_type, vl.location_name, 
                COALESCE(vl.confidence, 0.0), 
                COALESCE(vl.source, 'auto'), 
                COALESCE(vl.created_at, CURRENT_TIMESTAMP)
            FROM video_locations vl
            LEFT JOIN video_id_map m ON vl.video_id = m.old_id
            WHERE m.new_id IS NOT NULL
            ''')
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE video_locations;")
            cursor.execute("ALTER TABLE video_locations_new RENAME TO video_locations;")
        else:
            # Create video_locations table if it doesn't exist
            print("Creating new video_locations table...")
            cursor.execute('''
            CREATE TABLE video_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                location_type TEXT NOT NULL,
                location_name TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                source TEXT DEFAULT 'auto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
            )
            ''')
        
        # Create indexes for the video_locations table
        cursor.execute('CREATE INDEX idx_video_locations_video_id ON video_locations(video_id)')
        cursor.execute('CREATE INDEX idx_video_locations_location ON video_locations(location_type, location_name)')
        
        # Commit the transaction
        cursor.execute("COMMIT;")
        
        # Vacuum the database to reclaim space
        cursor.execute("VACUUM;")
        
        # Close the connection
        conn.close()
        
        print("Migration completed successfully.")
        return True
    except Exception as e:
        # Rollback on error
        try:
            cursor.execute("ROLLBACK;")
        except:
            pass
        
        print(f"Error during migration: {str(e)}")
        return False

def main():
    """Main function to run the migration."""
    # Get the database path from environment or use default
    db_path = os.environ.get('YTDATAHUB_DATABASE', None)
    
    if not db_path:
        # Use default path
        project_root = Path(__file__).parent.parent.parent
        db_path = str(project_root / 'data' / 'youtube_data.db')
    
    # Check if the database exists
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    # Run the migration
    return migrate_schema(db_path)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)