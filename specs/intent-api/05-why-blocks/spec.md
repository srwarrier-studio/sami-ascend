# intent-api/05 why-blocks

## Goal
A why answer carries its structure (headline, what moved, what coincided, how much is explained, the notes) in one `findings` block instead of a flat list of sentences, so the web can draw it as a readable summary.

## Behavior
- **New block `findings`**, used as the first block of every `why` answer that has a currency. It replaces the `text` block of that answer; the one-sentence answers (month not over, no data in the currency) stay `text`. It is written for a manager reading a report, in plain words:
  - `headline`: one plain sentence with the scope, the direction, the percentage, the month, and the new and old amounts in short form (`USD 113.6K` against `USD 94.7K`), for example "Sales of Sami-Sabinsa fell 13.6% in July 2026, to USD 94.7K from USD 109.6K in June 2026."
  - `items`: one per finding, movers first then offsets, in the analysis order. Each has `name`, `dimension` (a plain label: customer, product, and so on), `role` (`mover` or `offset`), `direction` (`up`, `down` or `flat`), `detail` (for example "down USD 11.3K (50.1%), 75.8% of the total fall"), `price_text` (the price and volume sentence in short amounts, or null) and `reasons`: one sentence for each cause path, starting "Possible reason:" and continuing "Behind that:" for each deeper step, with dates as `2 Aug 2026` and codes such as `MATERIAL_SHORTAGE` as `material shortage`.
  - `coverage`: `explained_percent` (a string) and `text`, one plain sentence ("We can explain about 76% of the change from the data we hold; the other 24% has no cause in our data.").
  - `notes`: the other-currency sentences, the limits and, for all companies, the group warning, in that order.
- The `trend`, `table` and `evidence` blocks do not change and still follow.
- **Templates only.** Every phrase is a fixed template filled from the analysis and the existing evidence steps; nothing is written by a model. The older `why_wording` sentences stay for the `evidence` block and `why-eval`.
- `why-eval` keeps scoring the analysis itself, so its results do not change.

## Acceptance cases
- A why answer's first block is `findings` with the headline naming the scope and currency, and `items` in the analysis order.
- A mover with a cause chain has one `reasons` sentence that starts "Possible reason:" and continues "Behind that:" for each deeper step; a mover with no cause has no reasons.
- An offset has `role` `offset`; a price-driven mover has `price_text`; amounts are short (`USD 12.4K`) and dates read `2 Aug 2026`.
- `coverage` carries the percentages and the sentence; a steady month still has a coverage sentence.
- All companies adds the group warning as the last note; one company does not.
- A finished-month refusal and a no-data answer are still one `text` block.
- The development scenarios still pass `why-eval` with the same scores.

## Out of scope
The web layout (synapse-web 20), changing which causes are found, other block types.

## Depends on
intent-api 04.
