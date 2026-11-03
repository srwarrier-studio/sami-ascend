CREATE VIEW IF NOT EXISTS export_summary_by_day AS
SELECT shipment_date,
       COUNT(*) AS shipment_count,
       SUM(net_amount) AS net_amount,
       currency,
       company_code
FROM export_shipment
GROUP BY shipment_date, currency, company_code;
