# shared/09 ui-kitchen-sink-parity

## Goal
`@sami/ui` ships one standardized, polished set of preconfigured widgets, and its playground matches the approved Synapse kitchen sink.

## Reference
Approved design: https://claude.ai/artifact/FyrY7tQuC9m18kTE6mME5R (sample dashboard, charts, components). Board and chart decisions are in the owner's board decision note.

## Behavior
- **Standardized widgets:** every widget has one fixed look decided in `@sami/ui`: colors, grid, axes, rounded corners, legend and motion. A widget takes data, a title and a value format, nothing about style. The same widget with other data looks the same. This is what lets users pick a widget from a list and a model pick it later.
- **Widget set** (each is a registry entry with a zod schema, description and size hints `minW`, `minH`, `defaultW`, `defaultH`):
  - `LineChart`: soft area fill, light grid, optional second series (`compare`, for example last month), legend, a marked latest point, compact axis labels (2M, 450K).
  - `BarChart`: rounded bars, neighbours dim on hover, latest bar highlighted, compact axis labels.
  - `DonutChart` (new): shares of a whole, such as paid, open and overdue, with the main share in the center and a legend.
  - `KpiCard`: value, signed delta with an arrow (green up, red down), caption and an optional sparkline.
  - `RankedList`: rows with a proportional bar under each label.
  - `DataTable`: right-aligned numbers, optional status pills (`Paid`, `Open`, `Overdue`).
- **Widget catalog** in the playground lists every registered widget with a live preview, its description and its size hints, from `registry.describe()`. It is the base for the board's widget picker.
- **Soft details:** `PageHeader` matches the soft shell; alerts use soft tinted backgrounds; status colors stay separate from the accent.
- **Launch screens** in the playground: a splash (brand mark, network drawing, load bar) and a sign-in card.
- **Dashboard demo** in the playground is built only from registry widgets with sample data, in the top layout, with the Edit layout, AI Mode, Add widget buttons and the page bar. They stay static; behavior is synapse-web 03.
- **Parity check:** the playground sections are compared with the artifact in light and dark for the teal and blue presets, using headless Chrome screenshots. Every difference is listed for the owner; each is fixed or accepted by the owner.
- The chart look follows the theme: palettes, radius and motion switches restyle charts too; colors come from Mantine variables, never hex.

## Acceptance cases
- The registry lists `LineChart`, `BarChart`, `DonutChart`, `KpiCard`, `RankedList` and `DataTable`; each renders with its sample props and shows the fallback card for bad props.
- No widget schema has a color, style, class or size-in-pixels prop; a test fails if one is added.
- `LineChart` with `compare` renders two series and a legend; without it, one series and no legend. The latest point is marked.
- `BarChart` highlights the last bar; `DonutChart` shows the main share and a legend entry per slice and rejects slices that do not sum to a positive total.
- `KpiCard` shows the delta with a sign and an arrow, and a sparkline only when `trend` is given.
- `RankedList` bar widths follow the values; `DataTable` right-aligns number columns and renders status pills for status columns.
- Axis labels use compact formats (`2M`, `450K`) and currency values keep the rupee format elsewhere.
- Every widget renders under each preset, radius and motion setting (test).
- `theme-only.test.ts`, the registry tests and the workspace-web tests still pass.
- Manual: the parity report lists every difference from the artifact, and the owner has accepted or asked for a fix on each.

## Out of scope
Drag, resize, the board store, the widget picker and AI Mode behavior (synapse-web 03), the mock data layer (synapse-web 01 and 02), choosing the grid library, a theme editor, changing the approved palette values.

## Depends on
shared 06 and 08 (done).
