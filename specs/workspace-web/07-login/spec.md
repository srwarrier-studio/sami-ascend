# workspace-web/07 login

## Goal
Workspace opens on the same sign-in page as Synapse (dark ground, brand block, sign-in card, Microsoft button) in Workspace's green, with its own animated background: a honeycomb with slow waves of light flowing across it.

## Why
The login is the first thing management sees. Workspace today shows a bare form on a white page, Synapse shows a polished one. One shared page means both apps look like one product and a later fix lands once.

## Behavior
- **Green palette in `palettes.ts`:** a `green` preset like the others, with the owner's brand color `#008043` as the main shade (index 6, the other nine derived from it); `workspacePalette = presets.green` next to `synapsePalette = presets.midnight`. Because the palette pickers list every preset, "Green" appears as a seventh swatch in them (owner decision); Synapse still starts on `midnight` and nothing else of Synapse changes.
- **`LoginLayout` in `@sami/ui`:** takes `background` (a node), `logo`, `name`, `tagline` and the `SignInCard` props. It draws the same page as Synapse's login (brand block, card, Microsoft button), with its own CSS that holds no color of its own: every color is derived from the app's brand shades, so Workspace is green and a later Synapse move would be navy by itself. Synapse's `LoginPage` and `Login.module.css` are not changed; moving Synapse onto the shared layout is a possible later phase.
- **Workspace background `Honeycomb`:** a canvas of hexagonal cells (the shape of the botanical and nutraceutical world) covering the page. Waves of light flow across it all the time: three slow travelling sine waves in different directions are added up per cell, so the pattern keeps shifting and never repeats a flash or a random spot. Colors are read from the brand shades of the page, low contrast, nothing over the card. Chosen by the owner from four candidates.
- **Old computers:** most of the organization uses old PCs, so the cost is kept low: 24 frames a second; the whole grid is one stroke and only the lit cells are filled and stroked again; the animation exists only on the sign-in page and stops as soon as the user is signed in; a frame meter measures the drawing time of the first 30 frames and, when the average is above 8 ms, stops the animation and leaves one still frame. No setting is needed.
- **Motion rules:** animated only when the app's motion setting is full and the user does not prefer reduced motion; otherwise one still frame. Workspace has no motion setting yet, so it is animated unless the user prefers reduced motion.
- **Brand:** name `Sami Workspace`, tagline `Plan. Order. Deliver.` (to confirm), logo the Synapse mark until a Workspace mark exists (to confirm).
- **Form:** the shared `SignInCard` (work email and password). The Microsoft button starts the real Entra sign-in (`entraLoginUrl`); Synapse keeps its "coming soon" note. The `?error=entra` alert shows above the card as the red problem line.
- **Errors:** wrong credentials show "Incorrect email or password"; an unreachable sign-in service shows the same message as Synapse.
- **Not changed:** routes, session handling, the shell and every other screen.

## Acceptance cases
- Workspace login shows the brand name, the tagline, the card with email and password, and the Microsoft button; signing in with right credentials reaches Home, wrong ones show the problem line.
- The Microsoft button points to the Entra login URL; `?error=entra` shows the Microsoft failure message.
- `Honeycomb` draws a still frame when animation is off; the light moves smoothly with time and never restarts; the grid is drawn in one stroke; the frame meter judges slow frames by their average (tests with a fake canvas context and a frame meter test).
- No Synapse file changes (the diff touches no `apps/synapse-web` path and leaves `palettes.ts` presets as they are); its tests still pass.
- `tsc` is clean and the `@sami/ui` parity test still passes.

## Out of scope
The workspace shell, home page, forms and tables (later phases of the UI pass; they pick up the new green palette automatically but are not reviewed here), a Workspace logo design, dark and light variants of the login (it is always dark), moving Synapse's login onto `LoginLayout`, the Microsoft button in Synapse.

## Depends on
workspace-web 06 (merged), synapse-web login as it is on `main`.
