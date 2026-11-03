CREATE VIEW IF NOT EXISTS production_summary_by_day AS
SELECT c.posting_date AS posting_date,
       SUM(c.run_hours) AS planned_hours,
       COALESCE(MAX(d.hours), 0) AS downtime_hours,
       SUM(c.target_value) AS target_value,
       SUM(c.yield_value) AS good_value,
       SUM(c.scrap_value) AS scrap_value,
       COUNT(*) AS confirmation_count,
       c.currency AS currency,
       c.company_code AS company_code
FROM production_confirmation c
LEFT JOIN (
    SELECT posting_date, company_code, SUM(downtime_hours) AS hours
    FROM work_center_downtime
    GROUP BY posting_date, company_code
) d ON d.posting_date = c.posting_date AND d.company_code = c.company_code
GROUP BY c.posting_date, c.currency, c.company_code;
