import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

def insert_transaction(t_type, amount, category, note):
    date = pd.Timestamp.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("transactions.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (date, type, amount, category, note)
        VALUES (?, ?, ?, ?, ?)
    """, (date, t_type, amount, category, note))
    conn.commit()
    conn.close()


# Connect to the database
conn = sqlite3.connect("transactions.db")

# Load data
df = pd.read_sql_query("SELECT * FROM transactions", conn)
# Convert date column to datetime format
df["date"] = pd.to_datetime(df["date"])

# Date filter
st.sidebar.subheader("📅 Filter by Date Range")
start_date = st.sidebar.date_input("Start date", df["date"].min().date())
end_date = st.sidebar.date_input("End date", df["date"].max().date())

# Apply date filter
df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]


# Optional filters
unique_categories = df["category"].unique().tolist()
selected_category = st.selectbox("Filter by category", ["All"] + unique_categories)

# Apply category filter
if selected_category != "All":
    df = df[df["category"] == selected_category]


# Title
st.title("💰 Personal Finance Dashboard")
with st.form("entry_form"):
    st.subheader("➕ Add New Transaction")

    t_type = st.selectbox("Type", ["income", "expense"])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    category = st.text_input("Category")
    note = st.text_input("Note")
    
    submitted = st.form_submit_button("Add Transaction")

    if submitted:
        insert_transaction(t_type, amount, category, note)
        st.success("Transaction added!")
        st.rerun()  # refresh the dashboard with new data


# Summary stats
income = df[df['type'] == 'income']['amount'].sum()
expense = df[df['type'] == 'expense']['amount'].sum()
net = income - expense

st.metric("Total Income", f"${income:.2f}")
st.metric("Total Expenses", f"${expense:.2f}")
st.metric("Net Balance", f"${net:.2f}")

# Pie chart
st.subheader("Spending Breakdown")
expense_by_category = df[df['type'] == 'expense'].groupby('category')['amount'].sum()

if not expense_by_category.empty:
    fig, ax = plt.subplots()
    ax.pie(
        expense_by_category,
        labels=expense_by_category.index,
        autopct='%1.1f%%',
        startangle=90
    )
    ax.axis('equal')     
    st.pyplot(fig)
else:
    st.write("No expenses yet.")

# Table
st.subheader("All Transactions")
st.dataframe(df)

