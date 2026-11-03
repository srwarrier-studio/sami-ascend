CREATE VIEW IF NOT EXISTS purchase_summary_by_supplier AS
SELECT supplier,
       MIN(supplier_name) AS supplier_name,
       order_date,
       SUM(net_amount) AS total_net_amount,
       COUNT(*) AS order_count,
       transaction_currency AS currency,
       company_code
FROM purchase_delivery
WHERE delivery_status != 'X'
GROUP BY order_date, supplier, transaction_currency, company_code;
