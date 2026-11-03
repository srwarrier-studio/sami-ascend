CREATE VIEW IF NOT EXISTS production_confirmation_row AS
SELECT c.confirmation_number AS confirmation_number,
       c.confirmation_counter AS confirmation_counter,
       c.production_order AS production_order,
       c.material AS material,
       c.material_description AS material_description,
       c.plant AS plant,
       c.work_center AS work_center,
       w.name AS work_center_name,
       c.shift AS shift,
       c.posting_date AS posting_date,
       c.yield_quantity AS yield_quantity,
       c.scrap_quantity AS scrap_quantity,
       c.target_quantity AS target_quantity,
       c.quantity_unit AS quantity_unit,
       c.scrap_reason AS scrap_reason,
       c.run_hours AS run_hours,
       c.yield_value AS yield_value,
       c.scrap_value AS scrap_value,
       c.target_value AS target_value,
       c.currency AS currency,
       c.company_code AS company_code
FROM production_confirmation c
LEFT JOIN work_center w ON w.plant = c.plant AND w.code = c.work_center;
