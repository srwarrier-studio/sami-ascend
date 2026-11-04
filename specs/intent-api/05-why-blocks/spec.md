# intent-api/05 why-blocks

## Goal
A why answer carries its structure (headline, what moved, what coincided, how much is explained, the notes) in one `findings` block instead of a flat list of sentences, so the web can draw it as a readable summary.

## Behavior
- **New block `findings`**, used as the first block of every `why` answer that has a currency. It replaces the `text` block of that answer; the one-sentence answers (month not over, no data in the currency) stay `text`.
  - `headline`: the existing headline sentence (scope, currency, change, the two months and the amounts).
  - `items`: one per finding, movers first then offsets, in the order the analysis gives. Each has `name`, `dimension` (customer, material, and so on), `role` (`mover` or `offset`), `direction` (`up`, `down` or `flat`), `change_text` (for example `101.2%` or `from nothing`), `amount_text` (for example `USD 12,434.18`), `share_text` (for example `90.7% of the change`, or null when the month is steady), `price_text` (the price and volume sentence, or null) and `paths`: a list of causes, each a list of step phrases from the first thing that coincided to what is behind it (the existing step sentences, so the wording is the same templates).
  - `coverage`: `explained_percent`, `unexplained_percent` (numbers as strings) and `text` (the existing explained / not explained sentence).
  - `notes`: the other-currency sentences, the limits and, for all companies, the group warning, in that order.
- The `trend`, `table` and `evidence` blocks do not change and still follow.
- **No new wording.** Every phrase comes from the existing `why_wording` templates and every figure from the analysis; nothing is written by a model.
- `why-eval` keeps scoring the analysis itself, so its results do not change.

## Acceptance cases
- A why answer's first block is `findings` with the headline naming the scope and currency, and `items` in the analysis order.
- A mover with a cause chain has `paths` with the first step then the steps behind it; a mover with no cause has an empty `paths`.
- An offset has `role` `offset`; a price-driven mover has `price_text`.
- `coverage` carries the percentages and the sentence; a steady month still has a coverage sentence.
- All companies adds the group warning as the last note; one company does not.
- A finished-month refusal and a no-data answer are still one `text` block.
- The development scenarios still pass `why-eval` with the same scores.

## Out of scope
The web layout (synapse-web 20), changing which causes are found, other block types.

## Depends on
intent-api 04.
