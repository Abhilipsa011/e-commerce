import sqlite3  # Make sure sqlite3 is imported
from create_tables import create_tables
from db_operations import (
    add_user,
    find_user_by_username,
    add_product,
    find_product_by_id,
    list_products,
    create_order,
    add_category,             # <-- Must import this
    get_category_id_by_name,  # <-- Must import this
    list_categories           # <-- Good for verification
)

# Import constants if needed, e.g., from database_setup or define here
DEFAULT_USERNAME = "default_user"
INITIAL_DEFAULT_USER_ID = 1  # Assuming this is the ID for default_user

if __name__ == "__main__":
    print("--- E-commerce Setup & Simulation ---")

    # 1. Create tables if they don't exist
    print("\n[1] Ensuring database tables exist...")
    try:
        create_tables()
        print("    Tables checked/created successfully.")
    except Exception as e:
        print(f"    ERROR creating tables: {e}")
        exit()  # Stop if tables can't be created

    # 2. Add sample data (run only if needed)
    print("\n[2] Adding Sample Data (if missing)...")

    # Add Categories first (check if they exist)
    print("    Checking/Adding Categories...")
    electronics_id = get_category_id_by_name("Electronics")
    if electronics_id is None:
        electronics_id = add_category("Electronics")  # Add category
        if electronics_id:
            print(f"      - Added 'Electronics' (ID: {electronics_id})")
        else:
            print("      - FAILED to add 'Electronics'")

    accessories_id = get_category_id_by_name("Accessories")
    if accessories_id is None:
        accessories_id = add_category("Accessories")  # Add category
        if accessories_id:
            print(f"      - Added 'Accessories' (ID: {accessories_id})")
        else:
            print("      - FAILED to add 'Accessories'")

    # Add users (check if they exist first to avoid errors on re-runs)
    print("    Checking/Adding Users...")
    user = find_user_by_username("alice")
    if not user:
        if add_user("alice", "alice@example.com", "pass1"):
            print("      - Added user 'alice'")
        else:
            print("      - FAILED to add user 'alice'")

    user = find_user_by_username("bob")
    if not user:
        if add_user("bob", "bob@example.com", "pass2"):
            print("      - Added user 'bob'")
        else:
            print("      - FAILED to add user 'bob'")

    # Add default user for GUI if it doesn't exist
    default_user = find_user_by_username(DEFAULT_USERNAME)
    if not default_user:
        # Ensure the default user gets the expected ID if possible,
        # though auto-increment usually handles this.
        if add_user(DEFAULT_USERNAME, f"{DEFAULT_USERNAME}@example.com", "password"):
            # Assuming add_user returns the new user_id or True on success
            # Let's find the user again to be sure about the ID for the message
            new_default_user = find_user_by_username(DEFAULT_USERNAME)
            if new_default_user:
                print(f"      - Added default GUI user '{DEFAULT_USERNAME}' (ID: {new_default_user['user_id']})")
            else:
                print(f"      - Added default GUI user '{DEFAULT_USERNAME}' (ID lookup failed)")
        else:
            print(f"      - FAILED to add default GUI user '{DEFAULT_USERNAME}'")

    # Add products (check if they exist first and use correct category IDs)
    print("    Checking/Adding Products...")
    if electronics_id is not None:  # Only add if category was successfully added/found
        prod1 = find_product_by_id(1)
        if not prod1:
            # Use the retrieved electronics_id
            if add_product("Laptop", "Fast laptop", 1199.99, 15, electronics_id):
                print("      - Added 'Laptop'")
            else:
                print("      - FAILED to add 'Laptop'")
        prod2 = find_product_by_id(2)
        if not prod2:
            # Use the retrieved electronics_id
            if add_product("Wireless Mouse", "Ergonomic mouse", 24.50, 50, electronics_id):
                print("      - Added 'Wireless Mouse'")
            else:
                print("      - FAILED to add 'Wireless Mouse'")
    else:
        print("      - Warning: Could not add Electronics products, category ID not available.")

    if accessories_id is not None:  # Only add if category was successfully added/found
        prod3 = find_product_by_id(3)
        if not prod3:
            # Use the retrieved accessories_id
            if add_product("USB Cable", "USB-C to USB-A", 9.99, 100, accessories_id):
                print("      - Added 'USB Cable'")
            else:
                print("      - FAILED to add 'USB Cable'")
    else:
        print("      - Warning: Could not add Accessories products, category ID not available.")

    # 3. List available products and categories for verification
    print("\n[3] Verifying Data...")
    try:
        print("    --- Current Categories ---")
        all_categories = list_categories()
        if all_categories:
            for cat in all_categories:
                # Assuming list_categories returns dicts like {'category_id': 1, 'name': 'Electronics'}
                print(f"      - ID: {cat['category_id']}, Name: {cat['name']}")
        else:
            print("      No categories found.")

        print("    --- Current Products ---")
        available_products = list_products()  # Assuming list_products joins with categories or handles it
        if available_products:
            for p in available_products:
                # Adjust keys based on what list_products actually returns
                cat_name = p.get('category_name', 'N/A')  # Example if category name is joined
                print(f"      - ID: {p['product_id']}, Name: {p['name']}, Cat: {cat_name}, Price: ${p['price']:.2f}, Stock: {p['stock']}")
        else:
            print("      No products found.")
        print("    ------------------------")
    except Exception as e:
        print(f"    ERROR verifying data: {e}")

    print("\n--- Setup & Simulation Complete ---")
