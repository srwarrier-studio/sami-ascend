# synapse-web/11 premium-look

## Goal
The whole Synapse app feels as premium as the new login page: the same deep navy and blue-white language, depth, hairline borders and refined type, in light and dark mode. Experimental: if the owner does not like it the branch is abandoned and nothing else changes.

## Behavior
- Opt-in: `UiProvider` gets a `look` prop (`standard` default, `premium`) that sets `data-look` on the root. Only synapse-web passes `premium`; workspace-web and the kitchen sink stay `standard` and unchanged.
- Palette: a `midnight` palette (brand blue from the login `#3b6fe0`, a navy `dark` scale and a cool blue-grey `gray` scale) used by `look="premium"`. The `teal` preset and the others stay.
- Surfaces:
  - dark mode canvas is a deep navy gradient, cards and bars are slightly lighter navy with a one-pixel light-blue hairline border and a soft shadow;
  - light mode canvas is a cool off-white, cards are white with a hairline border and a layered, very soft shadow;
  - the top bar and the page bar are glass-like (translucent, no heavy blur: nothing animated sits behind them).
- Type and spacing: slightly tighter letter-spacing on headings, KPI numbers larger and lighter-weight, uppercase small labels spaced out, more breathing room inside cards.
- Accents: the primary button, active tab and focus ring use the brand blue; pulses and highlights use the blue-white from the login. Chart series colours are refined to read well on navy and on white.
- Motion stays subtle (no rise-up entrance); hover lifts are small. Minimal motion still removes all animation.
- Covers every Synapse screen: login (unchanged), company picker, boards, widget drawer, preset tab, reports, AI Mode, save-board modal, notifications, the PDF frame.
- The PDF export keeps a clean white sheet regardless of the look.

## Acceptance cases
- With `look="premium"` the root carries `data-look="premium"`; with the default it does not.
- Existing tests pass unchanged; workspace-web tests and the kitchen sink are not affected.
- Contrast: text and the primary button keep 4.5:1 in both modes (tested for the `midnight` palette, as for the other presets).
- No inline styles and no new dependency.
- The owner walks through every Synapse screen in light and dark and approves, or the phase is abandoned.

## Out of scope
New widgets or layout changes, a theme switcher for users, restyling workspace-web, animation beyond what exists, real logos.

## Depends on
synapse-web 10 (the login page sets the language), shared ui-soft-theme.
