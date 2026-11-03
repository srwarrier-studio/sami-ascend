CREATE VIEW IF NOT EXISTS stock_movement_summary_by_hour AS
SELECT posting_date,
       CAST(substr(entry_date_time, 12, 2) AS INTEGER) AS posting_hour,
       COUNT(*) AS movement_count,
       company_code
FROM stock_movement
WHERE movement_type IN ('101', '131', '261', '601')
GROUP BY posting_date, posting_hour, company_code;
