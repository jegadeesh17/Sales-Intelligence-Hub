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