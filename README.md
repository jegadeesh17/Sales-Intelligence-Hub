# Sales Intelligence Hub

---

### **Project Overview**

Organizations with multiple branches face critical operational challenges: manual math errors in split payment calculations, lack of real-time financial visibility for directors, and security risks when branch managers access restricted data. This project builds a fully automated multi-branch sales monitoring and financial tracking system to solve these problems at the database layer.

The platform shifts business logic directly into PostgreSQL using SQL triggers and generated columns, ensuring mathematical integrity without application-layer intervention. A secure Streamlit web portal enforces strict Role-Based Access Control (RBAC), giving directors a full view while locking branch admins into their own scoped data.

---

### **Key Features**

* **Normalized 3NF Schema:** PostgreSQL database with `branches`, `users`, `customer_sales`, and `payment_splits` tables.
* **SQL Trigger Automation:** PL/pgSQL server-side triggers auto-recalculate received amounts across ledgers on installment events.
* **Generated Columns:** Postgres generated columns compute outstanding balances on the fly for guaranteed mathematical integrity.
* **Role-Based Access Control:** Super Admins view all branches; Branch Admins are locked into their own branch via parameterized queries.
* **bcrypt Authentication:** Secure password hashing for all user accounts.
* **Automated Data Seeding:** Python-based CSV ingestion script to safely populate the database architecture.
* **Interactive Streamlit Dashboard:** Live financial tracking portal with real-time sales and payment data.
* **Analytical SQL Suite:** Curated SQL queries for financial reporting and branch performance analysis.

---

### **Dataset**

* **Source:** Multi-branch sales and payment records (seeded via CSV)
* **Coverage:** Customer sales transactions, installment payments, branch operations
* **Format:** CSV data seeded into PostgreSQL via automated ingestion

#### **Key Tables**

* `branches` — Branch master data and region information
* `users` — Admin accounts with hashed passwords and role assignments
* `customer_sales` — Sales transactions per customer per branch
* `payment_splits` — Installment payment records linked to each sale

---

### **Project Structure**

```bash
Sales-Intelligence-Hub/
│
├── data/                           # Raw CSV seed data
│
├── app/
│   └── app.py                      # Streamlit RBAC dashboard application
│
├── src/
│   ├── database.py                 # Database connection and query layer
│   ├── seed_data.py                # Automated data ingestion and seeding script
│   ├── sales_management.sql        # Core schema: tables, triggers, generated columns
│   └── analytical_queries.sql     # Financial reporting SQL queries
│
├── project_presentation.ipynb     # Project summary notebook
├── requirements.txt               # Python dependencies
└── README.md
```

---

### **How It Works**

### **1. Database Schema & Automation**

* Creates a normalized 3NF schema in PostgreSQL
* Defines generated columns for automatic balance computation

```sql
-- Generated column: outstanding balance computed automatically
ALTER TABLE customer_sales
ADD COLUMN outstanding_balance NUMERIC
GENERATED ALWAYS AS (total_amount - received_amount) STORED;
```

---

### **2. SQL Trigger Automation**

PL/pgSQL triggers fire on every installment insert, update, or delete to keep ledger balances accurate:

```sql
CREATE OR REPLACE FUNCTION update_received_amount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_sales
    SET received_amount = (
        SELECT COALESCE(SUM(amount), 0)
        FROM payment_splits
        WHERE sale_id = NEW.sale_id
    )
    WHERE id = NEW.sale_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_received
AFTER INSERT OR UPDATE OR DELETE ON payment_splits
FOR EACH ROW EXECUTE FUNCTION update_received_amount();
```

---

### **3. Role-Based Access Control**

The authentication system uses bcrypt hashing and parameterized queries to enforce scoped data access:

| Role         | Access Level                              |
| ------------ | ----------------------------------------- |
| Super Admin  | All branches — full financial visibility  |
| Branch Admin | Own branch only — scoped parameterized SQL|

---

### **Model Performance**

| Metric                     | Result                               |
| -------------------------- | ------------------------------------ |
| Mathematical Integrity     | 100% (trigger-guaranteed)            |
| Balance Accuracy           | Real-time (generated columns)        |
| Auth Security              | bcrypt hashed (no plaintext storage) |

---

### **Interactive Application Deployment**

The project features a secure **Streamlit Web Application** with RBAC-enforced views, real-time payment tracking, and branch-level financial summaries.

#### **To Launch the Platform Locally:**
```powershell
streamlit run app/app.py
```

#### **Demo Logins:**

| Role         | Username        | Password   |
| ------------ | --------------- | ---------- |
| Super Admin  | `superadmin`    | `super123` |
| Branch Admin | `admin_chennai` | `admin123` |

---

### **Technology Stack**

| Category             | Tools                             |
| -------------------- | --------------------------------- |
| Programming          | Python                            |
| Database             | PostgreSQL, PL/pgSQL              |
| ORM / Integration    | Psycopg2, SQLAlchemy              |
| Authentication       | bcrypt                            |
| Data Processing      | Pandas                            |
| Notebook Environment | Jupyter Notebook                  |
| Web Framework        | Streamlit                         |

---

### **Getting Started**

### **1. Clone Repository**

```bash
git clone https://github.com/jegadeesh17/Sales-Intelligence-Hub.git

cd Sales-Intelligence-Hub
```

---

### **2. Configure Database**

Ensure PostgreSQL is running with the `sales_management` database created. Update `.env` with your credentials:

```env
DB_HOST=localhost
DB_NAME=sales_management
DB_USER=your_user
DB_PASSWORD=your_password
```

---

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

---

### **4. Seed Database**

```bash
python src/seed_data.py
```

---

### **5. Launch Dashboard**

```bash
streamlit run app/app.py
```

---

### **Example Use Case**

A multi-branch retail organization can use this system to:

1. Track real-time payment collections and outstanding balances per branch
2. Allow directors to compare branch-level financial performance
3. Enforce data privacy so branch managers only see their own data
4. Automatically reconcile payment splits without manual calculation

---

### **Future Improvements**

* PDF financial report generation for branch managers
* Email alerting for overdue installments
* Real-time branch performance dashboards with time-series trends
* Integration with accounting software (Tally, QuickBooks)

---

### **Contributors**

* **Jegadeesh D** — PostgreSQL schema design, PL/pgSQL trigger automation, RBAC authentication, data seeding, and Streamlit dashboard development

---

### **License**

MIT License
