# Tasks

- [x] 1. `Case`, a `CaseModel` port with `MockCaseModel`, the Laya adapter (one decision per pass) and settings (`PASS_MIN_CONFIDENCE`). Done when adapter tests with a mock transport pass, including unreachable and unreadable answers.
- [ ] 2. Month and period rules with fuzzy matching, the passes in order with early exit and rule fallback, refusals for scope and unsupported periods. Done when the reader acceptance cases pass with a mock model and with no model.
- [ ] 3. `AnswerQuestion` uses the case; `question` carries `scope` and `how_read`; widgets intent is reported for the page. Done when route and answer tests pass and the 05 and 03 tests still pass.
- [ ] 4. `case-eval` with the tuning and held-out sets, run with Laya off and on. Done when both reports are printed and recorded.
- [ ] 5. Per-line tone rephrase with the strict checks and the tone setting. Done when check tests pass and a run on all development scenarios is recorded.
- [ ] 6. Real-stack run, notes, roadmap line, close the phase. Done when the owner has tried it and docs are updated.
