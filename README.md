# 📊 Sales Intelligence Hub – Enterprise Documentation

The **Sales Intelligence Hub** is a multi-branch sales monitoring and automated financial tracking system designed to eliminate manual data entry inconsistencies and optimize revenue transparency across all corporate divisions. By centralizing transaction logs and automating payment split calculations directly inside a secure PostgreSQL database, the hub provides executives and branch managers with a single source of truth for financial health.

---

## 🎯 Key Business Benefits & Use Cases

- 📈 **Seamless Branch-Wise Performance Tracking:** Gain instant clarity into how individual branches are performing against target revenue thresholds.
- 💵 **Real-Time Revenue and Outstanding Payment Monitoring:** Instantly track actual cash collected against pending accounts receivable to optimize cash flow management.
- 🛡️ **Zero Human Calculation Errors:** Systematically eliminate rounding discrepancies, math mistakes, and reconciliation issues in multi-partner or customer split-payment installments.
- 💡 **Instant Trend and Leaderboard Insights:** Identify top-performing branches, customer payment behavior trends, and monthly sales volumes at the click of a button.

---

## 🏗️ System Architecture & Data Model (PostgreSQL)

To ensure maximum security and reliability, the system is built on a robust relational database model. In a relational database, different business entities—such as branches, users, sales, and payments—are securely linked to one another using defined constraints. This architecture guarantees that if branch details change, or a new user is added, all associated financial ledgers automatically stay synchronized and consistent.

### 📝 Data Tables Overview

1.  **Branches (`branches`):** Tracks corporate branch locations and their assigned administrators.
2.  **Users (`users`):** Manages user credentials (encrypted passwords), communication emails, and access control levels (**Super Admin** or **Branch Admin**).
3.  **Customer Sales (`customer_sales`):** The primary transaction ledger. It logs the customer name, unique identifier of the branch handling the transaction, the total **gross_sales** contract value, and the automated balance columns.
4.  **Payment Splits (`payment_splits`):** Tracks installment details, payment dates, and payment methods (such as **Cash**, **UPI**, or **Card**) for customers who pay in parts.

### 🤖 Core Automation Rules (Triggers & Generated Columns)

The database utilizes built-in server-side logic to ensure absolute mathematical integrity, removing calculation burdens from user interfaces and backend applications.

*   🤖 **Automatic Calculations (`pending_amount`):** The **pending_amount** column in the **customer_sales** table is a **GENERATED ALWAYS** SQL column. It calculates outstanding balances automatically using the equation:
    $$\mathbf{pending\_amount} = \mathbf{gross\_sales} - \mathbf{received\_amount}$$
    This calculation runs natively at the database engine level, preventing any client-side overrides or human errors.
*   ⚡ **Live Database Triggers:** When a payment installment is recorded or updated in the **payment_splits** table, a background database rule automatically recalculates the total money received and instantly updates the **received_amount** column in the associated **customer_sales** ledger.
    *   *Warning:* By executing this logic automatically, the system completely blocks manual calculation tampering, entry typos, or missing payment updates.

---

## 🔐 Security & Role-Based Access Control (RBAC)

The application enforces strict data segregation and protection protocols to guarantee that sensitive financial figures are only visible to authorized personnel.

*   🛡️ **Secure Authentication:** Users must log in via a dedicated, session-secured portal screen. Unauthorized attempts to bypass the gate or access dashboard URLs directly are strictly blocked.
*   👑 **Super Admin Role:** Grants unrestricted, cross-organizational visibility. A **Super Admin** can monitor financial metrics, view complete transaction ledgers, and add sales data for *all* branches across the entire enterprise.
*   🏢 **Branch Admin Role:** Strictly locks permissions to local operations. A **Branch Admin** can only view metrics, track pending rows, and record sales transactions *specifically for their assigned branch*. They are fully blind to other branches' data.

---

## 💻 Streamlit Interface & Dashboard Navigation

The interactive web console is organized into four main operational areas:

1.  🔑 **The Secure Gate (Login Page):** A clean interface requiring a username and password. User credentials and roles are validated against database records and managed in streamlit's session state.
2.  📊 **Executive KPI Cards:** Highlights three high-level business metrics updated dynamically based on the current user's role:
    *   **Total Gross Sales:** Total contract volume signed.
    *   **Total Collected:** Total cash received through payment splits.
    *   **Total Outstanding:** Remaining outstanding customer debt.
3.  ✏️ **Operational Forms:** Intuitive input modules for logging new sales records and applying real-time payment splits.
4.  📈 **The Command Center (Insights Section):** Displays visual trends including distribution graphs of payment methods (Cash/Card/UPI) and revenue-sharing payouts per branch.

---

## 🛠️ Step-by-Step Environment Setup & Deployment

Follow these copy-paste commands in your terminal to set up the local environment:

### 1. Project Directory Structure
Ensure files are organized in the project folder like this:
```text
sales_management_system/
├── app.py              # Streamlit Web Dashboard
├── database.py         # Database Connection Utility
├── seed_data.py        # Automated Seeding & Migration Tool
├── data/
│   ├── branches.csv
│   ├── users.csv
│   ├── customer_sales.csv
│   └── payment_splits.csv
├── schema.sql          # Table Schema Definitions
└── triggers.sql        # Postgres Trigger Definitions
```

### 2. Install Python Dependencies
Open your command terminal and install the required packages:
```bash
pip install pandas streamlit psycopg2 sqlalchemy
```

### 3. Create the Database Schema
Create the database schema using the schema and trigger definitions in your PostgreSQL database instance:
```bash
psql -U postgres -d sales_management -f schema.sql
psql -U postgres -d sales_management -f triggers.sql
```

### 4. Run the Seeding & Data Migration Framework
Run the migration script to load the base CSV records from the **data/** directory into your active database:
```bash
python seed_data.py
```

### 5. Launch the Dashboard
Start the Streamlit application server:
```bash
streamlit run app.py
```

The application will start, and a browser window will automatically open at `http://localhost:8501`.
