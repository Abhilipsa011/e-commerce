import tkinter as tk
from tkinter import ttk, messagebox, font
import hashlib

try:
    # Assuming db_operations.py is in the same directory
    from db_operations import find_user_by_username, add_user
except ImportError as e:
    print(f"Error importing db_operations in auth_gui.py: {e}")
    print("Ensure db_operations.py is in the same directory.")
    exit()

# --- Password Hashing (Basic Example - Use bcrypt in production!) ---
def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifies a provided password against a stored hash."""
    return stored_hash == hash_password(provided_password)
# --- End Password Hashing ---

class AuthWindow(tk.Tk):
    """Main Authentication Window (Login/Signup)."""
    def __init__(self, on_success_callback):
        super().__init__()

        # Import constants locally to potentially avoid circular import
        try:
            from gui_app import (BG_COLOR, FRAME_BG_COLOR, ACCENT_COLOR, ACCENT_LIGHT,
                                 TEXT_COLOR, BUTTON_FG_COLOR, BUTTON_BG_COLOR,
                                 BUTTON_ACTIVE_BG, ERROR_COLOR, SUCCESS_COLOR)
        except ImportError:
            print("CRITICAL: Could not import constants from gui_app.py")
            BG_COLOR = "#F0F0F0"
            FRAME_BG_COLOR = "#FFFFFF"
            ACCENT_COLOR = "#0078D7"
            TEXT_COLOR = "#000000"
            BUTTON_FG_COLOR = "#FFFFFF"
            BUTTON_BG_COLOR = ACCENT_COLOR
            BUTTON_ACTIVE_BG = "#005A9E"
            ERROR_COLOR = "#FF0000"
            SUCCESS_COLOR = "#008000"

        self.title("Login or Sign Up")
        self.geometry("400x450")
        self.configure(bg=BG_COLOR)
        self.on_success = on_success_callback
        self.logged_in_user = None

        # --- Styling ---
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            print("Warning: 'clam' theme not available, using default.")

        try:
            self.default_font = font.nametofont("TkDefaultFont")
            self.default_font.configure(size=10)
            self.heading_font = font.Font(family="Segoe UI", size=12, weight="bold")
            self.label_font = font.Font(family="Segoe UI", size=10)
            self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        except tk.TclError:
            print("Warning: Failed to load 'Segoe UI' font. Using default fonts.")
            self.default_font = font.nametofont("TkDefaultFont")
            self.heading_font = font.nametofont("TkDefaultFont")
            self.label_font = font.nametofont("TkDefaultFont")
            self.button_font = font.nametofont("TkDefaultFont")

        self.style.configure('.', font=self.default_font, background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure('TFrame', background=BG_COLOR)
        self.style.configure('Card.TFrame', background=FRAME_BG_COLOR, relief=tk.SOLID, borderwidth=1)
        self.style.configure('TLabel', background=BG_COLOR, foreground=TEXT_COLOR, font=self.label_font, padding=2)
        self.style.configure('Input.TLabel', background=FRAME_BG_COLOR, foreground=TEXT_COLOR, font=self.label_font)
        self.style.configure('Header.TLabel', background=FRAME_BG_COLOR, foreground=TEXT_COLOR, font=self.heading_font, padding=5)
        self.style.configure('Error.TLabel', background=FRAME_BG_COLOR, foreground=ERROR_COLOR, font=self.label_font)
        self.style.configure('Success.TLabel', background=FRAME_BG_COLOR, foreground=SUCCESS_COLOR, font=self.label_font)
        self.style.configure('TButton', font=self.button_font, padding=(10, 5), relief=tk.FLAT, borderwidth=1)
        self.style.map('TButton',
                       background=[('active', BUTTON_ACTIVE_BG), ('!disabled', BUTTON_BG_COLOR)],
                       foreground=[('!disabled', BUTTON_FG_COLOR)])
        self.style.configure('Accent.TButton', font=self.button_font, padding=(10, 5), relief=tk.FLAT, borderwidth=0)
        self.style.map('Accent.TButton',
                       background=[('active', BUTTON_ACTIVE_BG), ('!disabled', BUTTON_BG_COLOR)],
                       foreground=[('!disabled', BUTTON_FG_COLOR)])
        self.style.configure('TNotebook', background=BG_COLOR, borderwidth=0)
        self.style.configure('TNotebook.Tab', font=self.label_font, padding=[10, 5], background=BG_COLOR)
        self.style.map('TNotebook.Tab', background=[('selected', FRAME_BG_COLOR)])
        self.style.configure('TEntry', padding=5, fieldbackground=FRAME_BG_COLOR)

        # --- Widgets ---
        self.notebook = ttk.Notebook(self, style='TNotebook')

        # --- Login Tab ---
        self.login_frame = ttk.Frame(self.notebook, padding="20", style='Card.TFrame')
        self.notebook.add(self.login_frame, text='Login')

        ttk.Label(self.login_frame, text="Login", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(self.login_frame, text="Username:", style='Input.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.login_username_entry = ttk.Entry(self.login_frame, width=30, style='TEntry')
        self.login_username_entry.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(self.login_frame, text="Password:", style='Input.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.login_password_entry = ttk.Entry(self.login_frame, show="*", width=30, style='TEntry')
        self.login_password_entry.grid(row=2, column=1, pady=5, padx=5)

        self.login_message_label = ttk.Label(self.login_frame, text="", style='Error.TLabel', wraplength=300)
        self.login_message_label.grid(row=3, column=0, columnspan=2, pady=(10, 5))

        ttk.Button(self.login_frame, text="Login", command=self.handle_login, style='Accent.TButton').grid(row=4, column=0, columnspan=2, pady=(15, 0))

        # --- Sign Up Tab ---
        self.signup_frame = ttk.Frame(self.notebook, padding="20", style='Card.TFrame')
        self.notebook.add(self.signup_frame, text='Sign Up')

        ttk.Label(self.signup_frame, text="Create Account", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(self.signup_frame, text="Username:", style='Input.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.signup_username_entry = ttk.Entry(self.signup_frame, width=30, style='TEntry')
        self.signup_username_entry.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(self.signup_frame, text="Email:", style='Input.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.signup_email_entry = ttk.Entry(self.signup_frame, width=30, style='TEntry')
        self.signup_email_entry.grid(row=2, column=1, pady=5, padx=5)

        ttk.Label(self.signup_frame, text="Password:", style='Input.TLabel').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.signup_password_entry = ttk.Entry(self.signup_frame, show="*", width=30, style='TEntry')
        self.signup_password_entry.grid(row=3, column=1, pady=5, padx=5)

        ttk.Label(self.signup_frame, text="Confirm Password:", style='Input.TLabel').grid(row=4, column=0, sticky=tk.W, pady=5)
        self.signup_confirm_password_entry = ttk.Entry(self.signup_frame, show="*", width=30, style='TEntry')
        self.signup_confirm_password_entry.grid(row=4, column=1, pady=5, padx=5)

        self.signup_message_label = ttk.Label(self.signup_frame, text="", style='Error.TLabel', wraplength=300)
        self.signup_message_label.grid(row=5, column=0, columnspan=2, pady=(10, 5))

        ttk.Button(self.signup_frame, text="Sign Up", command=self.handle_signup, style='Accent.TButton').grid(row=6, column=0, columnspan=2, pady=(15, 0))

        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Focus on the first entry field
        self.login_username_entry.focus()

        # Bind Enter key for convenience
        self.login_password_entry.bind('<Return>', self.handle_login)
        self.signup_confirm_password_entry.bind('<Return>', self.handle_signup)

    def _set_message(self, label_widget, message, is_success=False):
        """Helper to set message label text and style."""
        label_widget.config(text=message, style='Success.TLabel' if is_success else 'Error.TLabel')

    def handle_login(self, event=None):
        """Handles the login attempt."""
        username = self.login_username_entry.get().strip()
        password = self.login_password_entry.get().strip()

        if not username or not password:
            self._set_message(self.login_message_label, "Username and password are required.")
            return

        try:
            print(f"Attempting login for username: '{username}'")
            user = find_user_by_username(username)
            print(f"User found in DB: {user}")

            if user:
                stored_hash = user['password_hash']
                print(f"Stored hash: {stored_hash}")
                provided_password_hash = hash_password(password)
                print(f"Provided password hashed: {provided_password_hash}")
                is_valid = verify_password(stored_hash, password)
                print(f"Password verification result: {is_valid}")

                if is_valid:
                    self._set_message(self.login_message_label, "Login successful!", is_success=True)
                    self.logged_in_user = dict(user) # Convert Row to dict

                    # --- ADD PRINT STATEMENT HERE ---
                    print(f"Login verified for {self.logged_in_user['username']}. Preparing to call on_success callback...")
                    # --------------------------------

                    self.withdraw() # Hide login window
                    if self.on_success:
                        # --- ADD PRINT STATEMENT HERE ---
                        print(f"Calling on_success callback with user_info: {self.logged_in_user}")
                        # --------------------------------
                        self.on_success(self.logged_in_user) # Call the callback (launch_main_app)
                    else:
                        # --- ADD PRINT STATEMENT HERE ---
                        print("Login successful, but no on_success callback was provided.")
                        # --------------------------------
                else:
                    self._set_message(self.login_message_label, "Invalid username or password.")
            else:
                self._set_message(self.login_message_label, "Invalid username or password.")
                print(f"User '{username}' not found in database.")

        except Exception as e:
            self._set_message(self.login_message_label, f"An error occurred: {e}")
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()

    def handle_signup(self, event=None):
        """Handles the signup attempt."""
        username = self.signup_username_entry.get().strip()
        email = self.signup_email_entry.get().strip()
        password = self.signup_password_entry.get().strip()
        confirm_password = self.signup_confirm_password_entry.get().strip()

        if not all([username, email, password, confirm_password]):
            self._set_message(self.signup_message_label, "All fields are required.")
            return

        if password != confirm_password:
            self._set_message(self.signup_message_label, "Passwords do not match.")
            return

        # Basic email validation (can be improved)
        if "@" not in email or "." not in email.split('@')[-1]:
             self._set_message(self.signup_message_label, "Invalid email format.")
             return

        try:
            existing_user = find_user_by_username(username)
            if existing_user:
                self._set_message(self.signup_message_label, "Username already exists.")
                return

            # Hash the password before storing
            hashed_password = hash_password(password)

            user_id = add_user(username, email, hashed_password)
            if user_id:
                self._set_message(self.signup_message_label, f"Account created successfully (ID: {user_id}). You can now log in.", is_success=True)
                # Optionally clear fields or switch to login tab
                self.signup_username_entry.delete(0, tk.END)
                self.signup_email_entry.delete(0, tk.END)
                self.signup_password_entry.delete(0, tk.END)
                self.signup_confirm_password_entry.delete(0, tk.END)
                self.notebook.select(self.login_frame) # Switch to login tab
                self.login_username_entry.focus()
            else:
                self._set_message(self.signup_message_label, "Failed to create account. Please try again.")
        except Exception as e:
            self._set_message(self.signup_message_label, f"An error occurred: {e}")
            print(f"Signup error: {e}")

# Example of how to run (will be called from gui_app.py)
if __name__ == "__main__":
    def on_login_success(user_info):
        print("Login successful from standalone test:", user_info)
        # In a real app, you'd close the auth window and open the main app window
        messagebox.showinfo("Login Success", f"Welcome {user_info['username']}!")
        # auth_app.destroy() # Close the auth window

    # You might need to ensure tables exist if running standalone
    try:
        from create_tables import create_tables
        create_tables()
    except Exception as e:
        print(f"Standalone test: Error creating tables: {e}")

    auth_app = AuthWindow(on_login_success)
    auth_app.mainloop()