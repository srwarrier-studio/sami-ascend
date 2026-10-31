# Tasks

- [ ] 1. Failure classes and the write limit: the gateway tells "not processed" from "unknown", and a wrapper allows `SAP_WRITE_LIMIT` writes at a time. Done when the classification and limit cases pass.
- [ ] 2. The order store: the repo interface, the SQLite implementation and the statuses with their transitions. Done when the save, claim, record, restart and own-orders cases pass.
- [ ] 3. Posting with the queue fallback and the two status routes. Done when the posting, `202`, status route, role and 503 cases pass.
- [ ] 4. The worker: claim, post, back-off, give-up, no retry of `unknown`, and its start in `run.py`. Done when the worker cases pass, including two workers and failing in every order.
- [ ] 5. The butterfly in-process case, the notes and the roadmap. Done when the butterfly case passes and the owner has the settings table.
