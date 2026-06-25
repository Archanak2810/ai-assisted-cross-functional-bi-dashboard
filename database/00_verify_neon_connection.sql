-- Run this in the Neon SQL Editor.
SELECT current_database() AS database, current_user AS db_user, CURRENT_TIMESTAMP AS server_time;

SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND table_schema IN ('sales','products','core','stores','marketing','finance','hr','payroll','supply_chain','manufacture','audit','customers','loyalty','support','call_center')
ORDER BY table_schema, table_name;

SELECT COUNT(*) AS orders_in_neon FROM sales.orders;
