import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
import datetime
import os

# --- Add ReportLab imports ---
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
    from reportlab.lib.units import inch
    from reportlab.lib import colors
except ImportError:
    messagebox.showerror("Missing Library", "ReportLab library not found. Please install it using:\n\npip install reportlab")
    exit()
# -----------------------------

try:
    from create_tables import create_tables
    from db_operations import (
        add_product, find_product_by_id, list_products, update_product_stock, delete_product,
        create_order,
        add_category, list_categories,
        get_user_orders, get_order_items
    )
    from auth_gui import AuthWindow
except ImportError as e:
    print(f"Error importing database/auth modules: {e}")
    print("Ensure database_setup.py, create_tables.py, db_operations.py, and auth_gui.py are present.")
    exit()

# --- Constants ---
ALL_CATEGORIES = "All Categories"
CURRENCY_SYMBOL = "₹"
# --- Color Palette ---
BG_COLOR = "#F0F0F0"
FRAME_BG_COLOR = "#FFFFFF"
ACCENT_COLOR = "#0078D7"
ACCENT_LIGHT = "#E0F2FF"
TEXT_COLOR = "#333333"
BUTTON_FG_COLOR = "#FFFFFF"
BUTTON_BG_COLOR = ACCENT_COLOR
BUTTON_ACTIVE_BG = "#005A9E"
TREE_HEADING_BG = "#E1E1E1"
TREE_ROW_EVEN_BG = "#FFFFFF"
TREE_ROW_ODD_BG = "#F5F5F5"
STATUS_BAR_BG = "#E1E1E1"
ERROR_COLOR = "#D32F2F"
SUCCESS_COLOR = "#388E3C"
# --- End Constants ---

# --- Invoice Directory ---
INVOICE_DIR = "invoices"


class AddProductWindow(tk.Toplevel):
    """Window for adding a new product."""
    def __init__(self, parent, categories_list, callback_on_save):
        super().__init__(parent)
        self.title("Add New Product")
        self.geometry("450x400")
        self.parent = parent
        self.callback = callback_on_save
        self.configure(bg=BG_COLOR)

        self.categories = {cat['name']: cat['category_id'] for cat in categories_list}
        if not self.categories:
             messagebox.showerror("No Categories", "Please add at least one category before adding products.", parent=self)
             self.destroy()
             return

        frame = ttk.Frame(self, padding="15 15 15 15", style='Card.TFrame')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Name:", style='Input.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(frame, width=40, style='TEntry')
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(frame, text="Description:", style='Input.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(frame, width=40, style='TEntry')
        self.desc_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(frame, text=f"Price ({CURRENCY_SYMBOL}):", style='Input.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.price_entry = ttk.Entry(frame, width=15, style='TEntry')
        self.price_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame, text="Stock:", style='Input.TLabel').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.stock_entry = ttk.Entry(frame, width=15, style='TEntry')
        self.stock_entry.grid(row=3, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame, text="Category:", style='Input.TLabel').grid(row=4, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        category_keys = sorted(list(self.categories.keys())) if self.categories else []
        self.category_combo = ttk.Combobox(frame, textvariable=self.category_var, values=category_keys, state='readonly', width=37, style='TCombobox')
        if category_keys:
            self.category_combo.current(0)
        self.category_combo.grid(row=4, column=1, sticky=tk.EW, pady=5)

        button_frame = ttk.Frame(frame, style='Card.TFrame')
        button_frame.grid(row=5, column=0, columnspan=2, pady=25)
        ttk.Button(button_frame, text="Save Product", command=self.save_product, style='Accent.TButton', width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.destroy, style='Outline.TButton', width=15).pack(side=tk.LEFT, padx=10)

        frame.columnconfigure(1, weight=1)
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        self.name_entry.focus()

    def save_product(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        price_str = self.price_entry.get().strip()
        stock_str = self.stock_entry.get().strip()
        category_name = self.category_var.get()

        if not all([name, price_str, stock_str, category_name]):
            messagebox.showerror("Missing Info", "Please fill in Name, Price, Stock, and select a Category.", parent=self)
            return

        try:
            price = float(price_str)
            stock = int(stock_str)
            if price < 0 or stock < 0:
                raise ValueError("Price and stock cannot be negative.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Invalid price or stock value: {e}", parent=self)
            return

        category_id = self.categories.get(category_name)
        if category_id is None:
             messagebox.showerror("Category Error", "Selected category not found.", parent=self)
             return

        try:
            product_id = add_product(name, desc, price, stock, category_id)

            if product_id:
                messagebox.showinfo("Success", f"Product '{name}' added successfully (ID: {product_id}).", parent=self)
                if self.callback:
                    self.callback()
                self.destroy()
            else:
                messagebox.showerror("Database Error", "Failed to add product to the database (add_product returned non-ID). Check console.", parent=self)
        except Exception as e:
             messagebox.showerror("Database Error", f"An error occurred while adding the product: {e}", parent=self)


class OrderHistoryWindow(tk.Toplevel):
    """Window to display user's order history."""
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.title("My Order History")
        self.geometry("900x600")
        self.parent = parent
        self.user_id = user_id
        self.configure(bg=BG_COLOR)

        self.style = ttk.Style(self)

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(left_frame, text="My Orders", font=parent.heading_font).pack(pady=(0, 10), anchor=tk.W)

        orders_tree_frame = ttk.Frame(left_frame)
        orders_tree_frame.pack(fill=tk.BOTH, expand=True)

        order_cols = ("ID", "Date", "Total")
        self.orders_tree = ttk.Treeview(orders_tree_frame, columns=order_cols, show='headings', style='Treeview', selectmode='browse')
        self.orders_tree.heading("ID", text="Order ID", anchor=tk.W)
        self.orders_tree.column("ID", width=80, stretch=False, anchor=tk.W)
        self.orders_tree.heading("Date", text="Date", anchor=tk.W)
        self.orders_tree.column("Date", width=150, anchor=tk.W)
        self.orders_tree.heading("Total", text=f"Total ({CURRENCY_SYMBOL})", anchor=tk.E)
        self.orders_tree.column("Total", width=100, anchor=tk.E)

        order_scrollbar = ttk.Scrollbar(orders_tree_frame, orient="vertical", command=self.orders_tree.yview)
        self.orders_tree.configure(yscrollcommand=order_scrollbar.set)
        order_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.orders_tree.tag_configure('oddrow', background=TREE_ROW_ODD_BG)
        self.orders_tree.tag_configure('evenrow', background=TREE_ROW_EVEN_BG)

        self.orders_tree.bind("<<TreeviewSelect>>", self.on_order_select)

        ttk.Label(right_frame, text="Order Details", font=parent.heading_font).pack(pady=(0, 10), anchor=tk.W)

        items_tree_frame = ttk.Frame(right_frame)
        items_tree_frame.pack(fill=tk.BOTH, expand=True)

        item_cols = ("Product", "Qty", f"Price ({CURRENCY_SYMBOL})", f"Item Total ({CURRENCY_SYMBOL})")
        self.items_tree = ttk.Treeview(items_tree_frame, columns=item_cols, show='headings', style='Treeview')
        self.items_tree.heading("Product", text="Product Name", anchor=tk.W)
        self.items_tree.column("Product", width=250, anchor=tk.W)
        self.items_tree.heading("Qty", text="Qty", anchor=tk.E)
        self.items_tree.column("Qty", width=60, anchor=tk.E)
        self.items_tree.heading(f"Price ({CURRENCY_SYMBOL})", text=f"Unit Price", anchor=tk.E)
        self.items_tree.column(f"Price ({CURRENCY_SYMBOL})", width=100, anchor=tk.E)
        self.items_tree.heading(f"Item Total ({CURRENCY_SYMBOL})", text="Item Total", anchor=tk.E)
        self.items_tree.column(f"Item Total ({CURRENCY_SYMBOL})", width=100, anchor=tk.E)

        item_scrollbar = ttk.Scrollbar(items_tree_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=item_scrollbar.set)
        item_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.items_tree.tag_configure('oddrow', background=TREE_ROW_ODD_BG)
        self.items_tree.tag_configure('evenrow', background=TREE_ROW_EVEN_BG)

        self.load_orders()

        self.transient(parent)
        self.grab_set()

    def load_orders(self):
        """Loads the user's orders into the orders treeview."""
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        orders = get_user_orders(self.user_id)
        if orders:
            for i, order in enumerate(orders):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                order_date_str = order['order_date']
                try:
                    dt_obj = datetime.datetime.fromisoformat(order_date_str)
                    formatted_date = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    formatted_date = order_date_str

                self.orders_tree.insert("", tk.END, values=(
                    order['order_id'],
                    formatted_date,
                    f"{order['total_amount']:.2f}"
                ), tags=(tag,))
        else:
            self.orders_tree.insert("", tk.END, values=("", "No orders found.", ""))

    def on_order_select(self, _event=None):
        """Loads items for the selected order."""
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        selected_items = self.orders_tree.selection()
        if not selected_items:
            return

        order_item_id = selected_items[0]
        try:
            order_id = int(self.orders_tree.item(order_item_id)['values'][0])
        except (IndexError, ValueError):
            return

        items = get_order_items(order_id)
        if items:
            for i, item in enumerate(items):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                item_total = item['quantity'] * item['price_at_order']
                self.items_tree.insert("", tk.END, values=(
                    item['product_name'],
                    item['quantity'],
                    f"{item['price_at_order']:.2f}",
                    f"{item_total:.2f}"
                ), tags=(tag,))
        else:
             self.items_tree.insert("", tk.END, values=("", "No items found for this order.", "", ""))


class EcommerceGUI(tk.Toplevel):
    def __init__(self, parent, user_info):
        try:
            super().__init__(parent)
            self.parent = parent
            self.user_info = user_info
            print("DEBUG: EcommerceGUI super().__init__() called successfully.")

            self.current_user_id = user_info['user_id']
            self.current_username = user_info['username']

            print(f"DEBUG: Initializing EcommerceGUI for {self.current_username}...")

            self.title(f"E-commerce Platform - Logged in as {self.current_username}")
            self.geometry("1100x750")
            self.configure(bg=BG_COLOR)
            self.protocol("WM_DELETE_WINDOW", self.on_closing)

            print("DEBUG: Applying styles...")
            self.style = ttk.Style(self)
            try:
                self.style.theme_use('clam')
            except tk.TclError:
                print("Warning: 'clam' theme not available, using default.")

            try:
                self.default_font = font.nametofont("TkDefaultFont")
                self.default_font.configure(size=10)
                self.heading_font = font.Font(family="Segoe UI", size=11, weight="bold")
                self.label_font = font.Font(family="Segoe UI", size=10)
                self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
                self.status_font = font.Font(family="Segoe UI", size=9)
            except tk.TclError:
                print("Warning: Failed to load 'Segoe UI' font. Using default fonts.")
                self.default_font = font.nametofont("TkDefaultFont")
                self.heading_font = font.nametofont("TkDefaultFont")
                self.label_font = font.nametofont("TkDefaultFont")
                self.button_font = font.nametofont("TkDefaultFont")
                self.status_font = font.nametofont("TkDefaultFont")

            self.style.configure('.', font=self.default_font, background=BG_COLOR, foreground=TEXT_COLOR)
            self.style.configure('TFrame', background=BG_COLOR)
            self.style.configure('Card.TFrame', background=FRAME_BG_COLOR, relief=tk.SOLID, borderwidth=1)
            self.style.configure('TLabel', background=BG_COLOR, foreground=TEXT_COLOR, font=self.label_font, padding=2)
            self.style.configure('Input.TLabel', background=FRAME_BG_COLOR, foreground=TEXT_COLOR, font=self.label_font)
            self.style.configure('Header.TLabel', background=FRAME_BG_COLOR, foreground=TEXT_COLOR, font=self.heading_font, padding=5)
            self.style.configure('Total.TLabel', background=FRAME_BG_COLOR, foreground=TEXT_COLOR, font=self.heading_font)
            self.style.configure('TButton', font=self.button_font, padding=(10, 5), relief=tk.FLAT, borderwidth=1)
            self.style.map('TButton',
                           background=[('active', BUTTON_ACTIVE_BG), ('!disabled', BUTTON_BG_COLOR)],
                           foreground=[('!disabled', BUTTON_FG_COLOR)])
            self.style.configure('Accent.TButton', font=self.button_font, padding=(10, 5), relief=tk.FLAT, borderwidth=0)
            self.style.map('Accent.TButton',
                           background=[('active', BUTTON_ACTIVE_BG), ('!disabled', BUTTON_BG_COLOR)],
                           foreground=[('!disabled', BUTTON_FG_COLOR)])
            self.style.configure('Outline.TButton', font=self.button_font, padding=(10, 5), relief=tk.SOLID, borderwidth=1)
            self.style.map('Outline.TButton',
                           foreground=[('active', ACCENT_COLOR), ('!disabled', ACCENT_COLOR)],
                           background=[('active', ACCENT_LIGHT), ('!disabled', FRAME_BG_COLOR)],
                           bordercolor=[('!disabled', ACCENT_COLOR)])
            self.style.configure('TCombobox', padding=5, fieldbackground=FRAME_BG_COLOR)
            self.style.map('TCombobox', fieldbackground=[('readonly', FRAME_BG_COLOR)])
            self.style.configure('TEntry', padding=5, fieldbackground=FRAME_BG_COLOR)
            self.style.configure('Treeview',
                                 background=FRAME_BG_COLOR,
                                 fieldbackground=FRAME_BG_COLOR,
                                 foreground=TEXT_COLOR,
                                 rowheight=28,
                                 font=self.label_font)
            self.style.map('Treeview',
                           background=[('selected', ACCENT_LIGHT)],
                           foreground=[('selected', TEXT_COLOR)])
            self.style.configure('Treeview.Heading',
                                 background=TREE_HEADING_BG,
                                 foreground=TEXT_COLOR,
                                 font=self.heading_font,
                                 padding=5,
                                 relief=tk.FLAT)
            self.style.map('Treeview.Heading', relief=[('active','groove')])
            self.style.configure('Status.TLabel', background=STATUS_BAR_BG, foreground=TEXT_COLOR, font=self.status_font, padding=5, relief=tk.SUNKEN, anchor=tk.W)
            print("DEBUG: Styles applied.")

            self.cart = {}
            self.categories_cache = []

            print("DEBUG: Creating widgets...")
            top_frame = ttk.Frame(self, padding="10 5")
            top_frame.pack(fill=tk.X, side=tk.TOP)

            middle_frame = ttk.Frame(self, padding="10 5")
            middle_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

            bottom_frame = ttk.Frame(self, padding="0")
            bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

            controls_frame = ttk.Frame(top_frame, style='TFrame')
            controls_frame.pack(fill=tk.X, expand=True, padx=10, pady=(0, 5))

            ttk.Label(controls_frame, text="Category:", style='TLabel').pack(side=tk.LEFT, padx=(0, 5), pady=10)
            self.category_filter_var = tk.StringVar()
            self.category_filter_combo = ttk.Combobox(controls_frame, textvariable=self.category_filter_var, state='readonly', width=25, style='TCombobox')
            self.category_filter_combo.pack(side=tk.LEFT, padx=5, pady=10)
            self.category_filter_combo.bind("<<ComboboxSelected>>", self.on_category_filter_select)

            ttk.Button(controls_frame, text="Order History", command=self.show_order_history, style='Outline.TButton').pack(side=tk.LEFT, padx=5, pady=10)

            ttk.Button(controls_frame, text="Logout", command=self.logout, style='Outline.TButton').pack(side=tk.RIGHT, padx=5, pady=10)
            ttk.Button(controls_frame, text="Add Product", command=self.open_add_product_window, style='Accent.TButton').pack(side=tk.RIGHT, padx=(5, 0), pady=10)
            ttk.Button(controls_frame, text="Add Category", command=self.add_new_category, style='Outline.TButton').pack(side=tk.RIGHT, padx=5, pady=10)

            products_outer_frame = ttk.Frame(middle_frame)
            products_outer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=5)
            products_frame = ttk.Frame(products_outer_frame, style='Card.TFrame', padding="10")
            products_frame.pack(fill=tk.BOTH, expand=True)
            ttk.Label(products_frame, text="Available Products", style='Header.TLabel').pack(side=tk.TOP, anchor=tk.W, pady=(0, 10))

            prod_tree_frame = ttk.Frame(products_frame, style='Card.TFrame')
            prod_tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            prod_cols = ("ID", "Name", "Category", "Price", "Stock")
            self.products_tree = ttk.Treeview(prod_tree_frame, columns=prod_cols, show='headings', style='Treeview')
            self.products_tree.heading("ID", text="ID", anchor=tk.W)
            self.products_tree.column("ID", width=50, stretch=False, anchor=tk.W)
            self.products_tree.heading("Name", text="Name", anchor=tk.W)
            self.products_tree.column("Name", width=220, anchor=tk.W)
            self.products_tree.heading("Category", text="Category", anchor=tk.W)
            self.products_tree.column("Category", width=120, anchor=tk.W)
            self.products_tree.heading("Price", text=f"Price ({CURRENCY_SYMBOL})", anchor=tk.E)
            self.products_tree.column("Price", width=90, anchor=tk.E)
            self.products_tree.heading("Stock", text="Stock", anchor=tk.E)
            self.products_tree.column("Stock", width=60, anchor=tk.E)

            prod_scrollbar = ttk.Scrollbar(prod_tree_frame, orient="vertical", command=self.products_tree.yview)
            self.products_tree.configure(yscrollcommand=prod_scrollbar.set)
            prod_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            self.products_tree.tag_configure('oddrow', background=TREE_ROW_ODD_BG)
            self.products_tree.tag_configure('evenrow', background=TREE_ROW_EVEN_BG)

            self.products_tree.bind("<<TreeviewSelect>>", self.on_product_select)

            prod_action_frame = ttk.Frame(products_frame, style='Card.TFrame', padding="5 0")
            prod_action_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False, pady=(10,0))

            self.add_to_cart_button = ttk.Button(prod_action_frame, text="Add to Cart", command=self.add_to_cart, state=tk.DISABLED, style='Accent.TButton')
            self.add_to_cart_button.pack(side=tk.LEFT, padx=(0, 5))

            self.update_stock_button = ttk.Button(prod_action_frame, text="Update Stock", command=self.update_selected_stock, state=tk.DISABLED, style='Outline.TButton')
            self.update_stock_button.pack(side=tk.LEFT, padx=5)

            self.delete_product_button = ttk.Button(prod_action_frame, text="Delete Product", command=self.delete_selected_product, state=tk.DISABLED, style='Outline.TButton')
            self.delete_product_button.pack(side=tk.LEFT, padx=5)

            cart_outer_frame = ttk.Frame(middle_frame)
            cart_outer_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=5)
            cart_frame = ttk.Frame(cart_outer_frame, style='Card.TFrame', padding="10")
            cart_frame.pack(fill=tk.BOTH, expand=True)
            ttk.Label(cart_frame, text="Shopping Cart", style='Header.TLabel').pack(side=tk.TOP, anchor=tk.W, pady=(0, 10))

            cart_tree_frame = ttk.Frame(cart_frame, style='Card.TFrame')
            cart_tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            cart_cols = ("ID", "Name", "Qty", f"Unit Price ({CURRENCY_SYMBOL})", f"Total ({CURRENCY_SYMBOL})")
            self.cart_tree = ttk.Treeview(cart_tree_frame, columns=cart_cols, show='headings', style='Treeview')
            for col in cart_cols: self.cart_tree.heading(col, text=col, anchor=tk.W if col != "Qty" else tk.E)
            self.cart_tree.column("ID", width=50, stretch=False, anchor=tk.W)
            self.cart_tree.column("Name", width=150, anchor=tk.W)
            self.cart_tree.column("Qty", width=50, anchor=tk.E)
            self.cart_tree.column(f"Unit Price ({CURRENCY_SYMBOL})", width=100, anchor=tk.E)
            self.cart_tree.column(f"Total ({CURRENCY_SYMBOL})", width=100, anchor=tk.E)

            cart_scrollbar = ttk.Scrollbar(cart_tree_frame, orient="vertical", command=self.cart_tree.yview)
            self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
            cart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            self.cart_tree.tag_configure('oddrow', background=TREE_ROW_ODD_BG)
            self.cart_tree.tag_configure('evenrow', background=TREE_ROW_EVEN_BG)
            self.cart_tree.tag_configure('error', foreground=ERROR_COLOR)

            self.cart_tree.bind("<<TreeviewSelect>>", self.on_cart_select)

            cart_info_frame = ttk.Frame(cart_frame, style='Card.TFrame', padding="10")
            cart_info_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False, pady=(10,0))
            self.cart_total_label = ttk.Label(cart_info_frame, text=f"Cart Total: {CURRENCY_SYMBOL}0.00", style='Total.TLabel')
            self.cart_total_label.pack(side=tk.LEFT, padx=5, pady=5)

            self.place_order_button = ttk.Button(cart_info_frame, text="Place Order", command=self.place_order, state=tk.DISABLED, style='Accent.TButton')
            self.place_order_button.pack(side=tk.RIGHT, padx=5, pady=5)
            self.remove_from_cart_button = ttk.Button(cart_info_frame, text="Remove Item", command=self.remove_selected_cart_item, state=tk.DISABLED, style='Outline.TButton')
            self.remove_from_cart_button.pack(side=tk.RIGHT, padx=(5, 0), pady=5)

            self.status_label = ttk.Label(bottom_frame, text="Welcome!", style='Status.TLabel')
            self.status_label.pack(fill=tk.X, expand=True)
            print("DEBUG: Widgets created.")

            print("DEBUG: Loading initial data...")
            try:
                self.load_categories_into_filter()
                self.load_products()
                self.update_cart_display()
                print("DEBUG: Initial data loaded successfully.")
            except Exception as e:
                messagebox.showerror("Application Initialization Failed",
                                     f"An error occurred during initial data loading.\nError: {e}\n\n"
                                     "The application may not function correctly.", parent=self)
                self.update_status(f"Initialization Error: {e}")
                print(f"ERROR during initial data load: {e}")

            print("DEBUG: EcommerceGUI initialization complete.")

        except Exception as e:
            print(f"FATAL ERROR during EcommerceGUI.__init__: {e}")
            import traceback
            traceback.print_exc()
            try:
                messagebox.showerror("Fatal Initialization Error",
                                     f"A critical error occurred while initializing the main window:\n{e}\n\n"
                                     "The application might close or be unstable.", parent=parent)
            except Exception as msg_e:
                print(f"Could not show error messagebox: {msg_e}")
            try:
                self.destroy()
            except:
                pass

    def update_status(self, message):
        """Updates the status bar label and prints the message to the console with a timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_text = f"[{timestamp}] {message}"
        try:
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                 self.status_label.config(text=status_text)
                 self.update_idletasks()
        except tk.TclError:
             print(f"Status (Label Error): {status_text}")
             pass
        print(f"Status: {status_text}")

    def load_categories_into_filter(self):
        """Loads categories into the filter dropdown and caches them."""
        self.update_status("Loading categories...")
        try:
            self.categories_cache = list_categories()
            category_names = [ALL_CATEGORIES] + sorted([cat['name'] for cat in self.categories_cache])
            self.category_filter_combo['values'] = category_names
            self.category_filter_combo.set(ALL_CATEGORIES)
            self.update_status(f"Loaded {len(self.categories_cache)} categories.")
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to load categories: {e}", parent=self)
            self.update_status(f"Error loading categories: {e}")
            self.categories_cache = []
            self.category_filter_combo['values'] = [ALL_CATEGORIES]
            self.category_filter_combo.set(ALL_CATEGORIES)

    def get_category_id_from_filter(self):
        """Gets the selected category ID from the filter dropdown."""
        selected_name = self.category_filter_var.get()
        if selected_name == ALL_CATEGORIES or not selected_name:
            return None
        for cat in self.categories_cache:
            if cat['name'] == selected_name:
                return cat['category_id']
        self.update_status(f"Warning: Category '{selected_name}' not found in cache.")
        return None

    def on_category_filter_select(self, _event=None):
        """Handler when a category is selected in the filter."""
        cat_id = self.get_category_id_from_filter()
        self.load_products(category_id=cat_id)

    def load_products(self, category_id=None):
        """Fetches products (filtered) and populates the products Treeview."""
        filter_msg = f" category ID {category_id}" if category_id is not None else " all categories"
        self.update_status(f"Loading products for{filter_msg}...")

        try:
            for item in self.products_tree.get_children():
                self.products_tree.delete(item)
        except tk.TclError:
            self.update_status("Error clearing product tree (window may be closing).")
            return

        try:
            products = list_products(category_id=category_id)
            if products:
                for i, product in enumerate(products):
                    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    pid = product.get('product_id', 'N/A')
                    name = product.get('name', 'N/A')
                    cat_name = product.get('category_name', 'N/A')
                    price = product.get('price', 0.0)
                    stock = product.get('stock', 0)
                    try:
                        self.products_tree.insert("", tk.END, values=(
                            pid,
                            name,
                            cat_name,
                            f"{CURRENCY_SYMBOL}{price:.2f}",
                            stock
                        ), tags=(tag,))
                    except tk.TclError:
                        self.update_status("Error inserting product row (window may be closing).")
                        break
                self.update_status(f"Loaded {len(products)} products{filter_msg}.")
            else:
                self.update_status(f"No products found for{filter_msg}.")
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to load products: {e}", parent=self)
            self.update_status(f"Error loading products: {e}")
        finally:
            self.on_product_select()

    def on_product_select(self, _event=None):
        """Handler when a product is selected."""
        try:
            selected_items = self.products_tree.selection()
            if selected_items:
                item_id = selected_items[0]
                item = self.products_tree.item(item_id)
                self.add_to_cart_button.config(state=tk.NORMAL)
                self.update_stock_button.config(state=tk.NORMAL)
                self.delete_product_button.config(state=tk.NORMAL)
                self.update_status(f"Selected: {item['values'][1]} (ID: {item['values'][0]})")
            else:
                self.add_to_cart_button.config(state=tk.DISABLED)
                self.update_stock_button.config(state=tk.DISABLED)
                self.delete_product_button.config(state=tk.DISABLED)
                self.update_status("No product selected.")
        except tk.TclError:
             self.update_status("Error handling product selection (window may be closing).")
             try:
                 self.add_to_cart_button.config(state=tk.DISABLED)
                 self.update_stock_button.config(state=tk.DISABLED)
                 self.delete_product_button.config(state=tk.DISABLED)
             except tk.TclError:
                 pass

    def on_cart_select(self, _event=None):
        """Handler when a cart item is selected."""
        try:
            selected_items = self.cart_tree.selection()
            if selected_items:
                item_id = selected_items[0]
                item_values = self.cart_tree.item(item_id)['values']
                if len(item_values) > 1 and not str(item_values[1]).endswith("Not Found"):
                    self.remove_from_cart_button.config(state=tk.NORMAL)
                    self.update_status(f"Selected cart item: {item_values[1]} (ID: {item_values[0]})")
                else:
                    self.remove_from_cart_button.config(state=tk.DISABLED)
                    self.update_status("Selected 'Not Found' item in cart.")
            else:
                self.remove_from_cart_button.config(state=tk.DISABLED)
                self.update_status("No cart item selected.")
        except tk.TclError:
            self.update_status("Error handling cart selection (window may be closing).")
            try:
                self.remove_from_cart_button.config(state=tk.DISABLED)
            except tk.TclError:
                pass

    def add_new_category(self):
        """Opens dialog to add a new category."""
        category_name = simpledialog.askstring("Add Category", "Enter new category name:", parent=self)
        if category_name:
            category_name = category_name.strip()
            if category_name:
                try:
                    cat_id = add_category(category_name)
                    if cat_id:
                        self.update_status(f"Category '{category_name}' added (ID: {cat_id}).")
                        self.load_categories_into_filter()
                    else:
                        messagebox.showerror("DB Error", f"Failed to add category '{category_name}'. It might already exist.", parent=self)
                        self.update_status(f"Failed to add category '{category_name}'.")
                except Exception as e:
                     messagebox.showerror("DB Error", f"An error occurred while adding category '{category_name}': {e}", parent=self)
                     self.update_status(f"Error adding category: {e}")
            else:
                messagebox.showwarning("Input Error", "Category name cannot be empty.", parent=self)

    def open_add_product_window(self):
        """Opens the Toplevel window to add a new product."""
        if not self.categories_cache:
             self.load_categories_into_filter()
        if not self.categories_cache:
             messagebox.showerror("Error", "Cannot add product: No categories loaded or exist. Please add a category first.", parent=self)
             return
        add_window = AddProductWindow(self, self.categories_cache, self.refresh_after_add)
        add_window.wait_window()

    def refresh_after_add(self):
         """Callback function to refresh product list after adding."""
         self.update_status("Refreshing product list after add/update...")
         self.on_category_filter_select()

    def update_selected_stock(self):
        """Updates stock for the selected product."""
        selected_items = self.products_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a product first.", parent=self)
            return

        item_id = selected_items[0]
        try:
            item_values = self.products_tree.item(item_id)['values']
            product_id = int(item_values[0])
            product_name = item_values[1]
            current_stock = item_values[4]
        except (IndexError, ValueError, tk.TclError):
             messagebox.showerror("Error", "Could not retrieve product details from selection.", parent=self)
             self.update_status("Error getting selected product details for stock update.")
             return

        new_stock = simpledialog.askinteger("Update Stock",
                                            f"Enter new stock quantity for '{product_name}' (ID: {product_id})\nCurrent Displayed Stock: {current_stock}",
                                            parent=self, minvalue=0)

        if new_stock is not None:
            try:
                if update_product_stock(product_id, new_stock):
                    self.update_status(f"Stock updated for '{product_name}' to {new_stock}.")
                    self.refresh_after_add()
                else:
                    messagebox.showerror("DB Error", f"Failed to update stock for product ID {product_id}. Product might not exist.", parent=self)
                    self.update_status(f"Failed to update stock for product ID {product_id} (DB operation returned false).")
                    self.refresh_after_add()
            except Exception as e:
                 messagebox.showerror("DB Error", f"An error occurred while updating stock for product ID {product_id}: {e}", parent=self)
                 self.update_status(f"Error updating stock for product ID {product_id}: {e}")
                 self.refresh_after_add()
        else:
            self.update_status("Stock update cancelled.")

    def delete_selected_product(self):
        """Deletes the selected product from the database."""
        selected_items = self.products_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a product to delete.", parent=self)
            return

        item_id = selected_items[0]
        try:
            item_values = self.products_tree.item(item_id)['values']
            product_id = int(item_values[0])
            product_name = item_values[1]
        except (IndexError, ValueError, tk.TclError):
             messagebox.showerror("Error", "Could not retrieve product details from selection.", parent=self)
             self.update_status("Error getting selected product details for deletion.")
             return

        if not messagebox.askyesno("Confirm Delete",
                                   f"Are you sure you want to permanently delete '{product_name}' (ID: {product_id})?\n"
                                   "This action cannot be undone and might fail if the product is part of an order.",
                                   parent=self, icon=messagebox.WARNING):
            self.update_status(f"Deletion of '{product_name}' cancelled.")
            return

        try:
            self.update_status(f"Attempting to delete product ID {product_id} ('{product_name}')...")
            if delete_product(product_id):
                self.update_status(f"Product '{product_name}' (ID: {product_id}) deleted successfully.")
                messagebox.showinfo("Success", f"Product '{product_name}' deleted.", parent=self)
                if product_id in self.cart:
                    del self.cart[product_id]
                    self.update_cart_display()
                self.refresh_after_add()
            else:
                messagebox.showerror("Deletion Failed", f"Could not delete product '{product_name}'. It might be referenced in existing orders or no longer exists.", parent=self)
                self.update_status(f"Failed to delete product ID {product_id}. Check database constraints or logs.")
                self.refresh_after_add()
        except Exception as e:
            messagebox.showerror("Deletion Error", f"An error occurred while deleting product ID {product_id}: {e}", parent=self)
            self.update_status(f"Error deleting product ID {product_id}: {e}")
            self.refresh_after_add()

    def add_to_cart(self):
        """Adds selected product to cart."""
        selected_items = self.products_tree.selection()
        if not selected_items:
             messagebox.showwarning("No Selection", "Please select a product to add to the cart.", parent=self)
             return

        item_id = selected_items[0]
        try:
            item_values = self.products_tree.item(item_id)['values']
            product_id = int(item_values[0])
            product_name = item_values[1]
        except (IndexError, ValueError, tk.TclError):
             messagebox.showerror("Error", "Could not retrieve product details from selection.", parent=self)
             self.update_status("Error getting selected product details for adding to cart.")
             return

        try:
            product_details = find_product_by_id(product_id)
            if not product_details:
                 messagebox.showerror("Error", f"Product '{product_name}' (ID: {product_id}) not found in database. It may have been deleted.", parent=self)
                 self.update_status(f"Product ID {product_id} not found when adding to cart.")
                 self.refresh_after_add()
                 return

            stock = product_details['stock']

            if stock <= 0:
                messagebox.showwarning("Out of Stock", f"'{product_name}' is currently out of stock.", parent=self)
                self.update_status(f"Attempted to add out-of-stock item '{product_name}' to cart.")
                return

            current_qty_in_cart = self.cart.get(product_id, 0)
            available_stock_for_adding = stock - current_qty_in_cart

            if available_stock_for_adding <= 0:
                 messagebox.showinfo("Cart Full", f"The maximum available stock ({stock}) for '{product_name}' is already in your cart.", parent=self)
                 self.update_status(f"No more stock available to add for '{product_name}'.")
                 return

            quantity = simpledialog.askinteger("Quantity", f"Enter quantity for '{product_name}':\n(Available to add: {available_stock_for_adding}, Total Stock: {stock})",
                                               parent=self, minvalue=1, maxvalue=available_stock_for_adding)

            if quantity is None:
                self.update_status("Add to cart cancelled.")
                return

            if quantity > available_stock_for_adding:
                 messagebox.showwarning("Insufficient Stock", f"Cannot add {quantity}. Only {available_stock_for_adding} more available (Stock: {stock}, In Cart: {current_qty_in_cart}).", parent=self)
                 return

            self.cart[product_id] = current_qty_in_cart + quantity
            self.update_status(f"Added {quantity} x '{product_name}' to cart. New cart quantity: {self.cart[product_id]}.")
            self.update_cart_display()

        except Exception as e:
             messagebox.showerror("Error", f"An error occurred while adding '{product_name}' to cart: {e}", parent=self)
             self.update_status(f"Error adding product ID {product_id} to cart: {e}")

    def remove_selected_cart_item(self):
        """Removes the selected item from the cart."""
        selected_items = self.cart_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select an item in the cart to remove.", parent=self)
            return

        item_id = selected_items[0]
        try:
            item_values = self.cart_tree.item(item_id)['values']
            product_id = int(item_values[0])
            product_name = item_values[1]
            if str(product_name).endswith("Not Found"):
                 messagebox.showerror("Error", "Cannot remove 'Not Found' item directly. It indicates an issue.", parent=self)
                 self.update_status("Attempted to remove 'Not Found' item from cart.")
                 return

        except (IndexError, ValueError, tk.TclError):
             messagebox.showerror("Error", "Could not retrieve item details from cart selection.", parent=self)
             self.update_status("Error getting selected cart item details for removal.")
             return

        if product_id in self.cart:
            del self.cart[product_id]
            self.update_status(f"Removed '{product_name}' (ID: {product_id}) from cart.")
            self.update_cart_display()
        else:
            messagebox.showerror("Sync Error", f"Item '{product_name}' (ID: {product_id}) not found in the internal cart data.", parent=self)
            self.update_status(f"Error: Tried to remove product ID {product_id} which was not found in self.cart.")
            self.update_cart_display()

    def update_cart_display(self):
        """Updates cart Treeview and total."""
        try:
            self.cart_tree.selection_set([])
            for item in self.cart_tree.get_children():
                self.cart_tree.delete(item)
        except tk.TclError:
            self.update_status("Error clearing cart tree (window may be closing).")
            return

        cart_total = 0.0
        valid_cart_items_exist = False
        items_to_remove_from_cart = []

        if self.cart:
            try:
                product_ids_in_cart = list(self.cart.keys())
                products_details = {pid: find_product_by_id(pid) for pid in product_ids_in_cart}

                row_index = 0
                for product_id, quantity in list(self.cart.items()):
                    product = products_details.get(product_id)
                    tag = 'evenrow' if row_index % 2 == 0 else 'oddrow'

                    if product:
                        price = product['price']
                        item_total = price * quantity
                        cart_total += item_total
                        try:
                            self.cart_tree.insert("", tk.END, values=(
                                product_id,
                                product['name'],
                                quantity,
                                f"{CURRENCY_SYMBOL}{price:.2f}",
                                f"{CURRENCY_SYMBOL}{item_total:.2f}"
                            ), tags=(tag,))
                            valid_cart_items_exist = True
                        except tk.TclError:
                            self.update_status("Error inserting cart row (window may be closing).")
                            break
                    else:
                        try:
                            self.cart_tree.insert("", tk.END, values=(
                                product_id,
                                f"ID:{product_id} Not Found",
                                quantity,
                                f"{CURRENCY_SYMBOL}?.??",
                                f"{CURRENCY_SYMBOL}?.??"
                            ), tags=(tag, 'error'))
                        except tk.TclError:
                             self.update_status("Error inserting 'Not Found' cart row (window may be closing).")
                             break

                        items_to_remove_from_cart.append(product_id)
                        self.update_status(f"Product ID {product_id} marked for removal from cart (not found in DB).")

                    row_index += 1

                if items_to_remove_from_cart:
                    for pid in items_to_remove_from_cart:
                        if pid in self.cart:
                            del self.cart[pid]
                    valid_cart_items_exist = any(pid in products_details and products_details[pid] for pid in self.cart)
                    self.update_status(f"Removed {len(items_to_remove_from_cart)} invalid items from cart.")

            except Exception as e:
                 messagebox.showerror("Cart Error", f"Error updating cart display: {e}", parent=self)
                 self.update_status(f"Cart display update error: {e}")
                 valid_cart_items_exist = False

        try:
            self.cart_total_label.config(text=f"Cart Total: {CURRENCY_SYMBOL}{cart_total:.2f}")
            self.place_order_button.config(state=tk.NORMAL if valid_cart_items_exist else tk.DISABLED)

            if not self.cart:
                 self.remove_from_cart_button.config(state=tk.DISABLED)
            elif not self.cart_tree.selection():
                 self.remove_from_cart_button.config(state=tk.DISABLED)

        except tk.TclError:
            self.update_status("Error updating cart total/button (window may be closing).")

    def generate_invoice_pdf(self, order_id, order_details, items_details):
        """Generates and saves a PDF invoice."""
        try:
            # Create the invoices directory if it doesn't exist
            if not os.path.exists(INVOICE_DIR):
                os.makedirs(INVOICE_DIR)
                self.update_status(f"Created directory: {INVOICE_DIR}")

            pdf_filename = os.path.join(INVOICE_DIR, f"invoice_{order_id}.pdf")
            doc = SimpleDocTemplate(pdf_filename)
            styles = getSampleStyleSheet()
            story = []

            # --- Styles ---
            title_style = styles['h1']
            title_style.alignment = TA_CENTER
            heading_style = styles['h2']
            heading_style.alignment = TA_LEFT
            normal_style = styles['Normal']
            normal_right_style = ParagraphStyle(name='NormalRight', parent=styles['Normal'], alignment=TA_RIGHT)
            total_style = ParagraphStyle(name='TotalStyle', parent=styles['h3'], alignment=TA_RIGHT)

            # --- Content ---
            story.append(Paragraph("INVOICE", title_style))
            story.append(Spacer(1, 0.2*inch))

            # Order Info
            order_date_str = order_details.get('order_date', 'N/A')
            try:
                dt_obj = datetime.datetime.fromisoformat(order_date_str)
                formatted_date = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_date = order_date_str

            story.append(Paragraph(f"<b>Order ID:</b> {order_id}", normal_style))
            story.append(Paragraph(f"<b>Order Date:</b> {formatted_date}", normal_style))
            story.append(Paragraph(f"<b>User:</b> {self.current_username} (ID: {self.current_user_id})", normal_style))
            story.append(Spacer(1, 0.2*inch))

            story.append(Paragraph("Items:", heading_style))
            story.append(Spacer(1, 0.1*inch))

            # Items Table
            table_data = [
                ['Product', 'Qty', f'Unit Price ({CURRENCY_SYMBOL})', f'Total ({CURRENCY_SYMBOL})'] # Header Row
            ]
            total_amount_calc = 0.0
            for item in items_details:
                name = item.get('product_name', 'N/A')
                qty = item.get('quantity', 0)
                price = item.get('price_at_order', 0.0)
                item_total = qty * price
                total_amount_calc += item_total
                table_data.append([
                    Paragraph(name, normal_style),
                    Paragraph(str(qty), normal_right_style),
                    Paragraph(f"{price:.2f}", normal_right_style),
                    Paragraph(f"{item_total:.2f}", normal_right_style)
                ])

            # Table Style
            item_table = Table(table_data, colWidths=[3*inch, 0.5*inch, 1.2*inch, 1.2*inch])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey), # Header background
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Header text color
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Align product name left
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'), # Align numbers right
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Header font
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige), # Body background
                ('GRID', (0, 0), (-1, -1), 1, colors.black) # Grid lines
            ]))
            story.append(item_table)
            story.append(Spacer(1, 0.2*inch))

            # Grand Total
            story.append(Paragraph(f"<b>GRAND TOTAL: {CURRENCY_SYMBOL}{total_amount_calc:.2f}</b>", total_style))
            story.append(Spacer(1, 0.2*inch))

            # Status & Footer
            story.append(Paragraph(f"<b>Status:</b> {order_details.get('status', 'N/A')}", normal_style))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("Thank you for your purchase!", normal_style))

            # --- Build PDF ---
            doc.build(story)
            self.update_status(f"Invoice PDF saved successfully: {pdf_filename}")
            messagebox.showinfo("Invoice Saved", f"Invoice PDF for Order ID {order_id} has been saved to:\n{os.path.abspath(pdf_filename)}", parent=self)
            return True # Indicate success

        except Exception as e:
            self.update_status(f"Error generating/saving PDF invoice for order {order_id}: {e}")
            messagebox.showerror("Invoice PDF Error", f"Failed to generate or save PDF invoice for Order ID {order_id}.\nError: {e}", parent=self)
            import traceback
            traceback.print_exc() # Print detailed error to console
            return False # Indicate failure

    def place_order(self):
        """Places the order and generates/saves a PDF invoice on success."""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Your shopping cart is empty.", parent=self)
            return

        self.update_status("Validating cart items for order...")

        cart_summary_lines = []
        product_ids_in_cart = list(self.cart.keys())
        try:
            products_details = {pid: find_product_by_id(pid) for pid in product_ids_in_cart}
        except Exception as e:
             messagebox.showerror("Order Error", f"Failed to fetch product details for validation: {e}", parent=self)
             self.update_status(f"Order validation failed (DB fetch error): {e}")
             return

        valid_items_for_order = {}
        items_to_remove_due_issue = []

        for pid, requested_qty in list(self.cart.items()):
            prod = products_details.get(pid)
            if prod:
                current_stock = prod['stock']
                if current_stock >= requested_qty:
                    name = prod['name']
                    price = prod['price']
                    cart_summary_lines.append(f"- {requested_qty} x {name} ({CURRENCY_SYMBOL}{price:.2f} ea.)")
                    valid_items_for_order[pid] = requested_qty
                else:
                    items_to_remove_due_issue.append(pid)
                    name = prod['name']
                    cart_summary_lines.append(f"! {requested_qty} x {name} (REMOVED - Insufficient Stock: {current_stock} left)")
                    self.update_status(f"Item ID {pid} ('{name}') removed from order due to insufficient stock ({requested_qty} > {current_stock}).")
            else:
                items_to_remove_due_issue.append(pid)
                cart_summary_lines.append(f"! ID:{pid} (REMOVED - Product Not Found)")
                self.update_status(f"Item ID {pid} removed from order (product not found).")

        if items_to_remove_due_issue:
            for pid in items_to_remove_due_issue:
                if pid in self.cart:
                    del self.cart[pid]
            self.update_cart_display()
            messagebox.showwarning("Cart Updated",
                                   "Some items were automatically removed from your cart due to stock issues or because they no longer exist.\n\n"
                                   "Please review your updated cart before proceeding.",
                                   parent=self)
            self.update_status("Order process stopped after validation removed items. User needs to review cart.")
            return

        if not valid_items_for_order:
             messagebox.showerror("Order Error", "No valid items remaining in the cart to place an order.", parent=self)
             self.update_status("Order failed: No valid items left after final validation.")
             return

        cart_summary = "\n".join(cart_summary_lines)
        final_order_total = sum(products_details[pid]['price'] * qty for pid, qty in valid_items_for_order.items())
        total_text = f"Final Order Total: {CURRENCY_SYMBOL}{final_order_total:.2f}"

        if not messagebox.askyesno("Confirm Order",
                                   f"Please confirm your order for user ID {self.current_user_id}:\n\n"
                                   f"{cart_summary}\n\n"
                                   f"{total_text}\n\n"
                                   f"Proceed with placing this order?"):
            self.update_status("Order cancelled by user at confirmation.")
            return

        self.update_status("Placing order...")
        order_items_list = list(valid_items_for_order.items())

        try:
            order_id = create_order(self.current_user_id, order_items_list)
            if order_id:
                self.update_status(f"Order {order_id} placed successfully.")

                # --- Generate and Save PDF Invoice ---
                try:
                    final_order_details = next((o for o in get_user_orders(self.current_user_id) if o['order_id'] == order_id), None)
                    final_items_details = get_order_items(order_id)

                    if final_order_details and final_items_details:
                        # Call the new PDF generation function
                        self.generate_invoice_pdf(order_id, final_order_details, final_items_details)
                    else:
                         self.update_status(f"Warning: Could not fetch complete details for PDF invoice generation (Order ID: {order_id}).")
                         messagebox.showwarning("Invoice Warning", f"Order {order_id} placed, but failed to fetch details to generate the PDF invoice.", parent=self)

                except Exception as invoice_e:
                    # Error handled within generate_invoice_pdf, just log here
                    self.update_status(f"Error during PDF invoice process for order {order_id}: {invoice_e}")
                    # Messagebox shown by generate_invoice_pdf
                # ---------------------------------

                messagebox.showinfo("Order Placed", f"Order (ID: {order_id}) placed successfully!", parent=self) # Show main success message after invoice attempt
                self.cart = {}
                self.update_cart_display()
                self.refresh_after_add()
            else:
                messagebox.showerror("Order Failed", "Could not place order. The database operation failed (e.g., stock levels changed during transaction). Please try again.", parent=self)
                self.update_status("Order placement failed (create_order returned non-ID). Transaction likely rolled back.")
                self.refresh_after_add()
        except Exception as e:
             messagebox.showerror("Order Error", f"An unexpected error occurred during order placement: {e}", parent=self)
             self.update_status(f"Order placement error: {e}")
             self.refresh_after_add()

    def show_order_history(self):
        """Opens the Order History window."""
        self.update_status("Opening order history...")
        history_window = OrderHistoryWindow(self, self.current_user_id)
        history_window.wait_window()
        self.update_status("Closed order history.")

    def logout(self):
        """Logs out the user and returns to the authentication window."""
        self.update_status("Logging out...")
        self.destroy()
        self.parent.deiconify()

    def on_closing(self):
        """Handles the closing of the application window."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.logout()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.withdraw()

        def launch_main_app(user_info):
            print(f"Login successful for {user_info['username']}. Launching main app...")
            ecommerce_app = EcommerceGUI(root, user_info)

        try:
            create_tables()
        except Exception as e:
             print(f"Error ensuring tables exist: {e}")
             messagebox.showerror("Database Error", f"Failed to initialize database tables: {e}")
             root.destroy()
             exit()

        auth_window = AuthWindow(launch_main_app)
        root.mainloop()

    except Exception as e:
        print(f"FATAL ERROR: An unexpected error occurred: {e}")
        try:
            messagebox.showerror("Fatal Error", f"A critical error occurred and the application must close:\n{e}")
        except Exception:
            pass
