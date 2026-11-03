CREATE VIEW IF NOT EXISTS purchase_summary_by_material_group AS
SELECT g.code AS material_group,
       g.name AS material_group_name,
       d.order_date AS order_date,
       SUM(d.net_amount) AS total_net_amount,
       SUM(d.net_amount_local) AS total_net_amount_local,
       'INR' AS local_currency,
       COUNT(*) AS order_count,
       d.transaction_currency AS currency,
       d.company_code AS company_code
FROM purchase_delivery d
JOIN material_group_of m ON m.material = d.material
JOIN material_group g ON g.code = m.material_group
WHERE d.delivery_status != 'X'
GROUP BY g.code, d.order_date, d.transaction_currency, d.company_code;
