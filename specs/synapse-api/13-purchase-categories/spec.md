# synapse-api/13 purchase-categories

## Goal
`pur-categories` and `pur-by-category-month` read butterfly's `PurchaseSummaryByMaterialGroup` instead of `mock_library.json`, and the purchase overview can name the biggest category.

## Why
Phase 11 left these two Purchase widgets on fixed numbers because the purchase contract had no material group; butterfly 15 added it.

## Behavior
- `PurchaseSource` gets `group_purchases(start, end)` (butterfly reads `PurchaseSummaryByMaterialGroup`, scoped by company; the mock implementation for tests).
- `pur-categories` donut: spend per material group over the current month and the two before it (orders are placed around the 24th, so a calendar month alone is often empty), groups with no spend left out, biggest first.
- `pur-by-category-month` stacked bars: spend per month for the last six months, one series per group that has any spend in them, zero for months without spend.
- Overview: with `pur-categories` on the board, the purchases topic can add `<group> is the biggest category over the last three months: <amount> (<share>% of purchases).`; it comes after the on-time and open-items sentences and the two-sentence cap per topic still applies.
- Nothing else changes; the mock library no longer lists or serves these two ids, and still serves Exports, Production and Finance cash.

## Acceptance cases
- Donut: rows of two months and two groups give two slices summing the groups, biggest first; spend older than three months and other currencies are left out.
- Stacked: six months, a series per group with spend, zeros for quiet months, the month labels end with the current month.
- Overview: the category sentence appears with `pur-categories` and is dropped by the cap when the board also shows `pur-ontime` and `pur-open`.
- The catalog has no duplicate ids; with butterfly 15 running the widgets match a direct read.

## Out of scope
Categories for sales, new butterfly entities.

## Depends on
butterfly 15, synapse-api 11 (purchase source and widgets), synapse-api 12 (branch base).
