# tracker.py
import sqlite3
from datetime import date
from typing import Optional, Iterable
import pandas as pd

DB_PATH = "transactions.db"


# ---------- low-level helpers ----------
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- schema ----------
def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT    NOT NULL,
                type     TEXT    NOT NULL CHECK(type IN ('income','expense')),
                amount   REAL    NOT NULL,
                category TEXT,
                note     TEXT
            )
            """
        )


# ---------- CRUD ----------
def insert_transaction(t_type: str, amount: float, category: str, note: str, d: date | str) -> None:
    date_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO transactions (date, type, amount, category, note) VALUES (?, ?, ?, ?, ?)",
            (date_str, t_type, amount, category, note),
        )


def update_transaction(
    tx_id: int,
    t_type: str,
    amount: float,
    category: str,
    note: str,
    d: date | str,
) -> None:
    date_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
    with _connect() as conn:
        conn.execute(
            """
            UPDATE transactions
               SET date = ?, type = ?, amount = ?, category = ?, note = ?
             WHERE id = ?
            """,
            (date_str, t_type, amount, category, note, tx_id),
        )


def delete_transaction(tx_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))


# ---------- reads ----------
def get_transactions_df() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query(
            "SELECT * FROM transactions ORDER BY date DESC, id DESC",
            conn,
        )


# ---------- bulk import / export ----------
def bulk_insert_df(df: pd.DataFrame) -> None:
    """Expect columns: date, type, amount, category, note (id optional/ignored)."""
    required = {"date", "type", "amount", "category", "note"}
    missing = required - set(df.columns.str.lower())
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    # Normalize column names to match table
    df = df.rename(columns=str.lower)[["date", "type", "amount", "category", "note"]]

    with _connect() as conn:
        df.to_sql("transactions", conn, if_exists="append", index=False)

