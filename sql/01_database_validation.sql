-- RetailMart / Neon PostgreSQL validation queries

-- 1. Confirm available schemas
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
ORDER BY schema_name;

-- 2. Confirm table availability by schema
SELECT table_schema, COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
GROUP BY table_schema
ORDER BY table_schema;

-- 3. Confirm key sales volume
SELECT COUNT(*) AS order_count
FROM sales.orders;

-- 4. Confirm basic order-date coverage
SELECT MIN(order_date) AS first_order_date,
       MAX(order_date) AS last_order_date
FROM sales.orders;

-- 5. Check duplicate order identifiers
SELECT order_id, COUNT(*) AS duplicate_count
FROM sales.orders
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
