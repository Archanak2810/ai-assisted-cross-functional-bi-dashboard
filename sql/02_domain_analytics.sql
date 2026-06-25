/*
RetailMart Domain-Wise & Cross-Functional BI Dashboard
Representative PostgreSQL analytical queries.
These queries can be executed in Neon SQL Editor or pgAdmin.
*/

-- 1. Monthly sales revenue, estimated product cost, profit and margin
WITH sales_fact AS (
    SELECT
        o.order_id,
        o.order_date::date AS order_date,
        oi.net_amount,
        oi.quantity,
        p.cost_price,
        oi.net_amount - (oi.quantity * p.cost_price) AS profit
    FROM sales.orders o
    JOIN sales.order_items oi ON oi.order_id = o.order_id
    JOIN products.products p ON p.product_id = oi.prod_id
    WHERE o.order_status IN ('Delivered', 'Shipped', 'Out for Delivery', 'Processing')
)
SELECT
    date_trunc('month', order_date)::date AS month,
    SUM(net_amount) AS revenue,
    SUM(quantity * cost_price) AS estimated_cost,
    SUM(profit) AS profit,
    ROUND(100.0 * SUM(profit) / NULLIF(SUM(net_amount), 0), 2) AS profit_margin_pct
FROM sales_fact
GROUP BY 1
ORDER BY 1;

-- 2. Top products by revenue and profit
WITH sales_fact AS (
    SELECT oi.prod_id, oi.net_amount, oi.quantity, p.product_name, p.cost_price
    FROM sales.orders o
    JOIN sales.order_items oi ON oi.order_id = o.order_id
    JOIN products.products p ON p.product_id = oi.prod_id
    WHERE o.order_status IN ('Delivered', 'Shipped', 'Out for Delivery', 'Processing')
)
SELECT
    product_name,
    SUM(net_amount) AS revenue,
    SUM(net_amount - quantity * cost_price) AS profit,
    ROUND(100.0 * SUM(net_amount - quantity * cost_price) / NULLIF(SUM(net_amount), 0), 2) AS margin_pct
FROM sales_fact
GROUP BY product_name
ORDER BY revenue DESC
LIMIT 20;

-- 3. Regional revenue, profit and orders
WITH sales_fact AS (
    SELECT o.order_id, oi.net_amount, oi.quantity, p.cost_price, r.region_name, r.state
    FROM sales.orders o
    JOIN sales.order_items oi ON oi.order_id = o.order_id
    JOIN products.products p ON p.product_id = oi.prod_id
    JOIN stores.stores s ON s.store_id = o.store_id
    JOIN core.dim_region r ON r.region_id = s.region_id
    WHERE o.order_status IN ('Delivered', 'Shipped', 'Out for Delivery', 'Processing')
)
SELECT
    region_name,
    state,
    COUNT(DISTINCT order_id) AS orders,
    SUM(net_amount) AS revenue,
    SUM(net_amount - quantity * cost_price) AS profit
FROM sales_fact
GROUP BY region_name, state
ORDER BY revenue DESC;

-- 4. RFM customer base table
WITH customer_value AS (
    SELECT
        o.cust_id,
        MAX(o.order_date) AS last_order_date,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.net_amount) AS monetary
    FROM sales.orders o
    JOIN sales.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Delivered', 'Shipped', 'Out for Delivery', 'Processing')
    GROUP BY o.cust_id
)
SELECT
    cust_id,
    (MAX(last_order_date) OVER () - last_order_date) AS recency_days,
    frequency,
    monetary
FROM customer_value
ORDER BY monetary DESC;

-- 5. Marketing campaign pacing to budget
SELECT
    c.campaign_name,
    c.budget,
    COALESCE(SUM(a.amount), 0) AS actual_spend,
    ROUND(100.0 * COALESCE(SUM(a.amount), 0) / NULLIF(c.budget, 0), 2) AS spend_to_budget_pct
FROM marketing.campaigns c
LEFT JOIN marketing.ads_spend a ON a.campaign_id = c.campaign_id
GROUP BY c.campaign_name, c.budget
ORDER BY actual_spend DESC;

-- 6. Email open, click and click-to-open rates
SELECT
    c.campaign_name,
    SUM(e.emails_sent) AS emails_sent,
    SUM(e.emails_opened) AS emails_opened,
    SUM(e.emails_clicked) AS emails_clicked,
    ROUND(100.0 * SUM(e.emails_opened) / NULLIF(SUM(e.emails_sent), 0), 2) AS open_rate_pct,
    ROUND(100.0 * SUM(e.emails_clicked) / NULLIF(SUM(e.emails_sent), 0), 2) AS ctr_pct,
    ROUND(100.0 * SUM(e.emails_clicked) / NULLIF(SUM(e.emails_opened), 0), 2) AS ctor_pct
FROM marketing.email_clicks e
JOIN marketing.campaigns c ON c.campaign_id = e.campaign_id
GROUP BY c.campaign_name
ORDER BY ctr_pct DESC;

-- 7. Finance expense categories
SELECT
    d.category_name,
    SUM(f.amount) AS total_expense
FROM finance.expenses f
LEFT JOIN core.dim_expense_category d ON d.exp_cat_id = f.exp_cat_id
GROUP BY d.category_name
ORDER BY total_expense DESC;

-- 8. Refund value by reason
SELECT
    reason,
    COUNT(*) AS refund_count,
    SUM(amount) AS refund_value
FROM audit.refund_log
GROUP BY reason
ORDER BY refund_value DESC;

-- 9. Payroll cost by department
SELECT
    d.dept_name,
    COUNT(DISTINCT e.employee_id) AS headcount,
    AVG(e.salary) AS average_salary,
    SUM(p.gross_salary) AS gross_payroll,
    SUM(p.net_salary) AS net_payroll
FROM stores.employees e
LEFT JOIN core.dim_department d ON d.dept_id = e.dept_id
LEFT JOIN payroll.pay_slips p ON p.employee_id = e.employee_id
GROUP BY d.dept_name
ORDER BY gross_payroll DESC NULLS LAST;

-- 10. Average recorded attendance hours by department
SELECT
    d.dept_name,
    COUNT(DISTINCT a.attendance_id) AS attendance_records,
    ROUND(AVG(EXTRACT(EPOCH FROM (a.check_out - a.check_in)) / 3600.0), 2) AS average_worked_hours,
    ROUND(100.0 * AVG(CASE WHEN a.check_out IS NULL THEN 1 ELSE 0 END), 2) AS missing_checkout_rate_pct
FROM hr.attendance a
JOIN stores.employees e ON e.employee_id = a.employee_id
LEFT JOIN core.dim_department d ON d.dept_id = e.dept_id
GROUP BY d.dept_name
ORDER BY average_worked_hours DESC;

-- 11. Inventory below reorder level
SELECT
    c.category_name,
    p.product_name,
    i.store_id,
    i.quantity_on_hand,
    i.reorder_level,
    (i.quantity_on_hand < i.reorder_level) AS below_reorder,
    i.quantity_on_hand * p.cost_price AS inventory_value
FROM products.inventory i
JOIN products.products p ON p.product_id = i.product_id
JOIN core.dim_brand b ON b.brand_id = p.brand_id
JOIN core.dim_category c ON c.category_id = b.category_id
ORDER BY below_reorder DESC, inventory_value DESC;

-- 12. Inbound supplier lead time
SELECT
    s.supplier_name,
    COUNT(*) AS shipment_count,
    ROUND(AVG(sc.arrival_date - sc.shipped_date), 2) AS avg_inbound_lead_days,
    SUM(sc.quantity) AS inbound_units
FROM supply_chain.shipments sc
JOIN products.suppliers s ON s.supplier_id = sc.supplier_id
GROUP BY s.supplier_name
ORDER BY avg_inbound_lead_days;

-- 13. Courier delivery performance
SELECT
    courier_name,
    status,
    COUNT(*) AS shipments,
    ROUND(AVG(delivered_date - shipped_date), 2) AS avg_delivery_days
FROM sales.shipments
GROUP BY courier_name, status
ORDER BY shipments DESC;

-- 14. Production yield and rejection rate by line
SELECT
    pl.line_name,
    SUM(wo.quantity_produced) AS units_produced,
    SUM(wo.rejected_quantity) AS units_rejected,
    ROUND(100.0 * SUM(wo.quantity_produced - wo.rejected_quantity) / NULLIF(SUM(wo.quantity_produced), 0), 2) AS yield_pct,
    ROUND(100.0 * SUM(wo.rejected_quantity) / NULLIF(SUM(wo.quantity_produced), 0), 2) AS rejection_rate_pct
FROM manufacture.work_orders wo
JOIN manufacture.production_lines pl ON pl.line_id = wo.line_id
GROUP BY pl.line_name
ORDER BY rejection_rate_pct DESC;

-- 15. Cross-functional marketing spend versus revenue and profit
WITH revenue_profit AS (
    SELECT
        date_trunc('month', o.order_date)::date AS month,
        SUM(oi.net_amount) AS revenue,
        SUM(oi.net_amount - oi.quantity * p.cost_price) AS profit
    FROM sales.orders o
    JOIN sales.order_items oi ON oi.order_id = o.order_id
    JOIN products.products p ON p.product_id = oi.prod_id
    WHERE o.order_status IN ('Delivered', 'Shipped', 'Out for Delivery', 'Processing')
    GROUP BY 1
), spend AS (
    SELECT date_trunc('month', spend_date)::date AS month, SUM(amount) AS marketing_spend
    FROM marketing.ads_spend
    GROUP BY 1
)
SELECT
    COALESCE(r.month, s.month) AS month,
    COALESCE(s.marketing_spend, 0) AS marketing_spend,
    COALESCE(r.revenue, 0) AS revenue,
    COALESCE(r.profit, 0) AS profit
FROM revenue_profit r
FULL OUTER JOIN spend s ON s.month = r.month
ORDER BY month;

-- 16. Cross-functional inventory capital and category margin
WITH category_sales AS (
    SELECT
        c.category_name,
        SUM(oi.net_amount) AS revenue,
        SUM(oi.net_amount - oi.quantity * p.cost_price) AS profit
    FROM sales.orders o
    JOIN sales.order_items oi ON oi.order_id = o.order_id
    JOIN products.products p ON p.product_id = oi.prod_id
    JOIN core.dim_brand b ON b.brand_id = p.brand_id
    JOIN core.dim_category c ON c.category_id = b.category_id
    WHERE o.order_status IN ('Delivered', 'Shipped', 'Out for Delivery', 'Processing')
    GROUP BY c.category_name
), category_inventory AS (
    SELECT
        c.category_name,
        SUM(i.quantity_on_hand * p.cost_price) AS inventory_working_capital
    FROM products.inventory i
    JOIN products.products p ON p.product_id = i.product_id
    JOIN core.dim_brand b ON b.brand_id = p.brand_id
    JOIN core.dim_category c ON c.category_id = b.category_id
    GROUP BY c.category_name
)
SELECT
    s.category_name,
    s.revenue,
    s.profit,
    ROUND(100.0 * s.profit / NULLIF(s.revenue, 0), 2) AS margin_pct,
    i.inventory_working_capital
FROM category_sales s
LEFT JOIN category_inventory i ON i.category_name = s.category_name
ORDER BY i.inventory_working_capital DESC NULLS LAST;
