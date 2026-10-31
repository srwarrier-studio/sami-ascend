# workspace-api/03 order-queue

## Goal
A sales order entered in workspace is never lost and never posted twice when SAP is slow, busy or down, with the smallest design that does it: try SAP at once as today, and when SAP cannot take it, keep it in a queue and let one worker post it later. Every limit defaults to the worst case (SAP takes one write at a time) and is a setting to raise when the real capacity is known.

This is a queue and a worker, not an event broker. The statuses below are the events; moving them onto a broker later changes the plumbing, not the rules.

## Behavior
### Posting (the existing route)
`POST /v1/workspace/sales-orders` keeps its request and its answers when SAP answers in time: `201` with the order, or `422 VALIDATION_FAILED` with SAP's details. What changes is what happens when SAP does not answer:

| What happened | Meaning | Result |
|---------------|---------|--------|
| SAP answered `201` | posted | `201` with the order, as today |
| SAP answered `400` | rejected | `422 VALIDATION_FAILED`, as today; nothing is queued |
| the app could not get one of the `SAP_WRITE_LIMIT` slots within `SAP_WRITE_WAIT_SECONDS`, the connection failed before anything was sent (refused, DNS, connect timeout), or SAP answered `503` or `429` | **not processed** (certain) | the order is saved as `queued`; `202 {id, status: "queued", message}` |
| the connection broke or timed out after the request was sent, or SAP answered any other `5xx` | **unknown** (SAP may have created it) | the order is saved as `unknown`; `202 {id, status: "unknown", message}`; it is never retried by the app |

- At most `SAP_WRITE_LIMIT` (default 1) writes to SAP are in flight at the same time in the whole process, the request threads and the worker together. A request that cannot get a slot waits up to `SAP_WRITE_WAIT_SECONDS` (default 2) and is then queued, so a burst of users cannot flood SAP.
- A saved order keeps the user (`sub`), the SAP username, the request id, the body as sent, the time and its status.

### The queue and the worker
- One worker thread per `ORDER_WORKERS` (default 1; 0 turns the worker off) takes `queued` orders whose time has come, oldest first, marks one `sending`, posts it through the same limit, and records the result:
  - `201`: `posted`, with the SAP order number;
  - `400`: `rejected`, with SAP's details;
  - not processed: back to `queued` with `attempts + 1` and the next try after a wait of 30 seconds, doubling each time up to 15 minutes; after `ORDER_MAX_ATTEMPTS` (default 8) it becomes `failed` (still certain it was not posted);
  - unknown: `unknown`, no retry.
- On start, any order left `sending` by a crash becomes `unknown`.
- The worker never runs inside the app factory; `run.py` starts it, so tests control it.

### Seeing what happened
Both routes need the `sales` role and show only the signed-in user's own orders (another user's id is `404`).
- `GET /v1/workspace/sales-order-requests/{id}` returns `id`, `status`, `attempts`, `created_at`, `updated_at`, and when known `sales_order`, `details` (for `rejected`) and `message`.
- `GET /v1/workspace/sales-order-requests?open=true` returns the user's orders that are `queued`, `sending`, `unknown` or `failed`, newest first, at most 50.
- The `unknown` message tells the user to look in the order list before entering the order again. Nothing in the app clears an `unknown` order; someone who has checked SAP does it later (out of scope here).

### Storage
SQLite through the standard library, one file (`ORDER_DB`, default beside the app), one table behind a small repo interface with an implementation for tests. The table is the only state; the worker holds none. A real database (Postgres) is the upgrade if several app instances share the queue.

### Settings (worst-case defaults)
`SAP_WRITE_LIMIT` 1, `SAP_WRITE_WAIT_SECONDS` 2, `ORDER_WORKERS` 1, `ORDER_MAX_ATTEMPTS` 8, `ORDER_DB`. The existing SAP timeout stays.

## Acceptance cases
- SAP healthy: `201` and `422` exactly as before; nothing is saved.
- Connection refused, connect timeout, `503` and `429` each give `202 queued` and a saved order; a read timeout, a broken connection and `500` each give `202 unknown` and a saved order that is never posted again.
- With `SAP_WRITE_LIMIT` 1 and one write held in flight, a second request waits and is queued; with a limit of 2 both go through; the slot is released after a failure.
- The worker posts a queued order once, records the SAP number and stops; a `400` becomes `rejected` with details; a repeat of not-processed backs off 30 s, 60 s, 120 s and so on to 15 minutes and becomes `failed` after the last attempt; an `unknown` result is never retried.
- Two workers never take the same order; an order is posted at most once whatever the failures (checked with a gateway that fails in every order).
- A crash leaves `sending` orders as `unknown` on start; `queued` orders survive a restart and are posted.
- The status routes: own order found, someone else's `404`, `open=true` lists only open statuses newest first, limit 50; the role and cookie rules of the other routes; a failing store is `503`.
- The request id and the user are on every saved order and on every post to SAP.
- Against butterfly in process: an order posted through a gateway that fails twice with `503` and then recovers ends `posted` with a real order number and exactly one order in butterfly.

## Out of scope
A message broker, events published to other services, an idempotency key from the browser, a SAP-side external reference to look an order up and retry an `unknown` one safely (the upgrade once the SAP team can add a customer reference field), clearing or re-sending `unknown` orders, the workspace-web screens for these statuses, an admin view, changing orders already posted, `shared/04` (who posts in SAP), failure modes in butterfly (butterfly 04).

## Depends on
workspace-api 01 and 02.
