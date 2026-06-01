# database.py
# ---------------------------------------------------------
# Purpose : Handles all PostgreSQL database interactions for
#           the Sales Management System.
#
# Functions:
#   get_db_connection() → opens and returns a database connection
#   verify_user()       → checks login credentials
#   fetch_sales_data()  → fetches sales records based on user role
# ---------------------------------------------------------

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── Database Connection ───────────────────────────────────────────────────────
# RealDictCursor makes psycopg2 return rows as dictionaries ({"column": value})
# instead of plain tuples, which is much easier to work with in Python.

def get_db_connection():
    """Open and return a new connection to the sales_management database."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "sales_management"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )
    return conn


# ── User Authentication ───────────────────────────────────────────────────────

import bcrypt

def verify_user(username, password):
    """
    Check if the given username and password match.
    Retrieves the record by username and verifies the hash with bcrypt.
    """
    conn = get_db_connection()
    cur  = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch the user record by username
    cur.execute(
        "SELECT user_id, username, role, branch_id, password FROM users WHERE username = %s",
        (username,)
    )
    user = cur.fetchone()

    cur.close()
    conn.close()

    if user:
        # Verify the stored hash matches the input password
        stored_hash = user['password']
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                # Remove the password hash from the returned user dictionary for security
                del user['password']
                return user
        except Exception:
            pass
            
    return None


# ── Sales Data Fetching ───────────────────────────────────────────────────────

def fetch_sales_data(role, branch_id=None):
    """
    Fetch sales records from the database based on the user's role.

    - Super Admin: can see sales from all branches
    - Admin: can only see sales from their own branch
    """
    conn = get_db_connection()
    cur  = conn.cursor(cursor_factory=RealDictCursor)

    if role == 'Super Admin':
        # Super Admin has access to all branch data
        cur.execute("""
            SELECT s.*, b.branch_name
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
        """)
    else:
        # Branch Admin can only see records belonging to their branch
        cur.execute("""
            SELECT s.*, b.branch_name
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
            WHERE s.branch_id = %s
        """, (branch_id,))

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


# ── Add New Sale & Fetch Branches ─────────────────────────────────────────────

def fetch_branches():
    """Fetch list of all branches from the database."""
    conn = get_db_connection()
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT branch_id, branch_name FROM branches ORDER BY branch_name")
    branches = cur.fetchall()
    cur.close()
    conn.close()
    return branches


def add_new_sale(branch_id, date, name, mobile_number, product_name, gross_sales, amount_paid, payment_method, status='Open'):
    """
    Insert a new customer sale and initial payment split inside a database transaction.
    The database trigger 'after_payment_insert' will auto-recalculate the balance columns.
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # 1. Insert the customer sale record
                cur.execute("""
                    INSERT INTO customer_sales (branch_id, date, name, mobile_number, product_name, gross_sales, received_amount, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 0.00, %s)
                    RETURNING sale_id
                """, (branch_id, date, name, mobile_number, product_name, gross_sales, status))
                
                sale_id = cur.fetchone()[0]
                
                # 2. Insert initial payment split if amount_paid > 0
                if amount_paid > 0:
                    cur.execute("""
                        INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                        VALUES (%s, %s, %s, %s)
                    """, (sale_id, date, amount_paid, payment_method))
                    
        return True, "Sale added successfully!"
    except psycopg2.IntegrityError as e:
        if "mobile_number" in str(e):
            return False, "Error: A customer with this mobile number already exists."
        return False, f"Integrity error: {e}"
    except Exception as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


def add_payment(sale_id, amount_paid, payment_date, payment_method):
    """
    Insert a new payment split into the payment_splits table.
    The database trigger 'after_payment_insert' will auto-recalculate the balance columns in customer_sales.
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                    VALUES (%s, %s, %s, %s)
                """, (sale_id, payment_date, amount_paid, payment_method))
        return True, "Payment recorded successfully!"
    except Exception as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


# ── SQL Predefined Queries for Analytics Tab ─────────────────────────────────

PREDEFINED_QUERIES = {
    1: {
        "title": "1. Retrieve all records from the customer_sales table",
        "category": "Basic Queries",
        "description": "Shows all sales records.",
        "sql_super": "SELECT * FROM customer_sales ORDER BY sale_id;",
        "sql_branch": "SELECT * FROM customer_sales WHERE branch_id = %s ORDER BY sale_id;",
    },
    2: {
        "title": "2. Retrieve all records from the branches table",
        "category": "Basic Queries",
        "description": "Shows details of branches.",
        "sql_super": "SELECT * FROM branches ORDER BY branch_id;",
        "sql_branch": "SELECT * FROM branches WHERE branch_id = %s ORDER BY branch_id;",
    },
    3: {
        "title": "3. Retrieve all records from the payment_splits table",
        "category": "Basic Queries",
        "description": "Shows all recorded payments/installments.",
        "sql_super": "SELECT * FROM payment_splits ORDER BY payment_id;",
        "sql_branch": """
            SELECT p.* 
            FROM payment_splits p 
            JOIN customer_sales s ON p.sale_id = s.sale_id 
            WHERE s.branch_id = %s 
            ORDER BY p.payment_id;
        """,
    },
    4: {
        "title": "4. Show only sales that are still open",
        "category": "Basic Queries",
        "description": "Filter sales where payment is pending (status is 'Open').",
        "sql_super": "SELECT * FROM customer_sales WHERE status = 'Open' ORDER BY sale_id;",
        "sql_branch": "SELECT * FROM customer_sales WHERE status = 'Open' AND branch_id = %s ORDER BY sale_id;",
    },
    5: {
        "title": "5. Calculate the total gross sales value across branches",
        "category": "Aggregation Queries",
        "description": "Sum of all sales amounts.",
        "sql_super": "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales;",
        "sql_branch": "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales WHERE branch_id = %s;",
    },
    6: {
        "title": "6. Calculate the total amount collected across all sales",
        "category": "Aggregation Queries",
        "description": "Sum of all received amounts.",
        "sql_super": "SELECT SUM(received_amount) AS total_received_amount FROM customer_sales;",
        "sql_branch": "SELECT SUM(received_amount) AS total_received_amount FROM customer_sales WHERE branch_id = %s;",
    },
    7: {
        "title": "7. Calculate the total outstanding amount across all sales",
        "category": "Aggregation Queries",
        "description": "Sum of all pending amounts.",
        "sql_super": "SELECT SUM(pending_amount) AS total_pending_amount FROM customer_sales;",
        "sql_branch": "SELECT SUM(pending_amount) AS total_pending_amount FROM customer_sales WHERE branch_id = %s;",
    },
    8: {
        "title": "8. Count how many sales each branch has recorded",
        "category": "Aggregation Queries",
        "description": "Number of sales per branch.",
        "sql_super": "SELECT branch_id, COUNT(sale_id) AS total_sales_count FROM customer_sales GROUP BY branch_id;",
        "sql_branch": "SELECT branch_id, COUNT(sale_id) AS total_sales_count FROM customer_sales WHERE branch_id = %s GROUP BY branch_id;",
    },
    9: {
        "title": "9. Show each sale along with the name of its branch",
        "category": "Join-Based Queries",
        "description": "Combines sale records with branch names using a JOIN.",
        "sql_super": """
            SELECT s.sale_id, s.name AS customer_name, s.product_name, b.branch_name, s.gross_sales
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
            ORDER BY s.sale_id;
        """,
        "sql_branch": """
            SELECT s.sale_id, s.name AS customer_name, s.product_name, b.branch_name, s.gross_sales
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
            WHERE s.branch_id = %s
            ORDER BY s.sale_id;
        """,
    },
    10: {
        "title": "10. Show total gross sales per branch, highest first",
        "category": "Join-Based Queries",
        "description": "Sum of gross sales grouped by branch, sorted descending.",
        "sql_super": """
            SELECT b.branch_name, SUM(s.gross_sales) AS branch_total_gross_sales
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
            GROUP BY b.branch_name
            ORDER BY branch_total_gross_sales DESC;
        """,
        "sql_branch": """
            SELECT b.branch_name, SUM(s.gross_sales) AS branch_total_gross_sales
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
            WHERE s.branch_id = %s
            GROUP BY b.branch_name;
        """,
    },
    11: {
        "title": "11. Show each sale alongside the payment method used",
        "category": "Join-Based Queries",
        "description": "Unique mapping of sales and payment methods.",
        "sql_super": """
            SELECT DISTINCT s.sale_id, s.name AS customer_name, p.payment_method
            FROM customer_sales s
            JOIN payment_splits p ON s.sale_id = p.sale_id
            ORDER BY s.sale_id;
        """,
        "sql_branch": """
            SELECT DISTINCT s.sale_id, s.name AS customer_name, p.payment_method
            FROM customer_sales s
            JOIN payment_splits p ON s.sale_id = p.sale_id
            WHERE s.branch_id = %s
            ORDER BY s.sale_id;
        """,
    },
    12: {
        "title": "12. Show each sale along with the responsible branch admin's name",
        "category": "Join-Based Queries",
        "description": "Combines sale records with branch admin details.",
        "sql_super": """
            SELECT s.sale_id, s.name AS customer_name, b.branch_name, b.branch_admin_name
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
            ORDER BY s.sale_id;
        """,
        "sql_branch": """
            SELECT s.sale_id, s.name AS customer_name, b.branch_name, b.branch_admin_name
            FROM customer_sales s
            JOIN branches b ON s.branch_id = b.branch_id
            WHERE s.branch_id = %s
            ORDER BY s.sale_id;
        """,
    },
    13: {
        "title": "13. Find all sales where outstanding amount > Rs.5000",
        "category": "Financial Tracking Queries",
        "description": "Shows customers with large pending balances.",
        "sql_super": """
            SELECT sale_id, name, branch_id, pending_amount
            FROM customer_sales
            WHERE pending_amount > 5000.00
            ORDER BY pending_amount DESC;
        """,
        "sql_branch": """
            SELECT sale_id, name, branch_id, pending_amount
            FROM customer_sales
            WHERE pending_amount > 5000.00 AND branch_id = %s
            ORDER BY pending_amount DESC;
        """,
    },
    14: {
        "title": "14. Show the top 3 highest gross sales",
        "category": "Financial Tracking Queries",
        "description": "Retrieves the top 3 sales by gross amount.",
        "sql_super": """
            SELECT sale_id, name, gross_sales
            FROM customer_sales
            ORDER BY gross_sales DESC
            LIMIT 3;
        """,
        "sql_branch": """
            SELECT sale_id, name, gross_sales
            FROM customer_sales
            WHERE branch_id = %s
            ORDER BY gross_sales DESC
            LIMIT 3;
        """,
    },
    15: {
        "title": "15. Show total collections broken down by payment method",
        "category": "Financial Tracking Queries",
        "description": "Sums collected amounts grouped by cash/UPI/card.",
        "sql_super": """
            SELECT payment_method, SUM(amount_paid) AS total_collected
            FROM payment_splits
            GROUP BY payment_method
            ORDER BY total_collected DESC;
        """,
        "sql_branch": """
            SELECT p.payment_method, SUM(p.amount_paid) AS total_collected
            FROM payment_splits p
            JOIN customer_sales s ON p.sale_id = s.sale_id
            WHERE s.branch_id = %s
            GROUP BY p.payment_method
            ORDER BY total_collected DESC;
        """,
    }
}


def execute_query(sql_query, params=None):
    """
    Execute a raw SQL query safely and return the results as a list of dictionaries.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(sql_query, params)
        if cur.description:
            data = cur.fetchall()
        else:
            conn.commit()
            data = []
        return data, None
    except Exception as e:
        return None, str(e)
    finally:
        cur.close()
        conn.close()