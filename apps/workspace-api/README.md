# workspace-api

Workflow backend for department users. Serves sales order routes to the workspace web app. Only users with the `sales` role may call them; an absent user's stand-in is given the `sales` role by an admin.

## Gateway
`SalesOrderGateway` (in `domain/gateways`) has `create(NewSalesOrder)` and `list_recent(top, skip)`. Use cases `CreateSalesOrder` and `ListSalesOrders` wrap it.

- `ButterflySalesOrderGateway` calls the Sales OData V4 contract in `docs/sap/sales-contract.md`. Set `SAP_BASE_URL` (default: butterfly on `http://localhost:8003` with the contract root path).
- `MockSalesOrderGateway` keeps orders in memory for tests; `reject_with(details)` makes the next creates fail.
- `SalesOrderRejected` carries every validation detail (branch on `code`); `SapUnavailable` covers timeouts, connection errors and `5xx`.

## Routes (`/v1/workspace`)
- `POST /sales-orders` creates an order, `201` with the order. Body: `sales_order_type`, `sold_to_party`, `transaction_currency`, `requested_delivery_date` (optional), `items` (`material`, `quantity` as string, `quantity_unit`).
- `GET /sales-orders?top=20&skip=0` lists newest first: `{orders, total}`.
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
