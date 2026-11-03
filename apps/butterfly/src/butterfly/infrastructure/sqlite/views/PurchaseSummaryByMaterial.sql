CREATE VIEW IF NOT EXISTS purchase_summary_by_material AS
SELECT material,
       MIN(material_description) AS material_description,
       order_date,
       SUM(ordered_quantity) AS total_quantity,
       MIN(quantity_unit) AS quantity_unit,
       SUM(net_amount) AS total_net_amount,
       transaction_currency AS currency,
       company_code
FROM purchase_delivery
WHERE delivery_status != 'X'
GROUP BY order_date, material, transaction_currency, company_code;
