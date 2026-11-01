# synapse-web/13 intent-demo

## Goal
In AI Mode, every question a manager asks is also sent to intent-api, and the answer shows how it was understood: the domain, the figures it recognised, how sure it is, or why it cannot answer yet. The existing answers (sami-agents, widgets) stay as they are.

## Why
intent-api (phase `intent-api/01`, merged) reads a question into approved scenarios but does not answer yet. Management should be able to see that part working in the real screen, with real questions, before the slots, data and answer phases are built. It also shows where the reading is wrong, which is how the scenario library and the Laya settings improve.

## Behavior
- A new `IntentClient` port in `src/ai/`, `ask(question)` returning an `IntentReading`, with `HttpIntentClient` (`POST {INTENT_URL}/v1/intent/match`, cookie, 10 s timeout, `INTENT_URL` from `VITE_INTENT_URL`, default `http://localhost:8006`) and a mock for the tests, like `AgentsClient`. Any failure, including a `503` with `problem: "cannot_classify_now"`, is `IntentUnavailable`.
- `IntentReading` is what the route returns that the screen needs: `domain`, `domainProbability`, `problem` (`null` or `cannot_answer`), `reason` (`not_about_business`, `not_sure`, `no_scenarios`, `nothing_matched`), `scenarios` (`id`, `probability`, `clause`) and `didYouMean`. Unknown or missing fields make the reading unusable (`IntentUnavailable`), never a guess.
- In `AiPage`, for every question that is not a `@builder` request, the intent call runs together with the existing agent call and neither waits for the other beyond what is needed to draw the message. When intent-api is not reachable the message is drawn as it is today, with nothing about intent on it.
- An `IntentCard` under the AI answer, small and quiet (no slide-up entrance, subtle motion): 
  - answered: "Understood as {Domain}" and one line per scenario with its readable name (the id with underscores as spaces, for example "sales top customers") and the probability as a percentage;
  - `not_about_business`: "This does not look like a question about our figures.";
  - `not_sure`: "I am not sure what you mean."; 
  - `no_scenarios`: "This is about {Domain}, which I cannot answer yet."; 
  - `nothing_matched`: "I could not tell which figure you want from {Domain}."; 
  - for refusals, "Did you mean {A} or {B}?" when `didYouMean` has names.
- Nothing else in AI Mode changes: board building, remembered context, the sami-agents answers and the widget answers are untouched. The card does not decide what the AI answers.

## Acceptance cases
- With a mock intent client returning an answered reading, the card shows the domain, each scenario with its percentage, and the agent answer is still drawn.
- Each of the four refusal reasons shows its sentence, and `didYouMean` shows the question to the manager.
- When the intent client fails, the message is exactly as before (no card, no error text).
- A `@builder` request never calls the intent client.
- `HttpIntentClient` sends the question with the cookie, reads a valid body, and treats a bad status, a network error, a timeout or an unreadable body as `IntentUnavailable`.

## Out of scope
Changing intent-api (it keeps returning scenario ids; readable names are made here), clicking a "did you mean" choice, showing the card for board requests, using the reading to decide the answer, a settings or on/off switch, new widgets, Docker.

## Depends on
`intent-api/01` (merged), `synapse-web/12`. To try it by hand: Laya running (see `apps/intent-api/README.md`), intent-api on port 8006 with the same `JWT_SECRET`, and `LAYA_URL` set.

## Open items for the owner
1. Is the card shown to every user, or only to management and admin like the route? (The route already refuses other roles, so other users would see no card.)
2. Should the card say "(draft)" or "preview" so managers know the reading is not an answer yet?
