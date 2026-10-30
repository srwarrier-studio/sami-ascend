# sami-agents/01 chat-graph

## Goal
A new service, `sami-agents`, answers AI Mode messages with a small local model (Ollama, `gemma3:270m`) through a LangGraph graph, so synapse-web AI Mode stops using the keyword mock. A first evaluation tells us whether a 270M model can do the job.

## Behavior
- New app `apps/sami-agents` (FastAPI, port 8005, a `uv` workspace member, same layers as the other APIs: `domain`, `application`, `infrastructure` with `infrastructure/api/<domain>/`, `entrypoint`).
- Route `POST /v1/agents/chat`, body `{ message }` (1 to 500 characters), the same session cookie as the other APIs (verified with `token-verification`; any signed-in user with access to Synapse). Response `{ reply, catalogIds, board }`, the same shape as synapse-web's `ChatPlanner.plan`; `board` is `{ name, catalogIds }` or `null`.
- The model never sees business data. It sees the widget catalog (id, title, description) and the user's message, and returns only widget ids as JSON that follows a schema (Ollama structured output, temperature 0). Widget data still comes from synapse-api when the browser draws the widgets.
- The LangGraph graph has these nodes:
  1. `route`: a message starting with `@builder` builds a board (up to 15 widgets, a short name from the message); anything else is an inline answer (up to 4 widgets).
  2. `select`: asks the model for ids.
  3. `validate`: drops ids not in the catalog and repeats, and keeps the limits. Nothing the model writes is shown to the user except through this step.
  4. `fallback`: if the model fails, times out, returns invalid JSON or nothing valid, picks widgets by keyword match over title and description (the logic of today's mock), so AI Mode always answers.
  5. `reply`: a sentence written by code from the chosen titles (`Here is Sales today and Top customers.`; `I could not find a matching widget.` when none), not by the model.
- Ports and adapters: `ChatModel` (`OllamaChatModel` over `httpx`, `MockChatModel`) and `CatalogSource` (`SynapseCatalogSource` calls synapse-api `/v1/synapse/catalog` and forwards the user's cookie, `MockCatalogSource`). Use cases and the graph see only the ports.
- Settings from environment (`pydantic-settings`): `OLLAMA_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `gemma3:270m`), `SYNAPSE_URL`, `MODEL_TIMEOUT_SECONDS` (default 20), `FRONTEND_URL` for CORS.
- Evaluation: `evals/prompts.json` holds about 20 prompts (inline questions and `@builder` requests) with the widget ids a reasonable answer must include. `uv run sami-agents eval` runs them against the real Ollama and prints, per prompt and in total, valid JSON rate, widget hit rate, fallback rate and seconds per answer; it is not part of the test suite. The owner reads the numbers and decides whether the 270M model is enough, or tries the other models already in Ollama.
- synapse-web gets `HttpChatPlanner` (calls `POST /v1/agents/chat` with credentials, `VITE_AGENTS_URL`) used by `main.tsx`; `MockChatPlanner` stays the default for tests. If the service is down, AI Mode shows a clear message and keeps the chat open.

## Acceptance cases
- `route`: `@builder` returns a board and up to 15 ids; other messages return up to 4 ids and `board: null`.
- `validate`: unknown and repeated ids are dropped; limits hold.
- Model returns valid ids: they are used. Model raises, times out, returns invalid JSON, or returns only unknown ids: the keyword fallback answers.
- Reply text is the code-built sentence; a model-written string never reaches the response.
- The route rejects a missing or invalid cookie (401), an empty or over-long message (422).
- `OllamaChatModel` sends the schema and the catalog and reads the ids (tests use `httpx.MockTransport`); `SynapseCatalogSource` forwards the cookie.
- `HttpChatPlanner` maps the response; an unreachable service gives a readable error in AI Mode.
- No test calls Ollama, synapse-api or the network.

## Out of scope
Streaming replies, conversation memory, answering questions about the numbers (the model sees no data), parameterised widgets (month, customer), the OpenUI comparison, other agents, hosting and GPU sizing, rate limiting, per-company filtering.

## Depends on
shared 02 (token verification), shared 03 (structured logging), synapse-api 05 (catalog), synapse-web 11. New dependency `langgraph` (and what it pulls in) is recorded in `tech-stack.md` with licence and supplier checked before task 2.
