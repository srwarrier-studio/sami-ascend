# synapse-web/16 company-scope

## Goal
The company chosen in the picker, and a widget currency, reach synapse-api and intent-api, and AI Mode no longer calls sami-agents.

## Why
synapse-api 10 scopes every read by `company` (an id or `all`) and widgets by `currency`; intent-api 04 answers `why` itself. The web still sends neither, and still falls back to sami-agents for `why`, the only thing it is used for.

## Behavior
- **Company choice.** The picker gets an `All companies` choice for users with several companies, stored like the company today (`synapse.company.<userid>`). `useCompany` returns the company id or `all`; a user with one company never sees it. The header switcher offers it too. The exported PDF header for `all` carries the group name and no single logo.
- **Company on every read.** `HttpCatalogClient.list` and `data` send `company` as a query parameter; the intent-api answer request sends `company` in its body. Changing the company reloads the catalog and drops the cached widget data. A `403 COMPANY_NOT_ALLOWED` is shown as "You do not have access to this company" and the choice resets to the first allowed company.
- **Currency.** synapse-api 10 takes `currency` on widget data (default `USD`, the group's main currency). The web asks for `USD` and draws money widgets (`valueFormat: "currency"`) with the dollar sign by rewriting it to `currency:USD`. A currency choice for the user was tried and dropped: it only changed the sign, not the figures, which misleads. A real choice needs figures converted at a rate, which finance has not decided.
- **`@sami/ui` (owner-approved extension).** `valueFormat` also accepts `currency:<CODE>`: the sign follows the code (`$` for USD, `₹` for INR) and numbers stay Indian-grouped; plain `currency` still means INR, so nothing else changes. The schema accepts `currency:` plus three capital letters.
- **Drop sami-agents.** `AgentsClient`, `HttpAgentsClient`, `AGENTS_URL`, the remembered follow-up context and the `agentsClient` route-context entry are removed. `AiPage` order: intent-api answer, then the widget planner; a `why` answer from intent-api is drawn with the same blocks (`text`, `trend`, `table`, `evidence`). The block parser and `SHOWN_PROBLEMS` move into `intentClient.ts` (they are already used from there). A follow-up question is sent alone; intent-api reads the month itself.
- Nothing else changes: boards, presets, export, login, the intent card.

## Acceptance cases
- A user of one company never sees `All companies`; a user of three can pick it, reload and still have it.
- With company `organica`, the catalog list and data requests carry `company=organica`; with `all`, `company=all`; the intent-api request body carries the same value.
- Changing company refetches the catalog; a `403 COMPANY_NOT_ALLOWED` shows the message and resets the choice.
- A money widget asks for `USD` and shows the dollar sign; a widget that is not money is left alone.
- A `why` question draws intent-api's blocks including `evidence`, with no call to port 8005.
- When intent-api refuses, the widget planner answers as today; when it is unavailable the message is exactly as before.
- No file under `src` mentions `agents` or `8005`; `tsc`, tests and lint pass.

## Out of scope
Other `@sami/ui` changes, deleting `apps/sami-agents` and merging the branches (the next step, below), exchange rates, splitting widgets by company, intent-api or synapse-api changes, Docker.

## Depends on
synapse-api 10, intent-api 04 (both on unmerged branches, so test with their worktrees or a mock client).

## After this phase (owner approval needed for each)
1. Delete `apps/sami-agents`, its roadmap entries (kept as history, marked removed), its lines in `scripts/dev.sh`, and the branches `sami-agents/*` and worktree `sami-ascend-agents-08`.
2. Merge in order: butterfly-12, workspace-api-04, synapse-api-10, intent-api-04, synapse-web-16, then close each phase with its tag.

## Open questions for the owner
1. Should the dashboard default to `all` for a multi-company user, or the first company?
2. (answered) No currency choice; USD only until finance decides on rates.
