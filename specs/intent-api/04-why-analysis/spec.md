# intent-api/04 why-analysis

## Goal
intent-api answers "why did sales (or purchases) change in <month>" itself, with the deterministic analysis sami-agents did (the graph, the movers, the causes and the offset), for one company or the group in one currency, so AI Mode no longer needs sami-agents.

## Behavior
- **`why` scenarios.** `sales_why` and `purchases_why` get an entry in `answers.toml` with `response = "why"` and the metric. `POST /v1/intent/answer` runs the analysis for them instead of answering `not_answerable_yet`. Laya still chooses the scenario; nothing else about matching changes.
- **Period.** `ReadPeriod` gives the month; it must be a finished month and is compared with the month before (as sami-agents does). Two periods or a future month stay `period_not_supported`, with the same sentence.
- **Moved from sami-agents, unchanged in behavior:** the graph (`graph.toml`, its loader and `graph check` / `graph show`, `docs/graph-maintenance.md`), the walk engine (root cause, impact, dependency), `AnalyseQuestion` with its thresholds (`SIGNIFICANT_PERCENT`, `MOVER_MIN_PERCENT`, `MOVER_MIN_SHARE`, `PRICE_MAJORITY_PERCENT`), the anomaly kinds, the answer scoring and the wording. The data port is intent-api's metric gateway (`SynapseMetricSource`), extended with the record reads the graph needs (`/records`) and the `company` and `currency` it forwards.
- **Company.** The answer request takes the optional `company` (default `all`) and sends it to every synapse-api read; the user's cookie authorizes it, so a company the user does not have is refused by synapse-api (`403`) and shown as such.
- **Currency.** The analysis reads each currency's comparison, uses the currency with the biggest change in the month (or the one the question names, `USD` or `INR`), and says the currency in the headline; another currency with a large change gets one extra sentence. Currencies are never added.
- **Answer.** The same blocks the web already draws (`text` for the headline, causes with their shares, the offset and the limits; `trend`; `table`; `evidence`), and the first sentence names the scope and the currency ("Sales of Sami-Sabinsa fell 14.5% in USD from July 2026 to August 2026 ..."). For the group scope the answer reports the figures and says the causes are for the group, without promising the story causes.
- **No model in the answer.** Every figure comes from synapse-api and the text is built from templates (Laya is only used to choose the scenario, as today). The Ollama question model and sentence writer, the tone rephrase and `understanding.json` are not moved.
- **Evaluation.** `intent-api why-eval [--final]` (moved from `analyst-eval`) asks one question per butterfly scenario in process and scores causes found, missed and invented against the ground truth in `apps/butterfly/scenarios/`, for `sabinsa` (`INA1`) in `USD`; the held-back scenarios stay held back.

## Acceptance cases
- Every moved test passes in intent-api (graph loader and check, walk, analyse, scoring, wording, anomaly kinds), with the mock data source.
- All 13 butterfly scenarios pass the evaluation for `sabinsa` and `USD`, including the held-back ones (the same cases that fail in sami-agents against butterfly 12 until sami-agents 08, which this phase replaces).
- "Why did sales fall in August?" answers through `POST /v1/intent/answer` with the contract, supplier and production causes and their shares (about 80%, 38% and the offset), a trend and an evidence block.
- The same question for `all` names the scope and currency and does not claim the story causes; for `INR` it answers in rupees; for a company the user does not have it answers that the company is not allowed.
- An unregistered metric, a month not over yet, no data and synapse-api down each have their sentence (the existing `figures_down` and period sentences are reused).
- `graph check` against `apps/synapse-api/registry.toml` passes, with `CompanyCode` known to the checker.

## Out of scope
The web changes (synapse-web drops the agents client in its own phase), deleting sami-agents (a later phase), generating the graph from the butterfly contract and registry, other domains' `why`, exchange rates, Laya training for new `why` wording.

## Depends on
synapse-api 10 (company scope and currency), butterfly 12, intent-api 03 (answers).
