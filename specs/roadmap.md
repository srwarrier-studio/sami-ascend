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
- 09 scenarios: several mock sales stories chosen with `BUTTERFLY_SCENARIO` (price cut, a late supplier with no sales effect, a customer lost with no contract event, a machine breakdown, a quiet month), each with a written ground truth, and two held back for the final test, so the AI analysis is tested on more than one story. done (tag `butterfly-phase-09-done`, 2026-10-31).
- 10 purchases (planned): purchase value in the drivers service (`NetAmount` on `PurchaseDelivery`, `PurchaseSummaryByDay`, `ByMaterial` and `BySupplier`), new events (purchase price change, ordered quantity change, demand growth that flows from sales through production to component purchases, supplier switch) and purchase scenarios with ground truth, two held back, so "why did purchases rise" can be built and tested. Depends on butterfly 09. done (tag `butterfly-phase-10-done`, 2026-10-31).

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
- 08 compare (planned): the metric layer: compare a metric between two periods split by a dimension (customer, material), volume against price, and a month's figure with its trend; generic, not one endpoint per question. Depends on butterfly 09. done (tag `synapse-api-phase-08-done`, 2026-10-31).
- 09 metrics-records: a registry file (`registry.toml`) names the metrics (sales now, purchases after butterfly 10) with their summary entities and dimensions, and the record types (contract, purchase delivery, production order, production component) with their key fields, date intervals and delay; generic `/metrics/{metric}/compare` and `/month` replace the sales-only routes of 08, and one `/records` read returns the rows of any registered type for a key and a window. A new metric or record type is a config change. Depends on butterfly 09. done (tag `synapse-api-phase-09-done`, 2026-10-31).

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
- 12 ai-answers: AI Mode asks sami-agents (`POST /v1/agents/analyse`) first and draws the answer as text, a trend chart, tables and an evidence list from the JSON blocks with the existing widgets; questions the agent cannot read fall back to the keyword widget planner, `@builder` never goes to the agent, a month not over yet and an unreachable service have their own messages. sami-agents refusals carry `problem`. done (tag `synapse-web-phase-12-done`, 2026-10-31).
- 13 intent-demo: every AI Mode question is also sent to intent-api and a small reading card under the answer shows how it was understood (domain with percentage, scenarios, or why it cannot answer and the nearest domains); silent when intent-api is down. done (tag `synapse-web-phase-13-done`, 2026-11-01).
- 14 intent-answers: AI Mode asks intent-api first (`POST /v1/intent/answer`) and draws its blocks (a sentence, plus a trend chart or ranked table only where the scenario needs one); two periods or a future one gives a sentence naming the periods read, synapse-api down says the figures are not available, and every other refusal (why, Finance and Inventory widgets, boards) falls through to the sami-agents and widget flow unchanged. done (tag `synapse-web-phase-14-done`, 2026-11-01).
- company-data (not numbered yet): filter synapse-api data by company and add the group view, an `All companies` choice in the picker for users with several companies that sums across them, plus widgets that split by company. All three companies are in one SAP system, so synapse-api filters and sums by company code in one query. Currency and intercompany rules still need an answer from finance. todo

## workspace-api (workflow backend)
- 01 sales-order-gateway: an interface to create and list sales orders, with an implementation that calls butterfly. done (tag `workspace-api-phase-01-done`, 2026-10-27)
- 02 sales-order-routes: role-checked routes for creating and listing orders. done (tag `workspace-api-phase-02-done`, 2026-10-27)
- 03 order-queue: an order that SAP cannot take is saved and posted later by one worker, never lost and never posted twice (an unclear result is shown as `unknown` and not retried); at most `SAP_WRITE_LIMIT` writes in flight (default 1, the worst case), every limit a setting. Queue and worker on SQLite, not a broker. done (tag `workspace-api-phase-03-done`, 2026-10-31).

## workspace-web (department users)
- 01 shell-and-login: app shell, login page, menu by role. done (tag `workspace-web-phase-01-done`, 2026-10-27)
- 02 sales-order-entry: form to enter a sales order with clear validation messages. done (tag `workspace-web-phase-02-done`, 2026-10-27)
- 03 sales-order-list: list and open the user's recent orders. todo
- 04 order-status: the new-order page understands the queue answers of workspace-api 03 (queued, unknown, order not saved), clears the form so nothing is entered twice, and shows a Waiting for SAP panel of the user's open orders. Depends on workspace-api 03. done (tag `workspace-web-phase-04-done`, 2026-10-31).

## sami-agents (AI service for AI Mode)
- 01 chat-graph: new FastAPI service (port 8005) with the cookie-checked `POST /v1/agents/chat` route that answers in OpenUI Lang, a LangGraph graph over `ChatModel` and `CatalogSource` ports with mocks, the Ollama adapter, and an evaluation tool (`sami-agents eval`) with 22 prompts; it found that small models alone are not good enough at choosing widgets. done (tag `sami-agents-phase-01-done`, 2026-10-30).
- 02 relevance-check: keyword proposals with stemming and an alias file, an optional Laya relevance check in a propose and verify loop (off by default: it did not beat the keywords in our tests), an optional small-model sentence writer behind strict checks (off by default), widgets returned as OpenUI Lang pinned by a contract test, and an evaluation tool with a tuning set and a held-out set. done (tag `sami-agents-phase-02-done`, 2026-10-31).

- 03 answer-questions: level 2 answers: "what were sales for August?" gets a sentence with the real figure, the change from the month before and a trend chart, as JSON blocks on the same `analyse` route (`question.intent` is `figure` or `why`). Reuses the question reader and trend block of 05. done (tag `sami-agents-phase-03-done`, 2026-10-31).
- 06 case-reader: the question is read in passes into a case: Laya (`typed-decisions`) decides intent, subject and direction one choice at a time with a confidence, rules and fuzzy matching read the month and the scope, and a pass it is unsure about falls back to the rules (Laya off or down: the old rules-only reader). Typos, loose wording, other periods, a scope like "sales to Acme" and chat questions get a clear reply instead of a wrong answer; `analyse` takes an optional `context` so a follow-up ("give me the reason for the decline") reuses the last question's metric and month; `case-eval` measures it (tuning 39 of 40 and held-out 25 of 29 with Laya on, against 29 and 19 with rules only); a per-line tone rephrase with a local model exists behind strict checks and is off by default (`TONE=plain`) because no small model passed reliably. synapse-web shows the new refusals, matches widgets by whole words and sends the follow-up context. done (tag `sami-agents-phase-06-done`, 2026-11-01).
- 04 graph: the entity graph as a file the owner maintains (`graph.toml`), its loader, `graph check` and `graph show` (checked against the synapse-api registry), the traversal engine in three modes (root cause, impact, dependency) with generic anomaly kinds (a date later than another, started or ended in the window, a value or count away from its own baseline, a status change), and a how-to (`docs/graph-maintenance.md`). Depends on synapse-api 09 and `docs/ai-analysis.md`. done (tag `sami-agents-phase-04-done`, 2026-10-31).
- 05 analyst: question understanding for any registered metric (sales, purchases), factor ranking by explained share with the unexplained rest, the validated answer, and evaluation on the butterfly scenarios including the held-back ones; a local model is optional (a question reader fallback and a checked rephrase) and no data leaves the machine. Includes purchases in the registry and graph, a `set_changed` anomaly kind and the `analyse` route that returns JSON answer blocks. Depends on sami-agents 04. done (tag `sami-agents-phase-05-done`, 2026-10-31).

## intent-api (reads a manager's question into approved scenarios)
- 01 scenario-rules: new FastAPI service (port 8006) with `POST /v1/intent/match` behind the cookie check, the scenario library `scenarios.toml` (6 domains, 14 draft scenarios, `scenarios check` and `show`), Laya (`typed-decisions`, run as its own service, no data leaves the company) choosing the domain and then the scenarios clause by clause, rules for `covers`, the floors and every refusal (`not_about_business`, `not_sure`, `no_scenarios`, `nothing_matched`, `cannot_classify_now` when Laya is down), the `unanswered.jsonl` log and command, and `intent-api eval` with a held-out part (79% exactly right on held-out answerable questions, 15% wrong answers; see the phase notes). Slots, data, answers and the web app come in later phases. done (tag `intent-api-phase-01-done`, 2026-11-01).

## ai-dashboard (POC, later, local-first)
- Not scheduled. Starts after synapse-web 03. See `notes.md` for the constraints. todo

## admin page
Lives in a web app, to be placed once the web apps are further along. Depends on auth-api 02.
