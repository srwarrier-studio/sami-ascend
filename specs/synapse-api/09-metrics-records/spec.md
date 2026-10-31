# synapse-api/09 metrics-records

## Goal
synapse-api answers "where did the change come from" for any registered metric (sales, purchases, later others) and returns the records around it for any registered record type, both driven by one registry file the owner maintains, so a new metric or record type is a config change and not a new endpoint.

This replaces the sales-only `/sales/compare` and `/sales/month` of phase 08. Records are rows that already exist in SAP (or butterfly), read when asked; there is no event stream.

## The registry
`apps/synapse-api/registry.toml`, read and checked at start; a bad entry stops the start with a message naming the entry. Sketch:

```toml
[metric.sales]
label = "Sales"
service = "sales"
measure = "TotalNetAmount"
quantity = "TotalQuantity"
date = "OrderDate"
currency = "Currency"
by.day = { entity = "SalesSummaryByDay", order = "OrderDate,Currency" }
by.customer = { entity = "SalesSummaryByCustomer", key = "SoldToParty", name = "CustomerName", order = "OrderDate,SoldToParty,Currency" }
by.material = { entity = "SalesSummaryByMaterial", key = "Material", name = "MaterialDescription", unit = "QuantityUnit", quantity = "TotalQuantity", order = "OrderDate,Material,Currency" }

[record.purchase_delivery]
service = "drivers"
entity = "PurchaseDelivery"
key_fields = ["Material", "Supplier", "PurchaseOrder"]
interval = { from = "PromisedDeliveryDate", to = "ActualDeliveryDate", fallback = "PromisedDeliveryDate", open_to_today = true }
delay = { due = "PromisedDeliveryDate", done = "ActualDeliveryDate" }
order = "PromisedDeliveryDate,PurchaseOrder"
```

- A **metric** names a service, the field that holds the amount, the date and the currency, and one summary entity per dimension (plus `day` for totals). SAP does the summing (summary views), synapse-api never pages through raw documents. A dimension may also name a `quantity` and `unit`; only those dimensions can split volume from price.
- A **record type** names a service, an entity, the fields a caller may look up by (`key_fields`, the first is the default), an optional `interval` (the dates a row is "active" between, for the window), an optional `delay` and the order.
- `service` is `sales` or `drivers`, mapped to the base URLs in settings (`sap_base_url`, the new `drivers_base_url`).
- The three sales entries and the four drivers entries ship in the file; purchases are added when butterfly 10 exists.

## Behavior
All routes are under `/v1/synapse`, roles `MANAGEMENT` and `ADMIN`, the 5-minute cache, `INVALID_QUERY` 422 and `SAP_UNAVAILABLE` 503, as in phase 08.

### `GET /metrics`
The registered metrics with `name`, `label`, their dimensions and whether each dimension can split volume from price; and `GET /records/types` the record types with their `key_fields`, whether they take a window and whether they have `delay_days`. sami-agents reads these to check its graph.

### `GET /metrics/{metric}/compare`
Exactly what phase 08's `/sales/compare` did (same query, same response, same rules: periods up to 400 days, `by`, `top`, `other` row, per currency, volume and price effect when the dimension has a quantity), for any registered metric. An unknown metric is 404 `METRIC_NOT_FOUND`; a `by` the metric does not have is `INVALID_QUERY`.

### `GET /metrics/{metric}/month`
Phase 08's `/sales/month` for any metric.

### `GET /records?type=<type>&key=<key>[&key_field=<field>][&start=<date>&end=<date>]`
- `type` and `key_field` come from the registry; an unknown type is 404 `RECORD_TYPE_NOT_FOUND`, a `key_field` not listed is `INVALID_QUERY`.
- `start` and `end` are required when the type has an `interval`, `start <= end`, at most 400 days; a type without one ignores them. `key` is 1 to 40 characters from letters, digits, `_` and `-`, because it goes into the SAP filter; anything else is `INVALID_QUERY`. Only field names from the registry are ever put in a filter.
- A row is returned when its interval overlaps the window. The interval is `from` to `to`; when `to` is empty it is `fallback`, and with `open_to_today` it is the later of `fallback` and today.
- Response: `type`, `key_field`, `key`, `start`, `end`, `records`: the SAP fields exactly as the contract names them (no renaming), ordered by the type's `order`. When the type has a `delay`, each record also has `delay_days`: the later of `done` (or today when empty) and `due`, minus `due`, never below 0.
- An empty result is an empty list.

### Shared reading
Paging, request id and error handling move out of `ButterflySalesSource` into one small OData reader that the sales source, the metric reads and the record reads all use. Requests the sales source sends today stay exactly as they are.

## Acceptance cases
- Everything listed in phase 08 still holds through `/metrics/sales/compare` and `/metrics/sales/month` (the same tests, moved), and the old `/sales/compare` and `/sales/month` no longer exist.
- Registry: the shipped file loads; an entry with a missing field, an unknown `service`, a `by` entity without `key`, an interval field that is not a string, or a duplicate name stops the start with a message that names it.
- A metric added in a test registry (a copy of sales with other entity names) works through the same routes with no code change; the same for a record type.
- `/metrics` and `/records/types` list what the registry holds.
- Against butterfly `august-contract`: `contract` for `0000100001` over 2026-07-01 to 2026-08-31 returns `0040000127` and not `0040000163`; `purchase_delivery` for `RAW-2002` over July returns `4500001207` with `delay_days` 12; `production_order` for `RM-1002` over July to August returns `0001000417` with `delay_days` 14 and `DelayReason` `MATERIAL_SHORTAGE`; `production_component` for `0001000417` returns the `RAW-2002` component.
- Against `breakdown-shortfall`: `production_order` for `RM-1005` over July returns the order with `MACHINE_BREAKDOWN` and `delay_days` 10.
- Interval rule: a delivery promised before the window and delivered inside it is returned; one delivered before the window is not; an open overdue item is returned for a window that includes today. `delay_days` is 0 for on-time rows and for an open item not yet due.
- Invalid: unknown `by` for the metric, a `key` with a quote, space or over 40 characters, `key_field` not allowed, `start` after `end`, over 400 days, missing `start` for a windowed type.
- Roles, 503 with nothing partial, the cache and the request id on every page behave as in phase 08, for every route.

## Out of scope
Pushing or streaming changes, company filtering, writes, `$expand`, joining two record types in one call, anomaly rules and the graph (sami-agents 04), purchase data (butterfly 10; its registry entries are added in sami-agents 05's first task or a one-line follow-up there), the SAP views.

## Depends on
synapse-api 07 and 08, butterfly 08 and 09, `docs/sap/drivers-contract.md`.
