CREATE VIEW IF NOT EXISTS scrap_summary_by_day AS
SELECT posting_date,
       scrap_reason,
       SUM(scrap_value) AS scrap_value,
       COUNT(*) AS confirmation_count,
       currency,
       company_code
FROM production_confirmation
WHERE scrap_reason IS NOT NULL
GROUP BY posting_date, scrap_reason, currency, company_code;
