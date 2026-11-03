CREATE VIEW IF NOT EXISTS export_summary_by_destination AS
SELECT shipment_date,
       country,
       MIN(country_name) AS country_name,
       COUNT(*) AS shipment_count,
       SUM(net_amount) AS net_amount,
       currency,
       company_code
FROM export_shipment
GROUP BY shipment_date, country, currency, company_code;
