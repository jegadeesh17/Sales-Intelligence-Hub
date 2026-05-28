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

# ── Database Connection ───────────────────────────────────────────────────────
# RealDictCursor makes psycopg2 return rows as dictionaries ({"column": value})
# instead of plain tuples, which is much easier to work with in Python.

def get_db_connection():
    """Open and return a new connection to the sales_management database."""
    conn = psycopg2.connect(
        host="localhost",
        database="sales_management",
        user="postgres",
        password="jaundice",
        port="5432"
    )
    return conn


# ── User Authentication ───────────────────────────────────────────────────────

def verify_user(username, password):
    """
    Check if the given username and password exist in the users table.
    Returns the user record as a dictionary if valid, or None if not found.

    Note: In a real production app, passwords should be hashed using
    a library like bcrypt — never stored or compared as plain text.
    """
    conn = get_db_connection()
    cur  = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT user_id, username, role, branch_id FROM users WHERE username = %s AND password = %s",
        (username, password)
    )
    user = cur.fetchone()

    cur.close()
    conn.close()
    return user


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