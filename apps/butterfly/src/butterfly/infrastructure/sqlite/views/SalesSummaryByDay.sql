CREATE VIEW IF NOT EXISTS sales_summary_by_day AS
SELECT order_date,
       SUM(total_net_amount) AS total_net_amount,
       COUNT(*) AS order_count,
       transaction_currency AS currency,
       company_code
FROM sales_order
WHERE overall_status != 'X'
GROUP BY order_date, transaction_currency, company_code;
