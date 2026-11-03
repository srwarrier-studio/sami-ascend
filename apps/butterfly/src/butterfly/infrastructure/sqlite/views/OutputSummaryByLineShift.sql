CREATE VIEW IF NOT EXISTS output_summary_by_line_shift AS
SELECT c.posting_date AS posting_date,
       c.work_center AS work_center,
       c.shift AS shift,
       MIN(w.name) AS work_center_name,
       SUM(c.yield_value) AS good_value,
       c.currency AS currency,
       c.company_code AS company_code
FROM production_confirmation c
LEFT JOIN work_center w ON w.plant = c.plant AND w.code = c.work_center
GROUP BY c.posting_date, c.work_center, c.shift, c.currency, c.company_code;
