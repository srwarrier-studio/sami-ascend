# synapse-web/09 preset-boards

## Goal
Management does not build boards from scratch: the Add widget drawer offers ready-made preset boards that become the user's own board in one click.

## Behavior
- The Add widget drawer gets two tabs, `Widgets` (today's library) and `Preset boards`.
- `presets.ts` holds the presets: `{ id, name, description, catalogIds }`, catalog ids only, no layout (widget order is the layout). A preset whose catalog ids are not in the loaded catalog drops those ids; a preset left with none is not listed.
- First presets (owner confirms the names and contents before task 1 starts):
  - `Sales overview`: sales today, month, year, orders this month, month on month, day sales, status split, month target.
  - `Customers and materials`: top customers, top materials, high value sales.
  - `Daily pulse`: sales today, orders this month, day sales, month target.
- The `Preset boards` tab lists each preset as a card with name, description and widget count. Choosing one (button `Use this board`) creates a new board named after the preset with its widgets (`buildWidgets`, so at most 15) and opens it; the drawer closes.
- At 3 boards the same replace flow as `SaveBoardModal` asks which board to replace, and changes nothing until confirmed.
- Choosing a preset never changes the board the user is on.
- Presets are the same for every company until the later company-data phase.

## Acceptance cases
- The drawer shows both tabs; `Widgets` behaves as before.
- Each listed preset shows name, description and widget count.
- `Use this board` creates a board with that name and those widgets, opens it, closes the drawer.
- At 3 boards the replace choice appears; confirming replaces the chosen board, cancelling changes nothing.
- A preset with unknown catalog ids drops them; one with none left is not listed.
- The current board is unchanged after choosing a preset.

## Out of scope
Editing or saving presets, presets per company or role, presets from synapse-api, preset thumbnails, adding a preset's widgets to the current board.

## Depends on
synapse-web 08.
