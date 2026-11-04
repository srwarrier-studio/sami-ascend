# synapse-web/20 why-layout

## Goal
AI Mode draws a why answer as a readable summary instead of a list of sentences: the headline, a card for each mover with its causes, how much is explained and the notes.

## Behavior
- A new answer block `findings` (intent-api 05) is read by `parseBlock` and drawn by a `FindingsBlock` component, with the existing `@sami/ui` components and no new dependency.
  - The headline in bold.
  - One card per item: the name with `By <dimension>` (or `Offset by <dimension>`), a badge with the change and an up, down or flat arrow (teal, red, grey), the amount and share on one line, the price sentence when there is one, and each cause as a short left-ruled list that starts `Coincided with:` and continues `Behind that:` for each deeper step.
  - A progress bar for the explained share with the coverage sentence under it.
  - The notes as small dimmed lines.
- A block that fails the check is dropped like any other unknown block. `text`, `trend`, `table` and `evidence` blocks draw as before, after the `findings` block.
- `@sami/ui` exports `ArrowUpIcon` and `ArrowDownIcon`.

## Acceptance cases
- A valid findings block parses; one with a malformed item is refused.
- The page shows the headline, every card with its change badge and amounts, the offset label, the cause lines with their prefixes, the coverage bar and sentence, and the notes.
- The answer layout has no inline style, hex colour or px value (the project's style tests pass).

## Out of scope
Changing which causes are found, a chart per mover, printing or exporting the answer.

## Depends on
intent-api 05.
