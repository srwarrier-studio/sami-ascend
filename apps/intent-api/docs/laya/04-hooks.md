# Prediction hooks

Hooks observe or change every decision without touching Laya's code. Opt-in; no hooks means unchanged behaviour. They also work with LangChain/LangGraph runnables (per node). `laya.hooks` is pure Python (importing `laya` does not load torch).

## Six events
| Event | Runs | May change |
|---|---|---|
| `on_predict_start` | Agent and Router, before inference | `states`, `questions`, token budgets, or `ctx.skip(results)` |
| `on_predict_end` | after results, success or failure | `results` |
| `on_route` | Router, after detection, before loading | `decision` |
| `on_load` | Router, after a checkpoint is built | observe only |
| `on_evict` | Router, after a checkpoint is freed | observe only |
| `on_error` | on failure | observe only |

Router-only: `on_route`, `on_load`, `on_evict`. `ONNXAgent` supports only the predict events. `laya.serve` and the MCP server call `Router.predict`, so Router hooks fire there automatically.

## How to attach
- Object with any subset of the six methods: `hooks=[Audit()]` (subclass `BaseHook` for no-op defaults). A class (not instance), an object with no events, or a plain callable in `hooks=` raises `TypeError`.
- Plain function for the two predict events only: `on_predict_start=fn`, `on_predict_end=fn`.
- Runtime: `agent.add_hook(h)`, `agent.remove_hook(h)` (by identity), `with agent.hooks_installed(h): ...`.
- Process-wide: `hooks.set_default_hooks(hooks=[...])`, `add_default_hook`, `clear_default_hooks`. Order: defaults, then instance, then per-call.
- Per call: `agent.system_one(state, q, on_predict_end=fn, hooks_raise=False)`.
- Async: wrap in `AsyncHook(obj)` or pass a plain async callable; runs to completion inside the sync core.

## PredictContext (one per public call, shared by start, error and end)
`states`, `questions`, `run_id` (uuid4 hex), `results` (None until done), `decision` (Router), `model`, `agent`, `router`, `max_len`, `head_max_len`, `usage`, `started_at`, `elapsed_ms`, `error`. Batch calls hold many states, so loop `zip(ctx.states, ctx.results)`; `ctx.usage` and `ctx.elapsed_ms` are call totals. Do not store `ctx` (memory leak); store the few fields you need.

`ctx.skip(results)` from a start hook skips the forward pass (cache hits); `on_predict_end` still runs and the Router adds `routing`. A cache key must cover states, questions (not `sort_keys`, order is positional), model, `max_len`, `head_max_len`.

## Errors
- `hooks_raise=True` (default): a hook exception propagates. `False`: warns (`RuntimeWarning`) and continues.
- A raise in `on_predict_start` aborts inference but `on_error` and `on_predict_end` still run. `on_error` and failure-path `on_predict_end` never mask the original exception (chained as `__context__`).
- A raise in success-path `on_predict_end` discards the computed result and fails the call: use `hooks_raise=False` for side-effect-only end hooks.
- `KeyboardInterrupt` and `SystemExit` always propagate.
- `hooks_timeout` (positive finite seconds, not a bool): a slow hook raises `TimeoutError` (or warns) but keeps running in its thread; give network calls their own timeouts.
- Recommended policy: guardrails and redaction `True`; metrics and tracing `False`; caches `True`.
- Warnings use Python's dedupe, so the stream is not a failure counter.

## Lifecycle notes
- `predict_batch([])` still fires hooks with `results=[]` and zero usage. `usage` is `None` only when the call failed before producing results.
- Router `predict_batch`: one context per request; start hooks all run before end hooks; end hooks run in reverse order; requests are grouped by `(questions, max_len, head_max_len)`.
- `elapsed_ms` on a Router excludes routing and cold loads.
- `hooks_concurrent=False` serialises hook calls with a re-entrant lock.
- A hook that calls `predict` recurses: guard it or use a separate hook-free agent.

## Patterns that map to our needs
- Audit log in `on_predict_end`: one JSON record per state with `run_id`, model, state, answers, usage, latency. Good for the unanswered/low-confidence log.
- Confidence gate in `on_predict_end`: rewrite low-confidence answers to a fallback and set `gated`.
- Cache: start hook `skip`s on a full hit, end hook stores. Useful if managers repeat questions.
- Metrics: count per model, collect `elapsed_ms`, `hooks_raise=False`.
- Token-budget shaping: raise `head_max_len` and `max_len` in a start hook for questions with many options (need about `16 + 8*k` head tokens for k options).
- `OptionStabilityHook`: probes reordered and renamed options in one batch and reports `soft_stability`, `stability`, and a decision `ACCEPT/VERIFY/ESCALATE`; cost about 2x (fast) to 3.7x (full) CPU latency. Calibrate cutoffs with `laya.hooks.calibrate_reliability`. A candidate way to catch confident wrong answers; not tried by us.

## Tracing
`run_id` ties start, error and end together. `on_route`, `on_load`, `on_evict` get their own contexts and run ids (a warm `Router.predict` makes 2 contexts, a cold one 3, one that also evicts 4). Close spans in `on_predict_end` only (it always runs). A nested `predict` inside a hook gets its own `run_id`; link it explicitly. OpenTelemetry works with a synchronous exporter or a queue.
