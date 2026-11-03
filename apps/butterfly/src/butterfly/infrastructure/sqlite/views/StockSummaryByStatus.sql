CREATE VIEW IF NOT EXISTS stock_summary_by_status AS
SELECT stock_status,
       SUM(stock_value) AS stock_value,
       COUNT(*) AS material_count,
       currency,
       company_code
FROM material_stock_row
GROUP BY stock_status, currency, company_code;
