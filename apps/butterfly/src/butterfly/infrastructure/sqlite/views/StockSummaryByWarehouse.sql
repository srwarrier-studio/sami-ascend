CREATE VIEW IF NOT EXISTS stock_summary_by_warehouse AS
SELECT plant,
       storage_location,
       MIN(storage_location_name) AS storage_location_name,
       SUM(stock_value) AS stock_value,
       COUNT(*) AS material_count,
       currency,
       company_code
FROM material_stock_row
GROUP BY plant, storage_location, currency, company_code;
