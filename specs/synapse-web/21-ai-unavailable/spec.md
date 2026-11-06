# synapse-web/21 ai-unavailable

## Goal
When intent-api cannot be reached or fails, AI Mode says so and offers a Try again button, instead of showing unrelated widgets from the keyword planner.

## Why
On 2026-11-06 Laya was not running, intent-api answered `503 cannot_classify_now`, and the AI page treated every failed call as "no reading" and fell back to `MockChatPlanner`: "why did our sales drop in July 206?" got "Here is Sales today, Sales this month, …". The reader is misled into thinking that is the answer.

## Behavior
- A question whose call to intent-api fails (not reachable, any non-OK status, unreadable answer) gets this reply and no widgets: "The AI service is not available right now. Please try again in a moment." with a **Try again** button.
- **Try again** removes that failed reply and asks the same question again, without a second copy of the question in the log; it can fail again and show the same reply.
- Unchanged: `@builder` requests (they never call intent-api), the "figures are not available" reply when synapse-api is down, refusals from a working intent-api (`not_sure`, `no_scenarios`, `nothing_matched`) still hand the question to the widget planner as designed in synapse-web 13 and 14, and why failures keep their own message.
- `MockIntentClient` (test double) answers "nothing matched" by default, so tests that want an outage pass an error explicitly.

## Acceptance cases
- With intent-api failing, a question shows the unavailable reply and its Try again button and draws no widgets or reading.
- Try again, with intent-api still failing, shows the reply again and the question appears once; once intent-api answers, the answer replaces the failed reply.
- `@builder` still builds a board while intent-api is failing.
- The existing AI page tests pass, the outage test changed to the new behavior.

## Out of scope
Changing what a refusal does, the intent-api and Laya side (shared 17), retry of other failures.
