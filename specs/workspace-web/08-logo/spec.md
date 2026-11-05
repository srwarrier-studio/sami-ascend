# workspace-web/08 logo

## Goal
Workspace has its own logo, a honeycomb cell with a hidden S, used on the sign-in page, in the app header and as the browser tab icon.

## Why
The sign-in page shows a placeholder mark (four squares) and the tab still has the Vite starter icon and the title `workspace-web`. Synapse has its own traced mark with two hidden S shapes (Sami Synapse). Workspace follows the same idea in its own shape.

## Behavior
- **The mark:** a hexagon split by an S-shaped channel into two halves, the left half solid and the right half half-tone, with one round dot cut out of the left half and one solid dot inside a ring cut in the right half (the design the owner chose from the options page). One SVG in `currentColor`, so it takes the colour of the page: light on the login, brand colour in the header.
- **`WorkspaceLogo`** (`src/brand/WorkspaceLogo.tsx`) draws the mark at a given size, replacing the placeholder. Mask ids are unique per use so several marks on one page do not clash.
- **Favicon:** `public/favicon.svg` is the mark in the Workspace green (`#008043`) and the Vite starter icon is removed; `index.html` title is `Sami Workspace`.
- **Header:** the app header shows the mark at 28 px and the name `Sami Workspace` where it now shows the title `Workspace`.
- **Name and tagline:** the name stays `Sami Workspace`; the tagline becomes `Work, delivered.` (from the owner's "Work Delivered Here", tightened to two beats; the word works for work done and for orders delivered). It changes in `config.ts` and in the sign-in test.
- Synapse and `@sami/ui` are not changed.

## Acceptance cases
- The sign-in page and the header both show the mark and the name `Sami Workspace`.
- The mark takes its colour from the surrounding text colour and is hidden from assistive technology.
- Two marks on one page do not share mask ids.
- `index.html` has the title `Sami Workspace` and links `/favicon.svg`, which holds the mark and no purple starter shape.
- All workspace-web tests and `tsc` pass.

## Out of scope
A dark-mode or mono variant, app icons for phones, a logo for the admin or Synapse apps, other taglines.

## Depends on
workspace-web 07 (merged).
