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
- 11 bar-labels: value labels above bars (whole lakhs, no decimals or rupee sign, 16 bars or fewer) on `BarChart` with a `valueLabels` switch, and the compact number format changed to the Indian system (K, L, Cr) everywhere. done (tag `shared-phase-11-done`, 2026-10-31).
- responsive-check (planned, number later): look at every Synapse screen at phone, tablet and desktop widths (login, company picker, app bar with the company pill, boards and bar labels, widget drawer, modals, AI Mode) and fix what breaks. todo

## butterfly (mock SAP, FastAPI, OData V4)
- 01 scaffold-sales-read: serve `SalesOrder` with `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count` from seed data. done (tag `butterfly-phase-01-done`, 2026-10-27)
- 02 sales-write: create and change a sales order, with validation errors in the OData V4 error format. done (tag `butterfly-phase-02-done`, 2026-10-27)
- 03 sales-summaries: read-only summary entities for dashboard totals (by day, customer, material). done (tag `butterfly-phase-03-done`, 2026-10-27)
- 04 failure-modes: configurable delays, errors and timeouts so the apps handle SAP being slow or down. todo
- 08 driver-data: a second read-only OData service (customer contracts, supplier deliveries, production orders and components, from `docs/sap/drivers-contract.md`) and a 14-month sales history with a built-in story that explains the August 2026 sales fall (`BUTTERFLY_SEED=story`, the default), so the AI analysis in `docs/ai-analysis.md` can be built before the SAP views exist. done (tag `butterfly-phase-08-done`, 2026-10-31).
- 09 scenarios: several mock sales stories chosen with `BUTTERFLY_SCENARIO` (price cut, a late supplier with no sales effect, a customer lost with no contract event, a machine breakdown, a quiet month), each with a written ground truth, and two held back for the final test, so the AI analysis is tested on more than one story. todo

## SAP consultant guide (`docs/sap/`, written from the contract, one phase each)
- Phases belong to the `butterfly` section but produce documents: 05 rap-sales-read-guide (CDS view entity, projection, service definition and binding for OData V4), 06 rap-sales-write-guide (behavior definition, validations, determinations), 07 rap-summary-views-guide (summary CDS views for dashboards). todo

## auth-api
- 00 auth-foundation: password and Entra login, JWT cookie, roles, SQLite store, create-admin CLI. done (commits `0486a36`, `04312fe`)
- 01 login-audit: record login success and failure in `audit_log`. todo
- 02 admin-endpoints: list, create, disable users and change roles, admin only. todo
- 03 entra-only-admins: allow users without a password so admins sign in through Entra (MFA). todo
- 04 user-companies: each user has the companies they may see (Sami Sabinsa Group Company, Sami Neutraceuticals Private Limited, Organica Aromatic; most users one, a CFO several), carried by `/me` and the token. done (tag `auth-api-phase-04-done`, 2026-10-30).
- Later, not scheduled: filter SAP data and boards by company (each company maps to an SAP company code).

## synapse-api (dashboard backend)
- 01 sales-source: an interface to read sales data, with an implementation that calls butterfly. done (tag `synapse-api-phase-01-done`, 2026-10-27)
- 02 sales-kpis: use cases for today, month-to-date, year-to-date, top customers and materials; cached and refreshed every 5 minutes. done (tag `synapse-api-phase-02-done`, 2026-10-28).
- 03 dashboard-routes: role-checked routes that return the data each catalog widget needs (month-on-month sales, day sales, recent high-value sales, top customers and materials). done (tag `synapse-api-phase-03-done`, 2026-10-28).
- 04 board-storage: each user's own boards (name, widgets with name, props and grid position), saved in SQLite behind a repo, with list, create, rename, delete and save-layout routes. Postponed: designed after synapse-web 03, from the board store the mock settles on. todo
- 05 catalog: the widget catalog and each widget's ready-to-render props served from synapse-api (`/v1/synapse/catalog`), sales entries from the sales source and the other domains from a mock library. done (tag `synapse-api-phase-05-done`, 2026-10-30).
- 07 summary-paging: read every sales summary completely with `$top` and `$skip`, so months after the first 100 days no longer show 0 against butterfly's story seed or the real SAP page size. done (tag `synapse-api-phase-07-done`, 2026-10-31).
- 08 compare (planned): the metric layer: compare a metric between two periods split by a dimension (customer, material), volume against price, and a month's figure with its trend; generic, not one endpoint per question. Depends on butterfly 09. todo
- 09 events (planned): one generic read of the rows of a node type (contract, production order, purchase delivery) for a key and a time window, from butterfly and later the SAP views. Depends on butterfly 09. todo

## synapse-web (management dashboards)
All three phases use mock data (session, sales data and board store behind interfaces); no synapse-api calls yet.
- 01 mock-shell: app shell in the soft look, mock login and `/me` session, the "not allowed" page, route guards. Depends on shared 08. done (tag `synapse-web-phase-01-done`, 2026-10-29).
- 02 widget-catalog: the predefined sales widgets (MoM sales, day sales, recent high-value sales table, top customers and materials, status split, KPI cards) on the `@sami/ui` registry, fed by the mock sales data. done (tag `synapse-web-phase-02-done`, 2026-10-29).
- 03 board: the user's own boards as tabs with an Edit mode (rename, add and delete boards, drag, reorder, remove, widget picker, AI Mode), saved in a mock board store, widgets auto-refresh every 5 minutes, no dropdown filters. done (tag `synapse-web-phase-03-done`, 2026-10-29).
- 04 ai-ready-review: check widgets against the AI dashboard needs before the POC. done (tag `synapse-web-phase-04-done`, 2026-10-29).
- 05 ai-chat: full-screen AI Mode chat with widgets inside answers, `@builder` board modal and save as board, on a mock planner. done (tag `synapse-web-phase-05-done`, 2026-10-30).
- 06 backend-catalog: login through auth-api, catalog and every widget's data from synapse-api, local catalog removed; the Widgets tab became a Reports placeholder. done (tag `synapse-web-phase-06-done`, 2026-10-30).
- 07 board-export: `Export PDF` on a board, one page sized to the board, raster capture at 3x with `html-to-image` and `jspdf`, placeholder logo and company name on top and a generated-by line below. done (tag `synapse-web-phase-07-done`, 2026-10-30).
- 08 company-picker: after sign-in the user chooses one of their companies (automatic for one, picker page for several), switches it from the header, and the exported PDF header carries its name and logo; the choice is remembered per user in `localStorage`, data is not filtered by company yet. done (tag `synapse-web-phase-08-done`, 2026-10-30).
- 09 preset-boards: a `Preset boards` tab in the Add widget drawer that creates a ready-made board in one click, with the replace flow at 3 boards. done (tag `synapse-web-phase-09-done`, 2026-10-30).
- 10 login-page: full-screen login with the neuron and electric-pulse animation as the background, a centred navy sign-in card and a Sign in with Microsoft placeholder button. done (tag `synapse-web-phase-10-done`, 2026-10-30).
- 11 premium-look: an opt-in premium look in `@sami/ui` (`look` prop, `midnight` palette, surface tokens, glass-like bars, refined widgets) applied to every Synapse screen, with the Synapse logo, name and tagline, and fixes to the donut labels and legend, chart tooltips, KPI fit and boards loading skeleton. done (tag `synapse-web-phase-11-done`, 2026-10-30).
- 12 ai-answers (planned): AI Mode talks to sami-agents and shows the answer as text, a chart and an evidence table, as JSON blocks drawn with the existing widgets (OpenUI is not needed for this). Depends on sami-agents 03. todo
- company-data (not numbered yet): filter synapse-api data by company and add the group view, an `All companies` choice in the picker for users with several companies that sums across them, plus widgets that split by company. All three companies are in one SAP system, so synapse-api filters and sums by company code in one query. Currency and intercompany rules still need an answer from finance. todo

## workspace-api (workflow backend)
- 01 sales-order-gateway: an interface to create and list sales orders, with an implementation that calls butterfly. done (tag `workspace-api-phase-01-done`, 2026-10-27)
- 02 sales-order-routes: role-checked routes for creating and listing orders. done (tag `workspace-api-phase-02-done`, 2026-10-27)

## workspace-web (department users)
- 01 shell-and-login: app shell, login page, menu by role. done (tag `workspace-web-phase-01-done`, 2026-10-27)
- 02 sales-order-entry: form to enter a sales order with clear validation messages. done (tag `workspace-web-phase-02-done`, 2026-10-27)
- 03 sales-order-list: list and open the user's recent orders. todo

## sami-agents (AI service for AI Mode)
- 01 chat-graph: new FastAPI service (port 8005) with the cookie-checked `POST /v1/agents/chat` route that answers in OpenUI Lang, a LangGraph graph over `ChatModel` and `CatalogSource` ports with mocks, the Ollama adapter, and an evaluation tool (`sami-agents eval`) with 22 prompts; it found that small models alone are not good enough at choosing widgets. done (tag `sami-agents-phase-01-done`, 2026-10-30).
- 02 relevance-check: keyword proposals with stemming and an alias file, an optional Laya relevance check in a propose and verify loop (off by default: it did not beat the keywords in our tests), an optional small-model sentence writer behind strict checks (off by default), widgets returned as OpenUI Lang pinned by a contract test, and an evaluation tool with a tuning set and a held-out set. done (tag `sami-agents-phase-02-done`, 2026-10-31).

- 03 answer-questions (planned): level 2 answers: the metric and period from the question, a sentence with the real figure and a trend chart, as JSON. Depends on synapse-api 08. todo
- 04 graph (planned): the entity graph as a file the owner maintains (`graph.toml`), its loader, `graph check` and `graph show`, the traversal engine in three modes (root cause, impact, dependency), and a how-to (`docs/graph-maintenance.md`). Depends on synapse-api 09 and `docs/ai-analysis.md`. todo
- 05 analyst (planned): question understanding, ranking, the validated answer, and evaluation on the butterfly scenarios including the held-back ones. Depends on sami-agents 03 and 04. todo

## ai-dashboard (POC, later, local-first)
- Not scheduled. Starts after synapse-web 03. See `notes.md` for the constraints. todo

## admin page
Lives in a web app, to be placed once the web apps are further along. Depends on auth-api 02.
