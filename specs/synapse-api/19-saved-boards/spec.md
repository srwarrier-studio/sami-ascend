# synapse-api/19 saved-boards

## Goal
Each user's boards are saved on the server, and a user can mark a board public so others can copy it. This is the former board-storage phase 04.

## Behavior
- **Store.** SQLite behind a repo port: board id, owner user id, owner name, name, `is_public`, widgets (id, catalog id, size, position), timestamps. A user has at most 3 boards, as in the web app.
- **Routes** under `/v1/synapse/boards`, any Synapse user (synapse-api 18 gate):
  - `GET` the caller's boards, each widget kept as saved.
  - `POST` create (name, `is_public`, optional widgets), `PATCH {id}` rename or set `is_public`, `PUT {id}/widgets` save layout, `DELETE {id}`. Only the owner may change or delete (`403` otherwise).
  - `GET /shared` public boards of other users, each with owner name and `shared: true`, widgets cut down to the ones the caller may see (synapse-api 18). A board left with no visible widget is not listed.
  - `POST /shared/{id}/copy` copies a visible shared board into the caller's own boards (name kept, private, only the widgets the caller may see); `409 BOARD_LIMIT` at 3 boards.
- Saving a board with a widget the caller may not see is `403 WIDGET_NOT_ALLOWED`.
- Own boards keep every widget, even if the owner's roles later lose access; the widgets are hidden when read, and returned again if access comes back.

## Acceptance cases
- A user lists only their own boards; another user never sees a private board by id (404).
- A public board appears in the other user's shared list with the owner name and without the widgets that user may not see.
- Copying makes an independent private board; later edits by the owner do not change the copy.
- A non-owner PATCH, PUT or DELETE is 403; the 4th board is refused.
- Boards survive a restart.

## Out of scope
Live (non-copy) sharing, per-user or per-group sharing, comments, versioning, migration of browser-only boards.

## Depends on
synapse-api 18.
