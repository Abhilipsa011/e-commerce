import sqlite3
import datetime

DATABASE_FILE = "my_ecommerce.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    # Return rows as dictionary-like objects (easier to access columns by name)
    conn.row_factory = sqlite3.Row
    print(f"Connected to database: {DATABASE_FILE}")
    return conn

def close_db_connection(conn):
    """Closes the database connection."""
    if conn:
        conn.close()
        print("Database connection closed.")
