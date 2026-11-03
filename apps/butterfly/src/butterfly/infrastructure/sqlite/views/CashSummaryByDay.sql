CREATE VIEW IF NOT EXISTS cash_summary_by_day AS
SELECT posting_date,
       direction,
       COUNT(*) AS payment_count,
       SUM(amount) AS amount,
       currency,
       company_code
FROM cash_payment
GROUP BY posting_date, direction, currency, company_code;
