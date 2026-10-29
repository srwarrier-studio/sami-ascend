# UI parity: playground vs approved Synapse kitchen sink

Compared 2026-10-29 with headless Chrome at 1440 wide, teal, soft, full motion. Artifact: https://claude.ai/artifact/FyrY7tQuC9m18kTE6mME5R. The artifact screenshot rendered in dark mode (headless follows the system), the playground in light; compare structure and spacing, not colours.

| Area | Artifact | Playground | Decision for owner |
|------|----------|------------|--------------------|
| App shell | Rounded frame, brand pill, pill nav, search, theme button, avatar | Same idea, plus help and bell icons, theme toggle and a user name and email | Keep; the artifact has no help or bell |
| Page bar | Inline at the end of the board card | Fixed to the viewport bottom, floating pill, three tabs visible | Per owner request; artifact is inline |
| Edit layout | Edit button toggles drag, arrows, remove on every widget | Edit toggles rename only; drag and remove arrive in synapse-web 03 | Planned |
| Board grid | 12-column grid with spans | Rows of equal columns | synapse-web 03 picks the grid library |
| Widget entrance | Rise-in animation | None | Owner dislikes rise-in |
| KPI card | Round arrow button on the card, sparkline absent | Sparkline, delta arrow, info button | Playground richer; confirm |
| Line chart | Dot ping on latest point, draw-in animation | Static latest dot, chart wipe | Minor |
| Donut | Centre share and legend with percents | Same, green/grey/red tones | Same |
| Tables | Row hover tint, 40 px rows, pager | Status pills, no pager, no row hover tint | Add pager when a table needs paging |
| Ranked list | Bars in accent and info colours | One colour (accent) | Keep one colour |
| Alerts | Tinted, icon, bold title | Tinted, icon, title | Same |
| Inputs | Bottom-border emphasis on fields | Mantine default border | Difference; decide if wanted |
| Chips, drop zone, steps, empty state, skeleton blob | Present | Chips, skeleton, progress yes; drop zone, empty-state blob, steps not built | Build when a screen needs them |
| Toast | Dark pill at bottom with action | Mantine notification, coloured | Different; confirm |
| AI drawer | Chat drawer | Not built | synapse-web 03 |
| Launch screens | Splash with network lines, sign-in card | Splash without network lines, sign-in card | Lines skipped |
| Fonts | IBM Plex Sans and Mono | Plex Sans only | Mono not needed yet |
| Theme lab | Palette, radius, motion | Adds layout; quick config also in the page bar | Same |
