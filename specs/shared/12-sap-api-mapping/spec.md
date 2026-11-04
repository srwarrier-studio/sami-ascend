# shared/12 sap-api-mapping

## Goal
Decide, entity by entity, which of the data the apps read can come from SAP's own released APIs (the SAP Business Accelerator Hub, https://api.sap.com) and which still needs a custom service, so butterfly can mirror the real contract and the document for the SAP consultants shrinks to the custom parts.

## Why
The SAP consultants have not started, so nothing on the SAP side depends on the contracts we invented in `docs/sap/`. If the standard APIs cover a read, using them means the real system answers the same URLs, fields and format as butterfly, SAP people already know them, and nobody builds that part in RAP. This phase is the study that makes the later butterfly and synapse-api changes safe; it changes no code.

## Behavior
- A new document `docs/sap/standard-api-mapping.md` with one row for every entity in `docs/sap/*-contract.md` (sales, drivers, inventory, production, export, finance): `SalesOrder`, `SalesOrderItem`, `SalesContract`, `PurchaseDelivery`, `CustomerInvoice`, `ProductionOrder`, `ProductionOrderComponent`, `MaterialStock`, `StockMovement`, `ProductionConfirmation`, `WorkCenterDowntime`, `ExportShipment`, `CashPayment`, and every summary and receivables view.
- Each row names: the closest released API (service name, version, OData V2 or V4, entity set), the field-by-field match for the fields the apps read (including company code, currency and the company-currency amount, dates and statuses), what is missing or different, and a decision: `standard` (read it directly), `standard + aggregate` (read rows, sum in synapse-api or a custom view), or `custom` (needs a Z service, with the reason).
- The edition is stated: which APIs belong to SAP S/4HANA Cloud Private Edition (the target) and which only to the public cloud edition, and what must be enabled in SAP for each (communication scenarios or services to activate), so the consultants can plan.
- A section on the protocol differences butterfly and the readers would have to handle: OData V2 against V4 (response wrapper, count, paging links, date and number formats, `$filter` functions, `$expand`), error format, authentication, CSRF for writes.
- A section on aggregation: where the summaries (`SalesSummaryByDay` and the others) should live, with the cost and risk of each option (read rows and sum in synapse-api, custom CDS views, analytical APIs), and a recommendation.
- A short list of the custom parts left for the consultants, replacing the current full contracts, and an updated `consultant-questions.md`.
- A proposed order of follow-up phases (butterfly standard-API mode per area, synapse-api adapters) with the size of each, for the owner to agree. No code, tests or seed data change in this phase.
- Sources are the public Hub documentation and sample responses only; no company data is used or sent anywhere.

## Acceptance cases
- Every entity named in the six contracts has a row and a decision; none is left blank.
- For each `standard` row the fields the apps read are all matched, or the gap is stated with how it is closed.
- Each row cites the API by name and version, so the owner can open it in the Hub.
- The aggregation section ends in one recommendation with its risks.
- The consultant list names only entities marked `custom`, with the fields and the reason.
- The owner has agreed the follow-up order before any code phase starts.

## Out of scope
Changing butterfly, synapse-api or the web apps, the OData V2 reader, authentication to a real SAP system, anything about the data of a real company.

## Depends on
shared 01 (the contracts being replaced).
