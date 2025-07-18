from fastapi import FastAPI
import sqlite3
from datetime import datetime

app = FastAPI()

def get_db():
    conn = sqlite3.connect("transactions.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"message": "Finance Tracker API is running"}

from pydantic import BaseModel

class Transaction(BaseModel):
    type: str
    amount: float
    category: str
    note: str

@app.post("/transactions")
def add_transaction(data: Transaction):
    date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (date, type, amount, category, note)
        VALUES (?, ?, ?, ?, ?)
    """, (date, data.type, data.amount, data.category, data.note))
    conn.commit()
    return {"status": "success"}

@app.get("/summary")
def get_summary():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
    income_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
    expense_total = cursor.fetchone()[0] or 0

    return {
        "income": income_total,
        "expenses": expense_total,
        "net": income_total - expense_total
    }

