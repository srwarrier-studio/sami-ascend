# Tasks

- [x] 1. Schemas, mapping and app skeleton: request and response models, domain mapping, `Settings` additions, app with CORS and request id, auth dependency, gateway dependency; add `fastapi` and `token-verification` dependencies. Done when the 401/403 cases and the malformed-body case pass.
- [x] 2. Create route: `POST /sales-orders` with `201`, `422` rejection and `503` mapping. Done when the create cases pass.
- [x] 3. List route: `GET /sales-orders` with paging, `INVALID_QUERY`, `503`. Done when the list cases pass.
- [ ] 4. Run script, README and `specs/notes.md`. Done when `workspace-api` starts on port 8002 and the README shows the routes.
