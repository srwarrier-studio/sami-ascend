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
`KpiCard`, `RankedList`, `DataTable`, `LineChart` and `BarChart` are registered by name with a zod schema and size hints (`minW`, `minH`, `defaultW`, `defaultH`).
- `registry.describe()` returns `{ name, description, schema (JSON schema), size }` for each widget, for a model's structured output.
- `registry.render(name, props)` validates and renders. Bad props or an unknown name give a "Cannot show widget" card, never an exception. Unknown props are ignored.
- Widget props are JSON only: no callbacks, no JSX. Widgets have no drag code; the synapse board places them.

## App frame
`AppFrame` takes `layout`: `top` (rounded brand pill, pill nav, content on a soft grey ground; synapse) or `side` (restyled sidebar; default).

## Playground
`pnpm --filter @sami/ui dev` opens the kitchen sink with a theme lab: switches for palette, radius, motion, layout and light or dark. Sections: tokens, buttons, inputs, data display, overlays, feedback, notifications, navigation, widgets and charts.

## Test
```
pnpm --filter @sami/ui test
pnpm --filter @sami/ui typecheck
```
