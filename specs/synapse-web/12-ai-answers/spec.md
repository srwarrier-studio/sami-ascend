# synapse-web/12 ai-answers

## Goal
In AI Mode a manager types "why did sales drop in August?" or "what were sales for August?" and sees the real answer from sami-agents: a sentence, a trend chart, tables and the evidence, drawn with the existing `@sami/ui` widgets.

## Behavior
### Asking
- `AgentsClient.ask(message)` posts `{question}` to `SAMI_AGENTS_URL/v1/agents/analyse` (new setting `VITE_AGENTS_URL`, default `http://localhost:8005`) with the cookie, and returns the JSON answer.
- `AiPage` first asks the agent. If the answer is `readable`, it is shown. If not, the message goes to the existing `ChatPlanner` (keyword widgets, `@builder`) exactly as today. A message starting with `@builder` never goes to the agent.
- If the agent says the month is not over (`problem: "not_finished"`), that text is shown and the planner is not tried. For any other unreadable question the planner runs; if it finds nothing, its own "could not match" message stands.
- `503`, a network error or a timeout (30 s) shows "The analysis service is not available right now." as an AI bubble; the planner is not used for it.

### Drawing the blocks
A message may carry `blocks`. They are drawn in order inside the AI bubble:
- `text`: one paragraph per line.
- `trend`: `LineChart` of `points` (`month`, `value`), the `marked` months highlighted if the chart supports it, else named in the title ("Sales, last 6 months"), money formatted with the currency.
- `table`: `DataTable` with the block's `title`, `columns` (as labels) and `rows`; money columns formatted with the answer currency; the "Share of change" column as percent.
- `evidence`: a list titled with the finding name, one line per step (`summary`), the step's document rows behind an expand/collapse.
- The `label` ("Mock data (butterfly)") is shown as a small badge on the answer.
- Bubbles with blocks use the wide layout already used for widgets.

### Backend change this phase needs (sami-agents, listed here as the spec allows)
- `refusal` returns `problem` (`unreadable` or `not_finished`). Only that field is added; existing tests keep passing.

## Acceptance cases
- A readable "why" answer shows the text lines, a line chart, a table per dimension and an evidence list; a "figure" answer shows text and the chart only.
- "show top customers" is unreadable for the agent and still shows widgets through the planner; `@builder build a sales board` never calls the agent.
- "why did sales fall this month" shows the not-over text and does not show widgets.
- A failing agent shows the unavailable text and the thread stays usable.
- The label badge shows only when `label` is not null.
- Unknown block types are skipped, not crashed on.
- Tests use a mock `AgentsClient`; no test calls the network.

## Out of scope
OpenUI Lang chat (`/v1/agents/chat`) for widgets, streaming answers, follow-up questions that keep context, saving an answer to a board, lakh formatting, other periods than a month, company filtering.

## Depends on
sami-agents 03 and 05 (merged), synapse-web 05.
