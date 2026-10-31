# Tasks

- [x] 1. Better proposals: word stemming, `aliases.json` and the reworked `KeywordMatcher` with skip lists, aliases for the widgets the evaluation missed, and the keyword-only score recorded. Done when the matcher cases pass and the keyword-only evaluation is above the 16 of 22 from phase 01.
- [x] 2. `RelevanceChecker` port with its mock and the propose and verify loop in the graph (approve, reject, budgets, unavailable means unchecked); the model-picking code removed. Done when the loop cases pass.
- [x] 3. `LayaRelevanceChecker`, its settings and the README recipe for `laya-serve`. Done when the adapter cases pass and Laya answers from the real server.
- [x] 4. `ReplyWriter` port, `OllamaReplyWriter` with validation and the fallback sentence, and the small-model choice. Done when the writer cases pass.
- [ ] 5. Evaluation of the whole pipeline (check on and off, one at a time and four at a time), numbers into `specs/notes.md`, and the OpenUI contract test. Done when the owner reads the results and approves.
