CREATE VIEW IF NOT EXISTS stock_summary_by_material_group AS
SELECT material_group,
       MIN(material_group_name) AS material_group_name,
       SUM(stock_value) AS stock_value,
       COUNT(*) AS material_count,
       currency,
       company_code
FROM material_stock_row
GROUP BY material_group, currency, company_code;
