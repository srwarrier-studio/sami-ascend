# Constitution

Rules for sami-ascend that do not change from phase to phase. If a phase needs to break
one, change this file first, with the owner's approval.

## Purpose
Replace the legacy SAP dynpro screens with a web UI for S/4HANA. React frontends talk to
Python (FastAPI) backends. Backends talk to SAP OData (RAP). The browser never calls SAP.

## How we work
1. **Small phases.** A phase has one goal in one sentence. At most 5 task groups.
2. **Small task groups.** About 5 files or 300 changed lines at most. If it grows, stop and split.
3. **Review before commit.** The agent finishes a task group, stops, and shows the changes.
   It commits only after the owner says so. One commit per task group.
4. **One branch per phase:** `<app>/phase-<nn>-<name>`, for example `auth-api/phase-01-login-audit`.
5. **Each app has its own phases** in `specs/<app>/<nn>-<name>/`. Phases that span apps live in
   `specs/shared/`. Several phases can be open at the same time; use one `git worktree` per
   open phase. The phase folder exists only on its own branch, and the current branch name
   tells a session which phase it is in. Open phases are listed by
   `git branch --list '*/phase-*'`, not in the roadmap.
6. **Phase folder:** `spec.md` (goal, behavior, acceptance cases, out of scope, depends on),
   `tasks.md`, `notes.md`, `reference/` for external material.
   `tasks.md` is a checklist (`- [ ]` / `- [x]`), each task with a one-line "Done when". The agent
   ticks a task in the same commit that finishes it.
7. **Spec first.** Agree the spec before code. Acceptance cases become tests.
8. **Closing a phase:**
   - All tests pass and the security checklist items touched are updated.
   - Important knowledge moves to `specs/notes.md`; `specs/roadmap.md` gets the status line.
   - Tag `<app>-phase-<nn>-done`, then delete the phase folder.
   - Merge without squashing, so the phase folder stays in history as change-management evidence.

## Code style
- Clean architecture with these folders per backend app: `domain` (entities, value objects,
  repository and service interfaces), `application` (use cases, DTOs), `infrastructure`
  (implementations, including the HTTP routers, schemas and deps under `infrastructure/api/<domain>/`),
  `entrypoint` (the ways the outside world reaches the app: app factory, server runner, CLI).
  Dependencies point inward only.
- Simple classes with clear names. One use case is one class with one `execute` method.
- Nothing clever: no metaprogramming, no deep inheritance, no abstractions with one use.
  The owner must be able to read the code and understand it.
- No comments unless they are directive or genuinely useful.
- Standard library first. A new dependency needs a reason in `tech-stack.md`.

## Testing
- Every use case and every rule has a test. Plain `pytest`, small tests, no fixtures framework.
- Tests never call SAP, Entra or the network.

## Parallel development
- SAP and auth are always behind an interface with a mock implementation.
- An API's contract (routes and schemas) is agreed in its phase spec, so the web app can be
  built against a mock before the API is finished.

## Security
- `docs/security-checklist.md` applies to every change. Section 1 on every PR.
- Never commit secrets. Authorization data stays in SAP; the app owns roles for page access.
