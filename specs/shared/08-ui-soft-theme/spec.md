# shared/08 ui-soft-theme

## Goal
`@sami/ui` renders the approved soft look (rounded cards, pill buttons, token-driven palette, optional motion) so synapse-web and workspace-web get it from one place.

## Reference
Approved design: the Synapse kitchen sink artifact, https://claude.ai/artifact/FyrY7tQuC9m18kTE6mME5R (tokens, theme lab, sample board). The saved decisions are in the owner's UI direction note: Carbon control heights, IBM Plex Sans, Phosphor icons, soft radius, motion on synapse and minimal on workspace.

## Behavior
- **Palettes:** `palettes.ts` stays the only file with hex values. It exports the presets `teal`, `blue`, `indigo`, `graphite` and `copper` as 10-shade tuples next to the existing slate gray, and the two app palettes: `synapsePalette` (teal) and `workspacePalette` (blue). The owner picks the final preset per app after comparing them in the playground; changing it is one line.
- **Radius:** the provider takes `radius: 'soft' | 'sharp'`, default `soft`. Soft: inputs 6px, menus and tiles 12px, cards and modals 16px, buttons pill. Sharp: 4px everywhere.
- **Motion:** the provider takes `motion: 'full' | 'minimal'`, default `full`, and writes it as `data-motion` on the document root. Full: cards rise in, hover lift, charts draw. Minimal: no animations, 120 ms hover and focus transitions only. `prefers-reduced-motion` forces minimal.
- **Control sizes** stay 24/32/40/48/56, body 14px, IBM Plex Sans.
- **Light and dark** both work for every preset; status colors (success, warning, danger, info) stay separate from the accent.
- **AppFrame** is restyled soft and gets `layout: 'top' | 'side'`. `top` is the rounded brand pill with a pill nav and the soft grey ground (synapse). `side` keeps today's sidebar structure, restyled (workspace). `NavItem`, `navGroups`, `user` and `onSignOut` keep their current shape, so workspace-web needs no change.
- **Playground** (`pnpm --filter @sami/ui dev`) shows every component and has switches for palette, radius, motion and light or dark.

## Acceptance cases
- Every preset has a 10-shade `brand` tuple, and `synapsePalette` and `workspacePalette` use `teal` and `blue`.
- The theme built for `soft` has radius 6 / 12 / 16 and pill buttons; for `sharp` every radius is 4.
- `UiProvider` sets `data-motion="full"` by default and `data-motion="minimal"` when asked.
- `theme-only.test.ts` still passes: no hex outside `palettes.ts`, no inline styles, no raw px in `src/` and `playground/`.
- `AppFrame` renders in both layouts with nav items, the active item, the badge, the user menu and sign out; the existing workspace-web tests pass unchanged.
- The registry and chart tests pass unchanged.
- Manual: the playground looks like the artifact in light and dark for each preset (owner check).

## Out of scope
Board widgets, drag and drop, the AI Mode panel and page tabs (synapse-web 03), the mock data layer (synapse-web 01), a new chart library, choosing the final preset, a theme editor in the apps.

## Depends on
shared 06 (done).
