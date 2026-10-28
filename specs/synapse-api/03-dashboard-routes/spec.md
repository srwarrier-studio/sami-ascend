# synapse-api/03 dashboard-routes

## Goal
synapse-api serves the sales numbers to management users through role-checked, cached HTTP routes.

## Behavior
- **Access:** roles `management` and `admin` may call every route; any other role gets 403, no cookie 401 (from `AuthDependencies`).
- **Routes** (prefix `/v1/synapse`, tag "Sales", all `GET`, `today` is the server date):
  - `/sales/today`, `/sales/month-to-date`, `/sales/year-to-date` → `{"totals": [{start, end, net_amount, order_count, currency}]}`
  - `/sales/month-on-month?months=12` → `{"months": [{year, month, net_amount, currency}]}`
  - `/sales/top-customers?top=5` → `{"customers": [{customer, name, net_amount, order_count, currency}]}`
  - `/sales/top-materials?top=5` → `{"materials": [{material, description, quantity, unit, net_amount, currency}]}`
  - `/sales/high-value-orders?minimum=100000&top=5` → `{"orders": [{order, customer_name, order_date, net_amount, currency, status}]}`
- Amounts are `Decimal` in the response models, as in workspace-api.
- **Caching:** each route reads through `SalesCache`; the key holds the route name, `today` and the query values.
- **Errors:** `InvalidQuery` → 422 `INVALID_QUERY`; `SapUnavailable` → 503 `SAP_UNAVAILABLE` (no SAP detail), same shapes as workspace-api.
- **Wiring:** `create_app(source, settings)` in `entrypoint/app.py`; `entrypoint/run.py` builds `ButterflySalesSource`, exits if `JWT_SECRET` is empty, serves on port 8004. CORS for `FRONTEND_URL`, `RequestIdMiddleware` outermost, `setup_logging("synapse-api")` in `entrypoint/__init__.py`.
- **New dependencies:** `fastapi`, `uvicorn`, `token-verification` (workspace), already used by workspace-api. `Settings` gains `jwt_secret` and `frontend_url`.
- `SalesCache` gets a lock, since FastAPI runs sync routes in threads.

## Acceptance cases
- Each route returns the documented body for a `MockSalesSource` and a fixed `today`.
- `management` and `admin` get 200; `sales` gets 403; no cookie gets 401.
- `top=0`, `top=51`, `months=0`, `months=25` give 422 `INVALID_QUERY`.
- A failing source gives 503 `SAP_UNAVAILABLE`; after one good call, a failing refresh still gives 200 with the old value.
- Two calls inside the cache time hit the source once; different query values do not share a cached result.
- The request id is returned in `X-Request-ID`.

## Out of scope
Board storage (phase 04), per-user data, filters beyond the query values above, `/me`, a background refresher, running against real butterfly (shared/05).

## Depends on
synapse-api 01 and 02 (done), shared 02 and 03 (done).
