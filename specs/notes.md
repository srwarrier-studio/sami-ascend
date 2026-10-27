# Project notes

Knowledge kept after phases close. Add to it when a phase ends. Keep entries short.

## Project
- Management users share one read-only SAP login; the app audits who actually did what.
- Authorization data lives in SAP. The app owns roles that control which pages and APIs a user may use.

## What we are building
- **synapse:** dashboards for management. Read-only, modern, single click, near real time (5 minutes). Management rejected the Fiori dashboards as old looking, with too many dropdowns, drilldowns and filters.
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

## Sales contract (`docs/sap/sales-contract.md`)
- Source of truth for butterfly, the gateways and the consultant guide. Change it first, then the code.
- Decimals are JSON strings; dates are `Edm.Date`; timestamps are UTC with `Z`; `OverallStatus` is `A`, `B`, `C`, `X`.
- Summaries are per day, one row per currency; MTD and YTD are summed by synapse-api. `$apply` is not used.
- Single-entity reads carry `@odata.etag`; `PATCH` needs `If-Match` and changes only `RequestedDeliveryDate`.
- Validation errors are one `VALIDATION_FAILED` with a `details` entry per field. Apps branch on `code`, never on `message`.
- Questions for the SAP consultants live in `docs/sap/consultant-questions.md`, not in phases. Service name and path are placeholders until confirmed.
- Check the examples with `uv run --with pytest pytest docs/sap`.

