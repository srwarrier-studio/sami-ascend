# synapse-api/20 analysis-rupees

## Goal
Every figure in the app is in rupees: the why analysis and the metric comparisons read the same company-currency amounts as the widgets, so a why answer no longer talks in dollars next to a board in rupees.

## Behavior
- `registry.toml`: the `sales` and `purchases` metrics measure `TotalNetAmountLocal` and read the currency from `LocalCurrency` (butterfly 19). Every document, in any document currency, is counted at its rupee amount, so a comparison has one result, in `INR`.
- A request for another currency finds no rows, as for the widgets (`There is no data in USD`).
- `intent-api why-eval` asks both metrics in `INR` (it used `USD` for sales). The evaluation runs against the same in-process butterfly as before.
- Nothing else changes: records, widgets and the board summary were already in rupees.

## Acceptance cases
- `why-eval` still passes the 10 development scenarios, and `why-eval --final` still gives 11 of 14 (`two-causes`, `cancellations` and `supplier-switch` stay unsolved, `double-cause` passes), with nothing invented and nothing blamed wrongly.
- Sales of the story company in August 2026 are still about 14.5% below July, now in `INR`.
- A summary row in dollars with a rupee amount is read as that rupee amount with currency `INR`.
- The group of three companies has one result in `INR`; the story is diluted (about 4.9% fall, steady by the thresholds) and the story customer still leads the fall.
- A why question in `USD` answers that there is no data in USD.

## Out of scope
Exchange rates (butterfly's fixed rate stays the source), showing other currencies, changing intent-api's currency reading.

## Depends on
synapse-api 16, butterfly 19.
