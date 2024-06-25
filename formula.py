import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

# Database setup
conn = sqlite3.connect('finance_tracker.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT,
        type TEXT,
        category TEXT,
        amount REAL
    )
''')
conn.commit()


# Add transaction to database
def add_transaction():
    date = date_entry.get()
    trans_type = type_var.get()
    category = category_entry.get()
    amount = amount_entry.get()

    if not date or not trans_type or not category or not amount:
        messagebox.showerror("Input Error", "All fields must be filled out")
        return

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Input Error", "Amount must be a number")
        return

    c.execute('''
        INSERT INTO transactions (date, type, category, amount)
        VALUES (?, ?, ?, ?)
    ''', (date, trans_type, category, amount))
    conn.commit()

    date_entry.delete(0, tk.END)
    category_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)

    messagebox.showinfo("Success", "Transaction added successfully")
    update_treeview()


# Update treeview with database contents
def update_treeview():
    for row in tree.get_children():
        tree.delete(row)

    c.execute('SELECT * FROM transactions')
    for row in c.fetchall():
        tree.insert("", "end", values=row)


# Generate spending report
def generate_report():
    c.execute('SELECT category, SUM(amount) FROM transactions WHERE type="Expense" GROUP BY category')
    data = c.fetchall()

    if not data:
        messagebox.showinfo("No Data", "No expenses recorded")
        return

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    fig, ax = plt.subplots()
    ax.pie(amounts, labels=categories, autopct='%1.1f%%')
    ax.axis('equal')

    report_window = tk.Toplevel(root)
    report_window.title("Spending Report")
    canvas = FigureCanvasTkAgg(fig, master=report_window)
    canvas.draw()
    canvas.get_tk_widget().pack()


# Main application window
root = tk.Tk()
root.title("Personal Finance Tracker")

# Input fields
tk.Label(root, text="Date (YYYY-MM-DD):").grid(row=0, column=0)
date_entry = tk.Entry(root)
date_entry.grid(row=0, column=1)

tk.Label(root, text="Type (Income/Expense):").grid(row=1, column=0)
type_var = tk.StringVar()
type_entry = ttk.Combobox(root, textvariable=type_var)
type_entry['values'] = ('Income', 'Expense')
type_entry.grid(row=1, column=1)

tk.Label(root, text="Category:").grid(row=2, column=0)
category_entry = tk.Entry(root)
category_entry.grid(row=2, column=1)

tk.Label(root, text="Amount:").grid(row=3, column=0)
amount_entry = tk.Entry(root)
amount_entry.grid(row=3, column=1)

tk.Button(root, text="Add Transaction", command=add_transaction).grid(row=4, column=0, columnspan=2)

# Treeview for displaying transactions
columns = ('id', 'date', 'type', 'category', 'amount')
tree = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
tree.grid(row=5, column=0, columnspan=2)

# Button to generate report
tk.Button(root, text="Generate Report", command=generate_report).grid(row=6, column=0, columnspan=2)

# Initial load of treeview data
update_treeview()

# Run the application
root.mainloop()

# Close database connection on exit
conn.close()
