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
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", "📋 Transactions", "📂 CSV Import/Export", "📈 Trends & Analytics"
])

# ====== Tab 1: Dashboard ======
with tab1:
    st.title("💰 Personal Finance Dashboard")
    
    # Add New Transaction Form
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

    # Step 1: Monthly Summary Cards
    current_month = datetime.date.today().strftime("%Y-%m")
    monthly_data = filtered_df[filtered_df['date'].dt.strftime("%Y-%m") == current_month]

    monthly_income = monthly_data[monthly_data['type'] == 'income']['amount'].sum()
    monthly_expense = monthly_data[monthly_data['type'] == 'expense']['amount'].sum()
    monthly_net = monthly_income - monthly_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("📈 Monthly Income", f"${monthly_income:.2f}")
    col2.metric("📉 Monthly Expenses", f"${monthly_expense:.2f}")
    col3.metric("💰 Net Balance", f"${monthly_net:.2f}")

    # Pie Chart
    st.subheader("Spending Breakdown")
    expense_by_category = (
        filtered_df[filtered_df['type'] == 'expense']
        .groupby('category')['amount']
        .sum()
    )
    if not expense_by_category.empty:
        fig, ax = plt.subplots()
        ax.pie(expense_by_category, labels=expense_by_category.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
    else:
        st.write("No expenses yet.")

    # Step 2: Category Budgets
    BUDGETS = {
        "grocery": 500,
        "food": 300,
        "shopping": 400,
        "investment": 1000,
    }
    st.subheader("🎯 Category Budgets")
    for category, budget in BUDGETS.items():
        spent = monthly_data[
            (monthly_data['type'] == 'expense') &
            (monthly_data['category'].str.lower() == category.lower())
        ]['amount'].sum()
        st.progress(min(spent / budget, 1.0))
        st.write(f"**{category.capitalize()}**: ${spent:.2f} / ${budget}")

# ====== Tab 2: Transactions ======
with tab2:
    st.subheader("All Transactions (With Delete Option)")
    for _, row in filtered_df.iterrows():
        c1, c2 = st.columns([6, 1])
        date_str = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")
        with c1:
            st.write(f"{date_str} | {row['type']} | ${row['amount']:.2f} | {row['category']} | {row['note']}")
        with c2:
            if st.button("🗑️ Delete", key=f"delete_{row['id']}"):
                delete_transaction(int(row['id']))
                st.success(f"Deleted transaction {row['id']}")
                st.rerun()

# ====== Tab 3: CSV Import/Export ======
with tab3:
    st.subheader("📂 CSV Export / Import")
    csv_buf = io.StringIO()
    filtered_df.to_csv(csv_buf, index=False)
    st.download_button(
    "📥 Download CSV",
    data=csv_buf.getvalue(),
    file_name="transactions_export.csv",
    mime="text/csv",
    key="download_csv_tab3"  # unique key
)

uploaded = st.file_uploader(
    "📤 Upload CSV to Add Transactions",
    type="csv",
    key="upload_csv_tab3"    # unique key
)

if uploaded is not None:
    up_df = pd.read_csv(uploaded)
    st.write("Preview:")
    st.dataframe(up_df.head())
    if st.button("Import Transactions", key="import_btn_tab3"):  # unique key
        try:
            bulk_insert_df(up_df)
            st.success("Transactions imported successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")
    
   

# ====== Tab 4: Add Trend Tab ======
with tab4:
    st.subheader("📈 Monthly Income vs Expenses")
    if not filtered_df.empty:
        monthly_summary = (
            filtered_df.groupby([filtered_df['date'].dt.to_period("M"), "type"])["amount"]
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )
        monthly_summary["date"] = monthly_summary["date"].astype(str)

        fig, ax = plt.subplots()
        ax.plot(monthly_summary["date"], monthly_summary.get("income", 0), marker="o", label="Income")
        ax.plot(monthly_summary["date"], monthly_summary.get("expense", 0), marker="o", label="Expenses")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount ($)")
        ax.set_title("Monthly Trends")
        ax.legend()
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.write("No data for trends yet.")

    # Top spending categories
    st.subheader("Top Spending Categories (This Month)")
    current_month = datetime.date.today().strftime("%Y-%m")
    month_data = filtered_df[filtered_df['date'].dt.strftime("%Y-%m") == current_month]
    top_categories = (
        month_data[month_data['type'] == 'expense']
        .groupby('category')['amount']
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    if not top_categories.empty:
        st.bar_chart(top_categories)
    else:
        st.write("No expenses this month to display.")


# =========================
# Monthly Summary Cards
# =========================
current_month = datetime.date.today().strftime("%Y-%m")
monthly_data = filtered_df[filtered_df['date'].dt.strftime("%Y-%m") == current_month]

monthly_income = monthly_data[monthly_data['type'] == 'income']['amount'].sum()
monthly_expense = monthly_data[monthly_data['type'] == 'expense']['amount'].sum()
monthly_net = monthly_income - monthly_expense

col1, col2, col3 = st.columns(3)
col1.metric("📈 Monthly Income", f"${monthly_income:.2f}")
col2.metric("📉 Monthly Expenses", f"${monthly_expense:.2f}")
col3.metric("💰 Net Balance", f"${monthly_net:.2f}")


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

# Top 5 Spending Categories
st.subheader("🏆 Top 5 Spending Categories")
expense_summary = (
    filtered_df[filtered_df['type'] == 'expense']
    .groupby('category')['amount']
    .sum()
    .sort_values(ascending=False)
    .head(5)
)

if not expense_summary.empty:
    st.table(expense_summary.reset_index().rename(columns={'category': 'Category', 'amount': 'Amount ($)'}))
else:
    st.write("No expenses yet.")

# Budget Warnings
st.subheader("🚨 Budget Overview")

# Define budgets for categories (you can adjust these numbers)
BUDGETS = {
    "grocery": 500,
    "shopping": 300,
    "food": 150,
    "entertainment": 200,
    "investment": 1000,
}

for category, budget in BUDGETS.items():
    spent = filtered_df[
        (filtered_df['type'] == 'expense') &
        (filtered_df['category'].str.lower() == category.lower())
    ]['amount'].sum()

    st.progress(min(spent / budget, 1.0))  # Show progress bar
    st.write(f"**{category.capitalize()}**: ${spent:.2f} / ${budget}")



# =========================
# Category Budgets
# =========================
BUDGETS = {
    "grocery": 500,
    "food": 300,
    "shopping": 400,
    "investment": 1000,
}

st.subheader("🎯 Category Budgets")
for category, budget in BUDGETS.items():
    spent = monthly_data[
        (monthly_data['type'] == 'expense') &
        (monthly_data['category'].str.lower() == category.lower())
    ]['amount'].sum()

    st.progress(min(spent / budget, 1.0))  # Cap at 100%
    st.write(f"**{category.capitalize()}**: ${spent:.2f} / ${budget}")


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

