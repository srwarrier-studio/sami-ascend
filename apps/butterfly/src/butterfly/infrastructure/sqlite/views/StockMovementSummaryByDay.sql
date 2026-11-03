CREATE VIEW IF NOT EXISTS stock_movement_summary_by_day AS
SELECT posting_date,
       SUM(CASE WHEN debit_credit_code = 'S' THEN amount ELSE 0 END) AS receipt_value,
       SUM(CASE WHEN debit_credit_code = 'H' THEN amount ELSE 0 END) AS issue_value,
       COUNT(*) AS movement_count,
       currency,
       company_code
FROM stock_movement
WHERE movement_type IN ('101', '131', '261', '601')
GROUP BY posting_date, currency, company_code;
