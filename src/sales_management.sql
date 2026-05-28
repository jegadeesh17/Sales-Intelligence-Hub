-- sales_management.sql
-- ---------------------------------------------------------
-- Purpose : Define the full database schema for the Sales
--           Management System, including tables, types,
--           generated columns, and an automated trigger.
--
-- Run this script once in PostgreSQL to create all tables
-- before running seed_data.py.
-- ---------------------------------------------------------


-- ====================================================================
-- SECTION 1: TABLE DEFINITIONS
-- ====================================================================

-- 1. Branches Table
-- Stores each physical branch and the name of its administrator.
CREATE TABLE branches (
    branch_id        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_name      VARCHAR(100) NOT NULL,
    branch_admin_name VARCHAR(100) NOT NULL
);


-- 2. Users Table
-- Stores login credentials and role assignments for each user.
-- Each user is linked to one branch (except Super Admin).
CREATE TYPE user_role AS ENUM ('Super Admin', 'Admin');

CREATE TABLE users (
    user_id   GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username  VARCHAR(100) NOT NULL,
    password  VARCHAR(255) NOT NULL,   -- Use a hashed value in production (e.g. bcrypt)
    branch_id INT          REFERENCES branches(branch_id) ON DELETE SET NULL,
    role      user_role    NOT NULL,
    email     VARCHAR(255) UNIQUE NOT NULL
);


-- 3. Customer Sales Table
-- Each row represents one product sale to a customer.
-- pending_amount is a PostgreSQL generated column — it is always calculated
-- automatically as (gross_sales - received_amount) and cannot be set manually.
CREATE TYPE sale_status AS ENUM ('Open', 'Close');

CREATE TABLE customer_sales (
    sale_id         GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id       INT           REFERENCES branches(branch_id) ON DELETE RESTRICT,
    date            DATE          NOT NULL,
    name            VARCHAR(100)  NOT NULL,
    mobile_number   VARCHAR(15)   UNIQUE NOT NULL,
    product_name    VARCHAR(30)   NOT NULL,
    gross_sales     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    received_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    pending_amount  DECIMAL(12,2) GENERATED ALWAYS AS (gross_sales - received_amount) STORED,
    status          sale_status   NOT NULL DEFAULT 'Open'
);


-- 4. Payment Splits Table
-- Records individual payment instalments against a sale.
-- One sale can have multiple payment records (e.g. partial payments over time).
CREATE TABLE payment_splits (
    payment_id     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sale_id        INT           REFERENCES customer_sales(sale_id) ON DELETE CASCADE,
    payment_date   DATE          NOT NULL,
    amount_paid    DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50)   NOT NULL   -- Cash / UPI / Card
);


-- ====================================================================
-- SECTION 2: TRIGGER FOR AUTOMATIC BALANCE UPDATES
-- ====================================================================

-- This trigger function runs automatically after every INSERT, UPDATE,
-- or DELETE on the payment_splits table.
-- It recalculates the total received_amount for the related sale
-- by summing all payment records for that sale_id.

CREATE OR REPLACE FUNCTION update_received_amount_fn()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_sales
    SET received_amount = COALESCE((
        SELECT SUM(amount_paid)
        FROM payment_splits
        WHERE sale_id = NEW.sale_id
    ), 0.00)
    WHERE sale_id = NEW.sale_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Bind the trigger to the payment_splits table.
-- It fires after any row is inserted, updated, or deleted.
CREATE TRIGGER after_payment_insert
AFTER INSERT OR UPDATE OR DELETE ON payment_splits
FOR EACH ROW
EXECUTE FUNCTION update_received_amount_fn();