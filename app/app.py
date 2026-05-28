# app.py
# ---------------------------------------------------------
# Purpose : Streamlit dashboard for the Sales Management System.
#           Supports role-based access control — Super Admins
#           see all branches, Branch Admins see only their own.
#
# How to run (from the app/ directory):
#   streamlit run app.py
# ---------------------------------------------------------

import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Add the 'src' directory to Python's path to allow importing the database module
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from database import verify_user, fetch_sales_data

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(page_title="Sales Intelligence Hub", layout="wide")

# ── Session State Initialisation ─────────────────────────────────────────────
# Streamlit re-runs the entire script on every user interaction.
# Session state lets us remember whether the user is logged in across re-runs.
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

# ── Login Screen ──────────────────────────────────────────────────────────────
if not st.session_state['logged_in']:
    st.title("Sales Intelligence Hub — Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = verify_user(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['user_info'] = user
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")

# ── Authenticated Dashboard ───────────────────────────────────────────────────
else:
    user_info = st.session_state['user_info']

    # Sidebar: show who is logged in and provide a logout button
    st.sidebar.title(f"Welcome, {user_info['username']}")
    st.sidebar.write(f"Role: **{user_info['role']}**")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.rerun()

    st.title("Branch-Based Sales Analytics Dashboard")

    # Fetch sales data for this user (filtered by role and branch automatically)
    raw_data = fetch_sales_data(user_info['role'], user_info['branch_id'])
    df = pd.DataFrame(raw_data)

    # Convert financial columns to numbers so we can do arithmetic on them.
    # errors='coerce' turns any non-numeric values into 0 instead of crashing.
    if not df.empty:
        df['gross_sales']     = pd.to_numeric(df['gross_sales'],     errors='coerce').fillna(0.0)
        df['received_amount'] = pd.to_numeric(df['received_amount'], errors='coerce').fillna(0.0)
        df['pending_amount']  = pd.to_numeric(df['pending_amount'],  errors='coerce').fillna(0.0)

    if not df.empty:
        # Show high-level summary metrics at the top
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Gross Sales",   f"Rs.{df['gross_sales'].sum():,.2f}")
        with col2:
            st.metric("Total Collected",     f"Rs.{df['received_amount'].sum():,.2f}")
        with col3:
            st.metric("Total Outstanding",   f"Rs.{df['pending_amount'].sum():,.2f}")

        st.divider()

        # Show the full transaction table below the KPIs
        st.subheader("Transaction Ledger")
        st.dataframe(df)
    else:
        st.info("No data recorded yet for your view.")