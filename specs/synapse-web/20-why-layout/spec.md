# synapse-web/20 why-layout

## Goal
AI Mode draws a why answer as a readable summary instead of a list of sentences: the headline, a card for each mover with its causes, how much is explained and the notes.

## Behavior
- A new answer block `findings` (intent-api 05) is read by `parseBlock` and drawn by a `FindingsBlock` component, with the existing `@sami/ui` components and no new dependency.
  - The headline in bold and larger, as the lead of a short report.
  - A **What moved most** section: for each mover an arrow (teal up, red down, grey flat), the name in bold with its kind (customer, product), the detail line ("up USD 12.4K (101.2%), 90.7% of the total rise"), the price sentence when there is one, and each reason as a plain dimmed sentence.
  - A **Partly offset by** section for the offsets, drawn the same way.
  - A **How much we can explain** section: a progress bar and the coverage sentence.
  - The notes as small dimmed lines.
- A block that fails the check is dropped like any other unknown block. `text`, `trend`, `table` and `evidence` blocks draw as before, after the `findings` block.
- `@sami/ui` exports `ArrowUpIcon` and `ArrowDownIcon`.

## Acceptance cases
- A valid findings block parses; one with a malformed item is refused.
- The page shows the headline, the three section titles, every mover with its arrow, detail line and reasons, the offsets under their own title, the coverage bar and sentence, and the notes.
- The answer layout has no inline style, hex colour or px value (the project's style tests pass).

## Out of scope
Changing which causes are found, a chart per mover, printing or exporting the answer.

## Depends on
intent-api 05.
