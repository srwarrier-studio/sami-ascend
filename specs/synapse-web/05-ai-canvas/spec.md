# synapse-web/05 ai-canvas

## Goal
AI Mode becomes a full page with a canvas on top and a chat box at the bottom; the user asks, and a mock planner draws catalog widgets on the canvas, which can be saved as a board.

## Behavior
- `/ai` is a page of its own. The AI Mode button on the board page links to it and the old `AiDrawer` is removed.
- Layout: the canvas (a `WidgetGrid` of `WidgetCell`, always in edit-like mode: remove, resize, drag to reorder) fills the page; a fixed chat box sits at the bottom with an input and send button; above it the last question and the AI's one-line reply; a side sheet shows the whole conversation. An empty canvas shows a short welcome and example prompts that fill the input when clicked.
- Toolbar: **Save as board**, **Clear**, **Undo** (last AI step or last clear).
- `ChatPlanner` (interface, `MockChatPlanner`): `plan(message, canvas) => Promise<{ reply: string; ops: CanvasOp[] }>`. `CanvasOp` is `add(catalogId)`, `remove(widgetId)`, `resize(widgetId, size)` or `replaceAll(catalogIds)`. This is the contract the OpenUI and Ollama engine will implement in a later phase.
- `MockChatPlanner` matches words in the message against catalog titles, descriptions and the domain names; "start over" or "clear" gives `replaceAll([])`; "remove x" gives `remove`; "bigger" or "smaller" gives `resize`; a message that is a board request ("build", "board", "review") gives `replaceAll` with that domain's widgets; no match gives a reply that says so with example prompts and no ops.
- `applyOps(widgets, ops)` is a pure function in `boards/layout.ts` and the only way ops touch the canvas. It drops unknown catalog ids, drops a catalog widget already on the canvas, clamps sizes to `allowedSizes`, and stops at `MAX_WIDGETS` (15).
- Save as board: needs at least one widget. With fewer than `MAX_BOARDS` (3) boards it asks for a name (the planner may suggest one), creates the board with the canvas widgets and opens it. At 3 boards it shows "You have 3 boards. Pick one to replace", lists them by name, and replaces the chosen board's name and widgets only after a confirm button that names that board.
- The canvas lives for the session only; refreshing clears it unless it was saved.
- Parameterised widgets (month, customer, top-N) are not part of this phase. The planner only draws the existing catalog widgets. They come with the engine phase, with `SalesData` queries behind typed parameters.

## Acceptance cases
- `applyOps`: add, remove, resize, replaceAll; unknown id ignored; duplicate ignored; size clamped; stops at 15.
- `MockChatPlanner`: a topic word adds its widgets; "start over" clears; "remove top customers" removes it; a board request fills the canvas; unrelated text returns no ops and says so.
- Page: empty welcome with prompts; sending a message shows the reply and draws widgets; remove, resize and reorder work on the canvas; Clear and Undo.
- Save: new board under the limit (named, opens it); at the limit it asks which board to replace, does nothing until confirmed, and the replaced board's widgets and name change; Save is disabled on an empty canvas.
- The board page's AI Mode links to `/ai`.

## Out of scope
OpenUI, Ollama, any model; answering data questions with parameterised charts; saving the conversation or canvas; real API.

## Depends on
synapse-web 04.
