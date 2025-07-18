import sqlite3
from datetime import datetime

# Connect to (or create) the database
conn = sqlite3.connect("transactions.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    type TEXT,
    amount REAL,
    category TEXT,
    note TEXT
)
""")
conn.commit()

import csv
import os

CSV_FILE = "transactions.csv"

# Create file with headers if not exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "type", "amount", "category", "note"])

from datetime import datetime

def add_transaction():
    t_type = input("Type (income/expense): ").strip().lower()
    amount = float(input("Amount: "))
    category = input("Category: ")
    note = input("Note: ")
    date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        "INSERT INTO transactions (date, type, amount, category, note) VALUES (?, ?, ?, ?, ?)",
        (date, t_type, amount, category, note)
    )
    conn.commit()
    print("Transaction added to database!")

def show_summary():
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
    income_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
    expense_total = cursor.fetchone()[0] or 0

    print(f"Total Income: ${income_total}")
    print(f"Total Expenses: ${expense_total}")
    print(f"Net: ${income_total - expense_total}")

def main():
    while True:
        print("\n=== Personal Finance Tracker ===")
        print("1. Add Transaction")
        print("2. Show Summary")
        print("3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_transaction()
        elif choice == "2":
            show_summary()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()


