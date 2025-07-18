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
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([date, t_type, amount, category, note])
    
    print("Transaction added!")

def show_summary():
    income_total = 0
    expense_total = 0

    with open(CSV_FILE, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["type"] == "income":
                income_total += float(row["amount"])
            elif row["type"] == "expense":
                expense_total += float(row["amount"])

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

