# workspace-web/04 order-status

## Goal
The new-order page understands the answers of the order queue (workspace-api 03), so nobody enters an order twice because SAP was slow, and the user can see which of their orders are still waiting for SAP.

Today the page turns a `202` into "Something went wrong. Try again", which invites a second entry of an order that is already safe in the queue.

## Behavior
### What the page shows after Create order
| Answer | Page |
|--------|------|
| `201` | as today: green "Sales order 0000012345 created", form cleared |
| `422` with details | as today: the messages on the fields |
| `202`, status `queued` | amber notice "Saved. SAP could not take the order right now; it will be sent automatically.", form cleared, order appears in the waiting list |
| `202`, status `unknown` | red notice "We could not confirm that SAP received the order. Do not enter it again; check with your SAP contact or the order list.", form cleared, order appears in the waiting list marked "Check in SAP" |
| `503` with code `STORE_UNAVAILABLE` | red "The order could not be saved and nothing was sent. Try again." (the form is kept) |
| any other `503` | as today: "SAP is not available. Try again in a moment." |
| anything else | as today: "Something went wrong. Try again." |

The Create button stays disabled while the request runs (as today), and the form is cleared on a `202` so the same order is not sent twice by pressing it again.

### Waiting for SAP
- Below the form, a panel **Waiting for SAP** lists the signed-in user's open orders from `GET /v1/workspace/sales-order-requests?open=true`: when it was entered, the customer, the number of items, and a status label: `queued` "Will be sent automatically", `sending` "Sending", `unknown` "Check in SAP", `failed` "Could not be sent". An order with `attempts` above 0 shows "tried N times".
- It loads when the page opens, after every submit that gives a `202`, and every 15 seconds while the page is open. It is hidden when there is nothing to show. A failure to load it shows one small grey line ("Could not load waiting orders"), never an error on the order form.
- An order that has been posted or rejected is no longer open and so leaves the list; the page does not announce it (the order list screen, workspace-web 03, is where finished orders are read).
- Nothing on this page clears or re-sends an order; `unknown` and `failed` ones stay until someone handles them (not built yet).

### API change in workspace-api
Order request responses (`GET .../sales-order-requests`, `.../{id}` and the `202`) gain `order`: the order as it was sent (`sold_to_party`, `transaction_currency`, `requested_delivery_date`, `items`), so the panel can say what is waiting. The saved body is already stored; this only exposes it, to the user who owns it.

### Client
`SalesOrderClient` keeps `create` and adds `openRequests()`. `CreateResult` gains `{ ok: false, kind: 'queued' | 'unknown', request }` and `kind: 'notSaved'` (the `STORE_UNAVAILABLE` case). Nothing else in the client changes.

## Acceptance cases
- `202` queued: amber notice, form cleared, the list reloaded; unknown: red notice with the do-not-enter-again text, form cleared, list reloaded.
- `STORE_UNAVAILABLE` keeps the form values and shows the "nothing was sent" text; a plain `503` shows the SAP text; `201` and `422` behave exactly as before (the existing page tests pass unchanged).
- The Create button is disabled while the request is running and the form is empty after a `202`.
- The panel shows customer, item count, time and the four labels, "tried N times" only when attempts is above 0, and is hidden when the list is empty.
- It reloads every 15 seconds (fake timers) and stops when the page is left; a failed load shows the grey line and leaves the order form untouched.
- Client: `202` bodies for queued and unknown map to the right `kind` with the request; `openRequests` returns the list and sends the cookie; an error response from the list is an error, not an empty list.
- workspace-api: the three responses carry `order`; another user's order is still `404`.
- No new dependency; all UI from `@sami/ui`.

## Out of scope
Clearing or re-sending an `unknown` or `failed` order, a notification when a waiting order is posted, the sales order list screen (workspace-web 03), a screen of finished requests, an idempotency key from the browser.

## Depends on
workspace-api 03, workspace-web 02.
