# shared/10 ui-parity-check

## Goal
`@sami/ui` gets the last pieces of the approved Synapse kitchen sink (soft page header and alerts, launch screens, widget catalog, bottom page bar) and the playground is compared with the artifact, every difference listed for the owner.

## Reference
Approved design: https://claude.ai/artifact/FyrY7tQuC9m18kTE6mME5R.

## Behavior
- **Soft `PageHeader` and `Alert`:** the header has no bottom border and sits on the ground; alerts are tinted (info, success, warning, error) with an icon, no border.
- **Launch screens:** `SplashScreen` (brand colour screen, mark, name, tagline, loading bar) and `SignInCard` (title, email, password, submit, optional error). Both take text and callbacks only.
- **`WidgetCatalog`:** lists every registry widget with name, description and an Add button (`onPick(name)`). The playground shows it as a section.
- **`PageBar`:** board tabs fixed at the bottom of the viewport. Three tabs are visible and the rest scroll sideways. `+ Add` ends the bar. In Edit mode a tab can be renamed (double click or pencil, Enter saves, Escape cancels). A quick config button opens a popover with palette, light or dark and motion; it calls `onConfigChange`.
- **Parity report:** screenshots of the playground and the artifact under the same settings, differences written to `docs/ui-parity.md`.

## Acceptance cases
- `PageHeader` has no border; `Alert` renders four tones with their icons.
- `SplashScreen` shows the name and tagline. `SignInCard` calls `onSubmit` with email and password and shows `error` when given.
- `WidgetCatalog` has one row per registry name and calls `onPick` with the name.
- `PageBar` shows all tabs; only three fit in view (a test checks the scroll container and the active tab is selected); `onSelect`, `onAdd` work; rename works only in Edit mode and ignores an empty name; the config popover reports palette, scheme and motion changes.
- The playground renders the new sections under every setting.
- `docs/ui-parity.md` exists with a table of differences.

## Out of scope
Board state, drag, storage (synapse-web 03), real login (synapse-web 01).

## Depends on
shared 09 (done).
