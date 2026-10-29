# synapse-web/04 ai-ready-review

## Goal
Check that the widgets are ready for the AI dashboard POC and record what is missing, with tests for what a small model needs.

## Behavior
A model must be able to (1) read a list of widgets, each with name, description, size and a JSON schema, (2) answer with a board as plain JSON `{ name, widgets: [{ widget, props }] }`, (3) have every answer checked before it is drawn.
- `docs/ai-ready-review.md` lists each need, the result (met, gap) and the fix or decision.
- Tests (`tests/aiReady.test.ts`): the descriptions list is JSON serializable and small enough for a small model's prompt (token estimate); every widget has a one-sentence description; schemas carry no style props; every catalog entry's props validate against its widget's JSON schema; a model-written board is accepted by a `parseAiBoard` check that rejects unknown widgets, bad props and empty boards, and the board JSON round-trips to `BoardWidget`-like entries.
- `parseAiBoard(json, names)` lives in synapse-web `src/ai/` and uses only the registry (`describe`, `render` fallback detection via the schema).

## Acceptance cases
As listed in Behavior; each gap found is either fixed or listed in the review as a decision for the POC.

## Out of scope
The model, prompts, Ollama, OpenUI comparison.

## Depends on
synapse-web 03.
