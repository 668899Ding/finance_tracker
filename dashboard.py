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
st.subheader("All Transactions (With Delete Option)")
    
# Delete and edit transactions            
for index, row in filtered_df.iterrows():
    col1, col2, col3 = st.columns([6, 2, 2])  # Add third column for Edit
    
    date_str = pd.to_datetime(row['date']).strftime("%Y-%m-%d")
    
    with col1:
        st.write(
            f"{date_str} | {row['type']} | ${row['amount']:.2f} | {row['category']} | {row['note']}"
        )
    
    with col2:
        if st.button("🗑️ Delete", key=f"delete_{row['id']}"):
            conn = sqlite3.connect("transactions.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (row["id"],))
            conn.commit()
            conn.close()
            st.success(f"Deleted transaction {row['id']}")
            st.rerun()
    
    with col3:
        if st.button("✏️ Edit", key=f"edit_{row['id']}"):
            st.session_state["edit_id"] = row["id"]
            st.rerun()

if "edit_id" in st.session_state:
    # Find the row to edit
    edit_id = st.session_state["edit_id"]
    row = filtered_df[filtered_df["id"] == edit_id].iloc[0]
    
    st.markdown("---")
    st.subheader(f"✏️ Edit Transaction {edit_id}")
    
    with st.form("edit_form"):
        new_type = st.selectbox("Type", ["income", "expense"], index=0 if row["type"] == "income" else 1)
        new_amount = st.number_input("Amount", min_value=0.0, format="%.2f", value=row["amount"])
        new_category = st.text_input("Category", value=row["category"])
        new_note = st.text_input("Note", value=row["note"])
        new_date = st.date_input("Date", value=pd.to_datetime(row["date"]).date())
        
        submitted = st.form_submit_button("Update Transaction")
        
        if submitted:
            conn = sqlite3.connect("transactions.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE transactions
                SET type = ?, amount = ?, category = ?, note = ?, date = ?
                WHERE id = ?
            """, (new_type, new_amount, new_category, new_note, new_date.strftime("%Y-%m-%d"), edit_id))
            conn.commit()
            conn.close()
            st.success("Transaction updated!")
            del st.session_state["edit_id"]
            st.rerun()



