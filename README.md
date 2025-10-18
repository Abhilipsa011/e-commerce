# 🛒 E-Commerce Management System (Tkinter + Python + Database)

## 📖 Project Description
The **E-Commerce Management System** is a **desktop-based shopping application** built using **Python’s Tkinter GUI library**.  
It provides an intuitive interface for customers to browse products, add items to their cart, and place orders — all within a desktop environment.  
The system also includes an **admin panel** for managing products, inventory, and user records.

The application uses a **relational database (MySQL / SQLite)** to store and manage data efficiently.  
It ensures **data persistence, fast queries, and secure record handling** for all e-commerce operations.

---

## ⚙️ Key Features

### 🛍️ Customer Features
- User registration and login system  
- Browse products by category  
- Add and remove products from the cart  
- Order summary and checkout process  
- Payment simulation and confirmation screen  

### 🧑‍💼 Admin Features
- Add, edit, and delete products  
- Manage categories and inventory  
- View all customer orders  
- Manage user records  

### 🗃️ Database Integration
- **SQLite/MySQL** used for backend storage  
- Structured tables for:
  - `users` – (UserID, Name, Email, Password)
  - `products` – (ProductID, Name, Price, Stock, Category)
  - `orders` – (OrderID, UserID, TotalAmount, Date)
  - `order_items` – (ItemID, OrderID, ProductID, Quantity)
- Full CRUD operations for all modules  

---

## 🧩 Tech Stack

| Component | Technology |
|------------|-------------|
| **Frontend (GUI)** | Tkinter (Python Standard GUI Library) |
| **Backend Logic** | Python (OOP + Functional Modules) |
| **Database** | SQLite / MySQL |
| **Data Handling** | SQL Queries via `sqlite3` / `mysql.connector` |
| **Authentication** | Password hashing & validation |

---

## 💡 Highlights
✅ Fully functional GUI built with **Tkinter Frames and Widgets**  
✅ Real-time **cart and inventory update**  
✅ Modular, reusable, and scalable Python code  
✅ Future-ready for **API and Web extensions**  

---
