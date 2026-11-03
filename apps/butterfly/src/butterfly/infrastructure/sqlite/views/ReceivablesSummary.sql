WITH p AS (SELECT ? AS as_of),
open_invoice AS (
    SELECT i.*,
           p.as_of AS as_of,
           i.net_amount - CASE WHEN i.clearing_date IS NOT NULL AND i.clearing_date <= p.as_of THEN i.cleared_amount ELSE 0 END AS open_amount
    FROM customer_invoice i, p
    WHERE i.invoice_date <= p.as_of
)
SELECT MIN(as_of) AS as_of_date,
       SUM(open_amount) AS open_amount,
       SUM(CASE WHEN due_date < as_of THEN open_amount ELSE 0 END) AS overdue_amount,
       COUNT(*) AS open_count,
       SUM(CASE WHEN due_date < as_of THEN 1 ELSE 0 END) AS overdue_count,
       transaction_currency AS currency,
       company_code
FROM open_invoice
WHERE open_amount > 0
GROUP BY transaction_currency, company_code
