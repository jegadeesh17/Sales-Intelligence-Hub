# 🎯 Sales Intelligence Hub

A multi-branch sales monitoring and automated financial tracking system designed to eliminate manual data entry inconsistencies and optimize revenue transparency.

## 📖 Project Overview
Organizations with multiple branches face severe operational challenges, including manual math errors when calculating split payments, lack of real-time visibility for directors, and security violations when branch managers access restricted data. 

This project shifts business logic directly to the database layer for high integrity, creating a fully automated PostgreSQL backend. An interactive Streamlit dashboard securely serves the data, enforcing strict Role-Based Access Control (RBAC) to separate Super Admins from Branch Admins.

## 🏗️ Architecture & Pipeline

1. **Database Design & Modeling**: A normalized 3NF relational schema in PostgreSQL containing tables for `branches`, `users`, `customer_sales`, and `payment_splits`.
2. **Database Automation**: 
   - **SQL Triggers**: PL/pgSQL server-side triggers automatically recalculate received amounts across ledgers whenever an installment is made, updated, or deleted.
   - **Generated Columns**: Postgres generated columns compute outstanding balances on the fly to guarantee mathematical integrity.
3. **Secure Web Dashboard**: An interactive web portal using Streamlit, featuring RBAC. Authentication is secured using `bcrypt` password hashing. Super Admins can view all branches, whereas Branch Admins are locked into their own specific branch views via parameterized SQL queries.
4. **Python-PostgreSQL Integration**: Clean, modular integration code using Psycopg2 and SQLAlchemy, alongside an automated data seeding script to safely ingest CSV data into the database architecture.

## 🚀 How to Run

1. **Verify Database Configuration**: Run Docker or local PostgreSQL and ensure the `sales_management` database is created.
2. **Execute Database Seeding**:
   ```bash
   python src/seed_data.py
   ```
3. **Run the Streamlit Dashboard**:
   ```bash
   streamlit run app/app.py
   ```
   **Demo Logins:**
   - **Super Admin**: Username `superadmin`, Password `super123`
   - **Branch Admin**: Username `admin_chennai`, Password `admin123`
