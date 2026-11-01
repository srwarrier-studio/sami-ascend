# Integrations and reference patterns

Not needed for intent-api today; kept so we know what exists. All integrations share: local mode (in-process) or remote mode (`base_url`, `api_key` to a `laya-serve`, no PyTorch on the client); confidence is uncalibrated by default; past about 20 candidates the shared token budget degrades quality (widening `max_len` and `head_max_len` helps at large rosters, can hurt small ones); hooks are local-only (hooks with a `base_url` raise `ValueError`); agent-backed nodes reject `task` and `lang_guess`.

## Architectural patterns (use-cases page)
Laya returns calibrated-ish distributions in one forward pass; embeddings retrieve, LLMs generate, Laya classifies, gates and routes.
1. **Smart ingress gateway:** classify complexity (`canned`, `structured`, `complex`) plus a `noul` "needs frontier reasoning"; resolve simple high-confidence requests locally, escalate otherwise (`min_confidence=0.85`, check `low_confidence`). The closest pattern to ours.
2. **Voice turn-taking:** `ack/reject/interrupt/inquiry` choice plus `is_interruption` noul (threshold 0.6 in the example).
3. **Pre-LLM prompt firewall:** `noul` questions for jailbreak, system-prompt extraction, credentials; a `BaseHook` raising in `on_predict_start` (`hooks_raise=True`) blocks the request. The example enforces two of its three questions (docs note this).
4. **Air-gapped RAG router:** a `choice` of domains picks one local index. Same shape as our domain-then-scenario flow; the docs add: gate low confidence or add a fallback if misrouting is costly.
5. **Hierarchical delegation:** `choice` assignee plus `score` priority 1 to 5; check whether a score comes back as a string or integer before comparing.
6. **High-volume ticket triage:** `decide_batch` with a strict schema (department enum, severity 1 to 5 integer, escalation boolean).
Deployment checklist: size host memory for resident weights and tune CPU threads; use `min_confidence` about 0.80 to 0.90 on critical gates; use `Router()` for mixed languages; shadow before going authoritative. Thresholds in the examples (0.5, 0.6, 0.85) are illustrative, not tuned.
Doc inconsistencies to be aware of: examples use `laya.load` in some places and `Agent(...)` in others; pattern 1 reads a `low_confidence` key that is only defined for answers when `min_confidence` is passed.

## Tool and function selection (`laya.integrations.tools`)
`LayaToolSelector(tools=[...])` (Python functions, LangChain/CrewAI/LlamaIndex tools, JSON-schema specs, dicts with `name` and `description`, or `"name: description"` strings). `select(query)` returns a `ToolRouteDecision` (`tool_name`, `tool_index`, `confidence`, `probabilities`, `is_fallback`, `is_direct_answer`); `aselect` async; `call(query, **kwargs)` runs the chosen tool; `allow_direct_answer=True` lets it say "no tool"; `confidence_threshold` with `fallback_tool` or `LayaLowConfidenceError`; `as_runnable()` for LCEL; remote mode with `base_url`. Claims 1,000 to 2,500 ms for LLM tool calling against about 33 ms (T4) for Laya. Selection reads names and descriptions only, so write them carefully.

## LangChain / LangGraph (`laya[langchain]`)
`LayaRouter(criteria, instructions, confidence_threshold=0.0, fallback=None)` for conditional edges; `LayaGuardrail(questions, action="raise"|"filter"|"annotate", threshold=0.5)` with `LayaGuardrailError`; `LayaTriage` (intent, urgency, frustration, churn risk); `LayaEvaluator` (rubrics, `evaluate_strings`); `LayaDecision(schema, state_key=...)`. `state_key` may be a callable. `batch()` runs one batched pass. On Apple silicon `LayaDecision.batch()` may need `max_concurrency=1`. Guardrail threshold on a `score` question is the probability of a serious/severe level, not the expected score.

## LlamaIndex (`laya[llamaindex]`)
`LayaSingleSelector(confidence_threshold, fallback_index)` for `RouterQueryEngine`, `LayaMultiSelector`, `LayaQueryRouter`. `raise_on_low_confidence=True` raises `LayaLowConfidenceError`.

## CrewAI (`laya.integrations.crewai`)
`LayaCrewRouter(confidence_threshold, fallback_agent_index)` with `route`, `aroute`, `delegate(task, agents)`; `LayaTaskGuard(action, threshold)` with `LayaTaskGuardError`.

## Agno (`laya[agno]`, needs `agno>=1.1.14,<2`)
`LayaAgnoRouter` (`route`, `route_team` for `Team(mode="route")`), `LayaAgnoGuardrail`, `LayaAgnoGuardrailError`. Selects an agent, does not run it.

## TypeScript
`laya-client` (npm, not yet published under that name, v0.1.0): dependency-free HTTP client for a self-hosted `laya-serve`; `predict` (to `/v1/systemone`) and `health`; no routing method; no retries; validates options client-side. In-process inference in JS is `laya-ts`.
