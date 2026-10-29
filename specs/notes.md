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
- `tests/test_contract.py` reads field tables and examples from `docs/sap/sales-contract.md`. Add new contract examples there and they are checked automatically.
- Tests are grouped in classes named for the use case (`pytest -v` is the coverage list). Run: `uv run --package butterfly --with pytest --with httpx pytest apps/butterfly -v`.

## butterfly writes
- `POST SalesOrder` validates everything in `NewOrderValidator` and returns all problems at once, ordered: not-allowed fields, header fields, items. Nothing is stored and no number is used when any problem exists. Number is `max + 1`, so the first new order is `0000012031`.
- `PATCH` checks in this order: order exists (404), `If-Match` present (428), etag equal to the current one (412), then the body (400). Only `RequestedDeliveryDate` can change; `A` and `B` orders only.
- `SalesOrder.etag` is derived from `LastChangeDateTime`. A change sets it to the later of now and the old value plus one second, so two changes in one second still get different etags.
- Reference data (`MasterDataRepo`) is the seed customers and materials; `INR` only; a material has one unit and one price. `CreatedByUser` is always `BUTTERFLY` until shared/04.
- Unknown paths and wrong methods return `RESOURCE_NOT_FOUND` / `METHOD_NOT_ALLOWED` in the error format. Any new exception type needs its own handler or it falls to the 500 middleware.
- Tests that need a fixed clock use `create_app(repo, now=...)`; `make_client()` in `tests/conftest.py` already does.
- `tests/test_contract_writes.py` replays the contract's POST and PATCH examples and checks that every detail code listed in the contract can be produced.

## butterfly summaries
- Three use cases (`SummarizeByDay`, `SummarizeByCustomer`, `SummarizeByMaterial`) read `SalesOrderRepo.list_all()` on every request and group in memory; nothing is stored. Rows come back sorted by date, then party or material, then currency.
- Cancelled (`X`) orders are excluded everywhere (consultant question 11). Material rows sum item quantity and amount; the unit and description come from the first item, which is safe because a material has one unit.
- `ListSalesSummary(summarize, fields)` applies the query options through `apply_list_query`; `add_summary_route` in `entrypoint/app.py` registers each entity. `OrderCount` uses the numeric filter type. Read by key is a 404; `$expand` is `UNSUPPORTED_QUERY_OPTION`.

## ui-kit (`packages/ui`, `@sami/ui`)
- Source-only package (`main` is `src/index.ts`), compiled by each app's Vite. Apps import only from `@sami/ui`; add a new Mantine component by re-exporting it from `src/index.ts`. Defaults live in the theme in `UiProvider.tsx`, not in wrappers.
- Style rule is tested: `tests/theme-only.test.ts` bans inline styles, hex/rgb colors and px values in `src/` and `playground/`. The TanStack SVG writes its own `style="display:block;overflow:visible"`; that is the library's.
- Chart colors: `src/charts.css` maps TanStack's `--ts-chart-1..6` to Mantine color variables, so palettes recolor charts.
- Registry (`src/registry.tsx`): one entry per widget with a zod schema, description and size hints. A new widget is one entry plus its component. Props must stay JSON-only. OpenUI is not integrated; `registry.describe()` feeds either OpenUI or schema-constrained JSON in the AI POC.
- Jsdom needs `matchMedia` and `ResizeObserver` stubs (`tests/setup.ts`); charts need `initialWidth` to render there.
- TanStack Charts vs Recharts (spike, 2026-10-27, 6 charts of 30 points, headless Chrome, heap after GC, 5 runs): chart code 39.7 kB gzip vs 102.7 kB, React excluded in both. JS heap about 2.3 MB vs 8.7 MB. DOM nodes 845 vs 1452. Both draw SVG; the gap is library overhead, not raster vs vector. The spike was plain charts without Mantine and was thrown away.
- Run: `pnpm --filter @sami/ui test`; `pnpm --filter @sami/ui dev` opens the playground.
- Soft theme (shared/08): `createSharedTheme('soft' | 'sharp')` builds the theme; soft is inputs 6, menus and tiles 12, cards and modals 16, buttons pill, sharp is 4 everywhere. Mantine omits CSS variables equal to its own defaults, so test the theme object, not the generated CSS.
- Palettes come from the approved Synapse kitchen sink artifact (https://claude.ai/artifact/FyrY7tQuC9m18kTE6mME5R): `presets` teal, blue, indigo, graphite, copper, each with `brand`, a slate `gray` and a `dark` scale; filled shade 6 reads at 4.5:1 with white (tested). `synapsePalette` is teal, `workspacePalette` is blue; the owner picks the final presets.
- Motion is plain CSS in `src/motion.css`, switched by `data-motion` on the root (`UiProvider` `motion` prop). Full: hover lift and chart wipe; no card entrance animation (the owner finds rise-up old-fashioned). Minimal and `prefers-reduced-motion`: no animation, 120 ms transitions. Framer-motion is not used; revisit in synapse-web 03 if widget exit or reorder animation needs it.
- `AppFrame` `layout` is `top` (synapse) or `side` (default). workspace-web does not import `AppFrame` yet, so its tests do not cover it; `tests/appframe.test.tsx` does.
- Playground: `playground/ThemeLab.tsx` holds the switches, `playground/TokensSection.tsx` the tokens; `tests/playground.test.tsx` renders every section under each preset, radius and motion setting.
- Chart widgets (shared/09): eleven registered widgets, all standardized, data and text props only. Colors come from `src/charts.css` (`--ts-chart-1..6` and `--sami-positive/caution/negative`, deepened with `light-dark()` so they suit both themes); series 1 is the palette primary, 2 is gray, 3 a lighter brand tint.
- TanStack Charts findings: bars are `path`, heatmap cells are `rect`; `fill`, `radius.stack` and similar are plain values, so shading uses a categorical `color` channel with a `color-mix()` range, never one mark per shade (the library builds a band axis order from the marks in sequence and the columns came out reversed in the browser, not in jsdom). A band scale needs a configured instance (`scaleBand().domain(...)`), not a factory, to keep a fixed order. `radius: { stack: 'outer' }` fails with a group layout. Tooltips take options as `tooltip: { use: tooltip, format }`. Axis labels use `ticks.format` and `tickLabels.thin.keep` so the month names are not thinned away.
- jsdom does not prove layout: check charts in headless Chrome (`google-chrome --headless=new --screenshot` or `--dump-dom`) before calling them done.
- Donut and gauge use the library's polar marks (`pie`, `radialArc`, `radialText`); the legend, sparkline and heat ramp are small HTML or SVG parts of our own. Compact axis labels use K and M (`formatCompact`); lakh and crore labels would be a one-line change.
- Calendar heatmap: weeks start Monday, the range is first to last date given, days with no value are empty cells, the last value wins for a repeated date. Hover text comes from `dayLabel`.
- Info popover: `help.ts` holds one function per widget type that takes the measure (default "the value"); `WidgetTitle` shows it; `info` replaces only "What it shows". A vague measure gives a vague sentence, so each catalog entry in synapse-web should set one.
- Decisions: no card rise-in animation (owner dislikes it); board tabs are the user's own boards with rename only in Edit mode; the bottom `PageBar` (three tabs visible, rest scroll, quick config on the right) is planned in shared/10.
- Parity (shared/10): `Alert` wraps Mantine's with a tone icon; `SplashScreen`, `SignInCard`, `WidgetCatalog` and `PageBar` take text and callbacks only (state lives in the app). `PageBar` is fixed at the bottom, three 8rem tabs visible, rest scroll; rename only when `editing`. Differences from the artifact are in `docs/ui-parity.md`. The playground opens a page from the URL hash (`#kitchen`).

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
- Order entry (`/sales-orders/new`): `src/orderForm.ts` holds the pure form logic (defaults, add/remove rows, request body, `mapDetails`); the page only wires it. `SalesOrderClient` reaches pages through router context, so tests pass a fake.
- SAP error `target` maps to fields: `SoldToParty` and the other header names, `_Item/<n>/Quantity` (zero-based row). Anything unmatched, such as `NO_ITEMS`, shows in the alert above the form. Branch on `code`, never on `message`.
- Customer, material and unit are free text until lookup endpoints exist; SAP is the validator.
- `tests/theme-only.test.ts` bans `@mantine/*` imports and inline styles in `src/`.

## synapse-api (`apps/synapse-api`)
- Source: `SalesSource` has the three summary reads and `high_value_orders(minimum, top)`. `ButterflySalesSource` takes `Settings` and an optional `httpx` transport (tests pass `MockTransport`). Adding up days, ranking and caching are phase 02.
- Query strings are built by hand with `%20`, as in workspace-api. `X-Request-ID` is sent only when `get_request_id()` has a value.
- Any status other than `200` and a body without `value` are `SapUnavailable`. `401`/`403` from SAP are not mapped yet; decide with shared/04.
- A null `CustomerName` or `MaterialDescription` becomes `""`, so entities keep plain `str`.
- High-value orders are limited by `$top` only; there is no paging past it.
- `setup_logging("synapse-api")` runs when `synapse_api.entrypoint` is imported, so the app and runner are always imported from there.
- Run: `uv run --package synapse-api --with pytest pytest apps/synapse-api -v`.
- KPIs (phase 02): use cases are built with a `SalesSource` and take `today` in `execute`, so a long-lived instance never holds yesterday's date. Everything is per currency, never added across currencies; `top` applies to each currency separately. Limits: `top` 1..50, `months` 1..24, otherwise `InvalidQuery` (phase 03 maps it to 422).
- Month-on-month gives every currency seen in the range a row for every month, zero when empty. Customer totals take the name from the first row, materials take unit and description from the first row.
- `SalesCache.get(key, load)` refreshes on read, not on a timer (`CACHE_SECONDS`, default 300). On `SapUnavailable` it returns the old value and logs a warning; with nothing stored it raises. Include `today` in the key where the result depends on it. It has a lock, since FastAPI runs sync routes in threads; the lock is held during the SAP call, so one slow call delays every route.
- Routes (phase 03): `/v1/synapse/sales/{today,month-to-date,year-to-date,month-on-month,top-customers,top-materials,high-value-orders}`, `management` and `admin` only. `create_app(source, settings, today, cache)` builds the cache from `CACHE_SECONDS` unless a test passes one with its own clock. The cache key is route name, `today` and query values; `InvalidQuery` is raised inside the loader, so it is 422 and never cached.
- Errors match workspace-api: 422 `INVALID_QUERY` with `message`, 503 `SAP_UNAVAILABLE` without detail. `MockSalesSource` counts calls (`calls`) and `recover()` undoes `fail()`.
- Run: `uv run --package synapse-api synapse-api` (port 8004; exits if `JWT_SECRET` is empty). CORS allows `FRONTEND_URL` (default `http://localhost:5173`) with credentials. Do not clear the lists a test passes to `MockSalesSource`; it keeps the same list object, and test modules share them.

## synapse-web (`apps/synapse-web`)
- Same structure as workspace-web: `App` takes a client and optional history; routes guard with `beforeLoad`; `Shell` uses `AppFrame` top layout. All UI from `@sami/ui`.
- Session is `SessionClient` (`me`, `login(email, password)`, `logout`); only `MockSessionClient` exists (password `mock`; `manager@`, `admin@`, `sales@mock-sami.com`). It becomes the contract for the real auth calls later. `canUseSynapse` allows `management` and `admin`.
- Run: `pnpm --filter synapse-web test`, `pnpm --filter synapse-web dev`.
- Widget catalog (synapse-web/02): `SalesData` (mock only) mirrors the synapse-api routes plus `daySales` and `statusSplit`, which have no route yet and need designing in synapse-api 04. `catalog` entries are `{ id, title, description, widget, load(data) }`; `load` returns registry props. `CatalogWidget` handles loading and errors. `/widgets` shows all entries.
- Board (synapse-web/03): `BoardStore` (`list`, `create`, `rename`, `remove`, `saveWidgets`) is the contract for synapse-api 04; a board is `{ id, name, widgets: { id, catalogId }[] }` and widget order is the layout (no x/y; each widget spans its registry `defaultW` of 12 columns, full width below `lg`). Drag is native HTML drag and drop plus earlier/later buttons for keyboards; no resize. The board title is renamed in the `PageHeader` in Edit mode (`PageBar` only selects, adds and sets quick config). AI Mode is a keyword match over the catalog, a stand-in for the AI POC. `CatalogWidget` reloads every 5 minutes (`REFRESH_MS`). UI palette and motion live in `main.tsx` state and reach pages through router context (`ui`, `setUi`); colour scheme uses `useColorScheme` from `@sami/ui`.
- AI readiness (synapse-web/04): findings in `docs/ai-ready-review.md`. `registry.validate` and `parseAiBoard` (`src/ai/`) check a model's board JSON. For the POC the model should pick catalog ids and fill text only, not data.
- Boards are limited to 3 (`MAX_BOARDS` in `useBoards`); a fourth `+ Add` shows the notification "Only 3 sheets allowed". The store itself does not enforce it, so synapse-api 04 must too.
- Toasts show at the top centre (`Notifications position` in `UiProvider`); bottom-right was missed because the PageBar sits at the bottom centre.
- Bento grid: board rows are a fixed 4.5rem unit (`grid-auto-rows`, dense) and each widget spans registry `defaultW` columns by `defaultH` rows; every widget card fills its cell (`.card`), charts measure the free height (`ChartCard`, min = their `height`), KPI cards reserve the delta line. Standard sizes: KPI 3x2, ranked, donut and gauge 4x4, charts 6x4, table and calendar 12x4.
