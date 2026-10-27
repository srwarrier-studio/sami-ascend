# Tech stack

| Area | Choice | Why / notes |
|------|--------|-------------|
| Backend | Python 3.14, FastAPI | One API per app, managed as a `uv` workspace (`apps/*-api`) |
| Frontend | React 19, TypeScript, Vite | `pnpm` workspace (`apps/*-web`, `shared/*` for shared JS packages) |
| Lint / test | oxlint, pytest | |
| Login | Entra ID (MSAL authorization code flow) and username/password | Entra users must be pre-registered; never auto-created |
| Session | Own JWT (HS256, `pyjwt`) in an httpOnly, Secure, SameSite=Lax cookie | The Entra token never reaches the browser |
| Passwords | argon2 via `pwdlib` | |
| User store | SQLite behind `UserRepo` / `AuthUnitOfWork` | Move to Postgres by adding an implementation; use cases do not change |
| SAP access | OData V4 (RAP) from each API through an interface | Frontend never calls SAP. Shared read-only SAP login for management users. S/4HANA is a private cloud on AWS |
| Mock SAP | `butterfly` (`apps/butterfly`), FastAPI | Serves the same OData V4 shapes as the real RAP services. The contract in `docs/sap/` is the source of truth for both butterfly and the consultant guide |
| Dashboard freshness | Polling, 5 minutes | RAP does not push. synapse-api caches and refreshes on a 5-minute cycle |
| Dashboard totals | Summary CDS views exposed as read-only entities | Safer for RAP beginners than `$apply`; revisit if SAP confirms aggregation support |
| Web UI | Mantine, imported only through the shared `@sami/ui` package (`packages/ui`) | Every web app gets the same components and styling from one place. Colors are the only per-app difference: workspace and synapse each pass their own palette to the provider |
| Routing (web) | TanStack Router, code-based routes | |
| Charts (web) | TanStack Charts v1 (SVG, optional canvas), wrapped in `@sami/ui` | Chosen over Recharts for fit with the TanStack stack; shared/06 compares size and memory, and the wrapper means a swap touches one package |
| Widgets (web) | Each widget is a React component taking one JSON-serializable props object, registered by name in one registry | Keeps the dashboard data-driven so a model can pick widgets later. No extra dependency now |
| AI dashboards | POC only, local-first, small model (e.g. Gemma 270M), not decided | A model this small should choose widgets and fill their parameters as structured output, not write UI code |
| Roles | App-owned, in the token: admin, management, purchase, stores, production, quality, sales, accounts | Page and API access. SAP still enforces data access |
| Logging | Structured JSON on stdout, request id across services | Provider-neutral; no custom log store or viewer |
| Audit | `audit_log` table owned by the app | Who did what; needed because SAP sees only the shared login |
| Hosting | AWS, private cloud | Log provider still to be confirmed; logging stays provider-neutral |

## Dependencies added so far
`fastapi[standard]`, `msal`, `pwdlib[argon2]`, `pyjwt` (auth-api).
`httpx` (workspace-api and synapse-api, to call butterfly/SAP over OData; also used by tests).
`@phosphor-icons/react` (icons, as Mantine recommends) and `@fontsource/ibm-plex-sans` (IBM Plex Sans, Carbon's typeface, self-hosted) in `@sami/ui`.
`@mantine/core`, `@mantine/hooks`, `@mantine/notifications` (toasts, same look as the other components), `@tanstack/charts`, `zod` (`@sami/ui`; zod gives one definition for prop validation and the JSON schema a model sees). Dev: `vitest`, `jsdom`, `@testing-library/*`, `vite`, `@vitejs/plugin-react`.
`@tanstack/react-router` and `@sami/ui` (workspace-web, which also uses vitest, jsdom and Testing Library as dev dependencies; routing needs guards on each route, which the router provides without a generator).
