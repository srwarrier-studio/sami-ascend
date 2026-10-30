# sami-agents/02 relevance-check

## Goal
AI Mode picks the right widgets reliably and quickly: a keyword search proposes widgets, Laya (a small classification model) checks that each one fits the request, rejected ones are skipped and the next is tried, and a small LLM only writes the sentence. Approved widgets go to the frontend as a widget stack, or as a board for `@builder`.

## Behavior
- The graph is `route`, then a loop of `propose` and `verify`, then `reply`. The model no longer picks widgets (phase 01 found the small models unreliable at it): `ChatModel.pick_widgets`, `OllamaChatModel` picking, and the `select` and `validate` steps are removed.
- `route`: as before. `@builder` makes a board (up to 15 approved widgets), anything else is an inline answer (up to 4).
- `propose`: `KeywordMatcher` ranks catalog entries for the message, skipping ids already approved or rejected, and returns the next best. It gets two additions: simple word stemming (`purchasing`, `purchases` and `purchase` match) and an alias list, `aliases.json` in the app (`{ "top-materials": ["products", "items", "goods"], "prod-downtime": ["machines", "stopping", "stoppage"] }`), which the owner edits; a test checks the file covers exactly the widgets in the catalog snapshot, and an id the live catalog does not have is ignored. A word in the title or an alias counts double a word in the description; ties keep catalog order.
- `verify`: the `RelevanceChecker` port returns the probability that a widget answers the message. `LayaRelevanceChecker` calls `laya-serve` (`POST /v1/systemone`, the `typed-decisions` checkpoint) with the request and the widget's title and description and a two-option choice (the widget answers the request, or is about something else). A widget is approved at or above `LAYA_THRESHOLD` (default 0.35, from the evaluation), otherwise rejected and the loop proposes the next. The loop stops at the limit, when no candidates are left, or at the check budget (8 checks inline, 15 for `@builder`) so a request never waits long.
- If Laya is down, times out or returns something unreadable, the rest of the candidates are approved without a check (up to the limit), so AI Mode still answers; the response is the same, a warning is logged with the request id.
- Nothing approved: the answer is `I could not find a matching widget.` with no widgets.
- `reply`: a `ReplyWriter` port; `OllamaReplyWriter` asks a small model for one short sentence (at most 30 words, `num_predict` 60, temperature 0) given the user's message and the approved titles. The sentence is used only if it is one line, at most 200 characters and free of `<`, `>`, backticks and markdown; otherwise the sentence is built by code from the titles as before. The writer escapes it. `MockReplyWriter` for tests.
- Output is the OpenUI Lang program from phase 01, unchanged: `Stack` with `Text` and `Widget` lines, or `Board(name, ids)` for `@builder`.
- Settings added: `LAYA_URL` (default `http://localhost:8000`), `LAYA_API_KEY`, `LAYA_THRESHOLD`, `LAYA_TIMEOUT_SECONDS` (default 5). `OLLAMA_MODEL` now names the sentence writer; the default is chosen by a quick test of the small models in this phase.
- Laya runs outside the `uv` workspace as `laya-serve` in a Python 3.13 environment with CPU-only torch (the README gives the recipe: install torch from the PyTorch CPU index before `laya[serve]`), listening on localhost only and protected by `LAYA_API_KEY`.
- The evaluation tool runs the whole pipeline; `--parallel` still runs batches at the same time. It reports passes with the check on and with it off (`--no-check`), the number of checks per answer, and seconds per answer.

## Acceptance cases
- `propose`: stemmed and alias words match; titles and aliases outrank descriptions; approved and rejected ids are skipped; an unknown alias id is reported.
- Loop: a rejected widget is skipped and the next candidate is checked; approved widgets are kept in order; the limits (4, 15) and the check budgets (8, 15) hold; nothing approved gives the not-found sentence.
- Laya unavailable, timing out or unreadable: unchecked candidates are used; the answer is still a valid program.
- `LayaRelevanceChecker` (tests use `httpx.MockTransport`): sends the key, the request, the widget and the two options; reads the probability; maps errors to unavailable.
- `ReplyWriter`: a clean sentence is used; multi-line, over-long, markup, empty, timeout and error fall back to the code sentence; injected quotes cannot break the program.
- The program always has a `root`, and only catalog ids appear in it.
- Evaluation: the keyword proposals alone reach the numbers recorded in task 1 on the tuning prompts and on a held-out set written before the aliases; with Laya on the whole pipeline is at least as good; the owner reads both.
- No test calls Laya, Ollama or the network.

## Out of scope
Fine-tuning Laya, ONNX, streaming, embeddings, parameterised widgets, conversation memory, per-company filtering, and the web side (`synapse-web/12 openui-chat` renders the text).

## Depends on
sami-agents 01, synapse-api 05.
