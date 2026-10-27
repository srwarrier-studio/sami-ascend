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

## Sales contract (`docs/sap/sales-contract.md`)
- Source of truth for butterfly, the gateways and the consultant guide. Change it first, then the code.
- Decimals are JSON strings; dates are `Edm.Date`; timestamps are UTC with `Z`; `OverallStatus` is `A`, `B`, `C`, `X`.
- Summaries are per day, one row per currency; MTD and YTD are summed by synapse-api. `$apply` is not used.
- Single-entity reads carry `@odata.etag`; `PATCH` needs `If-Match` and changes only `RequestedDeliveryDate`.
- Validation errors are one `VALIDATION_FAILED` with a `details` entry per field. Apps branch on `code`, never on `message`.
- Questions for the SAP consultants live in `docs/sap/consultant-questions.md`, not in phases. Service name and path are placeholders until confirmed.
- Check the examples with `uv run --with pytest pytest docs/sap`.

