# synapse-web/14 intent-answers

## Goal
In AI Mode, a question that intent-api can answer is answered from intent-api's blocks: a sentence with the real figure and, only where the scenario needs one, a trend chart or a ranked table. Every other question goes through the flow of today unchanged.

## Why
Phase 13 shows how intent-api read a question but the answer still comes from the keyword matcher, so "to whom did we sell the most in June" reads as Sales top customers (100%) and is answered with "Most overdue accounts". `intent-api/03` now answers from the scenario key (`POST /v1/intent/answer`). This phase draws that answer.

## Behavior
- `IntentClient` gets `answer(question)` returning an `IntentReply`: the `reading` (as in phase 13), `problem`, `reason` (the four reasons of phase 13 plus `not_answerable_yet` and `period_not_supported`), `periods` and `answers` (`scenario` and `blocks`). The blocks are the shapes `AnswerBlocks` already draws (`text`, `trend`, `table`); they are read with the same checks as the sami-agents blocks, and a block of an unknown shape makes the reply unusable. A `503` with `problem: "cannot_fetch_now"` is `IntentDataUnavailable`; any other failure is `IntentUnavailable`. `answer` replaces `ask` (the reading is part of the reply).
- `AiPage`, for a question that is not a `@builder` request, asks intent-api first (one call; the reading and the answer come together) and then:
  - answered: draw the blocks of each answer in order with `AnswerBlocks`, then the `IntentCard`; the sami-agents call is not made;
  - `period_not_supported`: draw "I can answer for one period at a time. I read {periods}." and the card; no other answer is tried, because the old flow would answer for a different period;
  - `IntentDataUnavailable`: draw "The figures are not available right now." and nothing else;
  - any other refusal (`not_answerable_yet`, `not_about_business`, `not_sure`, `no_scenarios`, `nothing_matched`) and `IntentUnavailable`: the flow of today (sami-agents, then the widget planner), with the card when there is a reading, as in phase 13.
- The card keeps its sentences; for an answered question it reads "Understood as ..." as before, with no "preview" wording once the answer comes from it. A `@builder` request never calls intent-api.
- A figure answer does not set the remembered context of the sami-agents follow-ups (a follow-up still goes to sami-agents as today).
- Nothing else changes: board building, widget answers, the sami-agents why answers.

## Acceptance cases
- With a mock client returning a ranking reply, the page draws the sentence and the table, the card, and does not call the agents client.
- A value reply draws one sentence and no chart; a trend reply draws the sentence and the chart.
- Two answers are drawn in the order returned.
- `period_not_supported` draws the sentence with the periods and no agents call; `cannot_fetch_now` draws the unavailable sentence.
- `not_answerable_yet` (for example a why question) falls through to the agents client as today and shows the card.
- When intent-api fails, the message is exactly as before phase 13.
- `HttpIntentClient.answer` sends the question with the cookie to `/v1/intent/answer`, reads a valid body, and treats a bad status, a network error, a timeout or an unreadable body as `IntentUnavailable`.

## Out of scope
Changing intent-api, clickable "did you mean", the `entity` slot, a switch to turn the new answers off, follow-up context for figure answers, Docker.

## Depends on
`intent-api/03` (merged), `synapse-web/13`. To try it by hand: the stack from `scripts/dev.sh` with Laya serving `intent-tuned-2`.

## Open items for the owner
1. Should the card stay under figure answers, or only under refusals and fall-through answers?
2. The card says "Reading preview" in phase 13. Drop "preview" now that the answer comes from it?
