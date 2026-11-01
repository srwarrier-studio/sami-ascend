# synapse-web/15 widget-answers

## Goal
When AI Mode answers a question with widgets or the agent after intent-api refused it, the card under the answer no longer says the question cannot be answered.

## Behavior
- `AiPage` already falls through to the sami-agents and widget flow when intent-api refuses (`no_scenarios`, `nothing_matched`, `not_sure`). Today the message keeps the whole reading, so the card shows "This is about Finance, which I cannot answer yet." under widgets that did answer.
- A message that shows widgets, a board, or an agent answer keeps the reading badge and the "Understood as <domain> (<probability>)" line when a domain was read, and drops the refusal sentence and the "Did you mean" line.
- A message that shows only text (the planner found nothing, the agent is unavailable) keeps the refusal sentence exactly as today.
- Answers drawn from intent-api blocks, the periods sentence and the "figures not available" sentence are unchanged.

## Acceptance cases
- Finance question, intent-api answers `no_scenarios`, the planner returns widgets: the widgets are drawn, the card says "Understood as Finance" and has no "cannot answer yet".
- Same refusal, the agent answers: the agent blocks are drawn, no refusal sentence.
- Same refusal, the planner returns no widgets and no board: the refusal sentence is shown as before.
- `not_about_business` or `not_sure` followed by widgets: no refusal sentence either.
- A reading with no domain and widgets: the badge only, no "Understood as" line.
- Existing aiPage and intent card tests keep passing.

## Out of scope
New Finance scenarios and real receivables data (butterfly 11 and later intent-api phases), changing what intent-api or the planner decides, card wording for refusals that end in text.

## Depends on
synapse-web 14.
