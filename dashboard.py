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
filtered_df = pd.read_sql_query("SELECT * FROM transactions", conn)
st.sidebar.header("Filter Transactions")

# Filter inputs
type_filter = st.sidebar.selectbox("Select Type", ["All", "income", "expense"])
category_filter = st.sidebar.text_input("Category (optional)")
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

filtered_df = filtered_df.copy()

if type_filter != "All":
    filtered_df = filtered_df[filtered_df["type"] == type_filter]

if category_filter:
    filtered_df = filtered_df[filtered_df["category"].str.contains(category_filter, case=False)]

filtered_df["date"] = pd.to_datetime(filtered_df["date"])
filtered_df = filtered_df[(filtered_df["date"] >= pd.to_datetime(start_date)) & (filtered_df["date"] <= pd.to_datetime(end_date))]

# 🔁 Use this filtered_df in all future steps instead of filtered_df
st.dataframe(filtered_df)

# Convert date column to datetime format
filtered_df["date"] = pd.to_datetime(filtered_df["date"])

# Date filter
st.sidebar.subheader("📅 Filter by Date Range")
import datetime
import pandas as pd  # Make sure this is already at the top

min_date = filtered_df["date"].min()
if pd.isnull(min_date):
    min_date = datetime.date.today()
else:
    min_date = min_date.date()

start_date = st.sidebar.date_input("Start date", min_date)

import pandas as pd
import datetime as dt

max_date = filtered_df["date"].max()
default_end_date = max_date.date() if pd.notna(max_date) else dt.date.today()

end_date = st.sidebar.date_input("End date", default_end_date)


# Apply date filter
filtered_df = filtered_df[(filtered_df["date"] >= pd.to_datetime(start_date)) & (filtered_df["date"] <= pd.to_datetime(end_date))]


# Optional filters
unique_categories = filtered_df["category"].unique().tolist()
selected_category = st.selectbox("Filter by category", ["All"] + unique_categories)

# Apply category filter
if selected_category != "All":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]


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
income = filtered_df[filtered_df['type'] == 'income']['amount'].sum()
expense = filtered_df[filtered_df['type'] == 'expense']['amount'].sum()
net = income - expense

st.metric("Total Income", f"${income:.2f}")
st.metric("Total Expenses", f"${expense:.2f}")
st.metric("Net Balance", f"${net:.2f}")

# Pie chart
st.subheader("Spending Breakdown")
expense_by_category = filtered_df[filtered_df['type'] == 'expense'].groupby('category')['amount'].sum()

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
st.dataframe(filtered_df)

