CREATE VIEW IF NOT EXISTS export_summary_by_mode AS
SELECT shipment_date,
       transport_mode,
       COUNT(*) AS shipment_count,
       company_code
FROM export_shipment
GROUP BY shipment_date, transport_mode, company_code;
