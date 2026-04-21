import streamlit as st
import pandas as pd
import sqlite3
from datetime import timedelta
from PIL import Image

# ------------------- CONFIG -------------------
st.set_page_config(page_title="Protein Lab", layout="wide")

# ------------------- SCREEN WIDTH -------------------
st.markdown("""
<script>
function sendWidth() {
    const width = window.innerWidth;
    window.parent.postMessage({
        type: "streamlit:setComponentValue",
        value: width
    }, "*");
}
sendWidth();
window.addEventListener("resize", sendWidth);
</script>
""", unsafe_allow_html=True)

if "screen_width" not in st.session_state:
    st.session_state.screen_width = 1200

def is_mobile():
    return st.session_state.screen_width < 768

# ------------------- SESSION -------------------
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ------------------- LOGO -------------------
try:
    logo = Image.open("logo.png")
    st.sidebar.image(logo, use_container_width=True)
except:
    st.sidebar.warning("Upload logo.png")

st.sidebar.title("Protein Lab")
st.sidebar.markdown("---")
st.sidebar.caption("Powered by Hrithik's Protein Lab")

page = st.sidebar.radio("Navigation", ["Dashboard", "Add Customer"])

# ------------------- STYLING -------------------
st.markdown("""
<style>
.metric-card {
    background-color: #111827;
    padding: 18px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #1f2937;
}
.metric-title { color: #9ca3af; font-size: 13px; }
.metric-value { color: white; font-size: 24px; font-weight: bold; }
button { width: 100%; height: 48px; font-size: 16px; border-radius: 10px; }
.card {
    background-color: #111827;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 12px;
    border: 1px solid #1f2937;
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

    name = st.text_input("Customer Name")
    phone = st.text_input("Phone Number")
    start_date = st.date_input("Start Date")
    plan = st.selectbox("Plan", list(plans.keys()))

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
            if x <= 0: return "Expired"
            elif x <= 3: return "Expiring Soon"
            else: return "Active"

        df["status"] = df["days_left"].apply(status)

        # METRICS
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="metric-card"><div class="metric-title">Customers</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><div class="metric-title">Sales</div><div class="metric-value">₹{df["price"].sum()}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><div class="metric-title">Profit</div><div class="metric-value">₹{int(df["profit"].sum())}</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        search = st.text_input("🔍 Search")

        if search:
            df = df[df["name"].str.contains(search, case=False) | df["phone"].str.contains(search)]

        df = df.sort_values(by="days_left")

        st.subheader("📋 Customers")

        for _, row in df.iterrows():

            if is_mobile():
                # -------- MOBILE CARD --------
                st.markdown('<div class="card">', unsafe_allow_html=True)

                st.markdown(f"### {row['name']}")
                st.write(f"📞 {row['phone']}")
                st.write(f"📦 {row['plan']}")
                st.write(f"💰 ₹{row['price']}")
                st.write(f"⏳ {row['days_left']} days")
                st.write(f"🔔 {row['status']}")

                col1, col2 = st.columns(2)

                if col1.button("✏️ Edit", key=f"edit_m_{row['id']}"):
                    st.session_state.edit_id = row["id"]

                if col2.button("🗑 Delete", key=f"del_m_{row['id']}"):
                    c.execute("DELETE FROM customers WHERE id=?", (row["id"],))
                    conn.commit()
                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

            else:
                # -------- DESKTOP TABLE --------
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2,2,2,2,2,1,1])

                col1.write(row["name"])
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

        # -------- EDIT --------
        if st.session_state.edit_id:
            st.markdown("---")
            st.subheader("✏️ Edit Customer")

            customer = c.execute("SELECT * FROM customers WHERE id=?", (st.session_state.edit_id,)).fetchone()

            if customer:
                name = st.text_input("Name", customer[1])
                phone = st.text_input("Phone", customer[2])
                start_date = st.date_input("Start Date", pd.to_datetime(customer[3]))
                plan = st.selectbox("Plan", list(plans.keys()), index=list(plans.keys()).index(customer[4]))

                colA, colB = st.columns(2)

                if colA.button("Update"):
                    price, profit_percent, days = plans[plan]
                    profit = price * profit_percent
                    end_date = start_date + timedelta(days=days)

                    c.execute("""
                    UPDATE customers SET name=?, phone=?, start_date=?, plan=?, price=?, profit_percent=?, profit=?, end_date=?
                    WHERE id=?
                    """, (name, phone, str(start_date), plan, price, profit_percent, profit, str(end_date), st.session_state.edit_id))

                    conn.commit()
                    st.session_state.edit_id = None
                    st.rerun()

                if colB.button("Cancel"):
                    st.session_state.edit_id = None
                    st.rerun()

    else:
        st.info("No customers yet 🚀")
