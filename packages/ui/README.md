# @sami/ui

The one place web apps get components from. Mantine for components, TanStack Charts for charts. Apps never import `@mantine/*` or `@tanstack/charts` directly.

## Use
```tsx
import { UiProvider, workspacePalette, Button, LineChart } from '@sami/ui'

<UiProvider palette={workspacePalette}>
  <Button>Sign in</Button>
  <LineChart title="Day sales" valueFormat="currency" data={[{ label: 'Mon', value: 120000 }]} />
</UiProvider>
```
- `UiProvider` takes a `palette`, plus `radius` (`soft` default, or `sharp`) and `motion` (`full` default, or `minimal`). `workspacePalette` (blue preset) and `synapsePalette` (teal preset) are the per-app palettes; `presets` also has `indigo`, `graphite` and `copper`. Font, spacing and component defaults are shared. Workspace passes `motion="minimal"`.
- Where to change the look: font, sizes, spacing, radius and component defaults are in `src/theme.ts` (`createSharedTheme(radius)`); colors are in `src/palettes.ts`; animations are in `src/motion.css`. Nothing else in the repo names a font, size or color. To change the font, edit the two `@fontsource` imports and `fontFamily` in `src/theme.ts`.
- All styling comes from the theme. No inline `style`, hex colors, `rgb()` or `px` values in `src/` or `playground/`; `tests/theme-only.test.ts` fails if one appears. Chart colors are mapped from Mantine variables in `src/charts.css`.
- `valueFormat`: `number`, `currency` (INR, en-IN) or `percent` (value is a fraction).

## Widgets and registry (AI-ready)
Eleven widgets are registered by name with a zod schema, a description and size hints (`minW`, `minH`, `defaultW`, `defaultH`): `KpiCard`, `LineChart`, `AreaChart`, `BarChart`, `StackedBarChart`, `DonutChart`, `GaugeChart`, `HeatmapChart`, `CalendarHeatmapChart`, `RankedList` and `DataTable`.
- Every widget has one fixed look. Props are data, a `title`, a `valueFormat` and the two text props below; there are no color, style or size props (`tests/standard.test.tsx` fails if one is added).
- `measure` (optional) is a short phrase for what the numbers count, such as "sales" or "orders". `info` (optional) replaces the "What it shows" sentence in the info popover.
- A small "i" button after each title opens a popover with "What it shows" and "How to read it", both written in terms of the measure. The texts live in `src/help.ts`; the button is `WidgetTitle`.
- `registry.describe()` returns `{ name, description, schema (JSON schema), size, help }` for each widget, for a model's structured output.
- `registry.render(name, props)` validates and renders. Bad props or an unknown name give a "Cannot show widget" card, never an exception. Unknown props are ignored.
- Widget props are JSON only: no callbacks, no JSX. Widgets have no drag code; the synapse board places them.
- Chart-specific props: `LineChart` takes `compare` (previous period), `label` and `compareLabel`; `StackedBarChart` takes `series` and `layout` (`stacked` or `grouped`); `DonutChart` slices may carry a `tone` (`positive`, `caution`, `negative`, `neutral`); `GaugeChart` takes `value` and `target`; `CalendarHeatmapChart` takes `days` as `{ date: 'YYYY-MM-DD', value }`; `DataTable` columns may use `format: 'status'` for a colored tag; `KpiCard` takes an optional `trend` for a sparkline.

## App frame
`AppFrame` takes `layout`: `top` (rounded brand pill, pill nav, content on a soft grey ground; synapse) or `side` (restyled sidebar; default).

## Playground
`pnpm --filter @sami/ui dev` opens the kitchen sink with a theme lab: switches for palette, radius, motion, layout and light or dark. Sections: tokens, buttons, inputs, data display, overlays, feedback, notifications, navigation, widgets and charts. The Dashboard page shows every registered widget (built from `registry.render`) with the static Edit, AI Mode and Add widget buttons.

## Test
```
pnpm --filter @sami/ui test
pnpm --filter @sami/ui typecheck
```
