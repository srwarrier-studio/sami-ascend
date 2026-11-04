# butterfly/21 standard-sales-order

## Goal
Butterfly answers the **real SAP Sales Order API** at SAP's own URLs, in SAP's own formats, for reading sales orders and their items, so synapse-api can be built against the real contract now and pointed at SAP later by changing a host and a user. The invented sales service stays untouched until every consumer has moved.

## Why
shared 12 saved the real specifications and sample responses of both versions of the service from the Hub sandbox (`docs/sap/standard/api_salesorder-v4/` and `docs/sap/standard/api_sales_order_srv-v2/`). The owner's private cloud runs S/4HANA 2022; whether it serves the V4 service is still to be confirmed, so both are served: V4 first, V2 as the fallback.

## Behavior
- **Two services, one store.** Both read the existing sales orders and items; nothing is copied.
  - **V4:** `/sap/opu/odata4/sap/api_salesorder/srvd_a2x/sap/salesorder/0001/` with entity sets `SalesOrder` and `SalesOrderItem`.
  - **V2:** `/sap/opu/odata/sap/API_SALES_ORDER_SRV/` with `A_SalesOrder` and `A_SalesOrderItem`.
  - Every other entity set of each real service exists and answers an empty collection, so a client that lists them does not fail.
- **`$metadata` is the real one.** Each service serves its saved real `$metadata` document unchanged.
- **Rows have every property of the real entity type**, in the real order, with the real type: the ones butterfly holds are filled, the rest are empty in the way SAP returns them (`""` for text, `null` for dates, `false` for flags, `0` where the type needs a number). A contract test compares the property names and JSON types of a row with the saved real sample.
- **Mapping from our order:**
  - `SalesOrder`, `SalesOrderType`, `SoldToParty`, `TransactionCurrency`, `CreatedByUser`, `LastChangeDateTime`, `RequestedDeliveryDate`, `TotalNetAmount` map by name.
  - `SalesOrderDate` comes from the order date; `CreationDate` and `CreationTime` from the creation time; `OverallSDProcessStatus` is `A`, `B` or `C` from the overall status.
  - `SalesOrganization` is derived from the company code (`INA1` to `1710`-style codes held in one table); on V4 `BillingCompanyCode` is the company code. **V2 has no company code**, as in SAP.
  - Items: `SalesOrder`, `SalesOrderItem`, `NetAmount`, `RequestedQuantity` and its unit, `TransactionCurrency`; `Product` (V4) or `Material` (V2) is the material; `SalesOrderItemText` is the material description.
  - Customer name, country and the rupee amounts are not in SAP's order, so they are not in these responses.
- **V4 behavior** (as the sandbox does it): `@odata.context`, `@odata.metadataEtag` and a row `@odata.etag`; `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count=true` giving `@odata.count`, `$expand=_Item` with a nested `$select`, `/$count` as plain text; amounts as JSON numbers, dates ISO, `LastChangeDateTime` as a timestamp with `Z`.
  - **`$apply`:** `groupby((fields),aggregate(Amount with sum as Alias))`, also after a leading `filter(...)`, on `SalesOrder` (by `SoldToParty`, `SalesOrderDate`, `BillingCompanyCode`, `TransactionCurrency`) and on `SalesOrderItem` (by `Product`, `TransactionCurrency`). Like SAP: `$orderby` on the alias is refused (400) and `countdistinct` answers 501 `$apply option not supported`.
  - **Currency rule:** a `$filter` on `TotalNetAmount` without a `TransactionCurrency` in the same filter is refused with SAP's message.
- **V2 behavior:** `{"d": {"results": [...]}}`, a `__metadata` block (`id`, `uri`, `type`, `etag`) and a deferred link per navigation property, dates as `/Date(ms)/`, amounts as strings, `$inlinecount=allpages` giving `d.__count`, `/$count` as plain text, `$expand=to_Item`. `$apply` is refused with SAP's V2 message.
- **Errors** use each service's own structure (V4: `error.code`, `message`, `@SAP__common.ExceptionCategory`, `innererror.ErrorDetails`; V2: `error.message.value`) with the real messages for the cases the samples show (unknown property, bad filter, amount filter without currency, unsupported option).
- **Model and repository changes** (the stored order must hold what SAP's create call and reads need, because workspace will create and change orders through this same service in the next phases):
  - `SalesOrder` gains `sales_organization`, `distribution_channel` and `division` (the standard create needs all three; SAP derives the company code from the sales organization) and `purchase_order_by_customer`. The sales organization follows the company code through one table in the master data module (`SALES_ORGANIZATIONS`), unless it is given; existing orders get the value of their company when an older database is migrated.
  - `SalesOrderItem` keeps its fields; the unit is stored as SAP's internal unit and the ISO unit is derived from a small unit table, because V4 has `RequestedQuantitySAPUnit` and `RequestedQuantityISOUnit` (not a plain unit).
  - Numbers are returned the way the samples show (`"1"`, item `"10"`, no leading zeros) and keys in a URL are accepted with or without them.
  - `customer_name`, `country` and the rupee amounts stay on our order for the old service only; the standard responses leave them out.
  - The stored tables (SQLite) and the in-memory repository get the new fields; an older database is rebuilt, as in earlier phases. The repository interface keeps its methods.
  - The filter, order-by and select engine reads its field names from one table per service (our custom names, V4 standard names, V2 standard names) instead of a single hard-coded table, so all three services share one engine.
- **Reads only.** Create and change in the standard format, schedule lines, partners, texts and the other business objects are later phases.

## Acceptance cases
- Both `$metadata` documents are byte for byte the saved real ones.
- A list row of each service has exactly the property names and JSON types of the saved real sample row; the mapped fields carry the order's values.
- `$top`, `$skip`, `$filter`, `$orderby`, `$select`, `$count` and `$expand` give the same shapes as the saved samples; V4 `$apply` groups and sums as in the sample and refuses the two unsupported cases with the real status and message.
- A V4 filter on the amount without a currency is refused exactly like the sandbox; the V2 service refuses `$apply`.
- V4 rows carry `BillingCompanyCode`, V2 rows have no company field, and a company-scoped filter on V4 returns only that company's orders.
- Everything in the existing butterfly suite still passes, with the old service unchanged.

## Out of scope
Writes in the standard format (the next phase, butterfly 22: create and change in the standard body, with the sales organization and the standard item fields, then workspace-api moves to it), the standard customer and business partner service that workspace needs for customer names (a later phase), schedule lines and the other entity sets' data, the billing, purchase and material document services (later phases), exchange rates, synapse-api changes (the next phase after this one).

## Depends on
shared 12 (the saved specifications and samples), butterfly 20.
