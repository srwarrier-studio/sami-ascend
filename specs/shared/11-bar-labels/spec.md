# shared/11 bar-labels

## Goal
Bar charts show each bar's value above it, so a manager reads the figure without hovering, starting with the month-on-month sales widget.

## Behavior
- `BarChart` in `@sami/ui` draws a label above every bar, in the same compact format as the axis (`₹9M`, `₹7.6M`, `1.2K`), with the widget's `valueFormat`.
- Labels are on by default and shown only when there are 16 bars or fewer, so a long chart is not cluttered.
- `valueLabels: false` turns them off. It is an optional boolean in the `BarChart` registry schema, so a backend can set it in a widget's props; any other value is rejected.
- Line, area and stacked charts are not changed.
- The tooltip, the highlighted latest bar and the premium look are unchanged.

## Acceptance cases
- Each bar's compact value is drawn in the chart; with `valueFormat` `number` the format has no currency sign.
- `valueLabels: false` draws none; more than 16 bars draw none.
- The registry accepts `valueLabels: true` and `false` and rejects a non-boolean.
- All existing chart, catalog and board tests still pass.

## Out of scope
Labels on line, area, stacked and donut charts, label positions inside bars, Indian lakh and crore format (the axis uses the same compact format).

## Depends on
shared 09 (chart widgets).
