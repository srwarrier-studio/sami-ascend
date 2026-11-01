# Tasks: synapse-web/14 intent-answers

- [x] 1. Client: `IntentClient.answer`, `IntentReply`, `HttpIntentClient.answer`, `MockIntentClient`, the shared block parser. Done when: the tests for a valid body, every failure and every block shape pass.
- [x] 2. AI Mode: `AiPage` asks intent-api first and draws blocks, the periods sentence and the unavailable sentence, falling through to today's flow for every other refusal. Done when: the acceptance cases pass in `aiPage.test.tsx`.
- [x] 3. Close-out: card wording after the owner's answers, README line, `notes.md`, roadmap. Done when: tests, types and lint pass and the phase is ready to merge.
