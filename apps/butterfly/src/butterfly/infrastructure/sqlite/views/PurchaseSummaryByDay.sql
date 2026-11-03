CREATE VIEW IF NOT EXISTS purchase_summary_by_day AS
SELECT order_date,
       SUM(net_amount) AS total_net_amount,
       SUM(net_amount_local) AS total_net_amount_local,
       'INR' AS local_currency,
       COUNT(*) AS order_count,
       transaction_currency AS currency,
       company_code
FROM purchase_delivery
WHERE delivery_status != 'X'
GROUP BY order_date, transaction_currency, company_code;
