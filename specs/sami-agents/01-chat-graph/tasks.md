# Tasks

- [x] 1. App scaffold: workspace member, settings, health route, cookie verification, structured logging, the `ChatModel` and `CatalogSource` ports with their mocks. Done when the scaffold and port tests pass.
- [x] 2. The graph (`route`, `select`, `validate`, `fallback`, `reply` with the OpenUI Lang writer) on the mocks, with `langgraph` added and recorded in `tech-stack.md`. Done when the graph acceptance cases pass.
- [ ] 3. `OllamaChatModel`, `SynapseCatalogSource` and the `POST /v1/agents/chat` route. Done when the adapter and route cases pass.
- [ ] 4. Evaluation prompts and `sami-agents eval`; run it against `gemma3:270m` and record the numbers in `specs/notes.md`. Done when the owner has read the results.
- [ ] 5. OpenUI text contract test and `README` (how to run Ollama and the service); the owner tries the route with `curl`. Done when the contract case passes and the owner has seen real answers.
