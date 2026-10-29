# synapse-web/05 ai-chat

## Goal
AI Mode is a full-screen chat: answers come back as messages with their charts inside, and `@builder` builds a whole board that opens in a modal and can be saved as a board.

## Behavior
- `/ai` is a page of its own with no app header: a page header (title, Back to boards) and a single centred chat column. The thread scrolls, the message box is pinned at the bottom, your messages are filled bubbles on the right, the AI's are plain bubbles on the left. An empty thread shows a welcome with example prompts (one for `@builder`) that send themselves. A "Thinking..." bubble shows while the planner works. The board page's AI Mode button (always visible) links here.
- There is no canvas. A normal question gets a reply message that carries the matching catalog widgets inside the message (at most 4), drawn with the same widget grid and live data as a board.
- `@builder <request>` asks for a whole board. The reply is a short message with an **Open board** button, and the board opens in a modal at once: the proposed widgets in a read-only grid, a suggested name, **Save as board** and **Close**. The modal can be reopened from the message.
- `ChatPlanner` (interface, `MockChatPlanner`): `plan(message) => Promise<{ reply: string; catalogIds: string[]; board?: { name: string; catalogIds: string[] } }>`. A message starting with `@builder` returns `board`; anything else returns `catalogIds`. This is the contract the OpenUI and Ollama engine will implement in a later phase.
- `MockChatPlanner`: a normal message adds the catalog widgets whose title or description share a word with it; `@builder` with a domain name (Sales, Inventory...) takes that domain's widgets and names the board "<Domain> review", otherwise it takes the matches, named "My board"; no match says so and shows how to ask.
- `buildWidgets(catalogIds)` in `boards/layout.ts` turns ids into board widgets: unknown ids and repeats are dropped and it stops at `MAX_WIDGETS` (15). It is the only way a proposal becomes board widgets.
- Save as board: with fewer than `MAX_BOARDS` (3) boards it asks for a name (prefilled), creates the board and opens it. At 3 boards it shows "You have 3 boards. Pick one to replace", lists them by name, and replaces the chosen board's name and widgets only after a confirm button that names that board.
- The conversation lives for the session only.
- Parameterised widgets (month, customer, top-N) are not part of this phase; they come with the engine phase.

## Acceptance cases
- `buildWidgets`: known ids kept in order; unknown and repeated ids dropped; stops at 15.
- `MockChatPlanner`: a topic word returns its widgets (at most 4); `@builder inventory board` returns an Inventory board with a name; `@builder` with nothing to build explains; unrelated text returns nothing and says so.
- Page: welcome and example prompts that send; your message and the reply appear in the thread; the reply carries the widgets; `@builder` opens the modal with the widgets and name; the modal closes and reopens from the message; the app navigation is hidden; Back to boards works; the board page's AI Mode links here.
- Save: new board under the limit (named, opens it); at the limit it asks which board to replace, does nothing until confirmed, and the replaced board's widgets and name change.

## Out of scope
OpenUI, Ollama, any model; parameterised data answers; editing a proposed board in the modal; saving the conversation; real API.

## Depends on
synapse-web 04.
