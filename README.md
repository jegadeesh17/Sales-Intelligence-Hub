# Sales Intelligence Hub

A multi-branch sales and installment-collections ledger that keeps its arithmetic in PostgreSQL, fronted by a Streamlit portal with role-based access. A trigger recomputes each sale's received amount from its payments, a generated column derives the pending balance, and branch admins only ever see their own branch.

## Features

- **Normalized schema:** PostgreSQL tables for `branches`, `users`, `customer_sales` and `payment_splits`, defined in `src/sales_management.sql`.
- **Trigger-maintained totals:** the PL/pgSQL function `update_received_amount_fn()` recalculates `received_amount` for a sale from its payment rows.
- **Generated balance:** `pending_amount` is a stored generated column, `gross_sales - received_amount`, so it cannot drift from the two values it derives from.
- **Role-based access:** Super Admins see every branch; Branch Admins are limited to their own branch through parameterized queries.
- **Password hashing:** passwords are hashed with bcrypt when the database is seeded.
- **Seeding script:** `src/seed_data.py` loads the CSVs in `data/` into the database.
- **Analytical queries:** `src/analytical_queries.sql` holds the reporting and branch-performance queries.
- **Streamlit dashboard:** sales and payment data by branch, with the view filtered by role.

## Quick start

Requires Python and a running PostgreSQL server with an empty `sales_management` database.

```bash
git clone https://github.com/jegadeesh17/Sales-Intelligence-Hub.git
cd Sales-Intelligence-Hub
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash; use .venv/bin/activate elsewhere
pip install -r requirements.txt
```

Create a file named `.env` with your database settings (see [Configuration](#configuration)), create the schema by running `src/sales_management.sql` against the `sales_management` database, then seed and launch:

```bash
python src/seed_data.py
streamlit run app/app.py
```

## Usage

Sign in with one of the seeded demo accounts from `data/users.csv`. These are sample credentials for the synthetic data only; change them for any real use.

| Role | Username | Password |
|---|---|---|
| Super Admin | `superadmin` | `super123` |
| Branch Admin (Chennai) | `admin_chennai` | `admin123` |

The seed data holds 8 branches, 1,000 sales and 2,011 payment rows, all synthetic.

## Running tests

This project has no automated test suite yet. `src/analytical_queries.sql` and the notebook `notebooks/SalesIntelligenceHub.ipynb` are the way to inspect the results.

## Configuration

`src/database.py` reads these variables from `.env` (defaults in brackets):

| Variable | Purpose |
|---|---|
| `DB_HOST` | PostgreSQL host (`localhost`) |
| `DB_NAME` | Database name (`sales_management`) |
| `DB_USER` | PostgreSQL user (`postgres`) |
| `DB_PASSWORD` | PostgreSQL password |

## Project structure

```
app/        Streamlit dashboard
data/       synthetic CSVs: branches, users, customer sales, payment splits
notebooks/  walkthrough notebook
src/        schema and trigger SQL, analytical queries, database access, seeding script
```

## Known limitations

- The trigger function reads `NEW.sale_id`, which is null on a `DELETE`, so deleting a payment does not refresh that sale's `received_amount`. Inserts and updates are handled.
- No automated tests.
- The demo passwords are listed above and stored in plain text in `data/users.csv` before seeding hashes them.

## License

[MIT](LICENSE)
