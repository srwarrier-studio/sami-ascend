CREATE VIEW IF NOT EXISTS sales_summary_by_customer AS
SELECT sold_to_party,
       MIN(customer_name) AS customer_name,
       order_date,
       SUM(total_net_amount) AS total_net_amount,
       SUM(total_net_amount_local) AS total_net_amount_local,
       'INR' AS local_currency,
       COUNT(*) AS order_count,
       transaction_currency AS currency,
       company_code
FROM sales_order
WHERE overall_status != 'X'
GROUP BY order_date, sold_to_party, transaction_currency, company_code;
