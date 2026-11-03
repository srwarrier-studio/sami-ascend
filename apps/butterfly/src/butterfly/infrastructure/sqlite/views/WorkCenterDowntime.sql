CREATE VIEW IF NOT EXISTS work_center_downtime_row AS
SELECT d.downtime_number AS downtime_number,
       d.production_order AS production_order,
       d.plant AS plant,
       d.work_center AS work_center,
       w.name AS work_center_name,
       d.posting_date AS posting_date,
       d.downtime_hours AS downtime_hours,
       d.downtime_cause AS downtime_cause,
       d.company_code AS company_code
FROM work_center_downtime d
LEFT JOIN work_center w ON w.plant = d.plant AND w.code = d.work_center;
