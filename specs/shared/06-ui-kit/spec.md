# shared/06 ui-kit

## Goal
One package, `@sami/ui` (`packages/ui`), gives every web app the same Mantine components, styling and charts, with an AI-ready component registry.

## Behavior
- **Provider:** `UiProvider` takes a `palette` (primary color and shade) and nothing else. Spacing, radius, typography and component defaults are fixed in the package. `workspacePalette` and `synapsePalette` are exported; each app passes its own.
- **Wrappers:** apps import components only from `@sami/ui`, never from `@mantine/*` or `@tanstack/charts`. First set: `AppShell`, `TextInput`, `PasswordInput`, `Button`, `NavLink`, `Alert`, `Loader`, `Card`, `Text`, `Title`. A wrapper re-exports the Mantine component with the shared defaults; no extra props invented.
- **Charts:** `LineChart` and `BarChart` wrap TanStack Charts v1. Props are plain data: `data` (array of `{ label, value }`), `title`, `valueFormat` (`"number"`, `"currency"`, `"percent"`). No callbacks, no JSX, no children.
- **Table:** `DataTable` takes `columns` (`{ key, label, format }`) and `rows`, for lists such as recent high-value sales.
- **AI-ready registry** (`registry.ts`): every data-driven component (`KpiCard`, `LineChart`, `BarChart`, `RankedList`, `DataTable`) is registered by name with its props type, a one-line description, a JSON schema for its props, and a size hint (`minW`, `minH`, `defaultW`, `defaultH` in grid units) so a board can place it. Widgets fill the box they are given and have no drag code; drag and drop belongs to the synapse board (see roadmap). Rules for registered components:
  - Props are JSON-serializable only (strings, numbers, booleans, arrays, objects); no functions, no React nodes.
  - Every prop has a safe default or is required; unknown props are ignored.
  - A bad props object renders a small "cannot show this widget" card, never throws.
  - `registry.describe()` returns the list of names, descriptions and schemas, ready to give to a model as structured-output constraints; `registry.render(name, props)` returns the element. The AI POC decides later whether to feed this to OpenUI or to plain schema-constrained JSON; this phase builds neither.
- **OpenUI check:** its site says it works with Mantine and other design systems and is open source, but does not document how a component library is described to it. Not adopted (see `specs/notes.md`). Keeping registered components JSON-only and schema-described works for both OpenUI and plain JSON.
- **Chart comparison:** a short spike builds the same trend and ranked-bar chart with TanStack Charts and Recharts, and records gzipped bundle size and memory in `specs/notes.md`. Recharts is not kept as a dependency afterwards.
- **Dependencies:** `@mantine/core`, `@mantine/hooks`, `@tanstack/charts`, `react`, `react-dom` (peer). Dev: `vitest`, `@testing-library/react`, `jsdom`. Record in `tech-stack.md`.
- **Layout:** flat package like `token-verification`. Workspace members in `pnpm-workspace.yaml`.

## Acceptance cases
Tests use jsdom; no network.
- `UiProvider` with each palette renders a `Button` using that palette's primary color; both palettes share the same radius and font.
- Every wrapper renders with its default props.
- `LineChart` and `BarChart` render one mark per data point and handle an empty `data` array with an "No data" message.
- `valueFormat` formats `1234.5` as `1,234.5`, as currency, and as percent.
- `registry.describe()` lists every registered name once, each with description and schema; every schema is valid JSON and has no function-typed property.
- `registry.render` with valid props renders; with wrong types, missing required props or an unknown name renders the fallback card without throwing.
- Sample props objects (one per component, kept in the test) validate against their schema.

## Out of scope
The AI dashboard itself, calling a model, OpenUI integration, dark mode, translations, Storybook, publishing to npm, form helpers (`@mantine/form`), tables and date pickers (add when a phase needs them).

## Depends on
Nothing. workspace-web 01 and synapse-web 02 depend on this.
