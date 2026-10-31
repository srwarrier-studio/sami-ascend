# sami-agents/06 case-reader

## Goal
AI Mode understands a manager's question the way a person would: a local model reads it in several passes into a "case", code answers from the case with checked facts, and a small local model rephrases the answer in a chosen tone. Typos, loose wording and random questions are handled; the numbers and causes are never written by a model.

## Why
The current reader is rules only. It fails on typos and loose phrasing ("Augsut", "why are sales so low"), ignores scope words ("sales to Acme") without warning, and the answer reads like fixed templates. A first test of Laya (`typed-decisions`) read intent, subject and direction right on 15 of 16 questions, including typos and random questions, in about 0.7 s.

## Behavior
### The case
`Case` holds what the passes found: `intent` (`why`, `figure`, `widgets`, `other`), `metric`, `direction`, `month` (and `compared_with`), `scope` (`all` or `restricted`, with the words that restrict it when known), and `confidence` for each pass. The case is returned in the answer as `question` (as today, plus `scope` and `how_read`: the passes that ran).

### Passes (intent, subject and direction by Laya, one decision each, in order, stopping early)
1. **Intent.** `other` stops here with the refusal text; `widgets` stops here and the page uses the widget planner as today.
2. **Subject.** One of the registered metrics, or `none` (refused with the help text). The choices are built from the registry and `understanding.json` words, so a new metric needs no code.
3. **Direction** (`why` only): rise, fall or change.
4. **Scope** is read by a rule, not by Laya (changed on 2026-10-31: Laya caught none of 6 restricted questions in two wordings, 9 of 15 overall, all of them the unrestricted ones). A preposition (`to`, `from`, `of`, `for`, `by`, `at`, `in`, `with`) followed by a word that is not a metric, direction, month, period or generic word (`our`, `customers`, `end`) marks the question `restricted`. It is refused with a clear message ("I can only explain the whole company's figure for now") and never answered as the total. The rule can refuse a question that is really about the whole company; that is the safer mistake.
5. **Period** is not a Laya pass: month names and phrases are read by rules with fuzzy matching (standard library `difflib`) so "Augsut" is August; "last month", a year, and "this month" as today. Anything that is not one month ("last quarter", "this year") is refused with a message that says so.
A pass whose best choice is below `PASS_MIN_CONFIDENCE` (default 0.5) falls back to the rules for that pass; if the rules cannot decide either, the question is refused, never guessed. Laya off or unreachable (`LAYA_URL` blank or an error): the current rules-only reader runs unchanged.

### The answer from the case
Unchanged: figures, movers, graph walk, explained share, blocks. The case only replaces how the question is read.

### Tone rephrase (optional, `OLLAMA_MODEL`, off by default)
- A `tone` setting (`plain`, `executive`, `friendly`; default `plain` = templates as today).
- Each `text` line is sent on its own with the tone to the small model and accepted only if: every number, date and name in the line is present, in any order, and none is added (figures such as "2026" must not be dropped); one line; no markup; not longer than twice the original. Otherwise that line keeps its template text. The checks apply per line, so one bad line never spoils the rest.
- The model never sees the analysis or evidence, only the finished line.
- The model and tone are tested on the answers of every development scenario; the phase records which models pass the checks and how often.

### Evaluation
`sami-agents case-eval` runs a question set (`evals/cases.json`, with a tuning set and a held-out set written before tuning) through the reader and prints intent, subject, direction, scope and period accuracy, and what was refused. Laya off vs on is reported side by side. The set includes typos, reordered and loose phrasings, scope words, unsupported periods and random questions.

## Acceptance cases
- Typo, order and loose-phrasing questions read the same case as their plain forms ("Why did sales drop in Augsut?", "august sales dropped, what happened").
- "hi", "what is the weather" and "tell me a joke" are refused at pass 1; "show me top customers" is passed to the widget planner.
- "why did sales to Acme drop in august" is refused as restricted, not answered as the total.
- "why did sales drop last quarter" is refused as not one month.
- A low-confidence pass falls back to rules; with rules also unsure it is refused.
- Laya down: the rules-only reader gives today's results and the answer says nothing different.
- The rephrase keeps a line only when it passes the checks; a line that drops "2026", adds a figure, adds praise with a number, or is empty keeps the template.
- No outside calls: Laya and Ollama are the only added hosts, both from settings, and `test_no_outside_calls` lists them.
- Held-out accuracy is reported with its limits, as for the keyword evaluation.

### Small change in synapse-web (added 2026-10-31, the spec allows it)
`parseAnswer` keeps the problems `restricted` and `not_one_month`, and `AiPage` shows the agent's text for `not_finished`, `restricted` and `not_one_month` (never the widget planner). `widgets` and `unreadable` still go to the planner. The page does not show `how_read` yet.

### Follow-up questions (added 2026-10-31 after the owner's try-out)
"Give me the reason for the decline" right after "What were sales for August 2026?" has no metric and no month, so it could not be read and the page showed an unrelated widget.
- `POST /v1/agents/analyse` accepts an optional `context`: `{metric, month}` (the metric name and `YYYY-MM` of the last answered question). The answer's `question` already carries both.
- Context only fills gaps: a metric or month the user typed always wins. It is used only when the question has an intent (a why or figure word, or Laya's intent pass says why or figure) and a metric or month is missing. A registered metric and a valid month are required, otherwise the context is ignored.
- `how_read` says when a part came from the previous question ("metric: from the previous question").
- The page remembers the `question` of the last readable answer and sends it with the next message; a new complete question replaces it.
- Acceptance: after a figure answer for sales in August, "why did it fall", "give me the reason for the decline" and "why?" each explain August sales; "why did purchases fall" uses purchases but August; "why did sales fall in June" uses June; with no context they are unreadable as before; a bad context is ignored.

## Out of scope
Fine-tuning a model, scope filters that actually answer for one customer, periods other than one month, several metrics in one question, a model writing figures or causes.

## Depends on
sami-agents 05 and 03 (merged), synapse-web 12 (merged: the page shows `question` and the answer unchanged; showing how the question was read is a later small web change).
