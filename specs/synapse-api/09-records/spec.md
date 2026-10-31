# synapse-api/09 records

## Goal
synapse-api returns the rows of one kind of record (contract, purchase delivery, production order, production component) for a key and a time window through one generic read, so the AI analysis can look at what happened around a customer, product or material without one endpoint per question.

This is a plain read, not an event stream: "records" are rows that already exist in SAP (or butterfly), fetched when asked.

## Behavior
One new route under `/v1/synapse`, same roles as the sales routes (`MANAGEMENT`, `ADMIN`), same 5-minute cache, same error format (`INVALID_QUERY` 422, `SAP_UNAVAILABLE` 503).

`GET /records?type=<type>&key=<key>&start=<date>&end=<date>[&key_field=<field>]`

| `type` | Allowed `key_field` (first is the default) | Window rule (a row is returned when its interval overlaps `start` to `end`) |
|--------|---------------------------------------------|------------------------------------------------------------------------------|
| `contract` | `SoldToParty`, `SalesContract` | `ValidFrom` to `ValidTo` |
| `purchase_delivery` | `Material`, `Supplier`, `PurchaseOrder` | `PromisedDeliveryDate` to `ActualDeliveryDate`; an open item runs to today, or to its promised date when not yet due |
| `production_order` | `Material`, `ProductionOrder` | `PlannedStartDate` to `ActualEndDate`; an open order runs to its planned end or today, whichever is later |
| `production_component` | `ProductionOrder`, `Material` | no window; `start` and `end` are ignored and may be left out |

- `start` and `end` are required for the first three types, `start <= end`, at most 400 days. `key` is 1 to 40 characters from letters, digits, `_` and `-`, because it goes into the SAP filter; anything else is `INVALID_QUERY`. An unknown `type` or a `key_field` not allowed for the type is `INVALID_QUERY`.
- Response: `type`, `key_field`, `key`, `start`, `end` and `records`, each record with the contract's fields in snake_case (`sales_contract`, `predecessor_contract`, `sold_to_party`, and so on, as in `docs/sap/drivers-contract.md`), ordered by the type's first date, then key.
- `purchase_delivery` and `production_order` records also carry `delay_days`: the later of its actual date (or today when still open) and the promised or planned end, minus that promised or planned end, never below 0. The contract says SAP does not return a delay, so this is the one place it is worked out. Contracts and components have no `delay_days`.
- An empty result is an empty list, not an error.
- Reads go to the drivers service (`ZUI_DRIVERS_O4`), paged like the sales summaries, with the key and the near side of the window in the `$filter` and the overlap rule applied here. Its base URL is a new setting. The paging and error handling shared with `ButterflySalesSource` move into one small reader that both use.

## Acceptance cases
- Against butterfly `august-contract`, `contract` for key `0000100001` over 2026-07-01 to 2026-08-31 returns `0040000127` (ended 2026-07-12) and not `0040000163` (valid from 2026-09-14); over 2026-09-01 to 2026-09-30 it returns `0040000163`.
- `purchase_delivery` for `RAW-2002` over July 2026 returns `4500001207` with `delay_days` 12; `production_order` for `RM-1002` over July to August returns `0001000417` with `delay_days` 14 and reason `MATERIAL_SHORTAGE`.
- `production_component` for `0001000417` returns the `RAW-2002` component; with `key_field=Material` and key `RAW-2002` it returns the orders that use it.
- Against `breakdown-shortfall`, `production_order` for `RM-1005` over July returns the order with reason `MACHINE_BREAKDOWN` and `delay_days` 10.
- Interval rule: a delivery promised before the window and delivered inside it is returned; one delivered before the window is not; an open overdue item is returned for a window that includes today.
- `delay_days` is 0 for an on-time row and for an open item not yet due.
- Invalid: unknown `type`, `key_field` not allowed for the type, key with a quote or space or over 40 characters, `start` after `end`, a window over 400 days, a missing `start` for a windowed type.
- Roles: `MANAGEMENT` and `ADMIN` pass, other roles 403, no cookie 401. A failing source is 503 and nothing partial is returned. An identical second call inside 5 minutes does not read again.
- Every request sends the request id; the sales source still passes its paging tests after the shared reader is extracted.

## Out of scope
Streaming or pushing changes, filtering by company, writes, `$expand`, any dimension beyond the key fields above, the graph and the anomaly rules (sami-agents 04), the SAP views.

## Depends on
synapse-api 07 (paging), synapse-api 08 (route and cache pattern), butterfly 08 and 09 (drivers data and scenarios), `docs/sap/drivers-contract.md`.
