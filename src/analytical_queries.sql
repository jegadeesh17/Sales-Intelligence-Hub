-- analytical_queries.sql
-- ---------------------------------------------------------
-- Purpose : A collection of SQL queries for exploring and
--           analysing sales data in the Sales Management System.
--
-- Queries are grouped into four categories:
--   1. Basic           — simple SELECT queries
--   2. Aggregation     — SUM, COUNT, GROUP BY
--   3. Join-Based      — multi-table queries using JOINs
--   4. Financial Tracking — filtering and ranking by money
-- ---------------------------------------------------------


-- ====================================================================
-- SECTION 1: BASIC QUERIES
-- ====================================================================

-- 1. Retrieve all records from the customer_sales table
SELECT * FROM customer_sales;

-- 2. Retrieve all records from the branches table
SELECT * FROM branches;

-- 3. Retrieve all records from the payment_splits table
SELECT * FROM payment_splits;

-- 4. Show only sales that are still open (not yet fully paid)
SELECT *
FROM customer_sales
WHERE status = 'Open';


-- ====================================================================
-- SECTION 2: AGGREGATION QUERIES
-- ====================================================================

-- 5. Calculate the total gross sales value across all branches
SELECT SUM(gross_sales) AS total_gross_sales
FROM customer_sales;

-- 6. Calculate the total amount collected across all sales
SELECT SUM(received_amount) AS total_received_amount
FROM customer_sales;

-- 7. Calculate the total outstanding (unpaid) amount across all sales
SELECT SUM(pending_amount) AS total_pending_amount
FROM customer_sales;

-- 8. Count how many sales each branch has recorded
SELECT branch_id, COUNT(sale_id) AS total_sales_count
FROM customer_sales
GROUP BY branch_id;


-- ====================================================================
-- SECTION 3: JOIN-BASED QUERIES
-- ====================================================================

-- 9. Show each sale along with the name of its branch
SELECT s.sale_id, s.name AS customer_name, s.product_name, b.branch_name, s.gross_sales
FROM customer_sales s
JOIN branches b ON s.branch_id = b.branch_id;

-- 10. Show total gross sales per branch, highest first
SELECT b.branch_name, SUM(s.gross_sales) AS branch_total_gross_sales
FROM customer_sales s
JOIN branches b ON s.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY branch_total_gross_sales DESC;

-- 11. Show each sale alongside the payment method used
SELECT DISTINCT s.sale_id, s.name AS customer_name, p.payment_method
FROM customer_sales s
JOIN payment_splits p ON s.sale_id = p.sale_id;

-- 12. Show each sale along with the responsible branch admin's name
SELECT s.sale_id, s.name AS customer_name, b.branch_name, b.branch_admin_name
FROM customer_sales s
JOIN branches b ON s.branch_id = b.branch_id;


-- ====================================================================
-- SECTION 4: FINANCIAL TRACKING QUERIES
-- ====================================================================

-- 13. Find all sales where the outstanding amount is greater than Rs.5000
SELECT sale_id, name, branch_id, pending_amount
FROM customer_sales
WHERE pending_amount > 5000.00
ORDER BY pending_amount DESC;

-- 14. Show the top 3 highest gross sales
SELECT sale_id, name, gross_sales
FROM customer_sales
ORDER BY gross_sales DESC
LIMIT 3;

-- 15. Show total collections broken down by payment method (Cash / UPI / Card)
SELECT payment_method, SUM(amount_paid) AS total_collected
FROM payment_splits
GROUP BY payment_method
ORDER BY total_collected DESC;