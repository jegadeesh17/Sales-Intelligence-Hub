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