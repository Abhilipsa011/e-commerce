import sqlite3
from database_setup import get_db_connection, close_db_connection
import datetime  # Needed for create_order

# --- Category Operations ---

def add_category(name):
    """Adds a new category to the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Category '{name}' might already exist.")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding category: {e}")
        return None
    finally:
        close_db_connection(conn)

def list_categories():
    """Lists all categories."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
        categories = cursor.fetchall()
        # Convert Row objects to dictionaries for easier use in GUI
        return [dict(row) for row in categories]
    except sqlite3.Error as e:
        print(f"Database error listing categories: {e}")
        return []
    finally:
        close_db_connection(conn)

def get_category_id_by_name(name):
    """Gets the category ID for a given category name."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_id FROM categories WHERE name = ?", (name,))
        result = cursor.fetchone()
        return result['category_id'] if result else None
    except sqlite3.Error as e:
        print(f"Database error getting category ID: {e}")
        return None
    finally:
        close_db_connection(conn)


# --- Product Operations ---

def add_product(name, description, price, stock, category_id):
    """Adds a new product to the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, description, price, stock, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, price, stock, category_id))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error adding product: {e}")
        return None
    finally:
        close_db_connection(conn)

def find_product_by_id(product_id):
    """Finds a product by its ID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.product_id, p.name, p.description, p.price, p.stock, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_id = ?
        """, (product_id,))
        product = cursor.fetchone()
        return dict(product) if product else None
    except sqlite3.Error as e:
        print(f"Database error finding product by ID: {e}")
        return None
    finally:
        close_db_connection(conn)

def list_products(category_id=None):
    """Lists all products, optionally filtered by category."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT p.product_id, p.name, p.description, p.price, p.stock, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
        """
        params = []
        if category_id is not None:
            query += " WHERE p.category_id = ?"
            params.append(category_id)
        query += " ORDER BY p.name"
        cursor.execute(query, params)
        products = cursor.fetchall()
        return [dict(row) for row in products]
    except sqlite3.Error as e:
        print(f"Database error listing products: {e}")
        return []
    finally:
        close_db_connection(conn)

def update_product_stock(product_id, new_stock):
    """Updates the stock quantity for a given product."""
    conn = None
    updated = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET stock = ? WHERE product_id = ?", (new_stock, product_id))
        conn.commit()
        # Check if any row was actually updated
        updated = cursor.rowcount > 0
        if not updated:
             print(f"Warning: No product found with ID {product_id} to update stock.")
    except sqlite3.Error as e:
        print(f"Database error updating stock for product ID {product_id}: {e}")
    finally:
        close_db_connection(conn)
    return updated

def delete_product(product_id):
    """Deletes a product from the database."""
    conn = None
    deleted = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Attempt to delete the product
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        if not deleted:
            print(f"Warning: No product found with ID {product_id} to delete.")
    except sqlite3.IntegrityError:
        # This occurs if the product is referenced in order_items
        print(f"Error: Cannot delete product ID {product_id} because it is referenced in existing orders.")
        deleted = False # Explicitly set to False on integrity error
    except sqlite3.Error as e:
        print(f"Database error deleting product ID {product_id}: {e}")
        deleted = False
    finally:
        close_db_connection(conn)
    return deleted


# --- User Operations ---

def add_user(username, email, password_hash):
    """Adds a new user to the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                       (username, email, password_hash))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Username '{username}' or email '{email}' might already exist.")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding user: {e}")
        return None
    finally:
        close_db_connection(conn)

def find_user_by_username(username):
    """Finds a user by username and returns their data including the password hash."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ensure the SELECT statement includes password_hash
        cursor.execute("SELECT user_id, username, email, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone() # fetchone() returns a Row object or None
        return user # Return the Row object directly (or None if not found)
    except sqlite3.Error as e:
        print(f"Database error finding user: {e}")
        return None
    finally:
        close_db_connection(conn)


# --- Order Operations ---

def create_order(user_id, items):
    """Creates a new order and associated order items, updating stock within a transaction."""
    conn = None
    order_id = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION") # Start transaction

        # 1. Create the order record
        order_date = datetime.datetime.now()
        cursor.execute("INSERT INTO orders (user_id, order_date) VALUES (?, ?)", (user_id, order_date))
        order_id = cursor.lastrowid

        # 2. Add order items and update stock
        for product_id, quantity in items:
            # Check current stock
            cursor.execute("SELECT stock, price FROM products WHERE product_id = ?", (product_id,))
            product_data = cursor.fetchone()
            if not product_data:
                raise ValueError(f"Product ID {product_id} not found during order creation.")
            current_stock = product_data['stock']
            price_at_order = product_data['price']

            if current_stock < quantity:
                raise ValueError(f"Insufficient stock for product ID {product_id} (requested: {quantity}, available: {current_stock}).")

            # Insert into order_items
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price_at_order)
                VALUES (?, ?, ?, ?)
            """, (order_id, product_id, quantity, price_at_order))

            # Update product stock
            new_stock = current_stock - quantity
            cursor.execute("UPDATE products SET stock = ? WHERE product_id = ?", (new_stock, product_id))

        # 3. Commit transaction
        conn.commit()
        print(f"Order {order_id} created successfully.")

    except (sqlite3.Error, ValueError) as e:
        print(f"Error creating order: {e}")
        if conn:
            conn.rollback() # Roll back changes if any error occurred
        order_id = None # Ensure order_id is None if transaction failed
    finally:
        close_db_connection(conn)

    return order_id

def get_user_orders(user_id):
    """Retrieves all orders for a specific user."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch total amount directly from orders table if stored, otherwise calculate later
        cursor.execute("""
            SELECT order_id, order_date, total_amount, status
            FROM orders
            WHERE user_id = ?
            ORDER BY order_date DESC
        """, (user_id,))
        orders = cursor.fetchall()
        return [dict(row) for row in orders]
    except sqlite3.Error as e:
        print(f"Database error getting user orders: {e}")
        return []
    finally:
        close_db_connection(conn)

def get_order_items(order_id):
    """Retrieves all items for a specific order, including product name."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Join with products table to get the product name
        # Note: Uses price_at_order stored in order_items
        cursor.execute("""
            SELECT oi.item_id, oi.product_id, p.name as product_name, oi.quantity, oi.price_at_order
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
        """, (order_id,))
        items = cursor.fetchall()
        return [dict(row) for row in items]
    except sqlite3.Error as e:
        print(f"Database error getting order items for order {order_id}: {e}")
        return []
    finally:
        close_db_connection(conn)