# shared/09 ui-chart-widgets

## Goal
`@sami/ui` ships one standardized set of chart and data widgets, and a sample dashboard page in the playground shows every chart type.

## Reference
Approved design: https://claude.ai/artifact/FyrY7tQuC9m18kTE6mME5R. Board and chart decisions are in the owner's board decision note.

## Behavior
- **Standardized widgets:** every widget has one fixed look decided in `@sami/ui`: colors, grid, axes, rounded corners, legend and motion. A widget takes data, a title and a value format, nothing about style. The same widget with other data looks the same. This lets users pick a widget from a list and a model pick it later.
- **Widget set**, each a registry entry with a zod schema, description and size hints (`minW`, `minH`, `defaultW`, `defaultH`):
  - `LineChart` (done in task 1): soft area fill, light grid, optional second series (`compare`), legend, marked latest point, compact axis labels (2M, 450K).
  - `BarChart` (done in task 1): rounded bars, neighbours dim on hover, latest bar highlighted, compact axis labels.
  - `AreaChart`: one filled trend over ordered labels, for cumulative or volume views.
  - `StackedBarChart`: bars split into named parts (for example paid, open, overdue per month) with a legend; `layout` is `stacked` or `grouped`.
  - `DonutChart`: shares of a whole with the main share in the center and a legend.
  - `GaugeChart`: a progress ring for one value against a target, with the percent in the center.
  - `HeatmapChart`: an intensity grid over two labelled axes (day by hour, customer by month) with a color ramp legend.
  - `KpiCard`: value, signed delta with an arrow (green up, red down), caption and an optional sparkline (`trend`).
  - `RankedList`: rows with a proportional bar under each label.
  - `DataTable`: right-aligned numbers and optional status pills.
- **Sample dashboard page** in the playground (the "Charts" page): every widget above with sample data in the top layout, plus the static Edit layout, AI Mode, Add widget buttons and the page bar. Behavior of those is synapse-web 03.
- Chart colors come from Mantine variables, so palettes, radius and motion switches restyle every chart; no hex in `src/` or `playground/`.

## Acceptance cases
- The registry lists the ten widgets above; each renders with its sample props and shows the fallback card for bad props.
- No widget schema has a color, style, class or pixel-size prop; a test fails if one is added.
- `LineChart` with `compare` renders two series and a legend; without it, one series and no legend; the latest point is marked.
- `BarChart` highlights the last bar. `AreaChart` renders one filled area.
- `StackedBarChart` renders one segment per part per bar in `stacked` and side-by-side bars in `grouped`, with a legend entry per part.
- `DonutChart` shows the main share and a legend entry per slice and rejects slices that do not sum to a positive total.
- `GaugeChart` shows the percent of target and caps the ring at 100% while still showing the real percent.
- `HeatmapChart` renders one cell per row and column pair and a color legend; a missing pair is an empty cell.
- `KpiCard` shows the delta with a sign and an arrow, and a sparkline only when `trend` is given.
- `RankedList` bar widths follow the values; `DataTable` right-aligns number columns and renders status pills for status columns.
- Axis labels use compact formats and currency values keep the rupee format elsewhere.
- Every widget renders under each preset, radius and motion setting (test).
- The "Charts" page renders every registered chart widget (test: its widget names equal the registry's chart names).
- `theme-only.test.ts`, the registry tests and the workspace-web tests still pass.

## Out of scope
Soft `PageHeader` and alerts, launch screens, the widget catalog section and the screenshot comparison with the artifact (shared 10), drag, resize, the board store, the widget picker and AI Mode behavior (synapse-web 03), the mock data layer (synapse-web 01 and 02), choosing the grid library, changing the approved palette values.

## Depends on
shared 06 and 08 (done).
