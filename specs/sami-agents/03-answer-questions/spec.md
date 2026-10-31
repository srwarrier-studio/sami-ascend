# sami-agents/03 answer-questions

## Goal
A user asks "what were sales for August?" and gets one sentence with the real figure, how it compares with the month before, and a trend chart, as the same JSON blocks the "why" answer uses.

## What is reused and what is new
- Reused: `QuestionReader` and its `understanding.json`, `DataSource.compare` and `trend`, the `trend` and `text` blocks, `MOCK_LABEL`, the route `POST /v1/agents/analyse`, cookie auth and roles.
- New: an `intent` on `Question` (`why` or `figure`), figure words in `understanding.json`, one use case `StateFigure`, figure wording, and `AnswerQuestion` choosing by intent. No new route and no new port.

## Behavior
### Reading the question
- `Question` gets `intent`. A text with a `why` word keeps today's reading (`why`). A text with a `figure` word ("what", "what is", "what were", "how much", "how many", "show me the", "tell me") and a registered metric and a month is `figure`. A `why` word wins when both are present.
- Direction is not needed for `figure`. The month rules are those of 05, except that the current month is allowed for `figure`: it is answered "so far" with no comparison, and the sentence says "so far this month".
- "show me sales and top customers" stays a level 1 chat question; the analyse route only gets what the user sends to it.
- `understanding.json` gets `figure` words; the registry test already forces words per metric.

### The figure
`StateFigure.execute(question, token)` calls `compare` for the month against the previous month and returns the metric label, currency, current, previous, change and change percent. The order count is not in `compare`, so it is not stated in this phase.
- A month with no figures (no rows) says "No <metric> were recorded in <month>" and gives no chart.
- A previous month of zero gives no percent ("up from nothing").

### The answer
Same JSON as 05 with `question.intent` added:
- `blocks`: `text` (the figure sentence, then the comparison sentence), `trend` (last 6 months, the month marked, as in 05).
- `analysis` is null for a figure answer (no findings).
- Wording is a template filled only from the figure: "Sales for August 2026 were ₹64.8 lakh, down 14.5% from July (₹75.7 lakh)." Amounts use the Indian format already used by the wording module. The same check as 05 (every number, date and name is in the figure) runs in a test.
- Offer the next step in the text only when the change is significant: "Ask why sales fell in August for the reasons."
- Optional model hooks from 05 are not used for figures.

### Errors
Unreadable and data-unavailable behave as in 05.

## Acceptance cases
- "What are the sales for August?", "how much did we purchase in September 2026", "what were purchases last month" read as `figure`; "why did sales fall in August" is still `why`; "show me sales" is unreadable.
- Figure sentence for a rise, a fall, an unchanged month, a month with no rows, a previous month of zero, the current month (so far, no comparison).
- The trend block holds 6 points with the month marked; a failing trend read keeps the text and adds a limit line instead of failing.
- Scenario through butterfly and synapse-api in process: `august-contract` August sales figure equals the compare total; `quiet-month` says the change is small.
- The route returns `intent` for both kinds and the existing 05 tests still pass unchanged.
- No outside calls (the 05 test passes unchanged).

## Out of scope
Periods other than a month (quarters, years, "last 7 days"), several metrics in one question, filters ("sales to Acme"), order counts, drawing the blocks (synapse-web 12), model use for figures.

## Depends on
sami-agents 05 (merged).
