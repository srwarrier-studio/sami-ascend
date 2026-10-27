# workspace-api/02 sales-order-routes

## Goal
workspace-api serves role-checked HTTP routes to create and list sales orders, using the phase 01 use cases and gateway.

## Behavior
- **Routes** (prefix `/v1/workspace`, tag `Sales orders`):
  - `POST /sales-orders` creates an order. `201` with the order.
  - `GET /sales-orders?top=20&skip=0` lists recent orders, newest first. `200` with `{ "orders": [...], "total": n }`.
- **Access:** login cookie checked by `AuthDependencies` from `token-verification` (same `JWT_SECRET` as auth-api). Allowed role: `sales` only, for both routes. `admin` is not allowed. A stand-in for an absent sales user is given the `sales` role by an admin (auth-api 02); no delegation code here. No cookie or bad token is `401`; wrong role is `403`.
- **JSON shape:** snake_case field names matching the domain entities. Decimals are strings (`"50.000"`), dates are `YYYY-MM-DD`, timestamps are UTC ISO with `Z`. Request body: `sales_order_type`, `sold_to_party`, `transaction_currency`, `requested_delivery_date` (optional), `items` (`material`, `quantity` as string, `quantity_unit`). Response order adds the read-only fields of `SalesOrder`, with `items`.
- **Errors:**
  - `SalesOrderRejected` is `422` with `{ "code": "VALIDATION_FAILED", "details": [{ "code", "target", "message" }] }`, details in the order SAP returned them.
  - `ValueError` from `ListSalesOrders` (bad `top` or `skip`) is `422` with `INVALID_QUERY`.
  - Malformed request body is FastAPI's default `422`.
  - `SapUnavailable` is `503` with `{ "code": "SAP_UNAVAILABLE" }`. No SAP detail leaks to the browser.
  - Web apps branch on `code`, never on `message`.
- **Wiring:** `entrypoint/app.py` builds the app, CORS for `FRONTEND_URL` with credentials, `RequestIdMiddleware` added last. Gateway is built from `Settings` and injected through a FastAPI dependency so tests can swap in `MockSalesOrderGateway`. `Settings` gains `JWT_SECRET` and `FRONTEND_URL`.
- **Run:** `workspace-api` script starts uvicorn on port 8002 with `log_config=None`.
- **Logging:** the app is imported from `workspace_api.entrypoint`, so `setup_logging` runs. No order content in logs.
- **Dependencies:** `fastapi[standard]` and `token-verification` (workspace package) added to `workspace-api`; no new third-party package.

## Acceptance cases
Tests use `TestClient`, `MockSalesOrderGateway` and tokens signed with a test secret. No network.
- No cookie is `401` on both routes; a token without `sales` (including `admin` alone) is `403`; a token with `sales` passes, also when it has other roles too.
- Create with a valid body returns `201` with the order number, status `A` and items; decimals stay exact.
- Create rejected by the gateway returns `422` `VALIDATION_FAILED` with every detail in order.
- Malformed create body (missing field, non-numeric quantity) is `422` and the gateway is not called.
- List returns newest first with `total`; `top` and `skip` page correctly; defaults are 20 and 0.
- `top=0`, `top=101`, `skip=-1` return `422` `INVALID_QUERY`.
- `SapUnavailable` on either route returns `503` `SAP_UNAVAILABLE`.
- Responses carry `X-Request-ID`.

## Out of scope
Delegation or acting-for another user (use the role grant instead), change order, single-order read, order lookup by number, per-user filtering of the list, audit log, SAP identity (shared/04), `401`/`403` from SAP, rate limiting, running against real butterfly (shared/05).

## Depends on
workspace-api 01 (done), shared 02 token-verification (done), shared 03 structured-logging (done), auth-api 00 (done, for the cookie).
