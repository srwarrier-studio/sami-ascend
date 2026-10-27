# Project notes

Knowledge kept after phases close. Add to it when a phase ends. Keep entries short.

## Project
- Management users share one read-only SAP login; the app audits who actually did what.
- Authorization data lives in SAP. The app owns roles that control which pages and APIs a user may use.

## What we are building
- **synapse:** dashboards for management. Read-only, modern, single click, near real time (5 minutes). Management rejected the Fiori dashboards as old looking, with too many dropdowns, drilldowns and filters.
- **synapse board (decided 2026-10-27):** users get a free board and add predefined widgets (MoM sales, day sales, recent high-value sales table and so on) by drag and drop. Each user has own boards only, no sharing. Widgets stay free of filters; the choice of widget is the customization. Drag and layout live in synapse-web, widgets and their size hints come from `@sami/ui`.
- **workspace:** daily-use workflow app for department users ("executives" means staff such as stores executives). Replaces SAP Logon. Users' top complaint is the old SAP Logon interface; they want more features and an easy, modern UI.
- **butterfly:** mock SAP OData V4 service in FastAPI, so the apps can be built before the ABAP side exists. Same endpoints and response shapes as the planned RAP services.
- **First slice:** Sales. An order entered in workspace must show in synapse within 5 minutes.
- **SAP consultants** have not used RAP. They need a detailed hand-holding guide with response formats. It is written from the contract in `docs/sap/`, not from memory.
- **Management wants local-first AI.** The AI dashboard is a POC with a small local model (Gemma 270M class). A model that small is unreliable at generating UI, so the plan is to let it pick from existing widgets and fill in their parameters using structured output. 
- **OpenUI** (https://www.openui.com/, by Thesys): open-source generative UI framework, React supported, works with Ollama and local models, uses its own line-based "OpenUI Lang" format. Only the home page was read; its claims (such as 58% fewer tokens than JSON) are unverified. A tiny model may follow schema-constrained JSON more reliably than a custom format, and the Gateway product is commercial. Not adopted. In the AI POC, run the same ~20 prompts with the same small model both ways (OpenUI Lang vs JSON with a schema) and keep whichever gives valid dashboards more often. Check the license and dependencies first (security checklist, supplier review).

## auth-api
- Entra gives `preferred_username` (the UPN), which may differ from the email in the user table. If Entra logins fail to match, check this first.
- The unit of work opens its connection and builds repos in `__enter__`; `__exit__` always rolls back, so use cases call `commit()` explicitly.
- Role order from the repo is sorted so token contents are stable.
- `Settings` reads the `.env` at the repo root, whatever the working directory.
- Logout only clears the cookie; tokens are not revoked server-side yet (see security checklist).
- `MockAuthUnitOfWork` has no audit repo; use `SqliteAuthUnitOfWork` with a temp file in tests that need audit.

## token-verification (`packages/token-verification`)
- Flat package, not layered: the layer rule is per backend app. `TokenVerifier`, `TokenClaims`, `Role` and `InvalidToken` never import FastAPI; `fastapi_deps.AuthDependencies` is the HTTP part.
- Each API builds `AuthDependencies(TokenVerifier(settings.JWT_SECRET))` with the same `JWT_SECRET` as auth-api. HS256 only; tokens missing `exp`, `sub`, `sap_username` or `roles`, or with an unknown role, are rejected.
- auth-api only issues tokens; verifying lives in the package. `Role` is defined once, in the package.
- Run package tests with `uv run --package token-verification --with pytest --with httpx pytest packages`.
- Secret rotation and revocation are still open (security checklist).

## structured-logging (`packages/structured-logging`)
- Flat package. `setup_logging(service)` once at import, then `app.add_middleware(RequestIdMiddleware)` added last so it is outermost. Run with `uvicorn.run(..., log_config=None)`; the `uvicorn` command installs its own plain-text log config.
- One JSON line per record: `timestamp`, `level`, `service`, `request_id`, `message`, `exception`. Access line is `METHOD path status ms`, never the query string.
- `X-Request-ID` is kept only if it matches `[A-Za-z0-9_-]{1,64}`; otherwise a UUID. Gateways should send `get_request_id()` as `X-Request-ID` on outgoing calls.
- `httpx`, `httpx2` (Starlette TestClient) and `httpcore` loggers are set to WARNING because they log full URLs with query strings.
- synapse-api and workspace-api must call it in their first phase. Tests that read log output use `caplog`; the stdout handler binds to the stream at import.
- Run tests with `uv run --package structured-logging --with pytest --with httpx --with fastapi pytest packages/structured-logging`.

## butterfly (`apps/butterfly`)
- Run: `uv run --package butterfly butterfly` (port 8003). Seed is built from today's date: 30 orders `0000012001` to `0000012030`, 2 to 3 items each. Data lives in memory behind `SalesOrderRepo`; writes add to the same repo.
- One `apply_list_query(rows, query, fields)` serves orders and items. A new entity needs only a field table in `application/filter/fields.py` (OData name, attribute, type) and a JSON mapper.
- `$filter` is a hand-written parser (`application/filter/parser.py`): `not` over `and` over `or`, lower-case operators, null fields match nothing, `any(`/`all(` rejected as unsupported.
- Errors: `INVALID_QUERY` (bad value, `target` is the option), `UNSUPPORTED_QUERY_OPTION` (400), `SALES_ORDER_NOT_FOUND` (404), `INTERNAL_ERROR` (500, `target` is the request id). The 500 is built by a middleware inside `RequestIdMiddleware`; a plain exception handler runs after the request id is cleared.
- Contract rules added while building: timestamp literals, `''` quote escape, empty values sort first ascending, `$select` follows field-table order, a single order accepts only `$expand`.
- `tests/test_contract.py` reads field tables and examples from `docs/sap/sales-contract.md`. Add new contract examples there and they are checked automatically; the summary example is skipped until butterfly/03.
- Tests are grouped in classes named for the use case (`pytest -v` is the coverage list). Run: `uv run --package butterfly --with pytest --with httpx pytest apps/butterfly -v`.

## butterfly writes
- `POST SalesOrder` validates everything in `NewOrderValidator` and returns all problems at once, ordered: not-allowed fields, header fields, items. Nothing is stored and no number is used when any problem exists. Number is `max + 1`, so the first new order is `0000012031`.
- `PATCH` checks in this order: order exists (404), `If-Match` present (428), etag equal to the current one (412), then the body (400). Only `RequestedDeliveryDate` can change; `A` and `B` orders only.
- `SalesOrder.etag` is derived from `LastChangeDateTime`. A change sets it to the later of now and the old value plus one second, so two changes in one second still get different etags.
- Reference data (`MasterDataRepo`) is the seed customers and materials; `INR` only; a material has one unit and one price. `CreatedByUser` is always `BUTTERFLY` until shared/04.
- Unknown paths and wrong methods return `RESOURCE_NOT_FOUND` / `METHOD_NOT_ALLOWED` in the error format. Any new exception type needs its own handler or it falls to the 500 middleware.
- Tests that need a fixed clock use `create_app(repo, now=...)`; `make_client()` in `tests/conftest.py` already does.
- `tests/test_contract_writes.py` replays the contract's POST and PATCH examples and checks that every detail code listed in the contract can be produced.

## ui-kit (`packages/ui`, `@sami/ui`)
- Source-only package (`main` is `src/index.ts`), compiled by each app's Vite. Apps import only from `@sami/ui`; add a new Mantine component by re-exporting it from `src/index.ts`. Defaults live in the theme in `UiProvider.tsx`, not in wrappers.
- Style rule is tested: `tests/theme-only.test.ts` bans inline styles, hex/rgb colors and px values in `src/` and `playground/`. The TanStack SVG writes its own `style="display:block;overflow:visible"`; that is the library's.
- Chart colors: `src/charts.css` maps TanStack's `--ts-chart-1..6` to Mantine color variables, so palettes recolor charts.
- Registry (`src/registry.tsx`): one entry per widget with a zod schema, description and size hints. A new widget is one entry plus its component. Props must stay JSON-only. OpenUI is not integrated; `registry.describe()` feeds either OpenUI or schema-constrained JSON in the AI POC.
- Jsdom needs `matchMedia` and `ResizeObserver` stubs (`tests/setup.ts`); charts need `initialWidth` to render there.
- TanStack Charts vs Recharts (spike, 2026-10-27, 6 charts of 30 points, headless Chrome, heap after GC, 5 runs): chart code 39.7 kB gzip vs 102.7 kB, React excluded in both. JS heap about 2.3 MB vs 8.7 MB. DOM nodes 845 vs 1452. Both draw SVG; the gap is library overhead, not raster vs vector. The spike was plain charts without Mantine and was thrown away.
- Run: `pnpm --filter @sami/ui test`; `pnpm --filter @sami/ui dev` opens the playground.

## Sales contract (`docs/sap/sales-contract.md`)
- Source of truth for butterfly, the gateways and the consultant guide. Change it first, then the code.
- Decimals are JSON strings; dates are `Edm.Date`; timestamps are UTC with `Z`; `OverallStatus` is `A`, `B`, `C`, `X`.
- Summaries are per day, one row per currency; MTD and YTD are summed by synapse-api. `$apply` is not used.
- Single-entity reads carry `@odata.etag`; `PATCH` needs `If-Match` and changes only `RequestedDeliveryDate`.
- Validation errors are one `VALIDATION_FAILED` with a `details` entry per field. Apps branch on `code`, never on `message`.
- Questions for the SAP consultants live in `docs/sap/consultant-questions.md`, not in phases. Service name and path are placeholders until confirmed.
- Check the examples with `uv run --with pytest pytest docs/sap`.


## workspace-api (`apps/workspace-api`)
- Gateway: `SalesOrderGateway` has `create` and `list_recent(top, skip)` only. `ButterflySalesOrderGateway` takes `Settings` and an optional `httpx` transport (tests pass `MockTransport`). List is newest first by `SalesOrder` descending, with `$count` and `$expand=_Item`.
- The list query string is built by hand with `%20`: `httpx` params would send `+` for spaces, which real SAP may not accept.
- `X-Request-ID` is sent only when `get_request_id()` has a value (it is `None` outside a request).
- Any unexpected status (not 201/200/400) and an unreadable `400` body are `SapUnavailable`. `401`/`403` from SAP are not mapped yet; decide with shared/04.
- `ListSalesOrders` raises `InvalidQuery` for `top` outside 1..100 or negative `skip`; routes (phase 02) turn it into 422.
- `setup_logging("workspace-api")` runs when `workspace_api.entrypoint` is imported; phase 02 must import the app from there.
- Run: `uv run --package workspace-api --with pytest pytest apps/workspace-api -v`.
- Routes (phase 02): `create_app(gateway, settings)` in `entrypoint/app.py` builds the app; tests pass `MockSalesOrderGateway`. `entrypoint/run.py` wires butterfly and starts uvicorn on 8002; it exits if `JWT_SECRET` is empty.
- Only the `sales` role may use the routes; `admin` alone gets 403. A stand-in gets the `sales` role through auth-api 02.
- `InvalidQuery` (domain error) becomes 422 `INVALID_QUERY`; `SalesOrderRejected` becomes 422 `VALIDATION_FAILED` with `details`; `SapUnavailable` becomes 503 `SAP_UNAVAILABLE` with no SAP detail.
- Route tests share `make_client` and `VALID_BODY` from `tests/test_routes_access.py`.

## workspace-web (`apps/workspace-web`)
- All UI comes from `@sami/ui`; no `@mantine/*` imports in the app. Auth calls live only in `src/api/auth.ts`; tests pass a fake `AuthClient` to `App`.
- `App` loads `/me` first, then creates the router with the loaded session. Route guards (`beforeLoad`) read the session from router context; `router.invalidate()` re-runs them when it changes (login, logout). Creating the router earlier remounts the first page.
- Menu and the `/sales-orders` guard share `allowedEntries` in `src/menu.ts`. Roles are matched with "any", so `admin` alone sees nothing.
- Tests use `createMemoryHistory`; `tests/setup.ts` copies the `@sami/ui` stubs plus `scrollTo`.
- Run: `pnpm --filter workspace-web test`.
