CREATE VIEW IF NOT EXISTS downtime_summary_by_day AS
SELECT posting_date,
       downtime_cause,
       SUM(downtime_hours) AS downtime_hours,
       COUNT(*) AS event_count,
       company_code
FROM work_center_downtime
GROUP BY posting_date, downtime_cause, company_code;
