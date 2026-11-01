# Tasks: intent-api/03 answers

- [ ] 1. Response table: `answers.toml`, its loader and `answers check`, the `Answer` and `Block` entities. Done when: the check passes on the library and fails on the three bad entries of the acceptance cases.
- [ ] 2. Period: the rules that read the period from the question and refuse unsupported ones. Done when: the tests list every phrasing and refusal (month, last month, this month, last year, a year, none, two periods).
- [ ] 3. Data gateway: `MetricSource` port, `SynapseMetricSource` (httpx, cookie forwarded) and a mock. Done when: month, compare and ranked compare are read and every failure is `MetricsUnavailable`.
- [ ] 4. Responders: value, compare, trend and ranking, with the sentence templates. Done when: each kind passes its test with the mock, including no data and two currencies.
- [ ] 5. Route: `POST /v1/intent/answer` (reading plus answers, refusals unchanged, `cannot_fetch_now`), the `unanswered.jsonl` log and the README. Done when: the route tests pass for single, combined and refused questions.
- [ ] 6. Close-out: `notes.md`, roadmap and README entries. Done when: all tests pass and the phase is ready to merge.
