# Tasks

- [x] 1. Dependencies, `Settings` additions and a lock in `SalesCache`. Done when `uv sync` works and a thread test on the cache passes.
- [x] 2. Response models and `create_app` with the three period-total routes, role check and error handlers. Done when access, body and 503 cases pass.
- [ ] 3. Month-on-month, top customers, top materials and high-value routes. Done when their body and 422 cases pass.
- [ ] 4. Cache wiring in the routes. Done when the cache hit, key and stale cases pass through HTTP.
- [ ] 5. `entrypoint/run.py`, logging setup, request id and CORS; notes updated in `specs/notes.md`. Done when the app starts against butterfly and the request id case passes.
