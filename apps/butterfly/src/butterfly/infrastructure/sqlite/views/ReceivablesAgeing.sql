WITH p AS (SELECT ? AS as_of),
open_invoice AS (
    SELECT i.*,
           p.as_of AS as_of,
           i.net_amount - CASE WHEN i.clearing_date IS NOT NULL AND i.clearing_date <= p.as_of THEN i.cleared_amount ELSE 0 END AS open_amount,
           i.net_amount_local - CASE WHEN i.clearing_date IS NOT NULL AND i.clearing_date <= p.as_of THEN i.cleared_amount_local ELSE 0 END AS open_amount_local
    FROM customer_invoice i, p
    WHERE i.invoice_date <= p.as_of
)
SELECT MIN(as_of) AS as_of_date,
       CASE
           WHEN julianday(as_of) - julianday(due_date) <= 0 THEN 'current'
           WHEN julianday(as_of) - julianday(due_date) <= 30 THEN '1-30'
           WHEN julianday(as_of) - julianday(due_date) <= 60 THEN '31-60'
           WHEN julianday(as_of) - julianday(due_date) <= 90 THEN '61-90'
           ELSE '90+'
       END AS age_bucket,
       SUM(open_amount) AS open_amount,
       SUM(open_amount_local) AS open_amount_local,
       'INR' AS local_currency,
       COUNT(*) AS open_count,
       transaction_currency AS currency,
       company_code
FROM open_invoice
WHERE open_amount > 0
GROUP BY age_bucket, transaction_currency, company_code
