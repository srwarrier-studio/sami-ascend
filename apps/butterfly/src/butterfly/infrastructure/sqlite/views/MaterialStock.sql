CREATE VIEW IF NOT EXISTS material_stock_row AS
SELECT s.material AS material,
       s.material_description AS material_description,
       s.material_group AS material_group,
       g.name AS material_group_name,
       s.plant AS plant,
       s.storage_location AS storage_location,
       l.name AS storage_location_name,
       s.stock_quantity AS stock_quantity,
       s.quantity_unit AS quantity_unit,
       s.stock_value AS stock_value,
       s.currency AS currency,
       s.reorder_level AS reorder_level,
       CASE WHEN s.stock_quantity = 0 THEN 'Z' WHEN s.stock_quantity < s.reorder_level THEN 'L' ELSE 'O' END AS stock_status,
       s.last_movement_date AS last_movement_date,
       s.company_code AS company_code
FROM material_stock s
LEFT JOIN material_group g ON g.code = s.material_group
LEFT JOIN storage_location l ON l.plant = s.plant AND l.code = s.storage_location;
