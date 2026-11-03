CREATE VIEW IF NOT EXISTS expense_summary_by_day AS
SELECT posting_date,
       expense_category,
       COUNT(*) AS payment_count,
       SUM(amount) AS amount,
       currency,
       company_code
FROM cash_payment
WHERE payment_type = 'E'
GROUP BY posting_date, expense_category, currency, company_code;
