# Standard SAP APIs against our contracts

Status: work in progress (shared phase 12). Sales and drivers entities are studied; inventory,
production, export and finance are listed as candidates only.

## Target release

The owner's private cloud runs **S/4HANA 2022** (stated 2026-11-04), and the owner reports that
OData V4 is supported on it. What is established:

- OData V4 as a platform feature on-premise has existed since S/4HANA 2020 FPS01, and ABAP
  Platform 2022 widened the set of released RAP business objects (for example `I_SALESORDERTP`,
  the released successor for the sales order BAPIs). Sources are community posts, not SAP's release
  notes; the owner's link (community.sap.com blog "ABAP Platform for SAP S/4HANA 2022") could not be
  opened by the tooling.
- The owner pasted this line from that blog: the ABAP Platform 2022 offers "the capability for the quick
  activation and consumption of services (SOAP, OData V2, OData V4)". So activating V4 services is
  an easy, supported step on 2022.
- **Not established:** whether the standard Sales Order **V4 service** (`API_SALESORDER`) is delivered
  and published on 2022. SAP Note 3492351 says it can be published on 2023 and has no documentation
  there. The consultants can settle it by searching for `API_SALESORDER` in the V4 service
  administration (`/IWFND/V4_ADMIN`) on the real system.

So the plan covers both: butterfly serves the order in V4 first and V2 as the fallback (we hold the
real specification for each, in `docs/sap/standard/`), and a configuration switch in synapse-api
picks the one to read. The version rule below resolves per API and per release.

## How to read this

- **Source of the field lists.** The released services below were read through the type
  definitions that SAP's Cloud SDK generates from each service's metadata
  (`@sap/cloud-sdk-vdm-*` packages), because the SAP Business Accelerator Hub itself needs a
  browser. They are public and reliable for names and types, but they can lag the newest Hub
  version. The `$metadata` of the real private-cloud system is the final authority, so every
  `standard` decision below is to be confirmed against it before code is written.
- **Verified** means the fields were read from those type definitions. **Candidate** means the
  API exists as far as we know but its fields were not read yet.
- **Decisions.** `standard` (read the entity directly), `standard + join` (needs two or more
  standard reads combined), `standard + aggregate` (read rows, sum them ourselves), `custom`
  (needs a Z service).
- **Version rule (owner decision, 2026-11-04): prefer OData V4.** Use the V4 version of an API
  when it exists with the fields we need, and V2 only when there is none. The service names in
  the tables are the ones whose fields were read; they are V2 unless stated (for example
  `API_SALES_ORDER_SRV`), and a V4 variant of each is to be looked up on the Hub and recorded here.
  Production orders already show both (`API_PRODUCTION_ORDER_2_SRV` V2, `API_PRODUCTIONORDER` V4).
  On a private edition V2 services are activated in `/IWFND/MAINT_SERVICE` and V4 services in
  `/IWFND/V4_ADMIN`.

## 1. Sales

Two real services were read on the Hub sandbox (sample data, no key saved):

- **V2, `API_SALES_ORDER_SRV`: the one to plan on for S/4HANA 2022.** Files in
  `docs/sap/standard/api_sales_order_srv-v2/`.
- **V4, `API_SALESORDER` (`srvd_a2x`, `0001`): what a newer release offers.** Files in
  `docs/sap/standard/api_salesorder-v4/`. Kept as the upgrade path; SAP Note 3492351 mentions it
  only for 2023 and later.

The sandbox is the newest public cloud, so field lists can be slightly newer than a 2022 system;
the consultants confirm on the real `$metadata`.

| Ours | V2 (2022) | V4 (later releases) | Decision for 2022 |
|---|---|---|---|
| `SalesOrder` | `A_SalesOrder`, 84 properties, key `SalesOrder` | `SalesOrder`, 90 properties | standard + join |
| `SalesOrderItem` | `A_SalesOrderItem`, 98 properties, keys `SalesOrder`, `SalesOrderItem` | `SalesOrderItem`, 95 properties | standard |
| `SalesSummaryByDay`, `...ByCustomer`, `...ByMaterial` | none; `$apply` is refused (400 `Invalid system query option specified`) | `$apply` works (section 5) | **standard + aggregate** in synapse-api, or custom views |

### V2 (target release): what the real service does

- Wrapper: `{"d": {"results": [...]}}`; each row has `__metadata` (`id`, `uri`, `type`, `etag`) and a
  deferred link for every navigation property (`to_Item`, `to_Partner`, `to_Text`, ...).
- Dates are `"/Date(1471392000000)/"`; `LastChangeDateTime` is `"/Date(1472796947125+0000)/"`;
  amounts are **strings** (`"TotalNetAmount": "52.65"`).
- Count: `$inlinecount=allpages` gives `d.__count` as a string; `/A_SalesOrder/$count` returns plain
  text. Filters, `$orderby`, `$select`, `$top` and `$expand=to_Item` work.
- Errors: `{"error": {"code", "message": {"lang", "value"}, "innererror": {...}}}`.
- Entity sets are prefixed `A_` (`A_SalesOrder`, `A_SalesOrderItem`, `A_SalesOrderHeaderPartner`, ...).
- **No company code on the header.** There is `SalesOrganization` (`"1710"` in the sample), but no
  `BillingCompanyCode` or `CompanyCode`. For 2022 the company code must come from a mapping of sales
  organization to company code (kept in synapse-api configuration, confirmed by the consultants), or
  from the billing document.
- Item fields: `Material`, `SalesOrderItemText`, `RequestedQuantity`, `RequestedQuantityUnit`,
  `NetAmount`, `TransactionCurrency`, `ProductionPlant`.

The tables below were first filled from the V4 service. The V2 names that differ are listed in the
V2 notes above; the V4 tables stay as the reference for later releases.

### SalesOrder fields (V4, later releases)

| Our field | Standard field | Match |
|---|---|---|
| `SalesOrder`, `SalesOrderType`, `SoldToParty`, `RequestedDeliveryDate`, `TransactionCurrency`, `TotalNetAmount`, `CreatedByUser`, `LastChangeDateTime` | same names | same (`TotalNetAmount` is a JSON number, dates are ISO) |
| `OrderDate` | `SalesOrderDate` (Date) | renamed |
| `OverallStatus` | `OverallSDProcessStatus` | one-letter code (`C` = completed), map to our words |
| `CreationDateTime` | `CreationDate` (Date) and `CreationTime` (TimeOfDay) | two fields |
| `CompanyCode` | **`BillingCompanyCode`** | present on the header (`"1710"` in the sample); this corrects the V2 reading, where it was missing |
| `CustomerName` | not on the order | join to the customer or business partner API |
| `Country` | not on the order | from the customer address |
| `TotalNetAmountLocal`, `LocalCurrency` | not on the order | gap: the company code currency amount is not served; needs the accounting document or a rate we hold |

### SalesOrderItem fields (V4, later releases)

| Our field | Standard field |
|---|---|
| `Material` | `Product` |
| `MaterialDescription` | `SalesOrderItemText` (short item text, not the product description) |
| `Quantity`, `QuantityUnit` | `RequestedQuantity`, `RequestedQuantitySAPUnit` and `RequestedQuantityISOUnit` |
| `NetAmount` | `NetAmount` |

Third-party connector pages listed other names (`ItemNetAmount`, `RequestedQuantityUnit`); the
real `$metadata` does not have them. Always trust the `$metadata`, not summaries.

### Billing document (candidate for invoiced revenue)

`API_BILLING_DOCUMENT_SRV` (V2 read so far; look up its V4 version) has `BillingDocumentDate`,
`CompanyCode`, `SoldToParty`, `TotalNetAmount`, `TransactionCurrency`, `AccountingDocument`,
`BillingDocumentIsCancelled`. Today our "sales" figures are order based (`OrderDate`). Moving to
billing documents would turn them into **invoiced** revenue, a business decision for the owner and
finance. With `BillingCompanyCode` now on the order, orders no longer need billing documents for
the company filter.

## 2. Drivers

| Ours | Closest standard | Decision | Status |
|---|---|---|---|
| `SalesContract` | `API_SALES_CONTRACT_SRV`, `A_SalesContract` | standard + join | Verified |
| `PurchaseDelivery` | `API_PURCHASEORDER_PROCESS_SRV` (`A_PurchaseOrder`, `A_PurchaseOrderItem`, `A_PurchaseOrderScheduleLine`) with `API_MATERIAL_DOCUMENT_SRV` (goods receipts) | standard + join | Verified |
| `CustomerInvoice` | `API_BILLING_DOCUMENT_SRV` with customer line items from the accounting APIs | standard + join | Billing document verified, accounting part candidate |
| `ProductionOrder`, `ProductionOrderComponent` | `API_PRODUCTION_ORDER_2_SRV` (V2) or `API_PRODUCTIONORDER` (V4) | standard, delay reason likely custom | Candidate |
| Purchase and receivables summaries | none | standard + aggregate | Verified: none exist |

### SalesContract

| Our field | Standard field (`A_SalesContract`) | Match |
|---|---|---|
| `SalesContract` | `SalesContract` | same |
| `SoldToParty` | `SoldToParty` | same |
| `ValidFrom`, `ValidTo` | `SalesContractValidityStartDate`, `SalesContractValidityEndDate` | renamed |
| `ContractValue` | `TotalNetAmount` | renamed |
| `TransactionCurrency` | `TransactionCurrency` | same |
| `ContractStatus` | `OverallSDProcessStatus`, `OverallSDDocumentRejectionSts` | map codes to our words |
| `PredecessorContract` | `ReferenceSDDocument` | likely, confirm the meaning |
| `CustomerName` | not on the contract | join to the customer API |
| `CompanyCode` | not on the contract (`SalesOrganization` only) | gap, as for orders |

The authorization scenario named in SAP's Cloud SDK documentation for this service is
`SAP_COM_0119` (Sales Contract Integration).

### PurchaseDelivery

Our entity is one row per purchase order item with a promised date, an actual date, the
delivered quantity and a status. In the standard model these are four different things:

| Our field | Standard source |
|---|---|
| `PurchaseOrder`, `PurchaseOrderItem` | `A_PurchaseOrderItem` keys |
| `Supplier` | `A_PurchaseOrder.Supplier` (name: supplier API) |
| `Material` | `A_PurchaseOrderItem.Material` (description: product API) |
| `OrderDate` | `A_PurchaseOrder.PurchaseOrderDate` |
| `OrderedQuantity`, `QuantityUnit` | `A_PurchaseOrderItem.OrderQuantity`, `PurchaseOrderQuantityUnit` |
| `NetAmount` | **no total on the item**: `NetPriceAmount` x `OrderQuantity` / `NetPriceQuantity` |
| `TransactionCurrency` | `A_PurchaseOrder.DocumentCurrency` |
| `CompanyCode` | `A_PurchaseOrder.CompanyCode` (present, unlike sales) |
| `PromisedDeliveryDate` | `A_PurchaseOrderScheduleLine.ScheduleLineDeliveryDate` |
| `ActualDeliveryDate`, `DeliveredQuantity` | goods receipts: `A_MaterialDocumentItem` with `PurchaseOrder`, `PurchaseOrderItem`, `GoodsMovementType` 101, header `PostingDate`, `QuantityInBaseUnit` |
| `DeliveryStatus` | derived from the two above, or `IsCompletelyDelivered` on the item |
| `NetAmountLocal`, `LocalCurrency` | the goods receipt item has `GdsMvtExtAmtInCoCodeCrcy` and `CompanyCodeCurrency`; open items have no local amount yet |

This needs a join across three reads, or a custom view in SAP. It is the clearest case for
deciding where joins live (section 5).

### CustomerInvoice (receivables)

The billing document gives the invoice, date, amount, company code and customer. The **due date,
cleared amount and clearing date** live in the accounting documents (customer open and cleared
items), not in the billing document. Candidate: the operational accounting document item and
journal entry APIs (`API_OPLACCTGDOCITEMCUBE_SRV`, `API_JOURNALENTRYITEMBASIC_SRV`). Not verified.

### ProductionOrder and components

Candidate: `API_PRODUCTION_ORDER_2_SRV` (`A_ProductionOrder_2`, components, operations), or the V4
`API_PRODUCTIONORDER`. SAP notes that `LastChangeDateTime` is a string in the V2 service and that
the two versions differ in system and user status handling. Our `DelayReason` (for example
`MATERIAL_SHORTAGE`, `MACHINE_BREAKDOWN`) has no obvious standard field; it is probably a custom
field, or derived from the confirmation variance reason. Not verified, to be read next.

## 3. Still to study (candidates, not verified)

| Ours | Candidate standard API |
|---|---|
| `MaterialStock` | `API_MATERIAL_STOCK_SRV` |
| `StockMovement` | `API_MATERIAL_DOCUMENT_SRV`: verified fields exist for material, plant, storage location, movement type, quantity, posting date, amount in company currency; company code is not on the item |
| `ProductionConfirmation` | `API_PROD_ORDER_CONFIRMATION_2_SRV` |
| `WorkCenterDowntime` | none known; probably custom |
| `ExportShipment` | outbound delivery and foreign trade APIs; probably partly custom |
| `CashPayment`, expenses | accounting document or bank APIs |

## 4. Protocol differences butterfly and our readers must handle

Only for an API that has no V4 version. OData V2 against our V4 (checked against the type definitions and SAP notes; format details to be
confirmed on the real system):

- Response wrapper: V2 wraps rows in `d.results`; our readers expect `value`.
- Counts and paging: V2 uses `$inlinecount` and `__next`; V4 uses `$count` and `@odata.nextLink`.
- Dates arrive as `/Date(...)/` strings in V2 (our contracts use ISO dates); decimals can arrive as
  strings.
- Many services keep the `A_` prefix on entity sets (`A_SalesOrder`), navigation properties start
  with `to_` (`to_Item`), and `$expand` is how you get items.
- Writes need a CSRF token fetch first.
- Behavior seen in SAP notes: some navigation properties are missing from `$metadata`; filter
  behavior differs by entity and needs testing per system.

## 5. Aggregation

Tested on the V4 sandbox (2026-11-04). The standard service **does** support `$apply`:

- `groupby((SoldToParty,BillingCompanyCode,TransactionCurrency),aggregate(TotalNetAmount with sum as Total))` works, also after a `filter(...)` step (`$apply=filter(...)/groupby(...)`), and on `SalesOrderItem` by `Product`.
- **Not supported:** `$orderby` on an aggregated alias (400), and `countdistinct` (501 `$apply option not supported`). So "top customers" needs all groups read and sorted by synapse-api, and order counts need a separate `$count=true` call with the same filter.
- `$count=true` works with `$filter` (the sandbox reports 455,439 matching orders).
- Quirk: filtering on `TotalNetAmount` requires the currency in the same filter
  (`and TransactionCurrency eq 'USD'`), otherwise 400.

Decision for sales on a release with V4: **standard + `$apply`**, no custom view, for the by-day, by-customer and
by-material figures. Orders per group and top-N are finished in synapse-api. This is confirmed
only for the V4 sales order service on the sandbox. **On V2 (the 2022 target) `$apply` is refused**,
so for 2022 the decision is standard + aggregate: read the filtered rows (paged, with
`$select` to keep them small) and sum in synapse-api with the existing cache, or ask the
consultants for a few custom summary views if the volume is too high. Each other API still needs
the same test.

## 6. What the consultants would still build (draft)

Not final. Candidates for custom services: the summary views if option 2 is chosen, the production
delay reason, work center downtime, and anything marked `custom` after the remaining entities are
studied. The current full contracts in `docs/sap/` stay as they are until the owner agrees this
list.

## 7. What the consultants would need to enable first (draft)

Nothing is enabled on the private cloud system yet (confirmed by the owner, 2026-11-04). Enabling
released standard services is a configuration task for the consultants, not a build, so it is
smaller than writing custom services. The usual steps on a private edition, to be confirmed by
them: add each V2 service to the service catalog and link a system alias (`/IWFND/MAINT_SERVICE`),
check the service node is active, publish V4 services in `/IWFND/V4_ADMIN`, create a technical
user for the apps with a **read-only** role limited to these services, and any communication
scenario or arrangement their release requires.

Services to ask for, in the order the apps need them (verified entities marked, the rest are
candidates to confirm on the system):

| Service | For | Status |
|---|---|---|
| `API_SALES_ORDER_SRV` | sales orders and items | verified |
| `API_BILLING_DOCUMENT_SRV` | company code, invoiced revenue, invoices | verified |
| `API_SALES_CONTRACT_SRV` | customer contracts | verified |
| `API_PURCHASEORDER_PROCESS_SRV` | purchase orders, items, schedule lines | verified |
| `API_MATERIAL_DOCUMENT_SRV` | goods receipts, stock movements | verified |
| business partner / customer and supplier names | names and countries | candidate |
| product master (descriptions, groups) | material descriptions | candidate |
| `API_PRODUCTION_ORDER_2_SRV` or `API_PRODUCTIONORDER` | production orders and components | candidate |
| `API_MATERIAL_STOCK_SRV` | stock | candidate |
| accounting document item APIs | receivables due and cleared dates | candidate |

Until the system has them, butterfly is our only source. SAP also offers a public **sandbox** for
many of these services with sample data; it is useful to check that our readers parse the real
response format, but its company codes and data are not ours.

## 8. Questions for the consultants

- Which of the services above can be enabled, and in what time?
- Is the company code recoverable on a sales order (sales organization to company code mapping)?
- Is the delay reason held in a custom field on production orders?
- What data volumes (orders per month, per company) do we expect, so we can pick the aggregation
  option?
- Is there a development or test system we can point to before production?
