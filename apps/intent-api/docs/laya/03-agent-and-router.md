# Agent and Router

Install: `pip install laya` (extras: `laya[serve]`, `laya[mcp]`, `laya[structured]` for pydantic, `laya[fast]`, `laya[langchain]`, `laya[llamaindex]`, `laya[agno]`). Laya declares `Requires-Python >=3.10`. Checked 2026-11-01: laya 0.4.19 with torch 2.15.0+cpu and transformers 5.22.1 installs and runs on Python 3.14.2 (the workspace version): model loads in about 6 s, calls take about 0.5 s. Install torch from the CPU index first (`--index-url https://download.pytorch.org/whl/cpu`) or the CUDA libraries are pulled in.

Import rule: most names from `laya`, but `ONNXAgent` is in `laya.onnx_agent` and fine-tuning in `laya.train`.

## load()
`laya.load(model_id_or_path="convaiinnovations/laya", device=None, token=None, subfolder=None, fast=False, compile=False, revision=None, expected_sha256=None, lang_temperatures=None, hooks=None, on_predict_start=None, on_predict_end=None, hooks_raise=True, hooks_concurrent=True, hooks_timeout=None, calibration=None, backend=None, onnx_path=None, compile_warmup=True, compile_cache=False, compile_mode="default")`

Returns an `Agent` (an `ONNXAgent` for `backend="onnx"`). Accepts the same checkpoint aliases as `Router`: `"typed-decisions"`, `"ml"` for multilingual. `subfolder` selects one checkpoint from the bundle and only that one downloads. Our tests: `laya.load("convaiinnovations/laya")` and `laya.load("typed-decisions")` both worked; load took about 5 s on CPU after the files were cached.

## Agent: the calls
- `system_one(state, questions, lang=None, hooks=..., max_len=None, head_max_len=None, min_confidence=None)` one state, returns `{"answers": {...}, "usage": {...}}`. `predict` is an alias. Empty questions return empty answers and zero usage without a forward pass.
- `predict_batch(states, questions, batch_size=None, lang=None, ..., sort_by_length=False, min_confidence=None)` same questions over many states in shared passes, results aligned by index. `sort_by_length` needs an explicit `batch_size` of 2 or more.
- `predict_long(state, questions, window=None, stride=None, aggregate="auto", batch_size=None, ...)` for text longer than the context: overlapping windows; `noul` takes the max over windows, `choice` and `score` take the most confident window. Not needed for manager questions.
- `decide`, `decide_batch` see 02.
- Calibration: `fit_temperatures`, `fit_binning`, `save_calibration(path)`, `load_calibration(path)`.
- Speed: `accelerate()` / `deaccelerate()` (TileLang, CUDA only), `warmup(shapes)`, `set_backend(name)`.

Token budget: `max_len` (total) and `head_max_len` (the options part) default from the checkpoint (about 512 and 192). Past about 20 options per question, option labels collapse into each other; see "Many options" in 05.

## Router
Picks a checkpoint per request, loads it on first use, evicts the least recently used (`max_loaded=2` by default).

`Router(models=None, device=None, token=None, revision=None, revisions=None, max_loaded=2, default="multilingual", auto_task_detection=False, standalone_repos=False, preload=False, lang_guess=None, hooks=..., agent_kwargs=None, sha256_digests=None)`

Routing order, first match wins:
1. `model=` pins a checkpoint (invalid names raise `ValueError`).
2. `task=` selects the checkpoint for the named task.
3. Auto task detection (`auto_task_detection=True`): `typed-decisions` only when the question ids exactly match a known typed-decisions set. It never infers from wording.
4. `lang=`: English goes to `english`, other recognised codes to `multilingual`.
5. `lang_guess=` (per call or on the router; a callable may return a code or `None`).
6. Built-in script and language detection (a light heuristic, weaker for short or ambiguous text); no signal means `default`.

The English checkpoint can be confident on text it handles badly outside English, so use `Router` for mixed-language input. The multilingual checkpoint scores below English on English slices.

Methods: `route`, `route_batch` (no checkpoint load), `predict`, `predict_batch` (mixed requests, grouped by checkpoint and schema), `predict_long`, `decide`, `decide_batch`, `load`, `preload`, `unload`, `attach`, `register(name, source)` / `unregister` (custom checkpoints: Hub id, `(repo, subfolder)`, or a local dir with `model.safetensors` and `rl_agent_config.json`), `registered`, `loaded`, `loaded_revisions`. `Router()` downloads nothing until first use. As a context manager it unloads on exit. `explain=True` adds a routing `diagnostic` (stage, reason, source).

The `Router` result is the normal payload plus a `routing` key (`model`, `repo`, `reason`, `detection`, `workflow`).

## Shortlisting and tournaments (many options)
- `predict_shortlist(agent, state, questions, embed_fn, k=20)` narrows a long choice to the top-k labels by embedding similarity, then answers once. Helpers: `shortlist_choice`, `embed_fn_from_agent`, `cached_embed_fn`.
- `predict_tournament(agent, state, questions, group_size=16)` narrows by elimination rounds with the decision model itself; no embedder. Probabilities come from the final pass over finalists only, so thresholds fitted on the full set need re-measuring.
- Both drop a caller-supplied `option_order` for narrowed choices.

## Presets, email, language helpers
`laya.detect_language`, `detect_script`, `is_english`; `clean_email_body`, `email_state`; the five question presets; `state_room`, `window_budget`, `collapsed_options` (sizing checks).

## ONNXAgent
`ONNXAgent(model_id_or_path, onnx_path="laya.onnx", ...)` runs an exported ONNX model on CPU; same `system_one`, `predict_batch`, `predict_long`, `decide` calls. `scripts/export_onnx.py --quantize` writes an INT8 model (about 2x faster than eager on CPU, 1.4 to 2.8x smaller) at a cost in accuracy and calibration; avoid it where confidence matters. `LAYA_CPU_AMP=bf16` runs the CPU forward in bf16, only on CPUs with native BF16 (otherwise the process can die with SIGILL).
