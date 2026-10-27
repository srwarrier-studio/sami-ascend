# Roadmap

One section per app. Each line is a phase: number, name, one-sentence goal, status.
Status: `todo` or `done` (tag, date). Open phases are the branches named `<app>/phase-*`.

First slice is Sales. Workspace enters sales orders, synapse shows them, within 5 minutes.
Everything runs against butterfly (mock SAP) until the real RAP services exist.

Build order for the first slice: butterfly 01-02 (done), workspace-api 01-02 (done), shared 06, workspace-web 01-02
(create an order from the browser), then butterfly 03, synapse-api 01-03, synapse-web 01-03.
workspace-web 03 and shared 04-05 can follow.

## shared
- 01 sales-odata-contract: agree the OData V4 Sales service (entities, fields, query options, error format) in `docs/sap/`. done (tag `shared-phase-01-done`, 2026-10-27)
- 02 token-verification: one package every API uses to check the login cookie. done (tag `shared-phase-02-done`, 2026-10-27)
- 03 structured-logging: JSON logs with a request id across services. done (tag `shared-phase-03-done`, 2026-10-27)
- 04 sap-identity-decision: decide who posts in SAP for workspace writes (real user or technical user) and record it. todo
- 05 sales-end-to-end: prove an order entered in workspace shows in synapse within 5 minutes. todo
- 06 ui-kit: `packages/ui` with the Mantine provider, shared styling and wrappers every web app imports (each app supplies only its own color palette), plus a TanStack Charts wrapper and a short size and memory comparison against Recharts. todo

## butterfly (mock SAP, FastAPI, OData V4)
- 01 scaffold-sales-read: serve `SalesOrder` with `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count` from seed data. done (tag `butterfly-phase-01-done`, 2026-10-27)
- 02 sales-write: create and change a sales order, with validation errors in the OData V4 error format. done (tag `butterfly-phase-02-done`, 2026-10-27)
- 03 sales-summaries: read-only summary entities for dashboard totals (by day, customer, material). todo
- 04 failure-modes: configurable delays, errors and timeouts so the apps handle SAP being slow or down. todo

## SAP consultant guide (`docs/sap/`, written from the contract, one phase each)
- Phases belong to the `butterfly` section but produce documents: 05 rap-sales-read-guide (CDS view entity, projection, service definition and binding for OData V4), 06 rap-sales-write-guide (behavior definition, validations, determinations), 07 rap-summary-views-guide (summary CDS views for dashboards). todo

## auth-api
- 00 auth-foundation: password and Entra login, JWT cookie, roles, SQLite store, create-admin CLI. done (commits `0486a36`, `04312fe`)
- 01 login-audit: record login success and failure in `audit_log`. todo
- 02 admin-endpoints: list, create, disable users and change roles, admin only. todo
- 03 entra-only-admins: allow users without a password so admins sign in through Entra (MFA). todo

## synapse-api (dashboard backend)
- 01 sales-source: an interface to read sales data, with an implementation that calls butterfly. todo
- 02 sales-kpis: use cases for today, month-to-date, year-to-date, top customers and materials; cached and refreshed every 5 minutes. todo
- 03 dashboard-routes: role-checked routes that return the data each catalog widget needs (month-on-month sales, day sales, recent high-value sales, top customers and materials). todo
- 04 board-storage: each user's own boards (name, widgets with name, props and grid position), saved in SQLite behind a repo, with list, create, rename, delete and save-layout routes. todo

## synapse-web (management dashboards)
- 01 shell-and-login: app shell, login page, and the "not allowed" page, using `/me`. todo
- 02 widget-catalog: the predefined sales widgets (MoM sales, day sales, recent high-value sales table, top customers and materials) built on the `@sami/ui` registry from shared/06. todo
- 03 board: a free board per user with drag, resize and a widget picker, saved through the board API, widgets auto-refresh every 5 minutes, no dropdown filters. todo
- 04 ai-ready-review: check widgets against the AI dashboard needs before the POC. todo

## workspace-api (workflow backend)
- 01 sales-order-gateway: an interface to create and list sales orders, with an implementation that calls butterfly. done (tag `workspace-api-phase-01-done`, 2026-10-27)
- 02 sales-order-routes: role-checked routes for creating and listing orders. done (tag `workspace-api-phase-02-done`, 2026-10-27)

## workspace-web (department users)
- 01 shell-and-login: app shell, login page, menu by role. todo
- 02 sales-order-entry: form to enter a sales order with clear validation messages. todo
- 03 sales-order-list: list and open the user's recent orders. todo

## ai-dashboard (POC, later, local-first)
- Not scheduled. Starts after synapse-web 03. See `notes.md` for the constraints. todo

## admin page
Lives in a web app, to be placed once the web apps are further along. Depends on auth-api 02.
