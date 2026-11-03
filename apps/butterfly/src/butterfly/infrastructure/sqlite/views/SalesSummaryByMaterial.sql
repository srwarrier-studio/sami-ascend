CREATE VIEW IF NOT EXISTS sales_summary_by_material AS
SELECT i.material AS material,
       MIN(i.material_description) AS material_description,
       o.order_date AS order_date,
       SUM(i.quantity) AS total_quantity,
       MIN(i.quantity_unit) AS quantity_unit,
       SUM(i.net_amount) AS total_net_amount,
       SUM(i.net_amount_local) AS total_net_amount_local,
       'INR' AS local_currency,
       o.transaction_currency AS currency,
       o.company_code AS company_code
FROM sales_order_item i
JOIN sales_order o ON o.sales_order = i.sales_order
WHERE o.overall_status != 'X'
GROUP BY o.order_date, i.material, o.transaction_currency, o.company_code;
