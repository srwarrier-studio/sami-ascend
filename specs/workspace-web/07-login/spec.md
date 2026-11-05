# workspace-web/07 login

## Goal
Workspace opens on the same sign-in page as Synapse (dark ground, brand block, sign-in card, Microsoft button) in Workspace's green, with its own animated background: documents flowing through the stations of a business process.

## Why
The login is the first thing management sees. Workspace today shows a bare form on a white page, Synapse shows a polished one. One shared page means both apps look like one product and a later fix lands once.

## Behavior
- **Workspace theme file:** `packages/ui/src/workspaceTheme.ts` holds the `green` palette (the owner's brand color `#008043` as the main shade, index 6, the other nine derived from it) and the login's green tone (ground gradient, card border and glow, input tints, button and line colors as CSS variables). `palettes.ts` only re-exports `workspacePalette` from it. `midnight`, `synapsePalette` and every Synapse file stay untouched.
- **`LoginLayout` in `@sami/ui`:** takes `background` (a node), `logo`, `name`, `tagline`, the `SignInCard` props and a `tone` (the variable block). It draws the same page as Synapse's login (brand block, card, Microsoft button), with its own CSS that holds no color of its own. Synapse's `LoginPage` and `Login.module.css` are not changed; moving Synapse onto the shared layout is a possible later phase.
- **Workspace background `ProcessFlow`:** a canvas at 30 fps like `SynapseNetwork`. Five stations in a row-and-curve layout (requisition, order, receipt, invoice, payment, drawn as small rounded squares with a line icon each), joined by soft lines. Small document cards (a rounded rectangle with two lines) travel from one station to the next; a station glows briefly as a card arrives; a second batch starts partway through the cycle. Colors from the login's green tone, low contrast, nothing over the card. Motion is slow and quiet.
- **Motion rules:** animated only when the app's motion setting is full and the user does not prefer reduced motion; otherwise one still frame. Workspace has no motion setting yet, so it is animated unless the user prefers reduced motion.
- **Brand:** name `Sami Workspace`, tagline `Plan. Order. Deliver.` (to confirm), logo the Synapse mark until a Workspace mark exists (to confirm).
- **Form:** the shared `SignInCard` (work email and password). The Microsoft button starts the real Entra sign-in (`entraLoginUrl`); Synapse keeps its "coming soon" note. The `?error=entra` alert shows above the card as the red problem line.
- **Errors:** wrong credentials show "Incorrect email or password"; an unreachable sign-in service shows the same message as Synapse.
- **Not changed:** routes, session handling, the shell and every other screen.

## Acceptance cases
- Workspace login shows the brand name, the tagline, the card with email and password, and the Microsoft button; signing in with right credentials reaches Home, wrong ones show the problem line.
- The Microsoft button points to the Entra login URL; `?error=entra` shows the Microsoft failure message.
- `ProcessFlow` draws a still frame when animation is off and starts and stops its frame loop on mount and unmount (a test with a fake canvas context, as Synapse's network test does).
- No Synapse file changes (the diff touches no `apps/synapse-web` path and leaves `palettes.ts` presets as they are); its tests still pass.
- `tsc` is clean and the `@sami/ui` parity test still passes.

## Out of scope
The workspace shell, home page, forms and tables (later phases of the UI pass; they pick up the new green palette automatically but are not reviewed here), a Workspace logo design, dark and light variants of the login (it is always dark), moving Synapse's login onto `LoginLayout`, the Microsoft button in Synapse.

## Depends on
workspace-web 06 (merged), synapse-web login as it is on `main`.
