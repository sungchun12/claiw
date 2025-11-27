import sqlite3
from contextlib import contextmanager

DB_PATH = "workflows.db"

def init_db():
    """Initialize the database with the workflows table."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                name TEXT PRIMARY KEY,
                description TEXT,
                code_content TEXT,
                file_path TEXT
            )
        """)
        conn.commit()

@contextmanager
def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()

