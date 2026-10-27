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
- `UiProvider` takes only a `palette`. `workspacePalette` (indigo) and `synapsePalette` (teal) are the only per-app difference; font, radius, spacing and component defaults are shared.
- All styling comes from the theme. No inline `style`, hex colors, `rgb()` or `px` values in `src/` or `playground/`; `tests/theme-only.test.ts` fails if one appears. Chart colors are mapped from Mantine variables in `src/charts.css`.
- `valueFormat`: `number`, `currency` (INR, en-IN) or `percent` (value is a fraction).

## Widgets and registry (AI-ready)
`KpiCard`, `RankedList`, `DataTable`, `LineChart` and `BarChart` are registered by name with a zod schema and size hints (`minW`, `minH`, `defaultW`, `defaultH`).
- `registry.describe()` returns `{ name, description, schema (JSON schema), size }` for each widget, for a model's structured output.
- `registry.render(name, props)` validates and renders. Bad props or an unknown name give a "Cannot show widget" card, never an exception. Unknown props are ignored.
- Widget props are JSON only: no callbacks, no JSX. Widgets have no drag code; the synapse board places them.

## Playground
`pnpm --filter @sami/ui dev` shows every component and widget under both palettes.

## Test
```
pnpm --filter @sami/ui test
pnpm --filter @sami/ui typecheck
```
