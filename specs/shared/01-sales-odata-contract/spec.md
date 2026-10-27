# shared/01 sales-odata-contract

## Goal
Agree one OData V4 Sales service contract in `docs/sap/`, so butterfly, the workspace and
synapse gateways and the SAP consultant guide are all built from the same document.

## Deliverable
`docs/sap/sales-contract.md` with the sections below. No code.

1. **Service**: name `ZUI_SALES_O4`, root `/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/`. Formats are JSON only.
2. **Entities**
   - `SalesOrder` (key `SalesOrder`): `SalesOrder`, `SalesOrderType`, `SoldToParty`, `CustomerName`, `OrderDate`, `RequestedDeliveryDate`, `TransactionCurrency`, `TotalNetAmount`, `OverallStatus`, `CreatedByUser`, `CreationDateTime`, `LastChangeDateTime`.
   - `SalesOrderItem` (key `SalesOrder`, `SalesOrderItem`): `Material`, `MaterialDescription`, `Quantity`, `QuantityUnit`, `NetAmount`. Navigation `_Item` from `SalesOrder`, `$expand` supported.
   - Summary entities (read-only, for phase butterfly/03): `SalesSummaryByDay`, `SalesSummaryByCustomer`, `SalesSummaryByMaterial`, each with `TotalNetAmount`, `OrderCount`, `Currency`.
3. **Types**: formats for dates (`Edm.Date`), timestamps (`Edm.DateTimeOffset`, UTC), amounts (`Edm.Decimal` sent as a JSON string, as OData V4 allows), and status values.
4. **Query options**: `$filter` (`eq ne gt ge lt le and or`, `contains`, `startswith`), `$select`, `$orderby`, `$top` (max 1000), `$skip`, `$count=true`. `$apply` is not used.
5. **Reads**: example request and full JSON response for list, single by key, `$count`, and `$expand=_Item`.
6. **Writes**: `POST SalesOrder` with items (deep insert) and `PATCH SalesOrder(...)` for header fields; the request and response bodies; `ETag` / `If-Match` on PATCH.
7. **Error format**: the OData V4 `{"error": {"code", "message", "target", "details": [...]}}` shape, with one example each for validation (400), not found (404), ETag mismatch (412), authorization (403), and server (500).
8. **Identity**: which user the call runs as is left to shared/04. The contract only says the request carries one SAP login.
9. **Open questions for SAP consultants**: list kept at the end of the document.

## Acceptance cases
- Every entity field has a name, an OData type, a nullable flag and one example value.
- Every example response is valid JSON and parses against the field table (checked by a small pytest that loads the JSON blocks).
- Butterfly phases 01 to 03 can be built with no further questions about shapes.
- The consultant guide can name every CDS element from the field tables.

## Out of scope
SAP-side implementation, authentication details, performance limits, butterfly code,
deleting orders, any entity outside Sales.

## Depends on
Nothing.
