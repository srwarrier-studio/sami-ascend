# synapse-web/03 board

## Goal
Users keep their own boards as tabs, arrange catalog widgets in Edit mode, and see them refresh every 5 minutes, all on a mock board store.

## Behavior
- `BoardStore` (interface, `MockBoardStore` in memory, seeded with one "Sales overview" board): `list`, `create(name)`, `rename(id, name)`, `remove(id)`, `saveWidgets(id, widgets)`. A board is `{ id, name, widgets: { id, catalogId }[] }`, widget order is the layout. This is the contract synapse-api 04 will implement.
- `/` shows the active board: widgets in a 12-column grid, each spanning its registry `defaultW`. The `PageBar` at the bottom lists the boards; `+ Add` creates "Board n" and opens it.
- Edit button toggles Edit mode. In Edit mode: the board title in the page header becomes editable (Enter or blur saves, empty is ignored, Escape cancels) — rename lives in the header, not in the bar; each widget shows move earlier, move later and remove buttons and can be dragged onto another widget to reorder; **Add widget** opens the widget catalog (`WidgetCatalog`) in a modal and adds the pick at the end; **AI Mode** opens a drawer where a sentence adds the catalog widgets whose title or description share a word with it (a stand-in for the AI POC; says when nothing matched); **Delete board** asks to confirm. Outside Edit mode none of these show. The last board cannot be deleted.
- Changes save to the store at once.
- Each widget reloads its data every 5 minutes (`refreshMs`, default 300000) and keeps showing the old data meanwhile.
- No dropdown filters anywhere.
- `@sami/ui` change: `PageHeader` takes `editing` and `onTitleChange`; `PageBar` loses rename (`editing`, `onRename`); the playground follows.

## Acceptance cases
- Store: create, rename, remove, saveWidgets, list; unknown id is an error.
- Board page: shows the first board's widgets; switching tabs shows the other board; add board.
- Outside Edit mode there are no edit controls and the title is not editable.
- Edit mode: rename in header; remove; move later and earlier; drag reorder; add widget from catalog; AI Mode adds matching widgets, reports no match; delete asks to confirm and cannot remove the last board.
- Refresh: after `refreshMs` the widget loads again and does not flash a skeleton.
- Header and PageBar tests updated.

## Out of scope
Resize, real API, saving per user, AI model.

## Depends on
synapse-web 02, shared 10.
