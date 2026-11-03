# synapse-web/19 saved-boards

## Goal
Boards are loaded and saved through synapse-api instead of the mock store, a board can be made public, and the Add widget drawer lists other people's public boards, tagged Shared, to copy.

## Behavior
- **Store.** An HTTP `BoardStore` replaces `MockBoardStore` (same port, plus `setPublic`, `listShared`, `copyShared`). Layout changes save as today (debounced), with a small failure message and no lost edit on error.
- **Public.** A `Public` switch in the board's Edit mode and in the AI save-as-board modal. A public board shows a `Public` badge in the header (not on its tab).
- **Drawer.** A `Layouts` tab in the Add widget drawer next to Preset boards (a small addition to `WidgetLibrary` in `@sami/ui`): shared boards as cards with the board name, `Shared` tag, owner name and widget count. One click opens the save modal (same replace flow at 3 boards) and saves a private copy through the normal create and save calls. Empty state: "No shared boards yet".
- **Access.** The catalog and boards already arrive filtered; the app shows a department user the widgets they may use, no placeholders for hidden ones. The app gate (`access.ts`) allows every role synapse-api 18 allows.
- Signed-out or a 403 on a board shows the existing "No access" message.

## Acceptance cases
- A board created, renamed and edited survives a reload and a new sign-in.
- A public board of user A appears under Layouts for user B with the Shared tag; copying it adds a private board for B.
- A shared board with Finance widgets shows B (production) only its non-Finance widgets, with no gap or placeholder.
- At 3 boards, copying asks to replace one.
- A production user can open Synapse and sees only Production widgets in the drawer.

## Out of scope
Live sharing, unsharing copies, a manage-sharing page.

## Depends on
synapse-api 18, synapse-api 19, synapse-web 18.
