# Roadmap

One section per app. Each line is a phase: number, name, one-sentence goal, status.
Status: `todo` or `done` (tag, date). Open phases are the branches named `<app>/phase-*`.

First slice is Sales. Workspace enters sales orders, synapse shows them, within 5 minutes.
Everything runs against butterfly (mock SAP) until the real RAP services exist.

Build order for the first slice: butterfly 01-03 (done), workspace-api 01-02 (done), shared 06, workspace-web 01-02
(create an order from the browser), then synapse-api 01-03 (done).
Change (2026-10-28): synapse is now frontend first. shared 08, then synapse-web 01-03 run against mock data behind
small interfaces (session, sales data, board store). When the mock is final, its interfaces become the contract for
synapse-api 04 and any missing dashboard routes, which are designed then. workspace-web 03 and shared 04-05 can follow.

## shared
- 01 sales-odata-contract: agree the OData V4 Sales service (entities, fields, query options, error format) in `docs/sap/`. done (tag `shared-phase-01-done`, 2026-10-27)
- 02 token-verification: one package every API uses to check the login cookie. done (tag `shared-phase-02-done`, 2026-10-27)
- 03 structured-logging: JSON logs with a request id across services. done (tag `shared-phase-03-done`, 2026-10-27)
- 04 sap-identity-decision: decide who posts in SAP for workspace writes (real user or technical user) and record it. todo
- 05 sales-end-to-end: prove an order entered in workspace shows in synapse within 5 minutes. todo
- 06 ui-kit: `packages/ui` with the Mantine provider, shared styling and wrappers every web app imports (each app supplies only its own color palette), plus a TanStack Charts wrapper and a short size and memory comparison against Recharts. done (tag `shared-phase-06-done`, 2026-10-27)
- 07 conventions-alignment: bring every app in line with the owner's conventions. At the start the agent asks the owner what to align (known so far: HTTP routers, schemas and deps under `infrastructure/api/<domain>/`, pydantic-settings, application ports moving to the 5xxx series), then updates the constitution or conventions file from the answers before touching code. Best done after synapse-api 04 and before auth-api 01-03 add more routes. todo
- 08 ui-soft-theme: bring the approved soft look into `@sami/ui`: token source with palette presets, soft radius, a motion switch (full for synapse, minimal for workspace), and the rounded pill app shell. The kitchen sink playground shows every component and the theme switches. done (tag `shared-phase-08-done`, 2026-10-28).
- 09 ui-chart-widgets: one standardized set of chart and data widgets (line, area, bar, stacked bar, donut, gauge, heatmap, calendar heatmap, KPI with sparkline, ranked list, table) registered in `@sami/ui`, with a sample dashboard page in the playground showing every chart type, an info popover on every widget and a `measure` prop to word it. Depends on shared 08. done (tag `shared-phase-09-done`, 2026-10-29).
- 10 ui-parity-check: soft page header and alerts, launch screens, a widget catalog section, a `PageBar` of board tabs fixed at the bottom (three visible, the rest scroll, + Add, rename in Edit mode, quick config for palette, light or dark and motion), and a screenshot comparison of the playground with the approved Synapse kitchen sink artifact, every difference listed for the owner. Depends on shared 09. done (tag `shared-phase-10-done`, 2026-10-29).

## butterfly (mock SAP, FastAPI, OData V4)
- 01 scaffold-sales-read: serve `SalesOrder` with `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count` from seed data. done (tag `butterfly-phase-01-done`, 2026-10-27)
- 02 sales-write: create and change a sales order, with validation errors in the OData V4 error format. done (tag `butterfly-phase-02-done`, 2026-10-27)
- 03 sales-summaries: read-only summary entities for dashboard totals (by day, customer, material). done (tag `butterfly-phase-03-done`, 2026-10-27)
- 04 failure-modes: configurable delays, errors and timeouts so the apps handle SAP being slow or down. todo

## SAP consultant guide (`docs/sap/`, written from the contract, one phase each)
- Phases belong to the `butterfly` section but produce documents: 05 rap-sales-read-guide (CDS view entity, projection, service definition and binding for OData V4), 06 rap-sales-write-guide (behavior definition, validations, determinations), 07 rap-summary-views-guide (summary CDS views for dashboards). todo

## auth-api
- 00 auth-foundation: password and Entra login, JWT cookie, roles, SQLite store, create-admin CLI. done (commits `0486a36`, `04312fe`)
- 01 login-audit: record login success and failure in `audit_log`. todo
- 02 admin-endpoints: list, create, disable users and change roles, admin only. todo
- 03 entra-only-admins: allow users without a password so admins sign in through Entra (MFA). todo

## synapse-api (dashboard backend)
- 01 sales-source: an interface to read sales data, with an implementation that calls butterfly. done (tag `synapse-api-phase-01-done`, 2026-10-27)
- 02 sales-kpis: use cases for today, month-to-date, year-to-date, top customers and materials; cached and refreshed every 5 minutes. done (tag `synapse-api-phase-02-done`, 2026-10-28).
- 03 dashboard-routes: role-checked routes that return the data each catalog widget needs (month-on-month sales, day sales, recent high-value sales, top customers and materials). done (tag `synapse-api-phase-03-done`, 2026-10-28).
- 04 board-storage: each user's own boards (name, widgets with name, props and grid position), saved in SQLite behind a repo, with list, create, rename, delete and save-layout routes. Postponed: designed after synapse-web 03, from the board store the mock settles on. todo
- 05 catalog: the widget catalog and each widget's ready-to-render props served from synapse-api (`/v1/synapse/catalog`), sales entries from the sales source and the other domains from a mock library. done (tag `synapse-api-phase-05-done`, 2026-10-30).

## synapse-web (management dashboards)
All three phases use mock data (session, sales data and board store behind interfaces); no synapse-api calls yet.
- 01 mock-shell: app shell in the soft look, mock login and `/me` session, the "not allowed" page, route guards. Depends on shared 08. done (tag `synapse-web-phase-01-done`, 2026-10-29).
- 02 widget-catalog: the predefined sales widgets (MoM sales, day sales, recent high-value sales table, top customers and materials, status split, KPI cards) on the `@sami/ui` registry, fed by the mock sales data. done (tag `synapse-web-phase-02-done`, 2026-10-29).
- 03 board: the user's own boards as tabs with an Edit mode (rename, add and delete boards, drag, reorder, remove, widget picker, AI Mode), saved in a mock board store, widgets auto-refresh every 5 minutes, no dropdown filters. done (tag `synapse-web-phase-03-done`, 2026-10-29).
- 04 ai-ready-review: check widgets against the AI dashboard needs before the POC. done (tag `synapse-web-phase-04-done`, 2026-10-29).
- 05 ai-chat: full-screen AI Mode chat with widgets inside answers, `@builder` board modal and save as board, on a mock planner. done (tag `synapse-web-phase-05-done`, 2026-10-30).

## workspace-api (workflow backend)
- 01 sales-order-gateway: an interface to create and list sales orders, with an implementation that calls butterfly. done (tag `workspace-api-phase-01-done`, 2026-10-27)
- 02 sales-order-routes: role-checked routes for creating and listing orders. done (tag `workspace-api-phase-02-done`, 2026-10-27)

## workspace-web (department users)
- 01 shell-and-login: app shell, login page, menu by role. done (tag `workspace-web-phase-01-done`, 2026-10-27)
- 02 sales-order-entry: form to enter a sales order with clear validation messages. done (tag `workspace-web-phase-02-done`, 2026-10-27)
- 03 sales-order-list: list and open the user's recent orders. todo

## ai-dashboard (POC, later, local-first)
- Not scheduled. Starts after synapse-web 03. See `notes.md` for the constraints. todo

## admin page
Lives in a web app, to be placed once the web apps are further along. Depends on auth-api 02.
