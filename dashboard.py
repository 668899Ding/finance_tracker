# dashboard.py
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io

from tracker import (
    init_db,
    get_transactions_df,
    insert_transaction,
    update_transaction,
    delete_transaction,
    bulk_insert_df,
)

st.set_page_config(page_title="Personal Finance Dashboard", layout="centered")

# --- init DB once ---
init_db()

# --- helpers ---
def load_data() -> pd.DataFrame:
    df = get_transactions_df()
    if df.empty:
        df = pd.DataFrame(columns=["id", "date", "type", "amount", "category", "note"])
    df["date"] = pd.to_datetime(df["date"])
    return df


# =========================
# Sidebar filters
# =========================
st.sidebar.header("Filters")

df = load_data()

type_filter = st.sidebar.selectbox("Transaction Type", ["All", "income", "expense"])
category_filter = st.sidebar.text_input("Category (optional)")

if df.empty:
    min_d = max_d = datetime.date.today()
else:
    min_d = df["date"].min().date()
    max_d = df["date"].max().date()

start_date = st.sidebar.date_input("Start Date", min_d)
end_date = st.sidebar.date_input("End Date", max_d)

filtered_df = df.copy()
if type_filter != "All":
    filtered_df = filtered_df[filtered_df["type"] == type_filter]

if category_filter:
    filtered_df = filtered_df[filtered_df["category"].str.contains(category_filter, case=False, na=False)]

filtered_df = filtered_df[
    (filtered_df["date"].dt.date >= start_date) & (filtered_df["date"].dt.date <= end_date)
]

# =========================
# Title
# =========================
st.title("💰 Personal Finance Dashboard")

# =========================
# Add New Transaction
# =========================
with st.form("entry_form"):
    st.subheader("➕ Add New Transaction")
    t_type = st.selectbox("Type", ["income", "expense"])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    category = st.text_input("Category")
    note = st.text_input("Note")
    date = st.date_input("Date", value=datetime.date.today())
    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        insert_transaction(t_type, amount, category, note, date)
        st.success("Transaction added!")
        st.rerun()

# =========================
# Summary
# =========================
income = filtered_df[filtered_df["type"] == "income"]["amount"].sum()
expense = filtered_df[filtered_df["type"] == "expense"]["amount"].sum()
net = income - expense

st.write(f"**Total Income:** ${income:.2f}")
st.write(f"**Total Expenses:** ${expense:.2f}")
st.write(f"**Net Balance:** ${net:.2f}")

# =========================
# Pie chart
# =========================
st.subheader("Spending Breakdown")
expense_by_category = (
    filtered_df[filtered_df["type"] == "expense"]
    .groupby("category")["amount"]
    .sum()
)

if not expense_by_category.empty:
    fig, ax = plt.subplots()
    ax.pie(expense_by_category, labels=expense_by_category.index, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.write("No expenses yet.")

# =========================
# Monthly trend
# =========================
st.subheader("📈 Monthly Income vs Expenses")
if not filtered_df.empty:
    monthly = (
        filtered_df.groupby([filtered_df["date"].dt.to_period("M"), "type"])["amount"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    monthly["date"] = monthly["date"].astype(str)

    fig, ax = plt.subplots()
    if "income" in monthly:
        ax.plot(monthly["date"], monthly["income"], marker="o", label="Income")
    if "expense" in monthly:
        ax.plot(monthly["date"], monthly["expense"], marker="o", label="Expenses")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount ($)")
    ax.set_title("Monthly Trends")
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.write("No data to show trend yet.")

# =========================
# CSV export / import
# =========================
st.subheader("📂 CSV Export / Import")

# Export (use filtered data so user can download what they see)
csv_buf = io.StringIO()
filtered_df.to_csv(csv_buf, index=False)
st.download_button(
    "📥 Download CSV",
    data=csv_buf.getvalue(),
    file_name="transactions_export.csv",
    mime="text/csv",
)

uploaded = st.file_uploader("📤 Upload CSV to Add Transactions", type="csv")
if uploaded is not None:
    up_df = pd.read_csv(uploaded)
    st.write("Preview:")
    st.dataframe(up_df.head())
    if st.button("Import Transactions"):
        try:
            bulk_insert_df(up_df)
            st.success("Transactions imported successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

# =========================
# Transactions list (Delete / Edit)
# =========================
st.subheader("All Transactions (With Delete / Edit)")

for _, row in filtered_df.iterrows():
    c1, c2, c3 = st.columns([6, 2, 2])
    date_str = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")

    with c1:
        st.write(f"{date_str} | {row['type']} | ${row['amount']:.2f} | {row['category']} | {row['note']}")

    with c2:
        if st.button("🗑️ Delete", key=f"del_{row['id']}"):
            delete_transaction(int(row["id"]))
            st.success(f"Deleted transaction {row['id']}")
            st.rerun()

    with c3:
        if st.button("✏️ Edit", key=f"edit_{row['id']}"):
            st.session_state["edit_id"] = int(row["id"])
            st.rerun()

# Edit form
if "edit_id" in st.session_state:
    edit_id = st.session_state["edit_id"]
    original = df[df["id"] == edit_id].iloc[0]

    st.markdown("---")
    st.subheader(f"✏️ Edit Transaction {edit_id}")

    with st.form("edit_form"):
        new_type = st.selectbox("Type", ["income", "expense"], index=0 if original["type"] == "income" else 1)
        new_amount = st.number_input("Amount", min_value=0.0, format="%.2f", value=float(original["amount"]))
        new_category = st.text_input("Category", value=original["category"])
        new_note = st.text_input("Note", value=original["note"])
        new_date = st.date_input("Date", value=pd.to_datetime(original["date"]).date())

        submitted = st.form_submit_button("Update Transaction")
        if submitted:
            update_transaction(edit_id, new_type, new_amount, new_category, new_note, new_date)
            st.success("Transaction updated!")
            del st.session_state["edit_id"]
            st.rerun()

