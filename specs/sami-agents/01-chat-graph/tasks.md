# Tasks

- [ ] 1. App scaffold: workspace member, settings, health route, cookie verification, structured logging, the `ChatModel` and `CatalogSource` ports with their mocks. Done when the scaffold and port tests pass.
- [ ] 2. The graph (`route`, `select`, `validate`, `fallback`, `reply`) on the mocks, with `langgraph` added and recorded in `tech-stack.md`. Done when the graph acceptance cases pass.
- [ ] 3. `OllamaChatModel`, `SynapseCatalogSource` and the `POST /v1/agents/chat` route. Done when the adapter and route cases pass.
- [ ] 4. Evaluation prompts and `sami-agents eval`; run it against `gemma3:270m` and record the numbers in `specs/notes.md`. Done when the owner has read the results.
- [ ] 5. `HttpChatPlanner` in synapse-web and the unreachable-service message. Done when the web cases pass and the owner tries AI Mode end to end.
