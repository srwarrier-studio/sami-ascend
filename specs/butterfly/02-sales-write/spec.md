# butterfly/02 sales-write

## Goal
Butterfly accepts `POST SalesOrder` (deep insert) and `PATCH SalesOrder('key')` as in `docs/sap/sales-contract.md` section 6, so an order created through an API shows up in the reads that already exist.

## Behavior
- **Create:** `POST {root}SalesOrder` with header fields and `_Item`. Returns `201` with the full order and items (as the `$expand=_Item` example), `@odata.etag`, and a `Location` header with the new order URL.
- **SAP fills in:** next `SalesOrder` number (continuing after the seed, `0000012031`), item numbers `000010`, `000020`..., `CustomerName` and `MaterialDescription` from master data, `OrderDate` (today, UTC), item `NetAmount` (quantity times the material's price), `TotalNetAmount`, `OverallStatus` `A`, `CreatedByUser` `BUTTERFLY` (identity is shared/04), both timestamps (now, whole seconds, UTC).
- **Master data:** the seed customers and materials become reference data behind a `MasterDataRepo`. A material has one unit and one price (the existing seed). Only currency `INR` is valid. Any non-empty `SalesOrderType` is accepted (the contract has no code for a bad type; question for consultants).
- **Validation (create):** all failures are collected and returned together as one `400 VALIDATION_FAILED` with a `details` entry per failure; `target` is the field path, items by zero-based position (`_Item/1/Quantity`). Codes: `FIELD_REQUIRED`, `CUSTOMER_UNKNOWN`, `MATERIAL_UNKNOWN`, `UNIT_INVALID` (unit is not the material's unit), `CURRENCY_INVALID`, `QUANTITY_NOT_POSITIVE`, `DELIVERY_DATE_IN_PAST` (before today; today is fine), `NO_ITEMS` (missing or empty `_Item`).
- **Body problems** (new, added to the contract first): a body that is not a JSON object is `400 INVALID_REQUEST_BODY`. A value of the wrong format (date not `YYYY-MM-DD`, quantity not a decimal string, a number where a string is required) is a detail `FIELD_INVALID`. A field the caller may not send (anything SAP fills in, or an unknown name) is a detail `FIELD_NOT_ALLOWED`. Nothing is created when any detail exists.
- **Change:** `PATCH {root}SalesOrder('key')` with `If-Match` and `{"RequestedDeliveryDate": "..."}`. Returns `200` with the full updated order (no items) and a new etag.
  - no `If-Match` is `428 ETAG_REQUIRED`; a value that is not the current etag is `412 ETAG_MISMATCH`; unknown order is `404`.
  - order status `C` or `X` is `400 VALIDATION_FAILED` with detail `ORDER_NOT_CHANGEABLE`; a past date is `DELIVERY_DATE_IN_PAST`; any other field is `FIELD_NOT_ALLOWED`; a null or missing date is `FIELD_REQUIRED`.
  - `LastChangeDateTime` always moves forward by at least one second, so the etag always changes even for two changes in the same second.
- **Storage:** the in-memory repo gets `add` and `update`; created and changed orders appear in `GET`, `$filter`, `$expand`, `_Item` and `$count` at once. Lost on restart.

## Acceptance cases
- The contract's create example (with `SalesOrderType`, `SoldToParty`, `RequestedDeliveryDate`, two items) returns 201 and a response with the same shape as the `$expand=_Item` example; totals equal the sum of item amounts.
- Two creates in a row get consecutive numbers; the second is listed after the first; `$count` goes up by one.
- Every validation code has a test; a body with several problems returns all of them in one response, in field order; an item error uses the right index.
- Nothing is stored after any 400.
- Create with `RequestedDeliveryDate` today is accepted; yesterday is rejected; omitted is accepted and stored as null.
- PATCH: success changes only the date and `LastChangeDateTime`; the old etag then gives 412; two PATCHes in the same second still change the etag; `C` and `X` orders are not changeable; `A` and `B` are.
- Both writes show the right `Content-Type: application/json` error body for 404, 412 and 428.
- Existing read tests still pass; `test_contract.py` checks the write examples in the contract.

## Out of scope
Delete, changing items, cancel as a PATCH, identity (`CreatedByUser` is fixed), authentication, persistence, concurrency, `SalesOrderType` validation, delays and failures (butterfly/04), summaries (butterfly/03).

## Depends on
butterfly/01 (done).
