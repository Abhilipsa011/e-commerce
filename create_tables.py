import sqlite3
from database_setup import get_db_connection, close_db_connection

def create_tables():
    """Creates the necessary database tables if they don't exist."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("Creating/Updating tables (if they don't exist)...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        print("- Ensured 'categories' table exists.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("- Ensured 'users' table exists with 'password_hash'.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                category_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (category_id)
            )
        """)
        print("- Ensured 'products' table exists with category link.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL DEFAULT 0.0,
                status TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        print("- Ensured 'orders' table exists.")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_at_order REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        """)
        print("- Ensured 'order_items' table exists.")

        conn.commit()
        print("Tables checked/created successfully.")

    except sqlite3.Error as e:
        print(f"Database error during table creation: {e}")
        if conn:
            conn.rollback()
    finally:
        close_db_connection(conn)

if __name__ == "__main__":
     create_tables()
