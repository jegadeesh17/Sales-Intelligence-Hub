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

from database import verify_user, fetch_sales_data, fetch_branches, add_new_sale, add_payment

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(page_title="Sales Intelligence Hub", layout="wide")

# ── Success Dialog Modal ──────────────────────────────────────────────────────
@st.dialog("Sale Added Successfully! 🎉")
def show_success_dialog(name, product, amount):
    st.success(f"Successfully recorded sale for **{name}**.")
    st.markdown(f"""
    **Details**:
    * **Customer**: {name}
    * **Product**: {product}
    * **Gross Sales**: Rs. {amount:,.2f}
    """)
    st.info("The database record has been created and balances updated via triggers.")
    if st.button("OK", use_container_width=True):
        st.rerun()


@st.dialog("Payment Recorded Successfully! 💳")
def show_payment_success_dialog(name, product, amount_paid, pending_before, pending_after):
    st.success(f"Successfully recorded payment for **{name}**.")
    st.markdown(f"""
    **Details**:
    * **Customer**: {name}
    * **Product**: {product}
    * **Amount Paid**: Rs. {amount_paid:,.2f}
    * **Pending Balance Before**: Rs. {pending_before:,.2f}
    * **New Pending Balance**: Rs. {pending_after:,.2f}
    """)
    st.info("The payment record has been added and sales balances updated via triggers.")
    if st.button("OK", use_container_width=True):
        st.rerun()

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

    # Sidebar navigation / Tabs
    st.sidebar.divider()
    page = st.sidebar.radio("Navigation", ["Sales Dashboard", "Add New Sale", "Record Payment"])

    # Fetch sales data for this user (filtered by role and branch automatically)
    raw_data = fetch_sales_data(user_info['role'], user_info['branch_id'])
    df = pd.DataFrame(raw_data)

    # Convert financial columns to numbers so we can do arithmetic on them.
    # errors='coerce' turns any non-numeric values into 0 instead of crashing.
    if not df.empty:
        df['gross_sales']     = pd.to_numeric(df['gross_sales'],     errors='coerce').fillna(0.0)
        df['received_amount'] = pd.to_numeric(df['received_amount'], errors='coerce').fillna(0.0)
        df['pending_amount']  = pd.to_numeric(df['pending_amount'],  errors='coerce').fillna(0.0)

    if page == "Sales Dashboard":
        st.title("Branch-Based Sales Analytics Dashboard")

        if not df.empty:
            # Convert date column to datetime.date object to allow comparison with st.date_input
            df['date'] = pd.to_datetime(df['date']).dt.date

            # ── Filters Panel ─────────────────────────────────────────────────────
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)

            with f_col1:
                branches = sorted(df['branch_name'].dropna().unique().tolist())
                branch_options = ["All Branches"] + branches if len(branches) > 1 else branches
                selected_branch = st.selectbox("Branch", options=branch_options)

            with f_col2:
                products = sorted(df['product_name'].dropna().unique().tolist())
                product_options = ["All Products"] + products
                selected_product = st.selectbox("Product", options=product_options)

            # Default date bounds based on available dataset
            min_date = df['date'].min()
            max_date = df['date'].max()
            if pd.isnull(min_date):
                min_date = pd.to_datetime("2024-01-01").date()
            if pd.isnull(max_date):
                max_date = pd.to_datetime("2024-12-31").date()

            with f_col3:
                start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)

            with f_col4:
                end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

            # Apply selected filters to dataset
            filtered_df = df.copy()
            if selected_branch != "All Branches":
                filtered_df = filtered_df[filtered_df['branch_name'] == selected_branch]
            if selected_product != "All Products":
                filtered_df = filtered_df[filtered_df['product_name'] == selected_product]
            
            filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]

            st.divider()

            # Show high-level summary metrics using filtered data
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Gross Sales",   f"Rs.{filtered_df['gross_sales'].sum():,.2f}")
            with col2:
                st.metric("Total Collected",     f"Rs.{filtered_df['received_amount'].sum():,.2f}")
            with col3:
                st.metric("Total Outstanding",   f"Rs.{filtered_df['pending_amount'].sum():,.2f}")

            st.divider()

            # Show the full transaction table below the KPIs using filtered data
            st.subheader("Transaction Ledger")
            if not filtered_df.empty:
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.warning("No records found matching the selected filter criteria.")
        else:
            st.info("No data recorded yet for your view.")

    elif page == "Add New Sale":
        st.title("Onboarding Form — Add New Sale")
        st.markdown("Use this form to record a new sale. The initial payment will automatically compute the total collected and outstanding amounts via database triggers.")

        with st.form("add_sale_form", clear_on_submit=False):
            st.subheader("Customer Details")
            customer_name = st.text_input("Customer Name", placeholder="e.g. Rahul Sharma")
            mobile_number = st.text_input("Mobile Number", placeholder="e.g. 9800000001")

            st.divider()
            st.subheader("Sale Details")
            
            # Role-based branch assignment
            if user_info['role'] == 'Super Admin':
                branches_list = fetch_branches()
                branch_names = [b['branch_name'] for b in branches_list]
                selected_branch_name = st.selectbox("Branch", options=branch_names)
                selected_branch_id = next(b['branch_id'] for b in branches_list if b['branch_name'] == selected_branch_name)
            else:
                branches_list = fetch_branches()
                user_branch_name = next((b['branch_name'] for b in branches_list if b['branch_id'] == user_info['branch_id']), "Unknown Branch")
                st.text_input("Branch", value=user_branch_name, disabled=True)
                selected_branch_id = user_info['branch_id']

            # Product Selection
            existing_products = sorted(df['product_name'].dropna().unique().tolist()) if not df.empty else []
            if not existing_products:
                existing_products = ["AI", "BA", "BI", "DA", "DS", "FSD", "ML", "SQL"]
            product_options = existing_products + ["Other (Enter custom name)..."]
            selected_product_opt = st.selectbox("Product", options=product_options)
            
            custom_product_name = ""
            if selected_product_opt == "Other (Enter custom name)...":
                custom_product_name = st.text_input("Custom Product Name", placeholder="e.g. AWS Cloud")

            gross_sales = st.number_input("Gross Sales Amount (Rs.)", min_value=0.0, step=500.0, format="%.2f")
            sale_date = st.date_input("Date of Sale", value=pd.Timestamp.now().date())
            sale_status = st.selectbox("Sale Status", options=["Open", "Close"])

            st.divider()
            st.subheader("Initial Payment Details")
            amount_paid = st.number_input("Initial Amount Paid (Rs.)", min_value=0.0, step=500.0, format="%.2f")
            payment_method = st.selectbox("Payment Method", options=["Cash", "UPI", "Card"])

            st.divider()
            submit_button = st.form_submit_button("Submit Sale")

        if submit_button:
            product_name = custom_product_name if selected_product_opt == "Other (Enter custom name)..." else selected_product_opt
            
            # Form Validation
            if not customer_name.strip():
                st.error("Please enter a valid customer name.")
            elif not mobile_number.strip():
                st.error("Please enter a valid mobile number.")
            elif not product_name.strip():
                st.error("Please specify a product name.")
            elif gross_sales <= 0:
                st.error("Gross sales must be greater than zero.")
            elif amount_paid > gross_sales:
                st.error("Initial payment cannot exceed gross sales.")
            else:
                success, message = add_new_sale(
                    branch_id=selected_branch_id,
                    date=sale_date,
                    name=customer_name.strip(),
                    mobile_number=mobile_number.strip(),
                    product_name=product_name.strip(),
                    gross_sales=gross_sales,
                    amount_paid=amount_paid,
                    payment_method=payment_method,
                    status=sale_status
                )
                if success:
                    show_success_dialog(customer_name.strip(), product_name.strip(), gross_sales)
                else:
                    st.error(message)

    elif page == "Record Payment":
        st.title("Record Payment")
        st.markdown("Use this form to record a new payment instalment for an existing customer sale. Balances will be recalculated via database triggers.")

        if df.empty:
            st.info("No active sales records found in your view to record payments against.")
        else:
            sales_list = df.to_dict('records')
            
            # Create a label mapping for selector options
            sale_options = []
            sale_map = {}
            for s in sales_list:
                label = f"{s['name']} | Product: {s['product_name']} | Branch: {s['branch_name']} (Pending: Rs. {s['pending_amount']:,.2f})"
                sale_options.append(label)
                sale_map[label] = s

            with st.form("record_payment_form", clear_on_submit=False):
                st.subheader("Select Sale & Payment Details")
                selected_label = st.selectbox("Select Customer / Sale Record", options=sale_options)
                
                selected_sale = sale_map[selected_label]
                pending_bal = float(selected_sale['pending_amount'])

                st.markdown(f"**Current Pending Balance**: Rs. {pending_bal:,.2f}")
                
                payment_amount = st.number_input(
                    "Amount Paid (Rs.)", 
                    min_value=0.0, 
                    max_value=max(0.0, pending_bal),
                    step=500.0, 
                    format="%.2f",
                    disabled=(pending_bal <= 0)
                )
                
                payment_date = st.date_input("Payment Date", value=pd.Timestamp.now().date())
                payment_method = st.selectbox("Payment Method", options=["Cash", "UPI", "Card"])

                st.divider()
                submit_payment = st.form_submit_button("Record Payment", disabled=(pending_bal <= 0))

            if pending_bal <= 0:
                st.info("This customer has already paid in full. No further payments are required.")

            if submit_payment:
                if payment_amount <= 0:
                    st.error("Please enter a payment amount greater than zero.")
                elif payment_amount > pending_bal:
                    st.error(f"Payment amount cannot exceed the pending balance of Rs. {pending_bal:,.2f}.")
                else:
                    success, message = add_payment(
                        sale_id=selected_sale['sale_id'],
                        amount_paid=payment_amount,
                        payment_date=payment_date,
                        payment_method=payment_method
                    )
                    if success:
                        new_pending = pending_bal - payment_amount
                        show_payment_success_dialog(
                            name=selected_sale['name'],
                            product=selected_sale['product_name'],
                            amount_paid=payment_amount,
                            pending_before=pending_bal,
                            pending_after=new_pending
                        )
                    else:
                        st.error(message)