# workspace-api

Workflow backend for department users. Serves sales order routes to the workspace web app. Only users with the `sales` role may call them; an absent user's stand-in is given the `sales` role by an admin.

## Gateway
`SalesOrderGateway` (in `domain/gateways`) has `create(NewSalesOrder)` and `list_recent(top, skip)`. Use cases `CreateSalesOrder` and `ListSalesOrders` wrap it.

- `ButterflySalesOrderGateway` calls the Sales OData V4 contract in `docs/sap/sales-contract.md`. Set `SAP_BASE_URL` (default: butterfly on `http://localhost:8003` with the contract root path).
- `MockSalesOrderGateway` keeps orders in memory for tests; `reject_with(details)` makes the next creates fail.
- `SalesOrderRejected` carries every validation detail (branch on `code`); `SapUnavailable` covers timeouts, connection errors and `5xx`.

## Routes (`/v1/workspace`)
- `POST /sales-orders` creates an order, `201` with the order. Body: `sales_order_type`, `sold_to_party`, `transaction_currency`, `requested_delivery_date` (optional), `company_code` (required, one of the user's companies from the token: `INA1` sabinsa, `INA2` neutraceuticals, `INA3` organica; another company is `403 COMPANY_NOT_ALLOWED`, nothing is sent), `items` (`material`, `quantity` as string, `quantity_unit`).
- `GET /sales-orders?top=20&skip=0` lists newest first: `{orders, total}`, only orders of the user's companies; every order has `company_code` and `country`.
- Errors: `401` no or bad login cookie, `403` no `sales` role, `422` with `VALIDATION_FAILED` (and `details`) or `INVALID_QUERY`, `503` `SAP_UNAVAILABLE`. Branch on `code`, never on `message`.

## Run
```
JWT_SECRET=<same as auth-api> uv run --package workspace-api workspace-api
```
Port 8002. `FRONTEND_URL` (default `http://localhost:5173`) is the allowed CORS origin. It refuses to start without `JWT_SECRET`.

## Test
```
uv run --package workspace-api --with pytest pytest apps/workspace-api -v
```
Tests never call the network; the butterfly gateway is tested with `httpx.MockTransport`.

## Order queue
`POST /v1/workspace/sales-orders` tries SAP at once. If SAP cannot take the order it is saved and a worker posts it later; if SAP may or may not have created it, it is saved as `unknown` and never sent again. See `specs/notes.md` (order queue) for the rules. Check an order with `GET /v1/workspace/sales-order-requests/{id}` or list your open ones with `?open=true`.

Settings (defaults assume SAP takes one write at a time, raise them when the real limits are known): `SAP_WRITE_LIMIT` (1), `SAP_WRITE_WAIT_SECONDS` (2), `ORDER_WORKERS` (1, 0 turns the worker off), `ORDER_MAX_ATTEMPTS` (8), `ORDER_DB` (`orders.db` in the app folder).

## Purchase requisitions (workspace-web contract)
`create_app(..., requisitions=PurchaseRequisitionGateway)`; `run.py` wires `ButterflyPurchaseRequisitionGateway` (`SAP_REQUISITION_URL`, `SAP_RELEASE_URL`, default butterfly on port 8003). Plants of each company are the `plants_by_company` setting (`INA1` 1000, `INA2` 2000, `INA3` 3000: placeholders).

Routes under `/v1/workspace`:
- `POST /purchase-requisitions` (role `purchase`): `{description, items: [{material, plant, quantity, unit, delivery_date, text?}]}` gives `201` with the requisition. A plant of another company is `403 COMPANY_NOT_ALLOWED`.
- `GET /purchase-requisitions?top=20&skip=0` and `GET /purchase-requisitions/{number}` (roles `purchase`, `management`): the user's companies only, newest first, `{requisitions, total}`; a requisition of another company is `404`.
- `POST /purchase-requisitions/{number}/release` (role `management`, the approver role until named): `{release_code, item?}` gives the requisition with the new statuses.

A requisition: `purchase_requisition`, `description`, `created_by_user`, `created_on`, `total_net_amount`, `items`. An item: `item`, `material`, `text`, `plant`, `company_code`, `quantity`, `unit`, `net_amount`, `currency`, `delivery_date`, `release_status` (`not_released`, `in_release`, `released`), `release_status_code` (`01`, `02`, `03`), `ordered`, `deleted`, `purchase_order`.

Errors: `401`, `403`, `404 NOT_FOUND`, `422 VALIDATION_FAILED` with `details` (`code`, `target`, `message`; targets are `items/0/material`, `items/1/quantity`, `release_code`, `item`), `503 SAP_UNAVAILABLE`. There is no queue for requisitions: the user retries on `503`. The list reads up to 1000 requisitions from SAP and filters and pages here.

Tests that use butterfly in process need it installed: `uv run --package workspace-api --with pytest --with-editable apps/butterfly pytest apps/workspace-api`. `test_order_queue_butterfly.py::test_an_order_refused_three_times_is_posted_once_when_sap_recovers` fails on `main` too (order number 12033 against 12031, the small seed grew).
