# seed_data.py
# ---------------------------------------------------------
# Purpose : Read branch, user, sales, and payment CSV files
#           and load them into the sales_management PostgreSQL
#           database.
#
# This script also fixes the auto-increment sequence counters
# after manually inserting rows with existing IDs from the CSV.
#
# How to run (from the src/ directory):
#   python seed_data.py
# ---------------------------------------------------------

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

# Build the path to the data folder relative to this script file.
# Using Path(__file__) means this works regardless of where you run it from.
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

# SQLAlchemy engine — the recommended way to use pandas .to_sql() with PostgreSQL.
# Connection string format: postgresql://username:password@host:port/database
engine = create_engine("postgresql://postgres:jaundice@localhost:5432/sales_management")


def seed_database():
    """Load all CSV files into the PostgreSQL database in the correct order."""

    print("Starting data migration into PostgreSQL...")

    try:
        # engine.begin() opens a transaction that auto-commits on success
        # and auto-rolls back if any step fails.
        with engine.begin() as connection:

            # Step 1: Load Branches
            # Branches must be inserted first because other tables reference branch_id.
            print("Loading Branches...")
            branches_df = pd.read_csv(DATA_DIR / 'branches.csv')
            branches_df.to_sql("branches", con=connection, if_exists="append", index=False)

            # Step 2: Load Users
            # Users reference branches, so branches must already exist.
            print("Loading Users...")
            users_df = pd.read_csv(DATA_DIR / 'users.csv')
            users_df.to_sql("users", con=connection, if_exists="append", index=False)

            # Step 3: Load Customer Sales
            # The pending_amount column is auto-calculated by PostgreSQL as a generated column
            # (gross_sales - received_amount), so we must not insert it manually.
            print("Loading Customer Sales...")
            sales_df = pd.read_csv(DATA_DIR / 'customer_sales.csv')

            if 'pending_amount' in sales_df.columns:
                sales_df = sales_df.drop(columns=['pending_amount'])

            # Set received_amount to 0 on initial load.
            # The payment trigger will recalculate this correctly in Step 4.
            if 'received_amount' in sales_df.columns:
                sales_df['received_amount'] = 0.00

            sales_df.to_sql("customer_sales", con=connection, if_exists="append", index=False)

            # Step 4: Load Payment Splits
            # Inserting payment records fires a PostgreSQL trigger that automatically
            # updates the received_amount in the customer_sales table.
            print("Loading Payment Splits (this triggers automatic balance recalculation)...")
            splits_df = pd.read_csv(DATA_DIR / 'payment_splits.csv')
            splits_df.to_sql("payment_splits", con=connection, if_exists="append", index=False)

            # Step 5: Fix auto-increment sequences
            # When we insert rows with manually specified IDs from the CSV files,
            # PostgreSQL's internal ID counter does not advance automatically.
            # We manually sync each sequence to avoid duplicate key errors on future inserts.
            print("Syncing primary key sequences...")
            connection.execute(text("SELECT setval('branches_branch_id_seq',      COALESCE((SELECT MAX(branch_id)+1      FROM branches),      1), false);"))
            connection.execute(text("SELECT setval('users_user_id_seq',            COALESCE((SELECT MAX(user_id)+1        FROM users),          1), false);"))
            connection.execute(text("SELECT setval('customer_sales_sale_id_seq',   COALESCE((SELECT MAX(sale_id)+1        FROM customer_sales), 1), false);"))
            connection.execute(text("SELECT setval('payment_splits_payment_id_seq',COALESCE((SELECT MAX(payment_id)+1     FROM payment_splits), 1), false);"))

        print("Database seeded successfully! All balances recalculated via triggers.")

    except Exception as e:
        print(f"Migration failed. Error details: {e}")


# Only run seed_database() when this file is executed directly.
# If another script imports this file, the seeding will not run automatically.
if __name__ == "__main__":
    seed_database()