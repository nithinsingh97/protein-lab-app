import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from PIL import Image

# ------------------- CONFIG -------------------
st.set_page_config(page_title="Protein Lab", layout="wide")

# ------------------- SESSION -------------------
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ------------------- RESPONSIVE MODE -------------------
view_mode = st.sidebar.radio("View Mode", ["Auto", "Desktop", "Mobile"])

def is_mobile():
    if view_mode == "Mobile":
        return True
    if view_mode == "Desktop":
        return False
    return False

# ------------------- LOGO -------------------
try:
    logo = Image.open("logo.png")
    st.sidebar.image(logo, use_container_width=True)
except:
    st.sidebar.warning("Upload logo.png")

st.sidebar.title("Protein Lab")
page = st.sidebar.radio("Navigation", ["Dashboard", "Add Customer"])

# ------------------- STYLING -------------------
st.markdown("""
<style>
.metric-card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #1f2937;
}
.metric-title {
    color: #9ca3af;
    font-size: 14px;
}
.metric-value {
    color: white;
    font-size: 26px;
    font-weight: bold;
}
button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------- DATABASE -------------------
conn = sqlite3.connect("customers.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    start_date TEXT,
    plan TEXT,
    price INTEGER,
    profit_percent REAL,
    profit REAL,
    end_date TEXT
)
""")
conn.commit()

# ------------------- PLAN CONFIG -------------------
plans = {
    "3 Days Trial": (1999, 0.30, 3),
    "Weekly Plan": (3499, 0.30, 7),
    "Monthly Single Meal": (7499, 0.30, 30),
    "Monthly Dual Meal": (11499, 0.25, 30)
}

# ------------------- ADD CUSTOMER -------------------
if page == "Add Customer":
    st.title("➕ Add Customer")

    if is_mobile():
        name = st.text_input("Customer Name")
        phone = st.text_input("Phone Number")
        start_date = st.date_input("Start Date")
        plan = st.selectbox("Plan", list(plans.keys()))
    else:
        col1, col2 = st.columns(2)
        name = col1.text_input("Customer Name")
        phone = col2.text_input("Phone Number")

        col3, col4 = st.columns(2)
        start_date = col3.date_input("Start Date")
        plan = col4.selectbox("Plan", list(plans.keys()))

    if st.button("Add Customer"):
        if name and phone:
            price, profit_percent, days = plans[plan]
            profit = price * profit_percent
            end_date = start_date + timedelta(days=days)

            c.execute("""
            INSERT INTO customers (name, phone, start_date, plan, price, profit_percent, profit, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, phone, str(start_date), plan, price, profit_percent, profit, str(end_date)))

            conn.commit()
            st.success("Customer Added")
            st.rerun()
        else:
            st.warning("Fill all fields")

# ------------------- DASHBOARD -------------------
if page == "Dashboard":

    st.title("📊 Dashboard")

    df = pd.read_sql("SELECT * FROM customers", conn)

    if not df.empty:
        df["start_date"] = pd.to_datetime(df["start_date"])
        df["end_date"] = pd.to_datetime(df["end_date"])
        df["days_left"] = (df["end_date"] - pd.Timestamp.today()).dt.days

        def status(x):
            if x <= 0:
                return "Expired"
            elif x <= 3:
                return "Expiring Soon"
            else:
                return "Active"

        df["status"] = df["days_left"].apply(status)

        # -------- METRICS --------
        total_customers = len(df)
        total_sales = df["price"].sum()
        total_profit = int(df["profit"].sum())

        trial_count = len(df[df["plan"] == "3 Days Trial"])
        weekly_count = len(df[df["plan"] == "Weekly Plan"])
        single_count = len(df[df["plan"] == "Monthly Single Meal"])
        dual_count = len(df[df["plan"] == "Monthly Dual Meal"])

        col1, col2, col3 = st.columns(3)

        col1.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Customers</div>
            <div class="metric-value">{total_customers}</div>
        </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Sales</div>
            <div class="metric-value">₹{total_sales}</div>
        </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Profit</div>
            <div class="metric-value">₹{total_profit}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        col4, col5, col6, col7 = st.columns(4)
        col4.metric("Trial Plans", trial_count)
        col5.metric("Weekly Plans", weekly_count)
        col6.metric("Single Meal", single_count)
        col7.metric("Dual Meal", dual_count)

        st.markdown("---")

        # -------- SEARCH --------
        search = st.text_input("🔍 Search by name or phone")

        if search:
            df = df[df["name"].str.contains(search, case=False) |
                    df["phone"].str.contains(search)]

        df = df.sort_values(by="days_left")

        # -------- CUSTOMER LIST --------
        st.subheader("📋 Customers")

        mobile = is_mobile()

        for _, row in df.iterrows():

            if mobile:
                # -------- MOBILE CARD --------
                with st.container():
                    st.markdown(f"""
                    ### {row['name']}
                    📞 {row['phone']}  
                    📦 {row['plan']}  
                    💰 ₹{row['price']}  
                    ⏳ {row['days_left']} days  
                    🔔 {row['status']}
                    """)

                    col1, col2 = st.columns(2)

                    if col1.button("✏️ Edit", key=f"edit_m_{row['id']}"):
                        st.session_state.edit_id = row["id"]

                    if col2.button("🗑 Delete", key=f"del_m_{row['id']}"):
                        c.execute("DELETE FROM customers WHERE id=?", (row["id"],))
                        conn.commit()
                        st.rerun()

                    st.markdown("---")

            else:
                # -------- DESKTOP TABLE --------
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2,2,2,2,2,1,1])

                if row["id"] == st.session_state.edit_id:
                    col1.markdown(f"👉 **{row['name']}**")
                else:
                    col1.write(f"**{row['name']}**")

                col2.write(row["plan"])
                col3.write(f"₹{row['price']}")
                col4.write(row["status"])
                col5.write(f"{row['days_left']} days")

                if col6.button("✏️", key=f"edit_{row['id']}"):
                    st.session_state.edit_id = row["id"]

                if col7.button("🗑", key=f"del_{row['id']}"):
                    c.execute("DELETE FROM customers WHERE id=?", (row["id"],))
                    conn.commit()
                    st.rerun()

        # -------- EDIT FORM --------
        if st.session_state.edit_id:
            st.markdown("---")
            st.subheader("✏️ Edit Customer")

            edit_id = st.session_state.edit_id

            customer = c.execute(
                "SELECT * FROM customers WHERE id=?", (edit_id,)
            ).fetchone()

            if customer:
                name = st.text_input("Name", customer[1])
                phone = st.text_input("Phone", customer[2])
                start_date = st.date_input("Start Date", pd.to_datetime(customer[3]))
                plan = st.selectbox(
                    "Plan",
                    list(plans.keys()),
                    index=list(plans.keys()).index(customer[4])
                )

                colA, colB = st.columns(2)

                if colA.button("Update"):
                    price, profit_percent, days = plans[plan]
                    profit = price * profit_percent
                    end_date = start_date + timedelta(days=days)

                    c.execute("""
                    UPDATE customers
                    SET name=?, phone=?, start_date=?, plan=?, price=?, profit_percent=?, profit=?, end_date=?
                    WHERE id=?
                    """, (name, phone, str(start_date), plan, price, profit_percent, profit, str(end_date), edit_id))

                    conn.commit()
                    st.success("Updated")
                    st.session_state.edit_id = None
                    st.rerun()

                if colB.button("Cancel"):
                    st.session_state.edit_id = None
                    st.rerun()

    else:
        st.info("No customers yet 🚀")
