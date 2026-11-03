# Questions for SAP consultants

Everything we cannot settle ourselves and must ask the SAP consultants. Add a question here
as soon as it comes up, under the document or area it belongs to. When answered, move it to
Answered with the answer and the date, and update the document that depended on it.

## Open

### Sales contract (`sales-contract.md`)
1. Service name, root path and namespace: confirm or replace section 1.
2. Is `OverallStatus` the right source, and are `A`, `B`, `C`, `X` the right codes?
3. Can `TotalNetAmount` and `NetAmount` be returned in the order currency, with pricing done on create?
4. Is `ETag` available on the order through RAP (`LastChangeDateTime` as the etag field)?
5. Can summary CDS views be exposed as read-only entities with the keys in section 2?
6. Is `$top` above 1000 rejected, and `$count` supported on all entities?
7. Do the validation detail codes in section 6 map to RAP messages with a stable `code`?
8. Which orders may a read-only management login see (sales organisation, plant)?
9. Which `SalesOrderType` values are valid on create, and which message code does SAP return for an invalid one? The contract has no detail code for it yet.
10. May a caller send fields that SAP fills in (for example `OverallStatus`)? We reject them with `FIELD_NOT_ALLOWED`; confirm RAP can do the same.
11. Do the summary CDS views exclude cancelled orders (`X`)? We assume yes. Can they be read by key, or only with `$filter`?

### Sales parity (`sap-parity-sales.md`)
12. Can RAP expose customers and materials as read-only entities with search by name, for value help on the order form?
13. Is one sales organisation, distribution channel and division per user enough, or must the user choose them on each order? Which values default from the customer?
14. Can RAP offer ship-to party, customer reference and date, pricing on read, cancel (reject) and item change on an open order?

### Company codes and country (`sales-contract.md`, `drivers-contract.md`)
15. The three group companies share one SAP client. The codes are `INA1`, `INA2` and `INA3` (owner); confirm which is Sami-Sabinsa Group, Sami Nutraceuticals and Organica Aromatics (assumed in that order).
16. Which field gives the company of a sales order, a purchase order, a production order and a billing document (for example the company code of the sales document, the plant's company code, the billing company code)? Can every CDS view expose it as `CompanyCode`?
17. Can `Country` come from the customer master (`LAND1`) on the order and the invoice, as an ISO two-letter code?
18. Are sales between the three companies (intercompany) booked as ordinary sales orders, or are they marked so they can be left out of group totals?
19. Are customer invoices read from billing documents (`VBRK`/`VBRP`) and open items from `BSID`/`BSAD`, and which fields hold the due date (`FAEDT` or a baseline date plus terms) and the clearing date?

### Inventory (`inventory-contract.md`)
18. Service name, root path and namespace for stock: confirm or replace section 1 (`ZUI_INVENTORY_O4`).
19. Is "warehouse" in the business a storage location of a plant, or a warehouse number of an extended warehouse management setup? The contract assumes storage locations.
20. Which stock counts as "on hand": unrestricted-use only, or also quality inspection and blocked stock?
21. Can `StockStatus` (and the reorder level it compares with) be derived in the CDS view? Where is the reorder point kept for the group's materials (plant data `MINBE`, or MRP groups)?
22. Which valuation does `StockValue` use (moving average price or standard price), and in which currency is it returned for each plant?
23. Can month-end stock value come from the valuation history (`MBEWH`), and from which month does it exist?
24. Which movement types post receipts and issues in your system, and can reversals be left out with a stable rule? The contract uses `101`, `131`, `261`, `601`, `561` and `702`.
25. Which timezone are the entry date and time of a material document stored in? `EntryDateTime` is UTC in the contract.
26. Can the material group (`MATKL`) and its text be exposed on stock rows without an extra call?


None yet.

### Production (`production-contract.md`)
27. Service name, root path and namespace for production confirmations: confirm or replace section 1 (`ZUI_PRODUCTION_O4`).
28. Does the plant confirm output per shift and work center (one `AFRU` row per shift), or per order and day? The contract assumes per shift.
29. Where is downtime kept: work center downtime in PM (maintenance notifications), a confirmation with a downtime reason, or an MES? What are the cause codes, and can they be mapped to `BREAKDOWN`, `CHANGEOVER`, `NO_MATERIAL`, `MAINTENANCE` and `OTHER`?
30. How are scrap and its reason recorded (scrap quantity and variance reason on the confirmation, or a quality notification)? Which reasons exist?
31. Is the planned output of a shift (`TargetQuantity`) available, or only the order total? We spread the order quantity over its shifts.
32. How are shifts defined (hours of morning, afternoon and night), and is `RunHours` the scheduled hours of the shift?
33. Which standard price values the yield and scrap, and in which currency?
