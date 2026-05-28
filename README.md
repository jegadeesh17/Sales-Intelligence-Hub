# Sales Intelligence Hub

---

### **Project Overview**

The **Sales Intelligence Hub** is a multi-branch sales monitoring and automated financial tracking system designed to eliminate manual data entry inconsistencies and optimize revenue transparency across all corporate divisions. By centralizing transaction logs and automating payment split calculations directly inside a secure PostgreSQL database, the hub provides executives and branch managers with a single source of truth for financial health.

The platform coordinates branches, users, customer sales, and installment payments, securing access via role-based authentication and exposing real-time insights through a modern dashboard interface.

---

### **Key Features**

* **Seamless Branch Performance Tracking:** Gain instant clarity into how individual branches are performing against target revenue thresholds.
* **Real-Time Revenue & Outstanding Payment Monitoring:** Instantly track actual cash collected against pending accounts receivable.
* **Role-Based Access Control (RBAC):** Restricts data views dynamically between Super Admins (cross-branch visibility) and Branch Admins (single-branch view).
* **Zero Human Calculation Errors:** Utilizes server-side PostgreSQL triggers and generated columns to guarantee mathematical integrity.
* **Interactive Streamlit Interface:** Features executive KPI cards, secure login portals, operational forms, and transaction visualization trends.

---

### **Database Schema & Automation Rules**

To ensure absolute reliability, the backend uses relational constraints, generated columns, and automatic triggers:

#### **Key Database Tables**

1. **Branches (`branches`):** Tracks corporate branch locations and assigned administrators.
2. **Users (`users`):** Manages user credentials (encrypted passwords), communication emails, and access control levels (**Super Admin** or **Branch Admin**).
3. **Customer Sales (`customer_sales`):** Logs customer names, branch links, gross contract values, and automated outstanding balances.
4. **Payment Splits (`payment_splits`):** Tracks installment details, payment dates, and payment methods (Cash, UPI, or Card).

#### **Core Database Automation Rules**

* **Automatic Outstanding Calculation:** The `pending_amount` column is defined as `GENERATED ALWAYS` at the table engine level:
  $$\mathbf{pending\_amount} = \mathbf{gross\_sales} - \mathbf{received\_amount}$$
* **Live Calculation Triggers:** Inserting or updating installment records in `payment_splits` triggers an automatic background recalculation of the `received_amount` in the corresponding `customer_sales` record, fully eliminating client-side tampering or entry typos.

---

### **Project Structure**

```bash
Sales-Intelligence-Hub/
│
├── app/
│   └── app.py              # Streamlit Web Dashboard
│
├── data/
│   ├── branches.csv
│   ├── customer_sales.csv
│   ├── customer_sales.xlsx
│   ├── payment_splits.csv
│   └── users.csv
│
├── src/
│   ├── database.py         # Database Connection Utility
│   ├── seed_data.py        # Automated Seeding & Migration Tool
│   ├── sales_management.sql # Table Schema & Trigger Definitions
│   └── analytical_queries.sql # Analytical Query Definitions
│
├── .gitignore
└── README.md
```

---

### **How It Works**

### **1. Database Setup**

Create a PostgreSQL database (e.g. `sales_management`) and configure your connection credentials. The schema definition contains foreign key relationships to prevent deletion anomalies:

```sql
-- Example Schema structure
CREATE TABLE customer_sales (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),
    branch_id INT REFERENCES branches(id),
    gross_sales NUMERIC(12,2),
    received_amount NUMERIC(12,2) DEFAULT 0.00,
    pending_amount NUMERIC(12,2) GENERATED ALWAYS AS (gross_sales - received_amount) STORED
);
```

---

### **2. Automated Payment Recalculation Trigger**

Whenever a split payment is registered, a database trigger executes a procedure to update the main sales ledger:

```sql
CREATE OR REPLACE FUNCTION update_received_amount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_sales
    SET received_amount = COALESCE((
        SELECT SUM(amount) 
        FROM payment_splits 
        WHERE sale_id = NEW.sale_id
    ), 0.00)
    WHERE id = NEW.sale_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

### **Database Configuration**

Ensure database connection keys are matched in your environment configuration or database connector files. The connection logic uses `sqlalchemy` and `psycopg2`.

---

### **Model & Query Metrics**

The platform executes advanced window functions and analytical queries (`analytical_queries.sql`) to calculate:
* Monthly rolling revenue per branch
* Transaction count leaderboards
* Payment method distribution ratios

---

### **Interactive Application Deployment**

The project features a secure **Streamlit Web Application** designed with clean styling and dynamic Plotly components.

#### **To Launch the Platform Locally:**
```powershell
python -m streamlit run ".\Sales Intelligence Hub\app\app.py"
```

---

### **Technology Stack**

| Category             | Tools                                         |
| -------------------- | --------------------------------------------- |
| Programming          | Python                                        |
| Database Engine      | PostgreSQL                                    |
| Database Connection  | SQLAlchemy, Psycopg2                          |
| Data Processing      | Pandas                                        |
| Web Framework        | Streamlit                                     |
| Visualization        | Plotly                                        |

---

### **Getting Started**

### **1. Install Dependencies**

```bash
pip install pandas streamlit psycopg2 sqlalchemy python-dotenv bcrypt
```

---

### **2. Configure Environment Variables**

Create a file named `.env` in the root of the project folder:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sales_management
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

---

### **3. Initialize PostgreSQL Schema & Triggers**

Execute the SQL definitions in your database client:

```bash
psql -U postgres -d sales_management -f src/sales_management.sql
```

---

### **3. Run Seeding & Migration Pipeline**

Seed the database with pre-populated records from the CSV directories:

```bash
python src/seed_data.py
```

---

### **4. Launch the Dashboard**

Start the Streamlit application server:

```bash
streamlit run app/app.py
```

---

### **Example Use Case**

Corporate financial controllers can use the hub to:
1. Log new customer sales contracts.
2. Accept partial installment payments via different payment types.
3. Automatically track pending debt across different regional branches.
4. Verify branch administrative compliance using secure login roles.

---

### **Future Improvements**

* Integration with online payment gateways (Stripe/PayPal APIs) for automatic split-ledger booking.
* Automated PDF invoice and receipt generation for clients.
* Multi-currency support and real-time exchange rate conversions.

---

### **Contributors**

* **Jegadeesh D** — Relational database modeling, SQL automation triggers, data migration script, and Streamlit application development

---

### **License**

MIT License
