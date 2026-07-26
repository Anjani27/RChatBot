"""SQLite connection and schema initialisation."""
import sqlite3
from app.core.config import SQLITE_DB_PATH

# Shared connection reused across the app
conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row


def init_db() -> None:
    """Create tables if they do not exist and handle migrations."""
    cursor = conn.cursor()
    
    # Create users table with email as primary key
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Create sessions table referencing email
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(email) REFERENCES users(email) ON DELETE CASCADE
        )
    """)

    # Create conversation_meta table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_meta (
            thread_id  TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Add email column if not exists
    cursor.execute("PRAGMA table_info(conversation_meta)")
    columns = [row[1] for row in cursor.fetchall()]
    if "email" not in columns:
        cursor.execute("ALTER TABLE conversation_meta ADD COLUMN email TEXT")
        
    conn.commit()


def get_new_conn() -> sqlite3.Connection:
    """Return a fresh connection (used for write operations to avoid locking)."""
    c = sqlite3.connect(SQLITE_DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    return c
