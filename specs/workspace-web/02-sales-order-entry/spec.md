# workspace-web/02 sales-order-entry

## Goal
A user with the `sales` role can enter a sales order in the browser and see clear messages when SAP rejects it.

## Behavior
- **Page:** `/sales-orders/new`, linked from the menu entry "New sales order" (role `sales`, same table in `menu.ts`). The existing `/sales-orders` path keeps "Coming soon" (the list is phase 03). Same guard as `/sales-orders`.
- **Form fields:**
  - Order type (text, default `OR`), Customer number (`SoldToParty`), Currency (text, default `INR`), Requested delivery date (optional, date input).
  - Item rows, at least one: Material, Quantity, Unit. "Add item" appends a row; "Remove" deletes a row (hidden while only one remains).
  - Free text for now: no customer or material lookup exists. Values are trimmed; the unit is sent as typed.
- **Submit:** `POST {WORKSPACE_URL}/v1/workspace/sales-orders` with credentials, JSON body `{ sales_order_type, sold_to_party, transaction_currency, requested_delivery_date, items: [{ material, quantity, quantity_unit }] }`. Quantity is sent as a string (decimal). An empty date is sent as `null`. The button is disabled while the request runs.
- **Success (`201`):** show "Sales order 0000012345 created" (from `sales_order` in the response) and reset the form to its defaults.
- **Validation (`422 VALIDATION_FAILED`):** body `{ code, details: [{ code, target, message }] }`.
  - `target` maps to a field: `SalesOrderType`, `SoldToParty`, `TransactionCurrency`, `RequestedDeliveryDate`, `_Item/<n>/Material|Quantity|QuantityUnit` (n is the zero-based row). Show the `message` under that field.
  - A detail with no matching field (for example `NO_ITEMS`) is listed in an alert above the form.
  - Fix-and-resubmit clears the old messages. The form keeps what the user typed.
- **Other failures:** `503` shows "SAP is not available. Try again in a moment." Any other error or network failure shows "Something went wrong. Try again." Both keep the form as typed.
- **Client code:** `api/salesOrders.ts` exposes a `SalesOrderClient` type with `create(order)` returning `{ ok: true, salesOrder } | { ok: false, kind: 'validation', details } | { ok: false, kind: 'unavailable' | 'failed' }`. Components never call `fetch`. The client reaches pages through router context, like the auth client, so tests pass a fake.
- **Config:** `VITE_WORKSPACE_URL` (default `http://localhost:8002`).
- **UI:** `@sami/ui` only, same rules as phase 01. If a Mantine component is missing from `@sami/ui` (for example `NumberInput` or a date input), re-export it there first; plain `TextInput` with `type="date"` is enough for the date.
- No new dependencies.

## Acceptance cases
Tests use a fake client; no network.
- Menu shows "New sales order" for `sales`, hidden for `admin` alone and `stores`; the route sends a user without `sales` to `/not-allowed`.
- Form starts with type `OR`, currency `INR` and one empty item row.
- "Add item" adds a row; "Remove" removes it; the last row cannot be removed.
- Submit sends the typed values (trimmed, empty date as `null`, quantity as string).
- `201` shows the order number and resets the form.
- `422` with a header target shows the message under that field; `_Item/1/Quantity` lands on the second row's quantity; an unmatched detail shows in the alert.
- Resubmitting clears old messages.
- `503` and a network failure show their messages and keep the typed values.
- The button is disabled while the request is pending.

## Out of scope
Customer and material search, pricing or totals preview, drafts, editing an existing order, the order list (03), client-side validation beyond "something typed" (SAP is the judge), session expiry.

## Depends on
workspace-web 01 (done), workspace-api 02 (done: `POST /v1/workspace/sales-orders`, `422 VALIDATION_FAILED`, `503 SAP_UNAVAILABLE`).
